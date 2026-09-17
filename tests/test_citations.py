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
SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "works" / "scripts" / "citations.py"
sys.path.insert(0, str(SCRIPT.parent))
import citations

OLD = "2026-01-01-study"
NEW = "2026-02-01-review"
OTHER = "2026-03-01-followup"
BASE = "https://example.test/works/"


class CitationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "snapshot"
        self.root.mkdir()
        self.db_path = Path(self.temp.name) / "index.sqlite"
        self.db = citations.database(self.db_path)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def write(self, path, text, root=None):
        target = (root or self.root) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def scan(self, root=None, name="local", complete=True, force=False, url_root=BASE):
        with self.db:
            return citations.scan_collection(self.db, name, root or self.root, complete,
                                             "dated capture", force, url_root)

    def incoming(self, path=OLD, collection="local"):
        return citations.query(self.db, "in", collection, path)

    def occurrences(self, result=None):
        result = self.incoming() if result is None else result
        return [citation for work in result["works"] for file in work["files"] for citation in file["citations"]]

    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "--db", str(self.db_path), *args],
                              capture_output=True, text=True, timeout=5)

    def test_parser_reference_links_images_and_code(self):
        text = '''[inline](dir/file_(draft).md)
![image](image%20file.md)
[full][id] [id][] [id]
[id]: <dir/space%20file.md#part> "title"
```md
[fenced](missing.md)
```
`[inline code](missing.md)`
'''
        links = citations.parse_markdown(text)
        self.assertEqual([link.destination for link in links],
                         ["dir/file_(draft).md", "image%20file.md"] + ["dir/space%20file.md#part"] * 3)
        self.assertEqual([link.line for link in links], [1, 2, 3, 3, 3])

    def test_parser_urls_and_source_order(self):
        text = 'https://example.test/a [b](b.md) <https://example.test/c>. `https://ignore.test/`'
        self.assertEqual([link.destination for link in citations.parse_markdown(text)],
                         ["https://example.test/a", "b.md", "https://example.test/c"])

    def test_later_contradiction_always_surfaces_without_query_terms_or_incoming_links(self):
        self.write(f"{OLD}/LOG.md", "Original finding: alpha budget control")
        self.write(f"{NEW}/notes/DETAILS.MD", f"This contradicts [the prior result](../../{OLD}/LOG.md).")
        self.scan()
        result = self.incoming()
        self.assertEqual([work["work"] for work in result["works"]], [NEW])
        file = result["works"][0]["files"][0]
        self.assertEqual(file["path"], f"{NEW}/notes/DETAILS.MD")
        self.assertEqual(file["citations"][0]["line"], 1)
        self.assertIn("contradicts", file["citations"][0]["context"])

    def test_no_limits_on_works_occurrences_or_context(self):
        long = "qualification " * 100 + "does NOT supersede the method"
        for i in range(61):
            self.write(f"2026-02-01-review-{i:02}/LOG.md", f"{long} [study](../{OLD}/LOG.md).")
        self.write(f"{NEW}/notes.md", "\n\n".join(f"Evidence {i}: [study](../{OLD}/LOG.md)." for i in range(80)))
        self.scan()
        self.assertEqual(len(self.incoming()["works"]), 62)
        self.assertEqual(len(self.occurrences()), 141)
        self.assertTrue(any(long in item["context"] for item in self.occurrences()))
        result = self.cli("in", "local", OLD, "--json")
        self.assertEqual(len(self.occurrences(json.loads(result.stdout))), 141)
        text = self.cli("in", "local", OLD)
        self.assertIn(long, text.stdout)
        self.assertIn("Evidence 79", text.stdout)
        self.assertNotEqual(self.cli("in", "local", OLD, "--limit", "1").returncode, 0)

    def test_internal_navigation_cannot_crowd_out_cross_work_citations(self):
        self.write(f"{OLD}/LOG.md", "\n".join(f"[local](part{i}.md)" for i in range(100)))
        self.write(f"{OLD}/part0.md", "[self](LOG.md)")
        self.write("README.md", f"[navigation]({OLD}/LOG.md)")
        self.write(f"{NEW}/LOG.md", f"[correction](../{OLD}/part99.md)")
        self.scan()
        self.assertEqual(len(self.occurrences()), 1)
        self.assertEqual(self.incoming()["works"][0]["work"], NEW)
        self.assertEqual(citations.query(self.db, "out", "local", OLD)["works"], [])

    def test_file_selection_includes_citations_to_every_file_and_artifact_in_work(self):
        self.write(f"{NEW}/LOG.md", f"[entry](../{OLD}/LOG.md) [sql](../{OLD}/sql/check.sql) [folder](../{OLD}/)")
        self.scan()
        result = self.incoming(f"{OLD}/LOG.md")
        self.assertEqual(len(self.occurrences(result)), 3)
        self.assertEqual(result["work"], OLD)
        self.assertEqual([c["target"]["status"] for c in self.occurrences(result)], ["missing", "unchecked", "unchecked"])

    def test_wip_and_finalized_citations_both_present_in_path_order(self):
        for work in (NEW, "_wip_question", OTHER):
            self.write(f"{work}/LOG.md", f"[study](../{OLD}/LOG.md)")
        self.scan()
        result = self.incoming()["works"]
        self.assertEqual([w["work"] for w in result], [NEW, OTHER, "_wip_question"])
        self.assertEqual([w["state"] for w in result], ["finalized", "finalized", "wip"])

    def test_nested_published_copy_belongs_to_containing_work(self):
        self.write(f"{NEW}/publish/{OTHER}/LOG.md", f"[original](../../../{OLD}/LOG.md)")
        self.scan()
        self.assertEqual(self.incoming()["works"][0]["work"], NEW)

    def test_every_occurrence_retains_opposing_wording_on_same_line(self):
        text = f"This confirms [study](../{OLD}/LOG.md) for A but contradicts [study](../{OLD}/LOG.md) for B."
        self.write(f"{NEW}/LOG.md", text)
        self.scan()
        self.assertEqual(len(self.occurrences()), 2)
        self.assertEqual([c["context"] for c in self.occurrences()], [text, text])

    def test_full_wrapped_paragraph_without_neighboring_blocks(self):
        text = f"# Heading\nThis does not\nsupersede [study](../{OLD}/LOG.md).\nIt changes one example.\n\nUnrelated next paragraph."
        self.write(f"{NEW}/LOG.md", text)
        self.scan()
        self.assertEqual(self.occurrences()[0]["context"], text.split("\n", 1)[1].split("\n\n")[0])

    def test_full_list_item_including_indented_later_paragraph(self):
        text = f"- Other item\n- This supersedes [study](../{OLD}/LOG.md).\n  Only for August.\n\n  September remains untested.\n- Not this item."
        self.write(f"{NEW}/LOG.md", text)
        self.scan()
        self.assertEqual(self.occurrences()[0]["context"], text.split("\n", 1)[1].rsplit("\n", 1)[0])

    def test_citation_in_second_list_paragraph_includes_item_introduction(self):
        text = f"- Other item\n- Qualification:\n\n  This contradicts [study](../{OLD}/LOG.md).\n- Other item"
        self.write(f"{NEW}/LOG.md", text)
        self.scan()
        self.assertEqual(self.occurrences()[0]["context"], text.split("\n", 1)[1].rsplit("\n", 1)[0])

    def test_reference_definition_is_not_confused_with_citing_context(self):
        text = f"The later review qualifies [study][old].\n\n[old]: ../{OLD}/LOG.md"
        self.write(f"{NEW}/LOG.md", text)
        self.scan()
        self.assertEqual(self.occurrences()[0]["context"], text.split("\n")[0])

    def test_outgoing_groups_distinct_works_and_target_fragments(self):
        self.write(f"{NEW}/LOG.md", f"[a](../{OLD}/LOG.md#one) [b](../{OLD}/LOG.md#one) [c](../{OLD}/LOG.md#two)")
        self.write(f"{NEW}/analysis.md", f"[other](../{OTHER}/sql/a.sql) [internal](LOG.md) https://example.test/unrelated")
        self.scan()
        result = citations.query(self.db, "out", "local", NEW)
        self.assertEqual([work["work"] for work in result["works"]], [OLD, OTHER])
        self.assertEqual([t["fragment"] for t in result["works"][0]["targets"]], ["one", "two"])

    def test_source_scoped_names_and_cross_collection_same_work_name(self):
        self.write(f"{OLD}/LOG.md", f"[remote](@team/{OLD}/LOG.md)")
        self.scan()
        with self.db:
            citations.replace_references(self.db, "local", {"team": "other"})
        result = self.incoming(collection="other")
        self.assertEqual(len(self.occurrences(result)), 1)
        self.assertEqual(self.occurrences(result)[0]["target"]["status"], "unchecked")
        self.assertEqual(result["works"][0]["collection"], "local")

    def test_provider_urls_resolve_to_works_and_preserve_original_context(self):
        self.write(f"{NEW}/LOG.md", f"Changed: {BASE}{OLD}/space%20file.md#finding.")
        self.write(f"{OLD}/space file.md", "Evidence")
        self.scan()
        target = self.occurrences()[0]["target"]
        self.assertEqual(target["path"], f"{OLD}/space file.md")
        self.assertEqual(target["status"], "cached")
        self.assertEqual(target["fragment"], "finding")

    def test_unresolved_names_and_escaping_paths_are_visible(self):
        self.write(f"{NEW}/LOG.md", f"[unknown](@absent/{OLD}/LOG.md) [bad](../../../escape.md)")
        self.scan()
        result = self.incoming()
        self.assertEqual(result["works"], [])
        self.assertEqual([x["target"]["status"] for x in result["unresolved"]], ["unbound", "invalid"])
        text = self.cli("in", "local", OLD).stdout
        self.assertIn("WARNING unbound", text)
        self.assertIn("WARNING invalid", text)

    def test_all_markdown_scanned_without_git_including_hidden_and_supporting(self):
        self.write("README.md", "Guide")
        self.write(".notes/hidden.MD", "Note")
        self.write(f"{NEW}/nested/notes.md", f"[old](../../{OLD}/LOG.md)")
        self.write(".git/ignored.md", "Metadata")
        self.write("data.csv", "Not Markdown")
        result = self.scan()
        self.assertEqual(result["seen"], 3)
        self.assertEqual(len(self.occurrences()), 1)
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables, {"collections", "refs", "files", "links"})

    def test_partial_scan_keeps_omitted_citations_and_snapshot_history(self):
        self.write(f"{NEW}/LOG.md", f"[old](../{OLD}/LOG.md)")
        self.scan()
        batch = Path(self.temp.name) / "batch"
        self.write(f"{OTHER}/LOG.md", "New work", batch)
        result = self.scan(root=batch, complete=False)
        self.assertEqual((result["mode"], result["removed"]), ("partial", 0))
        self.assertEqual(len(self.occurrences()), 1)
        info = citations.coverage(self.db)[0]
        self.assertEqual(info["indexed_files"], 2)
        self.assertEqual(info["complete_snapshot"], "dated capture")

    def test_complete_scan_removes_deleted_citations(self):
        path = self.write(f"{NEW}/LOG.md", f"[old](../{OLD}/LOG.md)")
        self.scan()
        path.unlink()
        self.assertEqual(self.scan()["removed"], 1)
        self.assertEqual(self.occurrences(), [])

    def test_failed_read_keeps_old_context_and_reports_gap(self):
        text = f"This contradicts [old](../{OLD}/LOG.md)."
        path = self.write(f"{NEW}/LOG.md", text)
        other = self.write(f"{OTHER}/LOG.md", "Keep on failed inventory")
        self.scan()
        other.unlink()
        path.write_bytes(b"invalid UTF-8 \xff")
        result = self.scan()
        self.assertEqual((result["mode"], result["removed"]), ("incomplete", 0))
        self.assertEqual(self.occurrences()[0]["context"], text)
        self.assertTrue(self.incoming()["coverage"][0]["errors"])
        self.assertEqual(path.read_bytes(), b"invalid UTF-8 \xff")

    def test_known_failed_reads_are_retried_and_partial_retains_prior_errors(self):
        self.write(f"{NEW}/LOG.md", f"[old](../{OLD}/LOG.md)")
        self.scan()
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            self.assertEqual(self.scan(force=True)["mode"], "incomplete")
            self.assertEqual(self.scan()["mode"], "incomplete")
        batch = Path(self.temp.name) / "batch"
        self.write(f"{OTHER}/LOG.md", "Other", batch)
        self.assertEqual(self.scan(root=batch, complete=False)["mode"], "incomplete")
        self.assertEqual(self.scan()["mode"], "complete")

    def test_incremental_reuse_and_force_replaces_context_and_edges(self):
        path = self.write(f"{NEW}/LOG.md", f"[old](../{OLD}/LOG.md)")
        self.scan()
        self.assertEqual(self.scan()["reused"], 1)
        stat = path.stat()
        path.write_text(f"[new](../{OLD}/LOG.md)", encoding="utf-8")
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertEqual(self.scan()["reused"], 1)
        self.assertIn("[old]", self.occurrences()[0]["context"])
        self.assertEqual(self.scan(force=True)["changed"], 1)
        self.assertIn("[new]", self.occurrences()[0]["context"])
        self.assertEqual(len(self.occurrences()), 1)

    def test_failed_enumeration_and_missing_root_do_not_erase_cache(self):
        self.write(f"{NEW}/LOG.md", f"[old](../{OLD}/LOG.md)")
        self.scan()
        def failed_walk(root, onerror):
            onerror(PermissionError(13, "denied", str(root / "locked")))
            return iter(())
        with patch.object(citations.os, "walk", failed_walk):
            self.assertEqual(self.scan()["mode"], "incomplete")
        self.assertEqual(self.scan(root=self.root / "missing")["mode"], "incomplete")
        self.assertEqual(len(self.occurrences()), 1)

    def test_symlinks_are_reported_not_followed(self):
        outside = self.write("outside.md", "Outside", Path(self.temp.name))
        try:
            (self.root / "alias.md").symlink_to(outside)
            (self.root / "linked").symlink_to(outside.parent, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"native symlinks unavailable: {error}")
        result = self.scan()
        self.assertEqual(result["mode"], "incomplete")
        self.assertEqual(result["changed"], 0)
        self.assertEqual({e["path"] for e in result["errors"]}, {"alias.md", "linked"})

    def test_initial_partial_scan_and_unknown_capture(self):
        self.write(f"{NEW}/LOG.md", "Finding")
        with self.db:
            citations.scan_collection(self.db, "local", self.root, False)
        info = citations.coverage(self.db)[0]
        self.assertIsNone(info["complete"])
        self.assertIsNone(info["complete_snapshot"])
        self.assertEqual(info["snapshot"], "unknown")

    def test_cli_incremental_reference_operations_do_not_repoint_other_names(self):
        self.assertEqual(self.cli("references", "add", "local", "research", "team").returncode, 0)
        self.assertEqual(self.cli("references", "add", "local", "lab", "team").returncode, 0)
        self.assertEqual(self.cli("references", "add", "local", "research", "other").returncode, 2)
        self.assertEqual(self.cli("references", "remove", "local", "lab").returncode, 0)
        result = self.cli("references", "list", "local", "--json")
        self.assertEqual(json.loads(result.stdout)["references"], {"research": "team"})
        self.assertEqual(self.cli("references", "remove", "local", "absent").returncode, 2)

    def test_cli_resolve_named_relative_and_encoded_paths(self):
        self.write(f"{OLD}/space file.md", "Finding")
        self.scan()
        self.cli("references", "add", "local", "self", "local")
        for args in (("--from", "local", f"@self/{OLD}/space%20file.md#section"),
                     ("--from", "local", "--source", f"{NEW}/LOG.md", f"../{OLD}/space%20file.md#section")):
            result = self.cli("resolve", *args, "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            target = json.loads(result.stdout)["target"]
            self.assertEqual(target["path"], f"{OLD}/space file.md")
            self.assertEqual(target["status"], "cached")
            self.assertEqual(target["url"], BASE + OLD + "/space%20file.md")
        self.assertEqual(self.cli("resolve", "--from", "local", "relative.md").returncode, 2)
        self.assertEqual(self.cli("resolve", "--from", "unknown", "@self/a.md").returncode, 2)

    def test_cli_scan_coverage_and_forget_preserve_identity_and_incoming(self):
        self.write(f"{NEW}/LOG.md", f"[target](@team/{OLD}/LOG.md)")
        result = self.cli("scan", "local", "--root", str(self.root), "--complete", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["scan"]["mode"], "complete")
        self.cli("references", "add", "local", "team", "other")
        self.assertEqual(self.cli("forget", "other").returncode, 0)
        self.assertEqual(len(self.occurrences(self.incoming(collection="other"))), 1)
        self.assertEqual(self.cli("coverage").returncode, 0)

    def test_cli_requires_inventory_scope_and_reports_failed_scan(self):
        self.assertEqual(self.cli("scan", "local", "--root", str(self.root)).returncode, 2)
        result = self.cli("scan", "local", "--root", str(self.root / "absent"), "--complete", "--json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["scan"]["mode"], "incomplete")
        self.assertEqual(self.cli("in", "local", "README.md").returncode, 2)
        self.assertEqual(self.cli("in", "unknown", OLD).returncode, 2)

    def test_global_options_before_or_after_command_and_default_private_cache(self):
        self.scan()
        before = self.cli("--json", "coverage")
        after = self.cli("coverage", "--json")
        self.assertEqual(json.loads(before.stdout), json.loads(after.stdout))
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "scan", "team", "--root", str(self.root),
                                 "--complete", "--json"], cwd=self.temp.name, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((Path(self.temp.name) / ".works/index.sqlite").is_file())

    def test_different_aliases_resolve_from_the_citing_collection(self):
        self.write(f"{NEW}/LOG.md", f"[a](@research/{OLD}/LOG.md) [b](@lab/{OLD}/LOG.md)")
        self.scan()
        other = Path(self.temp.name) / "other"
        self.write(f"{OTHER}/LOG.md", f"[c](@research/{OLD}/LOG.md)", other)
        self.scan(root=other, name="other", url_root="file://server/share/works/")
        with self.db:
            citations.replace_references(self.db, "local", {"research": "target", "lab": "target"})
            citations.replace_references(self.db, "other", {"research": "different"})
        self.assertEqual(len(self.occurrences(self.incoming(collection="target"))), 2)
        self.assertEqual(len(self.occurrences(self.incoming(collection="different"))), 1)
        self.assertEqual(self.incoming(collection="different")["works"][0]["collection"], "other")

    def test_encoded_provider_root_and_longest_matching_root(self):
        self.write(f"{NEW}/LOG.md", f"[a](https://example.test/space path/{OLD}/LOG.md)")
        self.scan(url_root="https://example.test/")
        target_root = Path(self.temp.name) / "target"
        self.write(f"{OLD}/LOG.md", "Finding", target_root)
        self.scan(root=target_root, name="target", url_root="https://example.test/space%20path/")
        occurrence = self.occurrences(self.incoming(collection="target"))[0]
        self.assertEqual(occurrence["target"]["path"], f"{OLD}/LOG.md")
        self.assertEqual(occurrence["target"]["status"], "cached")

    def test_search_ranking_and_old_cli_are_absent(self):
        for command in ("search", "show", "incoming", "outgoing", "set-references", "index", "status"):
            self.assertEqual(self.cli(command).returncode, 2)
        help_text = self.cli("--help").stdout
        self.assertIn("{in,out,resolve,scan,references,coverage,forget}", help_text)
        self.assertNotIn("--limit", help_text)
        self.assertNotIn("--alpha", help_text)

    def test_schema_change_requires_explicit_rebuild(self):
        self.db.execute("PRAGMA user_version=1")
        with self.assertRaisesRegex(ValueError, "rebuild"):
            citations.database(self.db_path)

    def test_scan_preserves_url_root_when_omitted_and_rejects_opaque_roots(self):
        self.scan()
        self.scan(url_root=None)
        self.assertEqual(citations.coverage(self.db)[0]["url_root"], BASE)
        with self.assertRaises(ValueError):
            self.scan(url_root=BASE + "?token=opaque")


class PackageTests(unittest.TestCase):
    def test_skill_and_document_links(self):
        root = SCRIPT.parents[1]
        skill = (root / "SKILL.md").read_text()
        self.assertIn("name: works\n", skill)
        self.assertIn("Do not filter citations.", skill)
        for source in (root / "SKILL.md", root / "SETUP.md", root / "INDEX.md"):
            for link in citations.parse_markdown(source.read_text()):
                target = urlsplit(link.destination)
                if not target.scheme and not target.netloc:
                    self.assertTrue((source.parent / unquote(target.path)).exists(), (source, link.destination))


if __name__ == "__main__":
    unittest.main()
