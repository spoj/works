#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

_DEFINITION = re.compile(r" {0,3}\[([^]\n]+)\]:[ \t]*(.*)$")
_URL = re.compile(r"(?:https?|file)://[^\s<>\"'`]+")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_BLOCK_START = re.compile(r" {0,3}(?:[-+*]|\d+[.)]|#{1,6})\s")


@dataclass(frozen=True, slots=True)
class Link:
    source: Path
    line: int
    destination: str
    start: int
    end: int


def _unescape(value: str) -> str:
    return re.sub(r"\\(.)", r"\1", value)


def _key(value: str) -> str:
    return " ".join(_unescape(value).strip().split()).casefold()


def _mask_code(line: str) -> str:
    return re.sub(r"(`+).*?(?:\1|$)", lambda m: " " * len(m.group()), line)


def _end(text: str, start: int, opening: str, closing: str) -> int:
    depth = 0
    angle = False
    i = start
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if opening == "(" and char == "<":
            angle = True
        elif opening == "(" and char == ">" and angle:
            angle = False
        elif not angle and char == opening:
            depth += 1
        elif not angle and char == closing:
            depth -= 1
            if not depth:
                return i
        i += 1
    return -1


def _destination(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("<"):
        match = re.match(r"<((?:\\.|[^>])*)>(.*)$", raw)
        rest = match.group(2).strip() if match else ""
        if not match or (rest and rest[0] not in "\"'("):
            return None
        return _unescape(match.group(1))
    raw = re.sub(r"\s+(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')\s*$", "", raw)
    return _unescape(raw)


def _visible(text: str) -> tuple[list[str], list[str | None]]:
    raw = text.splitlines()
    visible = []
    fence = None
    for line in raw:
        if fence:
            visible.append(None)
            char, length = fence
            if re.fullmatch(f" {{0,3}}{re.escape(char)}{{{length},}}[ \\t]*", line):
                fence = None
            continue
        marker = re.match(r" {0,3}(`{3,}|~{3,})", line)
        visible.append(None if marker else _mask_code(line))
        if marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
    return raw, visible


def _references(lines: list[str | None]) -> tuple[dict[str, str], set[int]]:
    definitions = {}
    definition_lines = set()
    for number, line in enumerate(lines):
        if line is None:
            continue
        match = _DEFINITION.fullmatch(line)
        if match:
            definition_lines.add(number)
            if destination := _destination(match.group(2)):
                definitions.setdefault(_key(match.group(1)), destination)
    return definitions, definition_lines


def _line_links(masked: str, original: str, source: Path, number: int, refs: dict[str, str]) -> list[Link]:
    links = []
    i = 0
    while i < len(masked):
        if masked[i] != "[":
            i += 1
            continue
        label_end = _end(masked, i, "[", "]")
        if label_end < 0:
            i += 1
            continue
        after = label_end + 1
        destination = None
        end = label_end
        if after < len(masked) and masked[after] == "(":
            close = _end(masked, after, "(", ")")
            if close >= 0:
                destination, end = _destination(original[after + 1:close]), close
        elif after < len(masked) and masked[after] == "[":
            close = _end(masked, after, "[", "]")
            if close >= 0:
                reference = original[after + 1:close].strip() or original[i + 1:label_end]
                destination, end = refs.get(_key(reference)), close
        else:
            destination = refs.get(_key(original[i + 1:label_end]))
        if destination is None:
            i += 1
            continue
        links.append(Link(source, number, destination, i, end + 1))
        masked = masked[:i] + " " * (end + 1 - i) + masked[end + 1:]
        i = end + 1
    for match in _URL.finditer(masked):
        destination = match.group().rstrip(".,;:!")
        for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
            while destination.endswith(closing) and destination.count(closing) > destination.count(opening):
                destination = destination[:-1]
        links.append(Link(source, number, destination, match.start(), match.start() + len(destination)))
    return links


def parse_markdown(text: str, source: str | Path = Path()) -> list[Link]:
    raw, visible = _visible(text)
    refs, definitions = _references(visible)
    return [link for number, line in enumerate(visible)
            if line is not None and number not in definitions
            for link in _line_links(line, raw[number], Path(source), number + 1, refs)]


def citation_context(lines: list[str], link: Link) -> str:
    line = link.line - 1
    first = last = line
    while (first > 0 and lines[first - 1].strip() and not _BLOCK_START.match(lines[first])
           and not _DEFINITION.fullmatch(lines[first - 1])):
        first -= 1
    while (last + 1 < len(lines) and lines[last + 1].strip() and not _BLOCK_START.match(lines[last + 1])
           and not _DEFINITION.fullmatch(lines[last + 1])):
        last += 1
    citation = lines[line][link.start:link.end]
    label = citation[:_end(citation, 0, "[", "]") + 1] if citation.startswith("[") else "[link]"
    if len(label) > 80:
        label = label[:77] + "..."
    before = re.sub(r"\s+", " ", "\n".join(lines[first:line] + [lines[line][:link.start]])).lstrip()
    after = re.sub(r"\s+", " ", "\n".join([lines[line][link.end:]] + lines[line + 1:last + 1])).rstrip()
    text = before + label + after
    start = max(0, len(before) - (320 - len(label)) // 2)
    end = min(len(text), start + 320)
    start = max(0, end - 320)
    return ("... " if start else "") + text[start:end] + (" ..." if end < len(text) else "")


def normalize_url(value: str) -> str:
    parsed = urlsplit(value)
    path = quote(unquote(parsed.path), safe="/:@!$&'()*+,;=-._~")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


def database(path: str | Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    if (db.execute("SELECT 1 FROM sqlite_master WHERE name = 'collections'").fetchone()
            and db.execute("PRAGMA user_version").fetchone()[0] != 1):
        db.close()
        raise ValueError("index schema changed; rebuild this disposable cache in a new database")
    db.executescript("""
        PRAGMA user_version = 1;
        CREATE TABLE IF NOT EXISTS collections (
            name TEXT PRIMARY KEY, url_root TEXT UNIQUE,
            attempted TEXT, complete TEXT, snapshot TEXT, complete_snapshot TEXT,
            mode TEXT NOT NULL DEFAULT 'unindexed', errors TEXT NOT NULL DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS refs (
            source TEXT NOT NULL REFERENCES collections(name),
            alias TEXT NOT NULL, target TEXT NOT NULL REFERENCES collections(name),
            PRIMARY KEY(source, alias)
        );
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            collection TEXT NOT NULL REFERENCES collections(name), path TEXT NOT NULL,
            mtime_ns INTEGER NOT NULL, size INTEGER NOT NULL, indexed TEXT NOT NULL,
            UNIQUE(collection, path)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS texts USING fts5(body);
        CREATE TABLE IF NOT EXISTS links (
            source INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            line INTEGER NOT NULL, destination TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS delete_text AFTER DELETE ON files BEGIN
            DELETE FROM texts WHERE rowid = old.id;
        END;
    """)
    return db


def set_references(db: sqlite3.Connection, source: str, refs: dict[str, str]) -> None:
    for name in [source, *refs, *refs.values()]:
        if not _NAME.fullmatch(name):
            raise ValueError(f"invalid collection key or reference name: {name}")
    db.executemany("INSERT INTO collections(name) VALUES (?) ON CONFLICT(name) DO NOTHING",
                   [(name,) for name in {source, *refs.values()}])
    db.execute("DELETE FROM refs WHERE source = ?", (source,))
    db.executemany("INSERT INTO refs(source, alias, target) VALUES (?, ?, ?)",
                   [(source, alias, target) for alias, target in refs.items()])


def index_collection(db: sqlite3.Connection, name: str, root: Path, complete: bool,
                     snapshot: str = "unknown", force: bool = False, url_root: str | None = None) -> dict:
    if not _NAME.fullmatch(name):
        raise ValueError(f"invalid collection key: {name}")
    if url_root is not None:
        parsed = urlsplit(url_root)
        if parsed.scheme not in ("http", "https", "file") or parsed.query or parsed.fragment:
            raise ValueError("URL root must be a directory http(s) or file URL without a query or fragment")
        url_root = normalize_url(url_root).rstrip("/") + "/"
    db.execute("INSERT INTO collections(name) VALUES (?) ON CONFLICT(name) DO NOTHING", (name,))
    previous = db.execute("SELECT errors FROM collections WHERE name = ?", (name,)).fetchone()
    db.execute("UPDATE collections SET url_root = ? WHERE name = ?", (url_root, name))
    root = root.expanduser().resolve()
    now = datetime.now(timezone.utc).isoformat()
    prior_errors = json.loads(previous["errors"])
    failed_paths = {error["path"] for error in prior_errors}
    errors = [] if complete else prior_errors
    seen = set()
    changed = 0
    reused = 0
    removed = 0
    if not root.is_dir():
        errors.append({"path": ".", "error": "supplied root is not a readable directory"})
    for directory, dirs, names in os.walk(
        root, onerror=lambda error: errors.append({"path": str(error.filename), "error": str(error)}),
    ):
        for item in dirs[:]:
            path = Path(directory) / item
            if item == ".git":
                dirs.remove(item)
            elif path.is_symlink() or path.is_junction():
                errors.append({"path": path.relative_to(root).as_posix(), "error": "directory link not followed"})
                dirs.remove(item)
        for item in sorted(names):
            path = Path(directory) / item
            if path.suffix.lower() != ".md":
                continue
            relative = path.relative_to(root).as_posix()
            seen.add(relative)
            try:
                if path.is_symlink():
                    raise ValueError("file link not followed")
                stat = path.stat()
                previous = db.execute(
                    "SELECT mtime_ns, size FROM files WHERE collection = ? AND path = ?", (name, relative),
                ).fetchone()
                if (not force and relative not in failed_paths and previous
                        and (previous["mtime_ns"], previous["size"]) == (stat.st_mtime_ns, stat.st_size)):
                    reused += 1
                    errors = [error for error in errors if error["path"] != relative]
                    continue
                body = path.read_text(encoding="utf-8-sig")
                links = [(link.line, link.destination) for link in parse_markdown(body, relative)]
            except (OSError, UnicodeError, ValueError) as error:
                errors = [item for item in errors if item["path"] != relative]
                errors.append({"path": relative, "error": str(error)})
                continue
            errors = [error for error in errors if error["path"] != relative]
            db.execute("DELETE FROM files WHERE collection = ? AND path = ?", (name, relative))
            row = db.execute(
                "INSERT INTO files(collection, path, mtime_ns, size, indexed) VALUES (?, ?, ?, ?, ?)",
                (name, relative, stat.st_mtime_ns, stat.st_size, now),
            ).lastrowid
            db.execute("INSERT INTO texts(rowid, body) VALUES (?, ?)", (row, body))
            db.executemany("INSERT INTO links(source, line, destination) VALUES (?, ?, ?)",
                           [(row, *link) for link in links])
            changed += 1
    if complete and not errors:
        for row in db.execute("SELECT id, path FROM files WHERE collection = ?", (name,)).fetchall():
            if row["path"] not in seen:
                db.execute("DELETE FROM files WHERE id = ?", (row["id"],))
                removed += 1
    mode = "incomplete" if errors else "complete" if complete else "partial"
    db.execute("""
        UPDATE collections SET attempted = ?,
            complete = CASE WHEN ? = 'complete' THEN ? ELSE complete END,
            complete_snapshot = CASE WHEN ? = 'complete' THEN ? ELSE complete_snapshot END,
            snapshot = ?, mode = ?, errors = ? WHERE name = ?
        """, (now, mode, now, mode, snapshot, snapshot, mode, json.dumps(errors), name))
    return {"collection": name, "mode": mode, "seen": len(seen), "changed": changed,
            "reused": reused, "removed": removed, "errors": errors}


def coverage(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("""
        SELECT collections.*, COUNT(files.id) AS indexed_files FROM collections
        LEFT JOIN files ON files.collection = collections.name
        GROUP BY collections.name ORDER BY collections.name
    """)
    return [dict(row) | {"errors": json.loads(row["errors"]), "references": dict(db.execute(
        "SELECT alias, target FROM refs WHERE source = ? ORDER BY alias", (row["name"],),
    ))} for row in rows]


def collection_path(value: str) -> str:
    path = posixpath.normpath(value)
    if path == ".." or path.startswith(("../", "/")) or "\\" in path:
        raise ValueError("reference path must stay inside its collection")
    return "" if path == "." else path


def contains(parent: str, child: str) -> bool:
    return not parent or child == parent.rstrip("/") or child.startswith(parent.rstrip("/") + "/")


def resolve_reference(collection: str, source: str, destination: str, collections: dict) -> dict:
    parsed = urlsplit(destination)
    target = {"collection": None, "path": None, "url": None, "status": "unchecked"}
    if destination.startswith("@"):
        alias, _, path = parsed.path[1:].partition("/")
        if not _NAME.fullmatch(alias):
            raise ValueError("invalid reference name")
        target["path"] = collection_path(unquote(path))
        target["collection"] = collections[collection]["references"].get(alias)
        if target["collection"] is None:
            target["status"] = "unbound"
    elif parsed.scheme or parsed.netloc:
        target["url"] = normalize_url(destination)
        for other in sorted(collections.values(), key=lambda c: len(c["url_root"] or ""), reverse=True):
            if other["url_root"] and contains(other["url_root"], target["url"]):
                target["collection"] = other["name"]
                target["path"] = collection_path(unquote(urlsplit(target["url"]).path[len(urlsplit(other["url_root"]).path):]))
                break
    else:
        target["collection"] = collection
        target["path"] = collection_path(posixpath.join(posixpath.dirname(source), unquote(parsed.path)) if parsed.path else source)
    if target["collection"] is not None and target["url"] is None:
        url_root = collections[target["collection"]]["url_root"]
        if url_root:
            target["url"] = normalize_url(urljoin(url_root, quote(target["path"], safe="/")))
    return target


def query(db: sqlite3.Connection, command: str, value: str, limit: int = 50, path: str = "") -> dict:
    report = coverage(db)
    collections = {c["name"]: c for c in report}
    if command == "search":
        phrase = '"' + value.replace('"', '""') + '"'
        rows = [dict(row) for row in db.execute("""
            SELECT files.collection, files.path, files.indexed,
                snippet(texts, 0, '[', ']', ' ... ', 32) AS excerpt
            FROM texts JOIN files ON files.id = texts.rowid
            WHERE texts MATCH ? ORDER BY rank, files.collection, files.path LIMIT ?
        """, (phrase, limit + 1))]
    else:
        if urlsplit(value).scheme in ("http", "https", "file"):
            if path:
                raise ValueError("supply either a collection and path or a URL")
            requested = resolve_reference("", "", value, collections)
        else:
            if value not in collections:
                raise ValueError(f"unknown collection key: {value}")
            requested = {"collection": value, "path": collection_path(path)}
        cached = {(row[0], row[1]) for row in db.execute("SELECT collection, path FROM files")}
        rows = []
        contexts = {}
        for row in db.execute("""
            SELECT files.id AS source_id, files.collection, files.path, files.indexed, links.line, links.destination
            FROM links JOIN files ON files.id = links.source
            ORDER BY files.collection, files.path, links.line, links.rowid
        """):
            item = dict(row)
            source_id = item.pop("source_id")
            try:
                target = resolve_reference(item["collection"], item["path"], item["destination"], collections)
            except ValueError as error:
                target = {"collection": None, "path": None, "url": None, "status": "invalid", "error": str(error)}
            source = resolve_reference(item["collection"], item["path"], "", collections)
            candidate = target if command == "incoming" else source
            if requested["collection"] is not None:
                match = (candidate["collection"] == requested["collection"]
                         and contains(requested["path"], candidate["path"]))
            else:
                match = candidate["url"] is not None and contains(requested["url"], candidate["url"])
            if not match:
                continue
            if target["collection"] is not None:
                if (target["collection"], target["path"]) in cached:
                    target["status"] = "cached"
                elif (collections[target["collection"]]["mode"] == "complete"
                      and target["path"].lower().endswith(".md")):
                    target["status"] = "missing"
            if source_id not in contexts:
                body = db.execute("SELECT body FROM texts WHERE rowid = ?", (source_id,)).fetchone()[0]
                lines = body.splitlines()
                contexts[source_id] = {}
                for link in parse_markdown(body):
                    contexts[source_id].setdefault((link.line, link.destination), []).append(citation_context(lines, link))
            item["context"] = contexts[source_id][(item["line"], item["destination"])].pop(0)
            item["target"] = target
            rows.append(item)
            if len(rows) > limit:
                break
    for item in rows[:limit]:
        item["url"] = resolve_reference(item["collection"], item["path"], "", collections)["url"]
        folder = item["path"].split("/", 1)[0]
        item["state"] = ("wip" if folder.startswith("_wip_") else "finalized"
                         if re.fullmatch(r"\d{4}-\d{2}-\d{2}-.+", folder) else "collection")
    return {"coverage": report, "matches": rows[:limit], "truncated": len(rows) > limit}


def _limit(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("limit must be non-negative")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Index local Markdown snapshots and resolve collection-scoped citations. No network access.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples (collection keys are private to this index):
  links.py index B --root ./snapshot-B --complete
  links.py set-references B --reference research=D --reference lab=D
  links.py set-references C --reference notes=D
  links.py incoming D 2026-01-01-study/     # find B and C citations, even before indexing D
  links.py outgoing B                     # inspect targets, including unbound names
  links.py search "shipment size" --limit 5
  links.py set-references B --clear       # remove all B's reference names

@research/path inside B uses B's declarations, not the reader's names.
Indexing files does not change these bindings. Read README declarations yourself;
set-references replaces the whole source mapping. No graph walking is performed.''')
    parser.add_argument("--db", type=Path, default=Path(".works/index.sqlite"),
                        help="private SQLite cache (default: .works/index.sqlite)")
    commands = parser.add_subparsers(dest="command", required=True)
    index = commands.add_parser("index", help="index a full snapshot or a partial update tree")
    index.add_argument("collection", metavar="COLLECTION", help="logical collection key in this private index")
    index.add_argument("--root", type=Path, required=True, metavar="DIRECTORY",
                       help="readable local tree or snapshot; preserve collection-relative paths")
    index.add_argument("--url-root", metavar="URL",
                       help="optional URL prefix for ordinary hyperlinks; omission removes URL mapping")
    mode = index.add_mutually_exclusive_group(required=True)
    mode.add_argument("--complete", action="store_true", help="full Markdown inventory; remove missing files only after success")
    mode.add_argument("--partial", action="store_true", help="upsert only; omitted files are not deleted")
    index.add_argument("--snapshot", default="unknown", help="source revision or capture time, when established")
    index.add_argument("--force", action="store_true", help="reread files even if size and mtime match")
    commands.add_parser("status", help="report coverage and bindings; compare with private follows")
    references = commands.add_parser("set-references", help="replace ALL reference names for one source collection",
                                    description="Replace this source's complete name-to-collection mapping; no file reads.")
    references.add_argument("collection", metavar="SOURCE_COLLECTION")
    reference_mode = references.add_mutually_exclusive_group(required=True)
    reference_mode.add_argument("--reference", action="append", default=[], metavar="NAME=COLLECTION",
                                help="a name used as @NAME/path in this source; repeat for all names, including nicknames")
    reference_mode.add_argument("--clear", action="store_true", help="explicitly remove every binding for this source")
    forget = commands.add_parser("forget", help="clear cached content, retaining identity and incoming references")
    forget.add_argument("collection")
    for command in ("incoming", "outgoing", "search"):
        sub = commands.add_parser(command, help={"incoming": "find citations and source context pointing to a collection, work or file",
                                                 "outgoing": "inspect citations and source context from a collection, work or file",
                                                 "search": "phrase search across all indexed Markdown"}[command])
        sub.add_argument("value", metavar="PHRASE" if command == "search" else "COLLECTION_OR_URL")
        if command != "search":
            sub.add_argument("path", nargs="?", default="", metavar="PATH",
                             help="literal collection-relative file or directory, not a URL; omitted means the whole collection")
        sub.add_argument("--limit", type=_limit, default=50, metavar="COUNT",
                         help="maximum matches (default: 50); output reports truncation")
    args = parser.parse_args(argv)
    refs = {}
    for entry in getattr(args, "reference", []):
        alias, separator, target = entry.partition("=")
        if not separator or alias in refs:
            parser.error("each --reference must be a unique NAME=COLLECTION binding")
        refs[alias] = target
    if args.command not in ("index", "set-references") and not args.db.is_file():
        parser.error("index does not exist; compare unindexed collections with the follow list")
    try:
        with database(args.db) as db:
            if args.command == "index":
                result = index_collection(db, args.collection, args.root, args.complete,
                                          args.snapshot, args.force, args.url_root)
                result["coverage"] = coverage(db)
                status = int(bool(result["errors"]))
            elif args.command == "set-references":
                set_references(db, args.collection, refs)
                result, status = {"coverage": coverage(db)}, 0
            elif args.command == "forget":
                db.execute("DELETE FROM files WHERE collection = ?", (args.collection,))
                db.execute("DELETE FROM refs WHERE source = ?", (args.collection,))
                db.execute("""UPDATE collections SET attempted = NULL, complete = NULL, snapshot = NULL,
                    complete_snapshot = NULL, mode = 'unindexed', errors = '[]' WHERE name = ?""", (args.collection,))
                result, status = {"coverage": coverage(db)}, 0
            elif args.command == "status":
                result, status = {"coverage": coverage(db)}, 0
            else:
                result, status = query(db, args.command, args.value, args.limit, getattr(args, "path", "")), 0
        print(json.dumps(result, indent=2))
        return status
    except (OSError, ValueError, sqlite3.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
