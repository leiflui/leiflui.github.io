from datetime import datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from scripts import arxiv_digest as digest
from scripts import arxiv_reviews as reviews
from scripts import review_arxiv as workflow


ROOT = Path(__file__).resolve().parents[1]
SOURCE = {"kind": "HTML paper text", "text": "The calculation includes an explicit convergence test.",
          "url": "https://arxiv.org/html/2610.00001v1"}


def review():
    return {"summary": "A clearly labelled synthetic test summary.",
            "relevance_score": 5, "relevance_reason": "Directly studies a selected topic.",
            "quality_score": 3, "quality_reason": "Reports an explicit numerical check.",
            "limitations": "The derivation and figures have not been independently verified.",
            "confidence": "moderate", "evidence_quote": "an explicit convergence test",
            "evidence_location": "Synthetic test text"}


def settings():
    preferences = digest.read_preferences(ROOT / "_data/arxiv_preferences.json")
    preferences["ai_review"]["max_papers"] = 2
    return preferences


def snapshot():
    preferences = settings()
    now = datetime(2026, 10, 22, 12, tzinfo=ZoneInfo("Asia/Hong_Kong"))
    start, end = digest.week_window(now, now.tzinfo)
    records = digest.parse_feed((ROOT / "tests/fixtures/arxiv_feed.xml").read_bytes())[2]
    return digest.make_snapshot(preferences, records, {"requests": 1, "records_scanned": 4,
        "papers_in_window": 4, "categories": preferences["categories"]}, start, end, now)


def document(data):
    return {"issue": data["issue"], "reviews": [
        {**review(), "id": paper["id"], "fingerprint": reviews.fingerprint(paper, settings()),
         "model": "Synthetic test model", "source": SOURCE["kind"],
         "source_url": paper["url"].replace("/abs/", "/html/"), "generated_at": data["generated_at"]}
        for paper in data["papers"][:2]]}


class SourceTests(unittest.TestCase):
    def test_unbounded_review_counts_and_invalid_enabled_are_rejected(self):
        for change in [{"max_papers": 11}, {"max_papers": True}, {"enabled": "true"}]:
            preferences = settings()
            preferences["ai_review"].update(change)
            with self.assertRaises(ValueError):
                reviews.options(preferences)

    def test_html_preserves_math_and_ignores_navigation_and_scripts(self):
        parser = reviews.PaperHTML()
        parser.feed('<nav>Site menu</nav><article class="ltx_document"><h1>Paper</h1>'
                    '<p>Equation <math alttext="x^2">duplicate math</math>.</p>'
                    '<p>MathML fallback <math><mi>z</mi></math>.</p>'
                    '<script>ignore this</script></article><footer>Site footer</footer>')
        self.assertIn("x^2", parser.text())
        self.assertIn("z", parser.text())
        for value in ["Site menu", "duplicate math", "ignore this", "Site footer"]:
            self.assertNotIn(value, parser.text())
        incomplete = reviews.PaperHTML()
        incomplete.feed('<article class="ltx_document">incomplete')
        self.assertEqual(incomplete.text(), "")

    def test_complete_html_needs_no_pdf(self):
        paper = snapshot()["papers"][0]
        raw = ('<article class="ltx_document"><p>' + "Scientific body text. " * 200 + '</p></article>').encode()
        fetch = Mock(return_value=raw)
        source = reviews.fetch_source(paper, fetch=fetch, sleep=lambda _: None)
        self.assertEqual(source["kind"], "HTML paper text")
        self.assertEqual(fetch.call_count, 1)

    def test_unreadable_or_oversized_text_falls_back_to_labelled_abstract(self):
        paper = snapshot()["papers"][0]
        fetch = Mock(side_effect=OSError("Unavailable"))
        source = reviews.fetch_source(paper, fetch=fetch, sleep=lambda _: None)
        self.assertTrue(source["kind"].startswith("Abstract only"))
        self.assertEqual(source["text"], paper["abstract"])
        raw = ('<article class="ltx_document">' + "x" * (reviews.MAX_TEXT_BYTES + 1) + '</article>').encode()
        source = reviews.fetch_source(paper, fetch=Mock(return_value=raw), sleep=lambda _: None)
        self.assertTrue(source["kind"].startswith("Abstract only"))


class ReviewTests(unittest.TestCase):
    def test_quality_needs_full_text_and_verbatim_evidence(self):
        for source, change in [(SOURCE, {"evidence_quote": "Invented evidence"}),
                               ({"kind": "Abstract only", "text": SOURCE["text"]}, {}),
                               (SOURCE, {"quality_score": True}),
                               (SOURCE, {"confidence": "high"})]:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    reviews.validate_review({**review(), **change}, source)
        abstract = {**review(), "quality_score": None, "evidence_quote": ""}
        self.assertIsNone(reviews.validate_review(abstract, {"kind": "Abstract only", "text": ""})["quality_score"])
        self.assertNotIn("quality_rank", reviews.validate_review({**review(), "quality_rank": "invented"}, SOURCE))

    def test_attaching_reviews_and_demo_make_no_network_calls(self):
        for demo in [False, True]:
            data = snapshot()
            data["demo"] = demo
            with patch.object(reviews, "read_url", side_effect=AssertionError("Unexpected network call")):
                reviews.enrich(data, settings())
                reviews.enrich(data, settings(), document(data))
            if demo:
                self.assertNotIn("ai_reviews", data)
            else:
                self.assertEqual(data["ai_reviews"]["completed"], 2)

    def test_changed_topics_or_versions_invalidate_stale_reviews(self):
        for changed in ["topics", "version"]:
            data = snapshot()
            old = document(data)
            preferences = settings()
            if changed == "topics":
                preferences["topics"][0]["keywords"].append("new research interest")
            else:
                for paper in data["papers"]:
                    paper["version"] += 1
            reviews.enrich(data, preferences, old)
            self.assertEqual(data["ai_reviews"]["completed"], 0)

    def test_bad_document_duplicate_ids_and_unsafe_source_are_rejected(self):
        data = snapshot()
        valid = document(data)
        for bad in [[], {**valid, "issue": "2026-10-13"},
                    {**valid, "reviews": valid["reviews"] * 2},
                    {**valid, "reviews": [{**valid["reviews"][0], "source_url": "javascript:alert(1)"}]}]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    reviews.enrich(data, settings(), bad)

    def test_relevance_and_quality_rank_independently_and_escape_output(self):
        data = snapshot()
        incoming = document(data)
        incoming["reviews"][1].update(relevance_score=2, quality_score=5)
        incoming["reviews"][0]["summary"] = '<script>unsafe</script> {{ site.secret }}'
        reviews.enrich(data, settings(), incoming)
        first, second = data["papers"][:2]
        self.assertEqual(first["ai_review"]["relevance_rank"], 1)
        self.assertEqual(second["ai_review"]["quality_rank"], 1)
        rendered = digest.render_body(data)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("{{ site.secret }}", rendered)
        self.assertIn("Ranked by relevance", rendered)
        self.assertIn("Ranked by scientific strength", rendered)


class ImportTests(unittest.TestCase):
    def prepare(self, root, data):
        source = lambda paper: {**SOURCE, "url": paper["url"].replace("/abs/", "/html/")}
        return workflow.prepare(root, data, settings(), source_fetch=source, sleep=lambda _: None)

    def test_prepare_import_and_metadata_rerun_preserve_reviews(self):
        data = snapshot()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            packet_directory = self.prepare(root, data)
            self.assertFalse((root / "files").exists())
            self.assertTrue((packet_directory / "manifest.json").exists())
            page = workflow.import_reviews(root, data, settings(), document(data))
            self.assertIn("Ranked by relevance", page.read_text())
            stored = json.loads(reviews.review_path(root, data["issue"]).read_text())
            rerun = snapshot()
            reviews.enrich(rerun, settings(), stored)
            self.assertEqual(rerun["ai_reviews"]["completed"], 2)
            self.assertEqual(stored["reviews"][0]["model"], "Synthetic test model")
            fetch = Mock(side_effect=AssertionError("Unchanged reviews must not fetch papers again"))
            workflow.prepare(root, rerun, settings(), source_fetch=fetch)
            self.assertEqual(json.loads((packet_directory / "manifest.json").read_text())["papers"], [])
            fetch.assert_not_called()

    def test_invalid_quote_or_fingerprint_changes_no_public_files(self):
        data = snapshot()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root, data)
            page = digest.publish(root, data)
            before = page.read_text()
            for change in [{"evidence_quote": "Invented evidence"}, {"fingerprint": "stale"}, {"model": ""}]:
                incoming = document(data)
                incoming["reviews"][0].update(change)
                with self.assertRaises(ValueError):
                    workflow.import_reviews(root, data, settings(), incoming)
                self.assertFalse(reviews.review_path(root, data["issue"]).exists())
                self.assertEqual(before, page.read_text())

    def test_partial_import_retains_other_reviews(self):
        data = snapshot()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root, data)
            incoming = document(data)
            workflow.import_reviews(root, data, settings(), incoming)
            incoming["reviews"] = incoming["reviews"][:1]
            incoming["reviews"][0]["summary"] = "Updated synthetic summary."
            workflow.import_reviews(root, data, settings(), incoming)
            stored = json.loads(reviews.review_path(root, data["issue"]).read_text())
            self.assertEqual(len(stored["reviews"]), 2)
            self.assertEqual(stored["reviews"][0]["summary"], "Updated synthetic summary.")

    def test_abstract_only_review_has_no_quality_rank(self):
        data = snapshot()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = lambda paper: {"kind": "Abstract only: unavailable", "text": paper["abstract"], "url": paper["url"]}
            workflow.prepare(root, data, settings(), source_fetch=source, sleep=lambda _: None)
            incoming = document(data)
            for entry in incoming["reviews"]:
                entry.update(quality_score=None, evidence_quote="")
            workflow.import_reviews(root, data, settings(), incoming)
            self.assertEqual(data["ai_reviews"]["quality_assessed"], 0)
            self.assertNotIn("quality_rank", data["papers"][0]["ai_review"])


if __name__ == "__main__":
    unittest.main()
