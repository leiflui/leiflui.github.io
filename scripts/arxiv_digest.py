"""Collect a completed week's arXiv metadata and publish a keyword-based digest."""

import argparse
from datetime import date, datetime, time as day_time, timedelta, timezone
import html
import json
import os
from pathlib import Path
import re
import sys
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

if __package__:
    from . import arxiv_reviews
else:
    import arxiv_reviews


ROOT = Path(__file__).resolve().parents[1]
NS = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}
API = "https://export.arxiv.org/api/query"
PAGE_SIZE = 200
MAX_RECORDS = 5000


def read_preferences(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for name in ["categories", "topics", "exclude_keywords"]:
        if not isinstance(data.get(name), list):
            raise ValueError(f"{name} must be a list")
    if not data["categories"] or any(not isinstance(c, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9.-]*", c) for c in data["categories"]):
        raise ValueError("Choose at least one valid arXiv category")
    if not data["topics"]:
        raise ValueError("Choose at least one topic")
    for topic in data["topics"]:
        if not isinstance(topic, dict) or not isinstance(topic.get("name"), str) or not topic["name"].strip():
            raise ValueError("Each topic needs a name")
        if not isinstance(topic.get("keywords"), list) or not topic["keywords"]:
            raise ValueError("Each topic needs at least one keyword")
        if any(not isinstance(k, str) or not k.strip() for k in topic["keywords"]):
            raise ValueError("Topic keywords must be non-empty strings")
    flags = data.setdefault("author_flags", {})
    if not isinstance(flags, dict):
        raise ValueError("author_flags must contain collaborator and notable-author lists")
    aliases = data.get("author_aliases", {})
    if not isinstance(aliases, dict) or any(not isinstance(name, str) or not name.strip() for name in aliases):
        raise ValueError("author_aliases must map author names to lists of alternate spellings")
    for values in [data["exclude_keywords"], flags.get("collaborators", []), flags.get("notable_authors", []), *aliases.values()]:
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError("Excluded keywords, author names and aliases must be lists of non-empty strings")
    if type(data.get("include_flagged_authors")) is not bool:
        raise ValueError("include_flagged_authors must be true or false")
    if type(data.get("max_papers")) is not int or not 1 <= data["max_papers"] <= 100:
        raise ValueError("max_papers must be between 1 and 100")
    ZoneInfo(data["timezone"])
    arxiv_reviews.options(data)
    return data


def week_window(now, zone, ending=None):
    local = now.astimezone(zone)
    end_date = date.fromisoformat(ending) if ending else local.date() - timedelta(days=(local.weekday() - 1) % 7)
    if end_date.weekday() != 1:
        raise ValueError("The week-ending date must be a Tuesday")
    end = datetime.combine(end_date, day_time.min, tzinfo=zone)
    if end > local:
        raise ValueError("The selected week has not finished yet")
    return end - timedelta(days=7), end


def instant(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("arXiv metadata contains a timestamp without a timezone")
    return parsed


def parse_feed(raw):
    try:
        root = ET.fromstring(raw)
        total = int(root.findtext("o:totalResults", default="-1", namespaces=NS))
        start = int(root.findtext("o:startIndex", default="-1", namespaces=NS))
        if total < 0 or start < 0:
            raise ValueError("Missing pagination metadata")
        papers = []
        for entry in root.findall("a:entry", NS):
            get = lambda name: " ".join(entry.findtext("a:" + name, default="", namespaces=NS).split())
            path = urlsplit(get("id")).path
            match = re.fullmatch(r"/abs/((?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7}))(?:v(\d+))?", path)
            if not match:
                raise ValueError("arXiv returned an error or an unrecognised paper ID")
            published, updated = get("published"), get("updated")
            instant(published)
            instant(updated)
            title, abstract = get("title"), get("summary")
            if not title or not abstract:
                raise ValueError("arXiv returned incomplete title or abstract metadata")
            identifier = match[1]
            version = int(match[2] or 1)
            authors = [" ".join(author.findtext("a:name", default="", namespaces=NS).split()) for author in entry.findall("a:author", NS)]
            papers.append({"id": identifier, "version": version, "title": title, "abstract": abstract,
                           "authors": authors, "published": published, "updated": updated,
                           "categories": [item.attrib["term"] for item in entry.findall("a:category", NS)],
                           "url": f"https://arxiv.org/abs/{identifier}v{version}",
                           "pdf_url": f"https://arxiv.org/pdf/{identifier}v{version}"})
        return total, start, papers
    except (ET.ParseError, KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid arXiv feed: {error}") from error


def fetch_page(query, start):
    params = {"search_query": query, "start": start, "max_results": PAGE_SIZE,
              "sortBy": "lastUpdatedDate", "sortOrder": "descending"}
    request = Request(API + "?" + urlencode(params), headers={
        "User-Agent": "LeifsWeeklyArxivDigest/1.0 (https://leiflui.github.io/arxiv-digest/)",
        "Accept": "application/atom+xml"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=60) as response:
                raw = response.read(10_000_001)
            if len(raw) > 10_000_000:
                raise ValueError("arXiv response exceeded the 10 MB limit")
            return parse_feed(raw)
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise ValueError(f"arXiv HTTP {error.code}; previous digests have been preserved") from error
        except (URLError, TimeoutError, OSError) as error:
            if attempt == 2:
                raise ValueError("arXiv is temporarily unavailable; previous digests have been preserved") from error
        time.sleep(3 * (attempt + 1))


def collect(preferences, start, end, fetch=fetch_page, sleep=time.sleep):
    query = "(" + " OR ".join("cat:" + category for category in preferences["categories"]) + ")"
    papers, scanned, offset, requests = {}, 0, 0, 0
    while offset < MAX_RECORDS:
        if requests:
            sleep(3)
        total, returned_start, batch = fetch(query, offset)
        requests += 1
        if returned_start != offset:
            raise ValueError("arXiv returned an unexpected result page; no digest was written")
        if not batch and offset < total:
            raise ValueError("arXiv returned an incomplete result page; no digest was written")
        dates = [instant(p["updated"]) for p in batch]
        if dates != sorted(dates, reverse=True):
            raise ValueError("arXiv results were not sorted by update date; no digest was written")
        scanned += len(batch)
        for paper in batch:
            if start <= instant(paper["updated"]) < end:
                old = papers.get(paper["id"])
                if old is None or paper["version"] > old["version"]:
                    papers[paper["id"]] = paper
        offset += len(batch)
        if not batch or offset >= total or min(dates) < start:
            return list(papers.values()), {"requests": requests, "records_scanned": scanned,
                                          "papers_in_window": len(papers), "categories": preferences["categories"]}
    raise ValueError(f"Stopped at the {MAX_RECORDS}-record scan limit before completing the week; narrow the categories")


def normal(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[-‐‑‒–—−]", " ", value).split())


def contains(text, phrase):
    return bool(re.search(r"(?<!\w)" + re.escape(normal(phrase)) + r"(?!\w)", normal(text)))


def author_name(value):
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    parts = re.sub(r"[^\w\s]", " ", "".join(c for c in decomposed if not unicodedata.combining(c))).split()
    return " ".join(part for i, part in enumerate(parts) if not (0 < i < len(parts) - 1 and len(part) == 1))


def select_papers(papers, preferences, start):
    matches, excluded = [], 0
    names_by_flag = {}
    for kind in ["collaborators", "notable_authors"]:
        names_by_flag[kind] = {
            name: {author_name(spelling) for spelling in [name, *preferences.get("author_aliases", {}).get(name, [])]}
            for name in preferences["author_flags"].get(kind, [])
        }
    for original in papers:
        paper = original.copy()
        text = paper["title"] + " " + paper["abstract"]
        if any(contains(text, phrase) for phrase in preferences["exclude_keywords"]):
            excluded += 1
            continue
        matched_topics, title_topics = [], []
        for topic in preferences["topics"]:
            if any(contains(text, keyword) for keyword in topic["keywords"]):
                matched_topics.append(topic["name"])
                if any(contains(paper["title"], keyword) for keyword in topic["keywords"]):
                    title_topics.append(topic["name"])
        author_set = {author_name(name) for name in paper["authors"]}
        flags = {kind: [name for name, spellings in names.items() if author_set & spellings]
                 for kind, names in names_by_flag.items()}
        if not matched_topics and not (preferences["include_flagged_authors"] and any(flags.values())):
            continue
        paper.update(topics=matched_topics, title_topics=title_topics, author_flags=flags,
                     score=len(matched_topics) + len(title_topics),
                     kind="New paper" if instant(paper["published"]) >= start else "Updated paper",
                     match_reason="Topic match" if matched_topics else "Flagged author; no topic keyword matched")
        matches.append(paper)
    matches.sort(key=lambda p: (-p["score"], -instant(p["updated"]).timestamp(), p["id"]))
    return matches, excluded


def escaped(value):
    # arXiv text must not become HTML or a Liquid template when Jekyll renders it.
    return html.escape(str(value)).replace("{", "&#123;").replace("}", "&#125;")


def render_body(snapshot):
    start, end = snapshot["window_start"], snapshot["window_end"]
    first_day = instant(start).strftime("%d %b %Y")
    last_day = (instant(end) - timedelta(days=1)).strftime("%d %b %Y")
    zone_label = "Hong Kong time" if snapshot.get("timezone", "Asia/Hong_Kong") == "Asia/Hong_Kong" else snapshot["timezone"]
    selected = snapshot["papers"][:snapshot["max_papers"]]
    notice = ('AI reviews are preliminary assessments of extracted text, not peer review or an independent correctness check.'
              if snapshot.get("ai_reviews", {}).get("completed") else
              'This issue uses metadata matching; no full-paper scientific assessment is claimed.')
    lines = [f'<div class="arxiv-digest"><p class="arxiv-kicker">Weekly research watch</p>',
             f'<p>Coverage: <time>{first_day}</time>–<time>{last_day}</time> ({escaped(zone_label)}).</p>',
             f'<p class="arxiv-notice">Selection uses titles, abstracts and configured author flags. {notice}</p>']
    if snapshot["demo"]:
        lines.append('<p class="arxiv-notice"><strong>SYNTHETIC DEMO.</strong> Paper records are fictional examples, not research recommendations.</p>')
    counts = snapshot["coverage"]
    lines.append(f'<p>{len(snapshot["papers"])} matches from {counts["papers_in_window"]} unique papers in the window; {snapshot["excluded"]} excluded by keyword. Showing {len(selected)}. All matches are available in the JSON download.</p>')
    reviews = snapshot.get("ai_reviews")
    if reviews:
        lines.append('<h2>AI paper reviews</h2>')
        lines.append(f'<p>{reviews["completed"]} of {reviews["requested"]} shortlisted papers have an AI summary; {reviews["quality_assessed"]} have a scientific assessment. Rankings compare only these reviewed papers, not every match. Ties retain the keyword shortlist order.</p>')
        if reviews["completed"]:
            lines.append('<p>Relevance and scientific strength are scored separately from 1 to 5. Scientific strength is a preliminary AI judgement of the evidence in extracted text, not peer review or an independent correctness check. Figures are not visually inspected. Author reputation does not determine this score.</p>')
            for field, heading in [("relevance_rank", "Ranked by relevance"), ("quality_rank", "Ranked by scientific strength")]:
                ranked = sorted([p for p in selected if field in p.get("ai_review", {})],
                                key=lambda p: p["ai_review"][field])
                lines.append(f'<details><summary>{heading}</summary><ol>')
                for paper in ranked:
                    lines.append(f'<li><a href="#paper-{escaped(paper["id"])}">{escaped(paper["title"])}</a></li>')
                lines.append('</ol></details>')
        if reviews["completed"] < reviews["requested"]:
            lines.append('<p>Some AI reviews are unavailable. Those papers retain their keyword matches and abstracts; no scientific score is inferred from missing text or service availability.</p>')
    for kind in ["New paper", "Updated paper"]:
        group = [paper for paper in selected if paper["kind"] == kind]
        lines.append(f'<h2>{"New papers" if kind == "New paper" else "Notable updates"} <span class="arxiv-count">{len(group)}</span></h2>')
        if not group:
            lines.append('<p>No matching papers in this section for the period searched.</p>')
        for paper in group:
            heading = escaped(paper["title"]) if snapshot["demo"] else f'<a href="{escaped(paper["url"])}">{escaped(paper["title"])}</a>'
            links = '<p>Paper links are disabled in this synthetic demo.</p>' if snapshot["demo"] else f'<p><a href="{escaped(paper["url"])}">arXiv abstract</a> · <a href="{escaped(paper["pdf_url"])}">PDF at arXiv</a></p>'
            lines.extend(['<article class="arxiv-card">', f'<h3 id="paper-{escaped(paper["id"])}">{heading}</h3>',
                          '<p class="arxiv-authors">' + escaped(", ".join(paper["authors"])) + '</p>',
                          '<p class="arxiv-badges">'])
            for topic in paper["topics"]:
                lines.append(f'<span class="arxiv-badge">{escaped(topic)}</span>')
            for key, label in [("collaborators", "Collaborator"), ("notable_authors", "Notable author")]:
                for name in paper["author_flags"][key]:
                    lines.append(f'<span class="arxiv-badge arxiv-{key}">{label}: {escaped(name)}</span>')
            lines.extend(['</p>', f'<p class="arxiv-meta">{escaped(paper["id"])}v{paper["version"]} · {escaped(", ".join(paper["categories"]))}</p>',
                          f'<p class="arxiv-meta">First submitted: {instant(paper["published"]).astimezone(timezone.utc).strftime("%d %b %Y")} · Last updated: {instant(paper["updated"]).astimezone(timezone.utc).strftime("%d %b %Y")} (UTC)</p>',
                          f'<p><strong>Why included:</strong> {escaped(paper["match_reason"])}. '
                          + escaped("; ".join(paper["topics"])) + '</p>',
                          f'<details><summary>Read the author-provided abstract</summary><p>{escaped(paper["abstract"])}</p></details>',
                          links])
            review = paper.get("ai_review")
            if review:
                quality = "Not assessed" if review["quality_score"] is None else f'{review["quality_score"]}/5 · rank {review["quality_rank"]}'
                source_link = escaped(review["source"]) if snapshot["demo"] else f'<a href="{escaped(review["source_url"])}">{escaped(review["source"])}</a>'
                lines.extend(['<div class="arxiv-review">',
                              '<h4>AI summary and assessment</h4>',
                              f'<p>{escaped(review["summary"])}</p>',
                              f'<p><strong>Relevance:</strong> {review["relevance_score"]}/5 · rank {review["relevance_rank"]}. {escaped(review["relevance_reason"])}</p>',
                              f'<p><strong>Scientific strength:</strong> {escaped(quality)}. {escaped(review["quality_reason"])}</p>',
                              f'<p><strong>Limitations:</strong> {escaped(review["limitations"])}</p>',
                              f'<p class="arxiv-meta">Source: {source_link} · Confidence: {escaped(review["confidence"])} · Model: {escaped(review["model"])}</p>'])
                if review["evidence_quote"]:
                    lines.append(f'<details><summary>Evidence cited by the review</summary><blockquote>{escaped(review["evidence_quote"])}</blockquote><p>{escaped(review["evidence_location"])}</p></details>')
                lines.append('</div>')
            lines.append('</article>')
    lines.extend(['<h2>How this issue was selected</h2>',
                  '<p>Topics: ' + escaped("; ".join(snapshot["topics"])) + '.</p>',
                  '<p>Categories: ' + escaped(", ".join(counts["categories"])) + '.</p>',
                  '<p>Title matches receive two points per topic; abstract-only matches receive one. This ranks keyword relevance, not quality. Author flags mark configured names and can include an otherwise unmatched paper within these categories. Excluded keywords take precedence. Name matching includes configured aliases and ignores accents, punctuation, case and optional middle initials; first initials are not expanded to full names.</p>',
                  f'<p>Read {counts["records_scanned"]} API records across {counts["requests"]} requests. Cross-listed papers are merged by arXiv ID. A revision can appear in a later issue as an update. API indexing delays may move or omit records around the window boundaries.</p>',
                  '<p>Source: <a href="https://arxiv.org/">arXiv</a>. This independent digest is not affiliated with or endorsed by arXiv. PDFs remain hosted by arXiv.</p>', '</div>'])
    return "\n".join(lines)


def make_snapshot(preferences, papers, coverage, start, end, now, demo=False):
    matches, excluded = select_papers(papers, preferences, start)
    return {"title": preferences["title"], "timezone": preferences["timezone"], "issue": end.date().isoformat(), "generated_at": now.isoformat(),
            "window_start": start.isoformat(), "window_end": end.isoformat(), "demo": demo,
            "topics": [topic["name"] for topic in preferences["topics"]], "max_papers": preferences["max_papers"],
            "excluded": excluded, "coverage": coverage, "papers": matches}


def atomic_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def publish(root, snapshot):
    if snapshot["demo"]:
        raise ValueError("Synthetic demo records cannot be published as real issues")
    root = Path(root)
    index_path = root / "_data/arxiv_digest.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {"issues": []}
    if not isinstance(index, dict) or not isinstance(index.get("issues"), list):
        raise ValueError("Existing digest index is invalid; refusing to replace it")
    issue = snapshot["issue"]
    page_path = root / f"_pages/arxiv-digest/{issue}.html"
    json_path = root / f"files/arxiv-digest/{issue}.json"
    front = '---\nlayout: single\ntitle: ' + json.dumps("arXiv digest · " + issue) + f'\npermalink: /arxiv-digest/{issue}/\nauthor_profile: true\n---\n'
    body = '{% include arxiv-digest-style.html %}\n<p><a href="{{ \'/arxiv-digest/\' | relative_url }}">All weekly digests</a></p>\n'
    body += f'<p><a href="{{{{ \'/files/arxiv-digest/{issue}.json\' | relative_url }}}}">Download all matches as JSON</a></p>\n'
    body += render_body(snapshot) + "\n"
    metadata = {"date": issue, "url": f"/arxiv-digest/{issue}/", "count": len(snapshot["papers"]),
                "displayed": min(len(snapshot["papers"]), snapshot["max_papers"]),
                "window_start": snapshot["window_start"], "window_end": snapshot["window_end"]}
    index["issues"] = sorted([item for item in index["issues"] if item["date"] != issue] + [metadata],
                             key=lambda item: item["date"], reverse=True)
    # The index is replaced last, after both linked files exist.
    atomic_text(page_path, front + body)
    atomic_text(json_path, json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    atomic_text(index_path, json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    return page_path


def preview(root, snapshot):
    directory = Path(root) / "local" / ("arxiv-demo" if snapshot["demo"] else "arxiv-preview")
    css = (ROOT / "assets/css/arxiv-digest.css").read_text()
    document = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    document += '<title>' + escaped(snapshot["title"]) + '</title><style>body{margin:0;background:#f8fafb;color:#27343f;font:17px/1.6 Georgia,serif}main{max-width:900px;margin:auto;padding:36px 20px}a{color:#006b82}h1,h2,h3{font-family:system-ui,sans-serif}' + css + '</style></head><body><main>'
    document += '<h1>' + escaped(snapshot["title"]) + '</h1>' + render_body(snapshot) + '</main></body></html>'
    atomic_text(directory / "index.html", document)
    atomic_text(directory / "digest.json", json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    return directory / "index.html"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preferences", type=Path, default=ROOT / "_data/arxiv_preferences.json")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--week-ending", help="Completed Tuesday boundary in the configured timezone, YYYY-MM-DD")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true", help="Offline synthetic preview; does not alter public pages")
    mode.add_argument("--preview", action="store_true", help="Live local preview; does not alter public pages")
    args = parser.parse_args()
    try:
        preferences = read_preferences(args.preferences)
        now = datetime.now(ZoneInfo(preferences["timezone"]))
        start, end = week_window(now, now.tzinfo, "2026-10-20" if args.demo else args.week_ending)
        if args.demo:
            preferences = {**preferences, "author_flags": {"collaborators": ["Example Collaborator"], "notable_authors": ["Example Notable Author"]}}
            _, _, papers = parse_feed((ROOT / "tests/fixtures/arxiv_feed.xml").read_bytes())
            papers = [p for p in papers if start <= instant(p["updated"]) < end]
            coverage = {"requests": 0, "records_scanned": len(papers), "papers_in_window": len(papers), "categories": preferences["categories"]}
        else:
            papers, coverage = collect(preferences, start, end)
        snapshot = make_snapshot(preferences, papers, coverage, start, end, now, args.demo)
        if not args.demo:
            cache_path = args.root / f'files/arxiv-digest/{snapshot["issue"]}.json'
            try:
                previous = json.loads(cache_path.read_text()) if cache_path.exists() else None
            except (OSError, ValueError):
                previous = None
            arxiv_reviews.enrich(snapshot, preferences, os.environ.get("OPENROUTER_API_KEY"), previous)
            if snapshot.get("ai_reviews"):
                print("AI reviews: " + snapshot["ai_reviews"]["status"])
        result = preview(args.root, snapshot) if args.demo or args.preview else publish(args.root, snapshot)
        print(f"Digest ready: {result.resolve()} ({len(snapshot['papers'])} matches; {coverage['requests']} arXiv requests)")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"arXiv digest failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
