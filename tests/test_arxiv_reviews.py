from datetime import datetime
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError
from zoneinfo import ZoneInfo

from scripts import arxiv_digest as digest
from scripts import arxiv_reviews as reviews


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


def fill(data, previous=None, preferences=None, **overrides):
    def produce(*args):
        return {**review(), "model": reviews.DEFAULT_MODEL, "source": SOURCE["kind"],
                "source_url": args[0]["url"].replace("/abs/", "/html/")}
    defaults = {"source_fetch": Mock(return_value=SOURCE), "model_fetch": Mock(return_value=1_000_000),
                "review_fetch": Mock(side_effect=produce), "sleep": lambda _: None}
    defaults.update(overrides)
    reviews.enrich(data, preferences or settings(), "synthetic-test-key",
                   previous=previous, **defaults)
    return defaults


class SourceAndCostTests(unittest.TestCase):
    def test_paid_models_and_unbounded_review_counts_are_rejected(self):
        for change in [{"model": "paid/model"}, {"max_papers": 11}, {"max_papers": True}]:
            preferences = settings()
            preferences["ai_review"].update(change)
            with self.assertRaises(ValueError):
                reviews.options(preferences)

    def test_model_catalog_must_confirm_zero_pricing(self):
        model = {"id": reviews.DEFAULT_MODEL, "context_length": 262144,
                 "pricing": {"prompt": "0", "completion": "0"}}
        fetch = lambda *args: json.dumps({"data": [model]}).encode()
        self.assertEqual(reviews.free_model(model["id"], fetch), 262144)
        model["pricing"]["request"] = "0.001"
        with self.assertRaises(ValueError):
            reviews.free_model(model["id"], fetch)
        with self.assertRaises(ValueError):
            reviews.free_model("missing:free", fetch)

    def test_html_extraction_preserves_math_and_ignores_navigation_and_scripts(self):
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

    def test_source_uses_complete_html_without_fetching_pdf(self):
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

    def test_inference_has_zero_price_cap_no_plugins_and_no_model_fallback(self):
        response = {"model": reviews.DEFAULT_MODEL, "choices": [
            {"finish_reason": "stop", "message": {"content": json.dumps(review())}}]}
        fetch = Mock(return_value=json.dumps(response).encode())
        reviews.request_review(snapshot()["papers"][0], ["Self-force"], SOURCE,
                               reviews.DEFAULT_MODEL, 1_000_000, "synthetic-test-key", fetch=fetch)
        payload = fetch.call_args.kwargs["payload"]
        self.assertEqual(payload["provider"]["max_price"], {"prompt": 0, "completion": 0, "request": 0})
        self.assertEqual(payload["plugins"], [])
        self.assertNotIn("models", payload)
        self.assertNotIn("tools", payload)
        fetch.reset_mock()
        for model, context in [("paid/model", 1_000_000), (reviews.DEFAULT_MODEL, 10)]:
            with self.assertRaises(ValueError):
                reviews.request_review(snapshot()["papers"][0], [], SOURCE, model, context, "synthetic-test-key", fetch=fetch)
        fetch.assert_not_called()


class ReviewAndCacheTests(unittest.TestCase):
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

    def test_missing_key_and_demo_make_no_service_calls(self):
        for demo in [False, True]:
            data = snapshot()
            data["demo"] = demo
            call = Mock(side_effect=AssertionError("Unexpected service call"))
            reviews.enrich(data, settings(), None, model_fetch=call, source_fetch=call, review_fetch=call)
            call.assert_not_called()
            if not demo:
                self.assertEqual(data["ai_reviews"]["completed"], 0)

    def test_successful_reruns_reuse_cache_and_changed_topics_invalidate_it(self):
        previous = snapshot()
        fill(previous)
        data = snapshot()
        call = Mock(side_effect=AssertionError("Cached review should not call a service"))
        fill(data, previous=previous, model_fetch=call, source_fetch=call, review_fetch=call)
        self.assertEqual(data["ai_reviews"]["completed"], 2)
        self.assertEqual(data["ai_reviews"]["requests"], 0)
        call.assert_not_called()
        preferences = settings()
        preferences["topics"][0]["keywords"].append("new research interest")
        data = snapshot()
        spies = fill(data, previous=previous, preferences=preferences)
        self.assertEqual(spies["review_fetch"].call_count, 2)

    def test_quota_or_model_failure_does_not_destroy_the_digest(self):
        for failure in [HTTPError("https://openrouter.ai", 429, "Quota", {}, None),
                        ValueError("Invalid model response")]:
            data = snapshot()
            before = [paper["id"] for paper in data["papers"]]
            fill(data, review_fetch=Mock(side_effect=failure))
            self.assertEqual(before, [paper["id"] for paper in data["papers"]])
            self.assertEqual(data["ai_reviews"]["completed"], 0)
            self.assertIn("Some AI reviews are unavailable", digest.render_body(data))
        call = Mock(side_effect=AssertionError("Unverified model must not be called"))
        data = snapshot()
        fill(data, model_fetch=Mock(side_effect=ValueError("Price not zero")), review_fetch=call)
        call.assert_not_called()

    def test_relevance_and_quality_rank_independently(self):
        values = [review(), {**review(), "relevance_score": 2, "quality_score": 5}]
        def produce(*args):
            return {**values.pop(0), "source": SOURCE["kind"], "source_url": args[0]["url"].replace("/abs/", "/html/"),
                    "model": reviews.DEFAULT_MODEL}
        data = snapshot()
        fill(data, review_fetch=produce)
        first, second = data["papers"][:2]
        self.assertEqual(first["ai_review"]["relevance_rank"], 1)
        self.assertEqual(second["ai_review"]["quality_rank"], 1)
        first["ai_review"]["summary"] = '<script>unsafe</script> {{ site.secret }}'
        rendered = digest.render_body(data)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("{{ site.secret }}", rendered)
        self.assertIn("Ranked by relevance", rendered)
        self.assertIn("Ranked by scientific strength", rendered)

    def test_invalid_cache_and_time_budget_keep_unreviewed_papers(self):
        data = snapshot()
        fill(data, previous={"papers": None}, clock=Mock(side_effect=[0, 600]))
        self.assertEqual(len(data["papers"]), 2)
        self.assertEqual(data["ai_reviews"]["completed"], 0)


if __name__ == "__main__":
    unittest.main()
