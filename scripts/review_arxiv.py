"""Prepare paper text for ChatGPT/Codex, or import its completed reviews. No model API is used."""

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys
import time

if __package__:
    from . import arxiv_digest as digest, arxiv_reviews as reviews
else:
    import arxiv_digest as digest
    import arxiv_reviews as reviews


def prepare(root, snapshot, preferences, source_fetch=reviews.fetch_source, sleep=time.sleep):
    directory = Path(root) / "local/arxiv-review" / snapshot["issue"]
    manifest = {"issue": snapshot["issue"], "instructions": reviews.PROMPT, "papers": []}
    path = reviews.review_path(root, snapshot["issue"])
    reviews.enrich(snapshot, preferences, json.loads(path.read_text()) if path.exists() else None)
    count = min(snapshot["max_papers"], reviews.options(preferences)["max_papers"])
    for number, paper in enumerate(snapshot["papers"][:count], 1):
        if paper.get("ai_review"):
            continue
        if manifest["papers"]:
            sleep(3)
        name = f"{number:02}.json"
        source = source_fetch(paper)
        packet = {"id": paper["id"], "version": paper["version"], "title": paper["title"],
                  "fingerprint": reviews.fingerprint(paper, preferences),
                  "topics": [topic["name"] for topic in preferences["topics"]],
                  "assess_scientific_strength": source["kind"] in {"HTML paper text", "PDF paper text"},
                  "source": source}
        digest.atomic_text(directory / name, json.dumps(packet, indent=2, ensure_ascii=False) + "\n")
        manifest["papers"].append({"id": paper["id"], "file": name})
    digest.atomic_text(directory / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return directory


def import_reviews(root, snapshot, preferences, incoming):
    if (not isinstance(incoming, dict) or incoming.get("issue") != snapshot["issue"]
            or not isinstance(incoming.get("reviews"), list) or not incoming["reviews"]):
        raise ValueError("Provide the issue date and a non-empty reviews list")
    directory = Path(root) / "local/arxiv-review" / snapshot["issue"]
    candidates = snapshot["papers"][:min(snapshot["max_papers"], reviews.options(preferences)["max_papers"])]
    positions = {paper["id"]: (number, paper) for number, paper in enumerate(candidates, 1)}
    accepted = {}
    for entry in incoming["reviews"]:
        if not isinstance(entry, dict) or entry.get("id") not in positions or entry["id"] in accepted:
            raise ValueError("Review must identify a unique shortlisted paper")
        number, paper = positions[entry["id"]]
        packet = json.loads((directory / f"{number:02}.json").read_text())
        fingerprint = reviews.fingerprint(paper, preferences)
        if packet.get("id") != paper["id"] or packet.get("fingerprint") != fingerprint or entry.get("fingerprint") != fingerprint:
            raise ValueError("Paper or preferences changed; prepare and review it again")
        source = packet["source"]
        result = reviews.validate_review(entry, source)
        result.update(id=paper["id"], fingerprint=fingerprint, model=entry.get("model"),
                      source=source["kind"], source_url=source["url"],
                      generated_at=datetime.now(timezone.utc).isoformat())
        accepted[paper["id"]] = result
    path = reviews.review_path(root, snapshot["issue"])
    document = json.loads(path.read_text()) if path.exists() else {"issue": snapshot["issue"], "reviews": []}
    # Validate existing records before merging; all checks finish before public files change.
    reviews.enrich(snapshot, preferences, document)
    for old in document["reviews"]:
        if old["id"] not in accepted:
            accepted[old["id"]] = old
    document = {"issue": snapshot["issue"], "reviews": list(accepted.values())}
    reviews.enrich(snapshot, preferences, document)
    digest.atomic_text(path, json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    return digest.publish(root, snapshot)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=digest.ROOT)
    parser.add_argument("action", choices=["prepare", "import"])
    parser.add_argument("--issue", help="Issue date; defaults to the newest published issue")
    parser.add_argument("--reviews", type=Path, help="JSON written by ChatGPT/Codex for import")
    args = parser.parse_args()
    try:
        issue = args.issue
        if issue is None:
            issue = json.loads((args.root / "_data/arxiv_digest.json").read_text())["issues"][0]["date"]
        if date.fromisoformat(issue).isoformat() != issue:
            raise ValueError("Issue must use YYYY-MM-DD")
        snapshot = json.loads((args.root / f"files/arxiv-digest/{issue}.json").read_text())
        if snapshot.get("demo") or snapshot.get("issue") != issue:
            raise ValueError("Use a real published issue")
        preferences = digest.read_preferences(args.root / "_data/arxiv_preferences.json")
        if not reviews.options(preferences)["enabled"]:
            raise ValueError("Enable ai_review in the preferences first")
        if args.action == "prepare":
            result = prepare(args.root, snapshot, preferences)
        else:
            if args.reviews is None:
                raise ValueError("Import requires --reviews PATH")
            result = import_reviews(args.root, snapshot, preferences, json.loads(args.reviews.read_text()))
        print(f"Review {args.action} ready: {result.resolve()}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(f"arXiv review failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
