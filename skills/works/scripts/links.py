#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

_DEFINITION = re.compile(r" {0,3}\[([^]\n]+)\]:[ \t]*(.*)$")
_URL = re.compile(r"(?:https?|file)://[^\s<>\"'`]+")


@dataclass(frozen=True, slots=True)
class Link:
    source: Path
    line: int
    destination: str


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
        links.append(Link(source, number, destination))
        masked = masked[:i] + " " * (end + 1 - i) + masked[end + 1:]
        i = end + 1
    for match in _URL.finditer(masked):
        destination = match.group().rstrip(".,;:!")
        for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
            while destination.endswith(closing) and destination.count(closing) > destination.count(opening):
                destination = destination[:-1]
        links.append(Link(source, number, destination))
    return links


def parse_markdown(text: str, source: str | Path = Path()) -> list[Link]:
    raw, visible = _visible(text)
    refs, definitions = _references(visible)
    return [link for number, line in enumerate(visible)
            if line is not None and number not in definitions
            for link in _line_links(line, raw[number], Path(source), number + 1, refs)]


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
    db.executescript("""
        CREATE TABLE IF NOT EXISTS collections (
            name TEXT PRIMARY KEY, base TEXT UNIQUE NOT NULL,
            attempted TEXT, complete TEXT, snapshot TEXT, complete_snapshot TEXT,
            mode TEXT NOT NULL DEFAULT 'partial', errors TEXT NOT NULL DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            collection TEXT NOT NULL REFERENCES collections(name) ON DELETE CASCADE,
            path TEXT NOT NULL, url TEXT NOT NULL,
            mtime_ns INTEGER NOT NULL, size INTEGER NOT NULL, indexed TEXT NOT NULL,
            UNIQUE(collection, path)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS texts USING fts5(body);
        CREATE TABLE IF NOT EXISTS links (
            source INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            line INTEGER NOT NULL, destination TEXT NOT NULL, target TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS links_target ON links(target);
        CREATE TRIGGER IF NOT EXISTS delete_text AFTER DELETE ON files BEGIN
            DELETE FROM texts WHERE rowid = old.id;
        END;
    """)
    return db


def index_collection(db: sqlite3.Connection, name: str, root: Path, base: str,
                     complete: bool, snapshot: str = "unknown", force: bool = False) -> dict:
    parsed = urlsplit(base)
    if parsed.scheme not in ("http", "https", "file") or parsed.query or parsed.fragment:
        raise ValueError("base must be a directory http(s) or file URL without a query or fragment")
    base = normalize_url(base).rstrip("/") + "/"
    previous = db.execute("SELECT base, errors FROM collections WHERE name = ?", (name,)).fetchone()
    if previous and previous["base"] != base:
        raise ValueError("collection identity changed; forget it explicitly before reusing the name")
    db.execute("INSERT INTO collections(name, base) VALUES (?, ?) ON CONFLICT(name) DO NOTHING", (name, base))
    root = root.expanduser().resolve()
    now = datetime.now(timezone.utc).isoformat()
    prior_errors = json.loads(previous["errors"]) if previous else []
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
                url = normalize_url(urljoin(base, quote(relative, safe="/")))
                links = [(link.line, link.destination, normalize_url(urljoin(url, link.destination)))
                         for link in parse_markdown(body, relative)]
            except (OSError, UnicodeError, ValueError) as error:
                errors = [item for item in errors if item["path"] != relative]
                errors.append({"path": relative, "error": str(error)})
                continue
            errors = [error for error in errors if error["path"] != relative]
            db.execute("DELETE FROM files WHERE collection = ? AND path = ?", (name, relative))
            row = db.execute(
                "INSERT INTO files(collection, path, url, mtime_ns, size, indexed) VALUES (?, ?, ?, ?, ?, ?)",
                (name, relative, url, stat.st_mtime_ns, stat.st_size, now),
            ).lastrowid
            db.execute("INSERT INTO texts(rowid, body) VALUES (?, ?)", (row, body))
            db.executemany("INSERT INTO links(source, line, destination, target) VALUES (?, ?, ?, ?)",
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
    return [dict(row) | {"errors": json.loads(row["errors"])} for row in rows]


def query(db: sqlite3.Connection, command: str, value: str, limit: int = 50) -> dict:
    if command == "search":
        phrase = '"' + value.replace('"', '""') + '"'
        rows = db.execute("""
            SELECT files.collection, files.path, files.url, files.indexed,
                snippet(texts, 0, '[', ']', ' ... ', 32) AS excerpt
            FROM texts JOIN files ON files.id = texts.rowid
            WHERE texts MATCH ? ORDER BY rank, files.url LIMIT ?
        """, (phrase, limit + 1)).fetchall()
    else:
        if urlsplit(value).scheme not in ("http", "https", "file"):
            raise ValueError("incoming/outgoing requires a canonical http(s) or file URL")
        target = normalize_url(value).rstrip("/")
        column = "links.target" if command == "incoming" else "files.url"
        rows = db.execute(f"""
            SELECT files.collection, files.path, files.url, files.indexed,
                links.line, links.destination, links.target
            FROM links JOIN files ON files.id = links.source
            WHERE {column} = ? OR instr({column}, ?) = 1
            ORDER BY files.collection, files.path, links.line LIMIT ?
        """, (target, target + "/", limit + 1)).fetchall()
    matches = []
    for row in rows[:limit]:
        item = dict(row)
        folder = item["path"].split("/", 1)[0]
        item["state"] = ("wip" if folder.startswith("_wip_") else "completed"
                         if re.fullmatch(r"\d{4}-\d{2}-\d{2}-.+", folder) else "collection")
        matches.append(item)
    return {"coverage": coverage(db), "matches": matches, "truncated": len(rows) > limit}


def _limit(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("limit must be non-negative")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index supplied Markdown trees; no network or permission checks.")
    parser.add_argument("--db", type=Path, default=Path(".works/index.sqlite"))
    commands = parser.add_subparsers(dest="command", required=True)
    index = commands.add_parser("index", help="index a full snapshot or a partial update tree")
    index.add_argument("collection")
    index.add_argument("--root", type=Path, required=True, help="readable tree, with collection-relative paths")
    index.add_argument("--base", required=True, help="canonical directory URL, not a download location")
    mode = index.add_mutually_exclusive_group(required=True)
    mode.add_argument("--complete", action="store_true", help="assert full collection inventory")
    mode.add_argument("--partial", action="store_true", help="upsert only; omitted files are not deleted")
    index.add_argument("--snapshot", default="unknown", help="source revision or capture time, when established")
    index.add_argument("--force", action="store_true", help="reread files even if size and mtime match")
    commands.add_parser("status", help="report known coverage; compare with the private follow list")
    forget = commands.add_parser("forget", help="remove a collection's cached text and links")
    forget.add_argument("collection")
    for command in ("incoming", "outgoing", "search"):
        sub = commands.add_parser(command)
        sub.add_argument("value", help="canonical file/work URL, or a search phrase")
        sub.add_argument("--limit", type=_limit, default=50)
    args = parser.parse_args(argv)
    if args.command != "index" and not args.db.is_file():
        parser.error("index does not exist; compare unindexed collections with the follow list")
    try:
        with database(args.db) as db:
            if args.command == "index":
                result = index_collection(db, args.collection, args.root, args.base,
                                          args.complete, args.snapshot, args.force)
                result["coverage"] = coverage(db)
                status = int(bool(result["errors"]))
            elif args.command == "forget":
                db.execute("DELETE FROM collections WHERE name = ?", (args.collection,))
                result, status = {"coverage": coverage(db)}, 0
            elif args.command == "status":
                result, status = {"coverage": coverage(db)}, 0
            else:
                result, status = query(db, args.command, args.value, args.limit), 0
        print(json.dumps(result, indent=2))
        return status
    except (OSError, ValueError, sqlite3.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
