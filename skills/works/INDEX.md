# Private citation lookup

Use [citations.py](scripts/citations.py) with Python 3.12+ and SQLite; no dependencies. Choose the local Python invocation. Commands below abbreviate `python "<skill>/scripts/citations.py"` as `citations.py`. Use `--help` for each command. Default output is text; `--json` returns the same complete information structurally. `--db PATH` selects a private cache instead of `.works/index.sqlite`.

Find and read Markdown with ordinary tools. This script supplies the reverse connections those tools do not automatically show. It has no search, ranking, age/size weighting, graph traversal, network access or publication operations.

## Read a work's citations

```bash
citations.py in local 2026-01-01-study/
citations.py out local 2026-01-01-study/
citations.py resolve --from local '@research/2026-01-01-study/LOG.md'
citations.py resolve --from local --source 2026-01-02-review/LOG.md '../2026-01-01-study/LOG.md'
```

**Before relying on a work, inspect `in`. Do not filter citations.**

- `in` shows every indexed incoming cross-work citation, grouped by citing collection/work, then filename. Every occurrence retains its source line, original destination and full surrounding paragraph or list item. Context is original Markdown, not a generated relationship label or a clipped excerpt. Repeated links are separate occurrences, including opposing claims on one line.
- `out` lists distinct cited works and destination paths/fragments. Repeated occurrences do not create extra destinations. Unresolved references remain visible separately.
- Both take a collection key and a work path. A path to any file inside a work selects the **whole work**, including citations targeting its supporting files and non-Markdown artifacts. There is no result limit, relevance filter or date filter. Ordering is deterministic by collection, work, file and line. If a shell/tool truncates output, save it to a file and read the remainder.
- A work is identified by its top-level `YYYY-MM-DD-slug/` or `_wip_slug/` directory. Nested supporting directories belong to that work. Identity includes the collection, so equal folder names in different collections are distinct. WIP/finalized labels describe paths, not approval or correctness.
- Within-work links, collection-level navigation and URLs outside known collection roots are not cross-work citations. All Markdown is scanned, but those links do not appear in `in`/`out`. Use `resolve` for an individual link and ordinary tools for other navigation.
- `resolve` explains the source-scoped name, destination collection/path, provider URL and cached availability. Relative links require `--source FILE`; named links use the `--from` collection's declarations. It does not check live access.

A later work need not match your search terms or have any incoming citations of its own to appear in `in`. Full context lets the reader decide whether it contradicts, extends or merely mentions the selected work.

## Collections, names and snapshots

The agent reads collection READMEs, identifies their referenced collections and supplies the bindings. This is not Git remote configuration: declarations travel with the writing, personal follows belong to the reader, and the cache records only supplied snapshots. Declaring a name neither retrieves nor follows its target.

```bash
citations.py references add local research team
citations.py references add local lab team
citations.py references list local
citations.py references remove local lab
citations.py scan team --root ./team-snapshot --complete --snapshot 'capture time or revision'
citations.py coverage
```

Names are case-sensitive letters/digits with `_`, `-` or `.`, starting with a letter or digit. Different names may identify the same collection. `add` preserves other bindings and refuses to repoint an existing name silently. These commands change only the private cache, not README declarations. `scan` never changes reference bindings. An unindexed collection can still be a known citation target.

`scan --url-root URL` supplies a path-addressable provider URL prefix, allowing ordinary HTTP(S)/file links to resolve to a collection. Omission leaves an existing mapping unchanged. Do not infer paths from opaque sharing URLs or invent URL aliases. Collection identity is independent of the local snapshot path.

## Coverage and refresh

Obtain readable snapshots through existing tools. Supply **all collection Markdown recursively**, including supporting evidence, instructions and WIPs, independent of Git tracking. Exclude runtime/dependency/cache trees before supplying the snapshot. Decode historical files only in cache copies with a recorded encoding assumption; preserve originals.

- `--complete` asserts a complete supplied Markdown inventory. Only a successful complete scan removes missing files. `--partial` updates supplied files without deleting omitted ones.
- Failed reads retain earlier citations/context with coverage warnings. Unchanged size/mtime reuse cached records; `--force` rereads them.
- `--snapshot` identifies source capture/version. Scanning time is separate and does not establish source freshness or current access.
- Every result includes coverage and failures. Compare it with private follows to identify collections absent from the cache. `in` also reports unresolved names/invalid links from scanned works because their destinations cannot be ruled out; `out` reports these for the selected work. Repair the bindings or inspect the source rather than interpreting an empty result as absence of later treatment.

Target status is `cached` for present Markdown; `missing` for an absent Markdown path in a successfully complete snapshot; `unchecked` for partial/unindexed targets, directories, attachments and external URLs; `unbound` for an undeclared name; or `invalid` for malformed/escaping paths. None proves truth, provider availability, heading validity or reader permission.

Extraction supports inline/reference Markdown links and ordinary URL mentions outside inline/fenced code, not every Markdown/HTML construct. Supplement it with ordinary source review when needed. Original destinations and full citation blocks are cached with file metadata; there is no full-text search index. The cache is disposable, not evidence.

`forget COLLECTION` clears that collection's cached files and outgoing bindings, retaining its identity and other collections' incoming references. It does not delete source files, revoke permissions or securely erase cached data. Keep the private follow list independent of SQLite.

Schema 2 requires rebuilding older caches from readable snapshots into a new database. No historical work or evidence file needs to change.
