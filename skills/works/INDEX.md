# Private Markdown index

Use [links.py](scripts/links.py) with Python 3.12+ and SQLite FTS5; no third-party dependencies. Choose the Python invocation for the local environment. Run `links.py --help` or `<command> --help` for arguments.

The agent obtains readable snapshots, interprets README reference declarations and identifies collections. The script does not access providers, parse declarations, walk the collection graph or verify permissions. Keep the database and personal follows private.

## Collection names and references

Choose an index-local key for each logical collection. Supply each source's complete name mapping separately from its files:

```bash
python "<skill>/scripts/links.py" index B --root "<snapshot of B>" --complete --snapshot "<capture/version>"
python "<skill>/scripts/links.py" set-references B --reference research=D --reference lab=D
python "<skill>/scripts/links.py" set-references C --reference notes=D
python "<skill>/scripts/links.py" incoming D 2026-01-01-study/
python "<skill>/scripts/links.py" outgoing B
python "<skill>/scripts/links.py" search "shipment size" --limit 5
python "<skill>/scripts/links.py" status
```

`[study](@research/2026-01-01-study/LOG.md)` in B and `@notes/...` in C resolve to D. Nicknames may share a target. Names are case-sensitive letters/digits with `_`, `-` or `.`, starting with a letter or digit. Ordinary relative links stay local; there is no fallback. Original citation text is retained.

`set-references` replaces **all** bindings for that source; omitted names are removed. `set-references B --clear` explicitly removes them all. Queries use current bindings even if no Markdown changed. `index` never changes bindings. A referenced target can remain unindexed; declaring it does not retrieve or subscribe to it.

`incoming` and `outgoing` take an index key and optional literal collection-relative file/directory path; omission means the whole collection. Quote paths with spaces; do not URL-encode them. Incoming finds citations from every indexed source. Both also accept an ordinary HTTP(S)/file URL instead of a key and path.

Each citation includes `context`: a short excerpt around that occurrence in the cached source paragraph or list item, not a relationship label or summary. Whitespace is collapsed, the cited link is shown as its label (bare URLs as `[link]`), and clipping is marked with `...`. Context is bounded to 320 characters plus clipping markers; the full destination and source line remain separate. Read the source for qualifications beyond the excerpt.

`index --url-root URL` optionally maps a path-addressable provider URL prefix to a collection. Omission removes that URL mapping, not identity or reference bindings. Without it, named/local references still work; results have no generated browser URL. Opaque sharing URLs remain external citations, not invented path mappings. Existing ordinary URL citations resolve to known roots; alternate URLs are not inferred.

## Coverage and refresh

Supply **all collection Markdown recursively**, including WIP, supporting evidence, README and instructions; Git tracking is irrelevant. Preserve complete contents and relative paths. Exclude and report runtime/dependency/cache boundaries. Decode historical files only in cache copies with a recorded encoding assumption; preserve original evidence.

- `--complete` asserts a full supplied Markdown inventory. Only a successful complete pass removes missing files. `--partial` upserts, retaining omitted content and unresolved failures. Failed reads preserve earlier content with coverage warnings. Neither mode proves provider freshness.
- Unchanged size/mtime reuse cached text. `--force` rereads it. `--snapshot` records supplied capture/version information; indexing time is not capture time. Default database: `.works/index.sqlite`; override with `--db PATH` before the command.
- Every query reports coverage, snapshot labels, failures and truncation. Compare with private follows to identify collections not yet known to the cache. An unindexed identity or failed command is not a successful refresh.
- Query states `wip`, `finalized` and `collection` are path-based labels, not proof of editorial review. “Complete” describes coverage, not finalization.

Citation target status:

- `cached`: Markdown content exists in the cache, possibly from an older snapshot; inspect coverage.
- `missing`: Markdown path absent from a successful complete supplied snapshot, not proof of absence at the provider.
- `unchecked`: target not checked; includes unindexed/partial targets, external URLs, directories and non-Markdown attachments.
- `unbound`: the source has no declaration binding for that name.
- `invalid`: malformed name or path escaping the collection.

Search is phrase search over all text. Citation extraction covers inline/reference Markdown links and URL mentions outside code, not every Markdown/HTML syntax. Supplement it with full-text searches and source review. Headings, non-Markdown contents, truth and access are not checked.

`forget COLLECTION` clears its cached text, outgoing citations and bindings but retains its identity and other collections' references to it. It does not revoke permissions or securely erase disk bytes.

The cache schema changed with collection-scoped references. Rebuild older databases from readable snapshots and declarations; the script rejects them rather than silently migrating or deleting cached evidence.
