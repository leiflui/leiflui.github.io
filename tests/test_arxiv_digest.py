import contextlib
from copy import deepcopy
from datetime import datetime, timedelta
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts import arxiv_digest as digest


ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 22, 12, tzinfo=ZoneInfo("Asia/Hong_Kong"))


def settings():
    result = digest.read_preferences(ROOT / "_data/arxiv_preferences.json")
    result["author_flags"] = {"collaborators": ["Example Collaborator"], "notable_authors": ["Example Notable Author"]}
    return result


def papers():
    return digest.parse_feed((ROOT / "tests/fixtures/arxiv_feed.xml").read_bytes())[2]


def snapshot(demo=False):
    start, end = digest.week_window(NOW, NOW.tzinfo)
    return digest.make_snapshot(settings(), papers(), {"requests": 1, "records_scanned": 4,
                                "papers_in_window": 4, "categories": settings()["categories"]}, start, end, NOW, demo)


class FeedAndWindowTests(unittest.TestCase):
    def test_completed_tuesday_week_is_stable_on_manual_reruns(self):
        start, end = digest.week_window(NOW, NOW.tzinfo)
        self.assertEqual(start.isoformat(), "2026-10-13T00:00:00+08:00")
        self.assertEqual(end.isoformat(), "2026-10-20T00:00:00+08:00")
        self.assertEqual((start, end), digest.week_window(NOW + timedelta(days=3), NOW.tzinfo))
        with self.assertRaises(ValueError):
            digest.week_window(NOW, NOW.tzinfo, "2026-10-21")
        with self.assertRaises(ValueError):
            digest.week_window(NOW, NOW.tzinfo, "2026-10-27")

    def test_atom_dates_authors_and_version(self):
        total, offset, records = digest.parse_feed((ROOT / "tests/fixtures/arxiv_feed.xml").read_bytes())
        self.assertEqual((total, offset, len(records)), (4, 0, 4))
        self.assertEqual(records[1]["version"], 2)
        self.assertEqual(records[1]["id"], "2608.00002")
        self.assertEqual(records[1]["authors"], ["Example Notable Author"])
        self.assertEqual(records[1]["categories"], ["astro-ph.HE", "gr-qc"])

    def test_bad_feed_does_not_become_an_empty_success(self):
        for value in [b"<html>maintenance</html>", b"not xml", b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/api/errors</id></entry></feed>']:
            with self.assertRaises(ValueError):
                digest.parse_feed(value)

    def test_pagination_rate_limit_deduplication_and_window(self):
        records = papers()
        start, end = digest.week_window(NOW, NOW.tzinfo)
        newer = deepcopy(records[0])
        newer["updated"] = "2026-10-21T00:00:00Z"
        old = deepcopy(records[3])
        old["id"] = "2609.00005"
        old["updated"] = "2026-10-01T00:00:00Z"
        batches = [[newer, records[0]], [records[0], records[1]], [records[2], records[3], old]]
        offsets = []
        def fetch(query, offset):
            self.assertIn("cat:gr-qc OR cat:astro-ph.HE", query)
            offsets.append(offset)
            return 100, offset, batches[len(offsets) - 1]
        sleeps = []
        found, coverage = digest.collect(settings(), start, end, fetch=fetch, sleep=sleeps.append)
        self.assertEqual(len(found), 4)
        self.assertEqual(offsets, [0, 2, 4])
        self.assertEqual(sleeps, [3, 3])
        self.assertEqual(coverage["requests"], 3)

    def test_incomplete_or_misordered_results_fail(self):
        start, end = digest.week_window(NOW, NOW.tzinfo)
        for batch in [[], list(reversed(papers()))]:
            with self.assertRaises(ValueError):
                digest.collect(settings(), start, end, fetch=lambda query, offset: (100, offset, batch), sleep=lambda seconds: None)


class MatchingTests(unittest.TestCase):
    def test_phrase_boundaries_hyphens_and_abbreviations(self):
        self.assertTrue(digest.contains("Extreme-mass-ratio inspirals", "extreme mass ratio inspirals"))
        self.assertTrue(digest.contains("A GRMHD simulation", "GRMHD"))
        self.assertFalse(digest.contains("stochastic", "TOC"))
        self.assertFalse(digest.contains("notgrmhdword", "GRMHD"))

    def test_topic_match_author_badges_and_updates(self):
        data = snapshot()
        self.assertEqual(len(data["papers"]), 3)
        by_id = {record["id"]: record for record in data["papers"]}
        self.assertEqual(by_id["2608.00002"]["kind"], "Updated paper")
        self.assertEqual(by_id["2610.00001"]["kind"], "New paper")
        self.assertEqual(by_id["2610.00003"]["topics"], [])
        self.assertEqual(by_id["2610.00003"]["author_flags"]["collaborators"], ["Example Collaborator"])
        self.assertIn("Flagged author", by_id["2610.00003"]["match_reason"])

    def test_exclusion_wins_over_author_and_topic(self):
        preferences = settings()
        preferences["exclude_keywords"] = ["Teukolsky"]
        start, _ = digest.week_window(NOW, NOW.tzinfo)
        found, excluded = digest.select_papers(papers(), preferences, start)
        self.assertEqual(excluded, 1)
        self.assertNotIn("2610.00001", [p["id"] for p in found])

    def test_author_only_inclusion_can_be_disabled(self):
        preferences = settings()
        preferences["include_flagged_authors"] = False
        start, _ = digest.week_window(NOW, NOW.tzinfo)
        found, _ = digest.select_papers(papers(), preferences, start)
        self.assertEqual(len(found), 2)

    def test_names_normalise_accents_but_do_not_guess_initials(self):
        self.assertEqual(digest.author_name("Éanna É. Example"), digest.author_name("Eanna E Example"))
        self.assertEqual(digest.author_name("Scott A. Hughes"), digest.author_name("Scott Hughes"))
        self.assertEqual(digest.author_name("Lisa V. Drummond"), digest.author_name("Lisa Drummond"))
        self.assertEqual(digest.author_name("João S. Santos"), digest.author_name("Joao Santos"))
        self.assertNotEqual(digest.author_name("A. Example"), digest.author_name("Alex Example"))
        self.assertNotEqual(digest.author_name("Huan Yang"), digest.author_name("Yang Yang"))

    def test_author_aliases_keep_one_badge_per_person(self):
        preferences = settings()
        preferences["author_flags"] = {"collaborators": ["Nicholas Yunes"], "notable_authors": ["João S. Santos"]}
        preferences["author_aliases"] = {"Nicholas Yunes": ["Nicolás Yunes"], "João S. Santos": ["João Sieiro dos Santos"]}
        start, _ = digest.week_window(NOW, NOW.tzinfo)
        paper = {**papers()[0], "title": "An unrelated title", "abstract": "No selected keywords."}
        for kind, canonical in [("collaborators", "Nicholas Yunes"), ("notable_authors", "João S. Santos")]:
            for spelling in [canonical, *preferences["author_aliases"][canonical]]:
                with self.subTest(spelling=spelling):
                    found, _ = digest.select_papers([{**paper, "authors": [spelling]}], preferences, start)
                    self.assertEqual(len(found), 1)
                    self.assertEqual(found[0]["author_flags"][kind], [canonical])
                    self.assertEqual(found[0]["topics"], [])
        found, _ = digest.select_papers([{**paper, "authors": ["Nicholas Yunes", "Nicolás Yunes", "João S. Santos", "João Sieiro dos Santos"]}], preferences, start)
        self.assertEqual(found[0]["author_flags"], preferences["author_flags"])

    def test_invalid_author_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            for aliases in [[], {"Nicholas Yunes": "Nicolás Yunes"}, {"Nicholas Yunes": [""]}]:
                with self.subTest(aliases=aliases):
                    preferences = settings()
                    preferences["author_aliases"] = aliases
                    path.write_text(json.dumps(preferences))
                    with self.assertRaises(ValueError):
                        digest.read_preferences(path)

    def test_invalid_preferences_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            invalid = settings()
            invalid["categories"] = ["gr-qc OR all:secret"]
            path.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                digest.read_preferences(path)

    def test_omitted_author_flags_default_to_empty_lists(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            preferences = settings()
            del preferences["author_flags"]
            path.write_text(json.dumps(preferences))
            preferences = digest.read_preferences(path)
            start, _ = digest.week_window(NOW, NOW.tzinfo)
            found, _ = digest.select_papers(papers(), preferences, start)
            self.assertEqual(len(found), 2)
            self.assertFalse(any(any(paper["author_flags"].values()) for paper in found))


class PublicationTests(unittest.TestCase):
    def test_render_escapes_html_and_liquid(self):
        data = snapshot()
        data["papers"][0]["title"] = '<script>alert(1)</script> {{ site.secret }}'
        rendered = digest.render_body(data)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("{{ site.secret }}", rendered)
        self.assertIn("&#123;&#123;", rendered)
        self.assertIn("Collaborator:", rendered)
        self.assertIn("Notable author:", rendered)

    def test_reruns_replace_the_issue_and_keep_the_archive(self):
        data = snapshot()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            digest.publish(root, data)
            digest.publish(root, data)
            index_path = root / "_data/arxiv_digest.json"
            self.assertEqual(len(json.loads(index_path.read_text())["issues"]), 1)
            next_issue = {**data, "issue": "2026-10-27"}
            digest.publish(root, next_issue)
            index = json.loads(index_path.read_text())
            self.assertEqual([issue["date"] for issue in index["issues"]], ["2026-10-27", "2026-10-20"])
            self.assertTrue((root / "_pages/arxiv-digest/2026-10-20.html").exists())
            exported = json.loads((root / "files/arxiv-digest/2026-10-20.json").read_text())
            self.assertEqual(len(exported["papers"]), 3)

    def test_corrupt_index_and_demo_cannot_replace_real_issues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "_data/arxiv_digest.json"
            path.parent.mkdir()
            path.write_text('{"issues":"broken"}')
            with self.assertRaises(ValueError):
                digest.publish(root, snapshot())
            self.assertEqual(path.read_text(), '{"issues":"broken"}')
            with self.assertRaises(ValueError):
                digest.publish(root, snapshot(demo=True))

    def test_limit_keeps_all_matches_in_export(self):
        data = snapshot()
        data["max_papers"] = 1
        self.assertEqual(digest.render_body(data).count('<article class="arxiv-card">'), 1)
        self.assertEqual(len(data["papers"]), 3)

    @patch.object(digest, "collect", side_effect=ValueError("API unavailable"))
    def test_failed_collection_writes_no_public_files(self, collect):
        with tempfile.TemporaryDirectory() as directory, patch("sys.argv", ["arxiv_digest", "--root", directory]), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(digest.main(), 1)
            self.assertEqual(list(Path(directory).iterdir()), [])

    @patch.object(digest, "collect", side_effect=AssertionError("Demo attempted a network call"))
    def test_demo_only_writes_local_preview(self, collect):
        with tempfile.TemporaryDirectory() as directory, patch("sys.argv", ["arxiv_digest", "--demo", "--root", directory]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(digest.main(), 0)
            path = Path(directory) / "local/arxiv-demo/index.html"
            self.assertIn("SYNTHETIC DEMO", path.read_text())
            self.assertIn("Paper links are disabled", path.read_text())
            self.assertFalse((Path(directory) / "_pages").exists())


if __name__ == "__main__":
    unittest.main()
