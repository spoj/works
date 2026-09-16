#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "works" / "scripts" / "links.py"
sys.path.insert(0, str(SCRIPT.parent))
from links import coverage, database, index_collection, normalize_url, parse_markdown, query, set_references

BASE = "https://example.test/collection/"


class LinksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="works-")
        self.scratch = Path(self.temp.name)
        self.root = self.scratch / "collection"
        self.root.mkdir()
        self.db_path = self.scratch / "private" / "index.sqlite"
        self.db = database(self.db_path)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def write(self, path, text, root=None):
        target = (root or self.root) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def index(self, root=None, name="team", base=BASE, complete=True, force=False):
        with self.db:
            return index_collection(self.db, name, root or self.root, complete, "test snapshot", force, base)

    def cli(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--db", str(self.db_path), *args],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=5,
        )

    def test_markdown_inline_reference_images_fences_and_code(self):
        links = parse_markdown('''[inline](dir/file_(draft).md)
![image](image%20file.md)
[full][id] [id][] [id]
[id]: <dir/space%20file.md#part> "title"
```md
[fenced](missing.md)
```
`[code](missing.md)`
''', "work/LOG.md")
        self.assertEqual([link.destination for link in links],
                         ["dir/file_(draft).md", "image%20file.md"] + ["dir/space%20file.md#part"] * 3)
        self.assertEqual([link.line for link in links], [1, 2, 3, 3, 3])

    def test_url_mentions_and_autolinks_without_double_counting(self):
        links = parse_markdown('''[linked](https://example.test/a)
<https://example.test/b> and https://example.test/c.
(https://example.test/d_(draft)).
`https://example.test/ignored`
''')
        self.assertEqual([link.destination for link in links], [
            "https://example.test/a", "https://example.test/b", "https://example.test/c",
            "https://example.test/d_(draft)",
        ])

    def test_every_markdown_file_without_git_and_canonical_paths(self):
        self.write("README.md", "Collection guide")
        self.write("2026-01-01-study/LOG.md", "Original finding")
        self.write("2026-01-02-review/evidence/DETAILS.MD", "Correction [study](../../2026-01-01-study/LOG.md#finding)")
        self.write(".notes/hidden.md", "Hidden appendix")
        self.write(".git/internal.md", "Git metadata")
        self.write("data.csv", "Not indexed")
        result = self.index()
        self.assertEqual((result["mode"], result["changed"]), ("complete", 4))
        matches = query(self.db, "incoming", BASE + "2026-01-01-study/")["matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["path"], "2026-01-02-review/evidence/DETAILS.MD")
        self.assertEqual(matches[0]["line"], 1)
        self.assertNotIn(str(self.root), matches[0]["url"])
        self.assertEqual(len(query(self.db, "search", "Hidden appendix")["matches"]), 1)
        self.assertEqual(query(self.db, "search", "Git metadata")["matches"], [])

    def test_cross_collection_citations_before_target_is_indexed(self):
        self.write("personal/LOG.md", "[team](https://example.test/team/study/LOG.md)")
        self.index()
        other = self.scratch / "download"
        self.write("study/LOG.md", "Team finding", other)
        self.index(other, "other", "https://example.test/team/")
        result = query(self.db, "incoming", "https://example.test/team/study")
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(len(result["coverage"]), 2)

    def test_network_file_citations_do_not_use_the_input_directory(self):
        self.write("source/LOG.md", "[other](../other/LOG.md)")
        base = "file://server/share/works/"
        self.index(base=base)
        result = query(self.db, "incoming", base + "other")
        self.assertEqual(result["matches"][0]["url"], base + "source/LOG.md")
        self.assertEqual(result["matches"][0]["target"]["url"], base + "other/LOG.md")

    def test_missing_targets_and_descendants_remain_queryable(self):
        self.write("source/LOG.md", "[gone](../gone/evidence.md)")
        self.index()
        self.assertEqual(len(query(self.db, "incoming", BASE + "gone")["matches"]), 1)
        self.assertEqual(query(self.db, "incoming", BASE + "gon")["matches"], [])

    def test_percent_encoding_fragments_and_literal_spaces(self):
        self.write("work/LOG.md", '[self](#scope) [space](space name.md "title")')
        self.write("work/space name.md", "Evidence")
        self.index()
        result = query(self.db, "outgoing", BASE + "work/")
        self.assertEqual([row["target"]["url"] for row in result["matches"]],
                         [BASE + "work/LOG.md", BASE + "work/space%20name.md"])
        self.assertEqual(len(query(self.db, "incoming", BASE + "work/space name.md#heading")["matches"]), 1)
        self.assertEqual(normalize_url("HTTPS://EXAMPLE.TEST/a%20b.md#x"), "https://example.test/a%20b.md")

    def test_literal_percent_in_source_path_is_not_decoded_as_link_text(self):
        self.write("literal%20name/LOG.md", "[self](#scope) [other](details.md)")
        self.index()
        matches = query(self.db, "outgoing", "team")["matches"]
        self.assertEqual([m["target"]["path"] for m in matches],
                         ["literal%20name/LOG.md", "literal%20name/details.md"])
        self.assertEqual(matches[0]["target"]["url"], BASE + "literal%2520name/LOG.md")
        self.assertEqual(len(query(self.db, "incoming", "team", path="literal%20name/LOG.md")["matches"]), 1)

    def test_partial_never_deletes_omitted_files(self):
        self.write("old/LOG.md", "[earlier](../first/LOG.md)")
        self.index()
        completed = coverage(self.db)[0]["complete"]
        batch = self.scratch / "batch"
        self.write("new/LOG.md", "New contribution", batch)
        result = self.index(batch, complete=False)
        self.assertEqual((result["mode"], result["removed"]), ("partial", 0))
        self.assertEqual(len(query(self.db, "incoming", BASE + "first")["matches"]), 1)
        self.assertEqual(coverage(self.db)[0]["indexed_files"], 2)
        self.assertEqual(coverage(self.db)[0]["complete"], completed)

    def test_partial_initial_index_does_not_claim_completeness(self):
        self.write("work/LOG.md", "Partial snapshot")
        self.index(complete=False)
        row = coverage(self.db)[0]
        self.assertEqual(row["mode"], "partial")
        self.assertIsNone(row["complete"])
        self.assertIsNone(row["complete_snapshot"])

    def test_complete_removes_missing_text_and_edges(self):
        source = self.write("work/LOG.md", "Unique obsolete phrase [target](../target/LOG.md)")
        self.index()
        source.unlink()
        result = self.index()
        self.assertEqual(result["removed"], 1)
        self.assertEqual(query(self.db, "search", "Unique obsolete phrase")["matches"], [])
        self.assertEqual(query(self.db, "incoming", BASE + "target")["matches"], [])

    def test_failed_read_retains_old_content_and_omitted_files(self):
        source = self.write("work/LOG.md", "Old wording [target](../target/LOG.md)")
        omitted = self.write("other/LOG.md", "Other work")
        self.index()
        completed = coverage(self.db)[0]["complete"]
        source.write_bytes(b"invalid UTF-8 \xff")
        omitted.unlink()
        result = self.index()
        self.assertEqual((result["mode"], result["removed"]), ("incomplete", 0))
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(coverage(self.db)[0]["complete"], completed)
        self.assertEqual(len(query(self.db, "search", "Old wording")["matches"]), 1)
        self.assertEqual(len(query(self.db, "incoming", BASE + "target")["matches"]), 1)
        self.assertEqual(coverage(self.db)[0]["indexed_files"], 2)
        self.assertEqual(source.read_bytes(), b"invalid UTF-8 \xff")

    def test_partial_keeps_prior_failures_until_rechecked(self):
        self.write("bad.md", "old")
        self.index()
        self.write("bad.md", "new longer")
        original = Path.read_text
        def fail(path, *args, **kwargs):
            if path.name == "bad.md":
                raise PermissionError("denied")
            return original(path, *args, **kwargs)
        with patch.object(Path, "read_text", fail):
            self.assertEqual(self.index()["mode"], "incomplete")
        batch = self.scratch / "batch"
        self.write("other.md", "Other", batch)
        self.assertEqual(self.index(batch, complete=False)["mode"], "incomplete")
        self.assertEqual(coverage(self.db)[0]["errors"][0]["path"], "bad.md")
        self.write("bad.md", "Recovered", batch)
        self.assertEqual(self.index(batch, complete=False)["mode"], "partial")
        self.assertEqual(coverage(self.db)[0]["errors"], [])

    def test_known_failed_reads_are_retried_despite_unchanged_metadata(self):
        self.write("work/LOG.md", "Cached finding")
        self.index()
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            self.assertEqual(self.index(force=True)["mode"], "incomplete")
            self.assertEqual(self.index()["mode"], "incomplete")
            self.assertEqual(self.index(complete=False)["mode"], "incomplete")
        self.assertEqual(self.index()["mode"], "complete")

    def test_failed_enumeration_does_not_remove_cached_files(self):
        self.write("work/LOG.md", "Retained")
        self.index()
        def walk(root, onerror):
            onerror(PermissionError(13, "denied", str(root / "locked")))
            return iter(())
        with patch("links.os.walk", walk):
            result = self.index()
        self.assertEqual(result["mode"], "incomplete")
        self.assertEqual(coverage(self.db)[0]["indexed_files"], 1)

    def test_missing_root_is_not_an_empty_complete_snapshot(self):
        self.write("work/LOG.md", "Retained")
        self.index()
        self.assertEqual(self.index(self.scratch / "missing")["mode"], "incomplete")
        self.assertEqual(coverage(self.db)[0]["indexed_files"], 1)

    def test_symlink_is_not_silently_ignored_or_followed(self):
        outside = self.write("outside.md", "Outside content", self.scratch)
        try:
            (self.root / "alias.md").symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {error}")
        result = self.index()
        self.assertEqual(result["mode"], "incomplete")
        self.assertEqual(result["changed"], 0)
        self.assertEqual(query(self.db, "search", "Outside content")["matches"], [])

    def test_directory_link_gap_is_reported(self):
        self.write("linked/inside.md", "Not to be read")
        original = Path.is_symlink
        with patch.object(Path, "is_symlink", lambda path: path.name == "linked" or original(path)):
            result = self.index()
        self.assertEqual(result["mode"], "incomplete")
        self.assertEqual(result["changed"], 0)
        self.assertEqual(result["errors"][0]["path"], "linked")

    def test_incremental_reuse_and_forced_reread(self):
        source = self.write("work/LOG.md", "first")
        self.index()
        self.assertEqual(self.index()["reused"], 1)
        stat = source.stat()
        source.write_text("other", encoding="utf-8")
        os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertEqual(self.index()["reused"], 1)
        self.assertEqual(self.index(force=True)["changed"], 1)
        self.assertEqual(len(query(self.db, "search", "other")["matches"]), 1)
        self.assertEqual(query(self.db, "search", "first")["matches"], [])

    def test_replacement_does_not_leave_old_edges(self):
        self.write("work/LOG.md", "[old](../old/LOG.md)")
        self.index()
        self.write("work/LOG.md", "[replacement](../new/LOG.md)")
        self.index()
        self.assertEqual(query(self.db, "incoming", BASE + "old")["matches"], [])
        self.assertEqual(len(query(self.db, "incoming", BASE + "new")["matches"]), 1)
        self.assertEqual(self.db.execute("SELECT count(*) FROM texts").fetchone()[0], 1)

    def test_full_text_includes_code_and_unparsed_multiline_links(self):
        self.write("work/details.md", "```\nimportant quoted correction\n```\n[old](\nhttps://example.test/old\n)")
        self.index()
        self.assertEqual(len(query(self.db, "search", "important quoted correction")["matches"]), 1)
        self.assertEqual(len(query(self.db, "search", "https://example.test/old")["matches"]), 1)

    def test_result_limit_is_explicit(self):
        self.write("work/LOG.md", "[a](../target/a.md) [b](../target/b.md)")
        self.index()
        result = query(self.db, "incoming", BASE + "target", 1)
        self.assertTrue(result["truncated"])
        self.assertEqual(len(result["matches"]), 1)
        self.assertTrue(query(self.db, "search", "target", 0)["truncated"])

    def test_location_changes_do_not_change_identity(self):
        self.write("source/LOG.md", "[target](../target/LOG.md)")
        self.index()
        self.index(base="https://example.test/different/")
        result = query(self.db, "incoming", "team", path="target")
        self.assertEqual(result["matches"][0]["target"]["url"], "https://example.test/different/target/LOG.md")
        with self.assertRaises(ValueError):
            self.index(base="https://example.test/share?token=opaque")
        with self.assertRaises(sqlite3.IntegrityError):
            self.index(name="duplicate", base="https://example.test/different/")

    def test_cli_nested_cwd_complete_partial_status_and_forget(self):
        self.write("work/LOG.md", "Distinctive phrase [target](../target/LOG.md)")
        nested = self.scratch / "unrelated cwd"
        nested.mkdir()
        result = self.cli("index", "team", "--root", str(self.root), "--url-root", BASE, "--complete", cwd=nested)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["mode"], "complete")
        result = self.cli("search", "Distinctive phrase", cwd=nested)
        self.assertEqual(len(json.loads(result.stdout)["matches"]), 1)
        self.assertEqual(self.cli("status").returncode, 0)
        self.assertEqual(self.cli("forget", "team").returncode, 0)
        self.assertEqual(coverage(self.db)[0]["mode"], "unindexed")
        self.assertEqual(self.db.execute("SELECT count(*) FROM texts").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT count(*) FROM links").fetchone()[0], 0)

    def test_cli_requires_explicit_scope_and_reports_failed_index(self):
        self.assertEqual(self.cli("index", "team", "--root", str(self.root), "--url-root", BASE).returncode, 2)
        result = self.cli("index", "team", "--root", str(self.scratch / "missing"), "--url-root", BASE, "--complete")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["mode"], "incomplete")
        self.assertEqual(self.cli("incoming", BASE, "--limit", "-1").returncode, 2)
        self.assertEqual(self.cli("incoming", "not-a-canonical-address").returncode, 2)

    def test_default_database_is_private_to_the_current_workspace(self):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "index", "team", "--root", str(self.root),
             "--url-root", BASE, "--complete"],
            cwd=self.scratch, capture_output=True, text=True, encoding="utf-8", timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.scratch / ".works" / "index.sqlite").is_file())

    def test_wip_references_are_labelled_and_reclassified_on_finalization(self):
        self.write("2026-01-01-study/LOG.md", "Finished finding")
        self.write("_wip_review/details.md", "Draft correction [study](../2026-01-01-study/LOG.md)")
        self.write("README.md", "Collection guide")
        self.index()
        self.assertEqual(query(self.db, "incoming", BASE + "2026-01-01-study")["matches"][0]["state"], "wip")
        self.assertEqual(query(self.db, "search", "Draft correction")["matches"][0]["state"], "wip")
        self.assertEqual(query(self.db, "search", "Collection guide")["matches"][0]["state"], "collection")
        (self.root / "_wip_review").rename(self.root / "2026-01-02-review")
        self.index()
        matches = query(self.db, "incoming", BASE + "2026-01-01-study")["matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["state"], "finalized")
        self.assertEqual(matches[0]["path"], "2026-01-02-review/details.md")

    def test_citation_context_preserves_relationship_wording_in_both_directions(self):
        examples = [
            "This finding directly contradicts [xx](@d/LOG.md).",
            "We found the methods in [xx](@d/LOG.md) useful and made one improvement.",
            "We confirm the boundary established in [xx](@d/LOG.md).",
            "This supersedes [xx](@d/LOG.md).",
        ]
        self.write("LOG.md", "\n\n".join(examples))
        self.index(base=None)
        with self.db:
            set_references(self.db, "team", {"d": "D"})
        expected = [text.replace("(@d/LOG.md)", "") for text in examples]
        for command, collection in [("incoming", "D"), ("outgoing", "team")]:
            matches = query(self.db, command, collection)["matches"]
            self.assertEqual([m["context"] for m in matches], expected)
            self.assertEqual([m["line"] for m in matches], [1, 3, 5, 7])
            self.assertTrue(all(m["destination"] == "@d/LOG.md" for m in matches))

    def test_context_uses_the_reference_occurrence_not_its_definition(self):
        self.write("LOG.md", "Unrelated paragraph.\n\nWe do not\nconfirm [xx][study]; the boundary remains uncertain.\n\n[study]: @d/LOG.md\n")
        self.index(base=None)
        match = query(self.db, "outgoing", "team")["matches"][0]
        self.assertEqual(match["context"], "We do not confirm [xx]; the boundary remains uncertain.")
        self.assertEqual(match["target"]["status"], "unbound")

    def test_context_does_not_mix_neighboring_list_items_or_reference_definitions(self):
        self.write("LOG.md", "- Earlier unrelated item.\n- We do not\n  confirm [xx][study]; uncertainty remains.\n"
                   "- Later unrelated item.\n[study]: @d/LOG.md\n")
        self.index(base=None)
        match = query(self.db, "outgoing", "team")["matches"][0]
        self.assertEqual(match["context"], "- We do not confirm [xx]; uncertainty remains.")

    def test_context_is_centered_on_each_repeated_citation_in_a_long_line(self):
        self.write("LOG.md", "Earlier unrelated details. " * 40 + "We contradict [xx](@d/LOG.md). "
                   + "Other details. " * 80 + "We confirm [xx](@d/LOG.md). " + "Later details. " * 40)
        self.index(base=None)
        matches = query(self.db, "outgoing", "team")["matches"]
        self.assertIn("We contradict [xx].", matches[0]["context"])
        self.assertNotIn("We confirm", matches[0]["context"])
        self.assertIn("We confirm [xx].", matches[1]["context"])
        self.assertNotIn("We contradict", matches[1]["context"])
        for match in matches:
            self.assertLessEqual(len(match["context"]), 328)
            self.assertTrue(match["context"].startswith("... "))
            self.assertTrue(match["context"].endswith(" ..."))

    def test_context_retains_cached_wording_after_source_change_and_failed_read(self):
        source = self.write("LOG.md", "We do not confirm [study](study.md).")
        self.index()
        source.write_bytes(b"bad UTF-8 \xff")
        self.assertEqual(self.index()["mode"], "incomplete")
        with patch.object(Path, "read_text", side_effect=AssertionError("must use cached text")):
            matches = query(self.db, "incoming", "team", path="study.md")["matches"]
        self.assertEqual(matches[0]["context"], "We do not confirm [study].")

    def test_context_keeps_prose_when_the_citation_url_is_long(self):
        url = "https://example.test/" + "x" * 1000
        self.write("LOG.md", "This supersedes " + url + ".\n\nWe extend [methods](" + url + ").")
        self.index(base=None)
        matches = json.loads(self.cli("outgoing", "team").stdout)["matches"]
        self.assertEqual([m["context"] for m in matches], ["This supersedes [link].", "We extend [methods]."])
        self.assertTrue(all(m["destination"] == url for m in matches))

    def test_diamond_nicknames_and_source_scoped_names(self):
        for source, body, refs in [
            ("A", "[B](@b/LOG.md) [C](@c/LOG.md)", {"b": "B", "c": "C", "research": "E"}),
            ("B", "[D](@research/study/LOG.md) [D again](@lab/study/LOG.md)", {"research": "D", "lab": "D"}),
            ("C", "[D](@notes/study/LOG.md) [E](@research/study/LOG.md)", {"notes": "D", "research": "E"}),
        ]:
            root = self.scratch / source
            self.write("LOG.md", body, root)
            self.index(root, source, None)
            with self.db:
                set_references(self.db, source, refs)
        result = query(self.db, "incoming", "D", path="study")
        self.assertEqual([m["collection"] for m in result["matches"]], ["B", "B", "C"])
        self.assertEqual([m["destination"] for m in result["matches"]],
                         ["@research/study/LOG.md", "@lab/study/LOG.md", "@notes/study/LOG.md"])
        self.assertTrue(all(m["target"]["status"] == "unchecked" for m in result["matches"]))
        self.assertEqual(query(self.db, "incoming", "E")["matches"][0]["collection"], "C")
        self.assertEqual(next(c for c in result["coverage"] if c["name"] == "D")["mode"], "unindexed")

    def test_explicit_reference_never_falls_back_to_local(self):
        self.write("LOG.md", "[remote](@unknown/target.md) [local](./@unknown/target.md)")
        self.write("@unknown/target.md", "Local file")
        self.index(base=None)
        matches = query(self.db, "outgoing", "team")["matches"]
        self.assertEqual(matches[0]["target"]["status"], "unbound")
        self.assertIsNone(matches[0]["target"]["collection"])
        self.assertEqual(matches[1]["target"]["status"], "cached")
        self.assertEqual(matches[1]["target"]["collection"], "team")

    def test_binding_replacement_resolves_without_rereading_and_removal_does_not_linger(self):
        self.write("LOG.md", "[one](@research/LOG.md) [two](@lab/LOG.md)")
        self.index(base=None)
        with self.db:
            set_references(self.db, "team", {"research": "D", "lab": "D"})
        self.assertEqual(self.index(base=None)["reused"], 1)
        with patch.object(Path, "read_text", side_effect=AssertionError("must not read files")), self.db:
            set_references(self.db, "team", {"research": "E"})
            self.assertEqual(query(self.db, "incoming", "D")["matches"], [])
            self.assertEqual(len(query(self.db, "incoming", "E")["matches"]), 1)
            self.assertEqual(query(self.db, "outgoing", "team")["matches"][1]["target"]["status"], "unbound")
        with self.db:
            set_references(self.db, "team", {})
        self.assertEqual(query(self.db, "incoming", "E")["matches"], [])

    def test_target_status_distinguishes_unchecked_missing_and_cached(self):
        self.write("LOG.md", "[target](@d/study/LOG.md) [attachment](@d/data.pdf)")
        self.index(base=None)
        with self.db:
            set_references(self.db, "team", {"d": "D"})
        root = self.scratch / "D"
        root.mkdir()
        self.index(root, "D", None, complete=False)
        self.assertEqual(query(self.db, "incoming", "D")["matches"][0]["target"]["status"], "unchecked")
        self.index(root, "D", None)
        matches = query(self.db, "incoming", "D")["matches"]
        self.assertEqual([m["target"]["status"] for m in matches], ["missing", "unchecked"])
        target = self.write("study/LOG.md", "Target", root)
        self.index(root, "D", None)
        self.assertEqual(query(self.db, "incoming", "D")["matches"][0]["target"]["status"], "cached")
        target.write_bytes(b"bad UTF-8 \xff")
        self.index(root, "D", None)
        result = query(self.db, "incoming", "D")
        self.assertEqual(result["matches"][0]["target"]["status"], "cached")
        self.assertEqual(next(c for c in result["coverage"] if c["name"] == "D")["mode"], "incomplete")

    def test_forget_retains_incoming_identity_but_clears_affected_content(self):
        self.write("LOG.md", "[target](@d/LOG.md)")
        self.index(base=None)
        root = self.scratch / "D"
        self.write("LOG.md", "Private target", root)
        self.index(root, "D", None)
        with self.db:
            set_references(self.db, "team", {"d": "D"})
            set_references(self.db, "D", {"back": "team"})
        result = self.cli("forget", "D")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(query(self.db, "search", "Private target")["matches"], [])
        incoming = query(self.db, "incoming", "D")
        self.assertEqual(incoming["matches"][0]["target"]["status"], "unchecked")
        self.assertEqual(next(c for c in incoming["coverage"] if c["name"] == "D")["references"], {})

    def test_reference_paths_fragments_root_queries_and_escapes(self):
        self.write("source/LOG.md", "[ok](@d/study/part%20one.md#finding) [bad](@d/../escape.md) [local bad](../../escape.md)")
        self.index(base=None)
        with self.db:
            set_references(self.db, "team", {"d": "D"})
        matches = query(self.db, "outgoing", "team")["matches"]
        self.assertEqual(matches[0]["target"]["path"], "study/part one.md")
        self.assertEqual(matches[0]["destination"], "@d/study/part%20one.md#finding")
        self.assertEqual([m["target"]["status"] for m in matches[1:]], ["invalid", "invalid"])
        self.assertEqual(len(query(self.db, "incoming", "D", path="study/part one.md")["matches"]), 1)
        self.assertEqual(query(self.db, "incoming", "D", path="stud")["matches"], [])
        self.assertTrue(query(self.db, "incoming", "D", limit=0)["truncated"])

    def test_copy_uses_destination_collection_bindings(self):
        self.write("LOG.md", "[target](@research/LOG.md)")
        self.index(name="B", base=None)
        self.index(name="C", base=None)
        with self.db:
            set_references(self.db, "B", {"research": "D"})
            set_references(self.db, "C", {"research": "E"})
        self.assertEqual(query(self.db, "incoming", "D")["matches"][0]["collection"], "B")
        self.assertEqual(query(self.db, "incoming", "E")["matches"][0]["collection"], "C")

    def test_url_and_named_references_converge_when_url_root_is_known(self):
        self.write("LOG.md", "[named](@d/study/LOG.md) [url](https://example.test/D/study/LOG.md)")
        self.index(base=None)
        with self.db:
            set_references(self.db, "team", {"d": "D"})
        self.assertEqual(len(query(self.db, "incoming", "D")["matches"]), 1)
        root = self.scratch / "D"
        self.write("study/LOG.md", "Target", root)
        self.index(root, "D", "https://example.test/D/")
        self.assertEqual(len(query(self.db, "incoming", "D")["matches"]), 2)
        self.assertEqual(len(query(self.db, "incoming", "https://example.test/D/study")["matches"]), 2)
        self.index(root, "D", "https://example.test/moved/")
        result = query(self.db, "incoming", "D")
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["target"]["url"], "https://example.test/moved/study/LOG.md")
        self.assertEqual(len(query(self.db, "incoming", "https://example.test/D/study")["matches"]), 1)

    def test_cycles_need_no_recursive_resolution(self):
        self.write("LOG.md", "[back](@self/LOG.md)")
        self.index(base=None)
        with self.db:
            set_references(self.db, "team", {"self": "team"})
        self.assertEqual(len(query(self.db, "incoming", "team")["matches"]), 1)

    def test_cli_binding_replacement_clear_and_query_arguments(self):
        self.write("LOG.md", "[target](@research/study/LOG.md)")
        self.assertEqual(self.cli("index", "B", "--root", str(self.root), "--complete").returncode, 0)
        result = self.cli("set-references", "B", "--reference", "research=D", "--reference", "lab=D")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.cli("incoming", "D", "study/")
        self.assertEqual(json.loads(result.stdout)["matches"][0]["destination"], "@research/study/LOG.md")
        self.assertEqual(self.cli("set-references", "B").returncode, 2)
        self.assertEqual(self.cli("set-references", "B", "--reference", "bad").returncode, 2)
        self.assertEqual(self.cli("set-references", "B", "--reference", "x=D", "--reference", "x=E").returncode, 2)
        self.assertEqual(self.cli("set-references", "B", "--reference", "bad/name=D").returncode, 2)
        self.assertEqual(self.cli("set-references", "B", "--reference", "x=invalid/key").returncode, 2)
        self.assertEqual(len(query(self.db, "incoming", "D")["matches"]), 1)
        self.assertEqual(self.cli("set-references", "B", "--clear").returncode, 0)
        self.assertEqual(query(self.db, "incoming", "D")["matches"], [])
        self.assertEqual(self.cli("incoming", "https://example.test/", "extra").returncode, 2)

    def test_old_cache_requires_explicit_rebuild(self):
        old = self.scratch / "old.sqlite"
        with sqlite3.connect(old) as db:
            db.execute("CREATE TABLE collections (name TEXT)")
            db.execute("INSERT INTO collections VALUES ('retained')")
        db.close()
        with self.assertRaisesRegex(ValueError, "rebuild"):
            database(old)
        with sqlite3.connect(old) as db:
            self.assertEqual(db.execute("SELECT name FROM collections").fetchone()[0], "retained")
        db.close()

    def test_unknown_freshness_is_not_invented(self):
        with self.db:
            index_collection(self.db, "team", self.root, True, url_root=BASE)
        row = coverage(self.db)[0]
        self.assertEqual(row["snapshot"], "unknown")
        self.assertEqual(row["complete_snapshot"], "unknown")


class PackageTest(unittest.TestCase):
    def test_skill_frontmatter_and_setup_link(self):
        root = SCRIPT.parents[1]
        skill = (root / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        self.assertIn(f"name: {root.name}\n", frontmatter)
        description = frontmatter.split("description: ", 1)[1].strip()
        self.assertTrue(0 < len(description) <= 1024)
        self.assertEqual(skill.count("[SETUP.md](SETUP.md)"), 1)

    def test_package_document_links_resolve(self):
        root = SCRIPT.parents[3]
        for source in (root / "README.md", SCRIPT.parents[1] / "SKILL.md", SCRIPT.parents[1] / "SETUP.md", SCRIPT.parents[1] / "INDEX.md"):
            for link in parse_markdown(source.read_text(encoding="utf-8"), source):
                target = urlsplit(link.destination)
                if not target.scheme and not target.netloc:
                    self.assertTrue((source.parent / unquote(target.path)).exists(), link)


if __name__ == "__main__":
    unittest.main()
