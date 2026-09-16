# Private Markdown index

Use the bundled [indexer](scripts/links.py), not a script copied into each collection. It requires Python 3.12+ with SQLite FTS5 and no third-party dependencies. Choose the Python invocation according to the local environment and instructions. The script does not access remote services or verify permissions.

Obtain a readable collection tree or update batch through existing tools. Preserve relative paths and complete file contents, not excerpts. Keep runtime/dependency directories and private caches out of supplied snapshots and report these boundaries. Establish a path-addressable canonical directory URL (`https://…/` or `file://…/`) independently of the checkout, mount or download path. Resolve opaque sharing links separately; URL aliases are not inferred.

Index **every `.md` recursively in the supplied collection tree**, including WIP, supporting files, evidence extracts, README and optional instructions. Git tracking is irrelevant. Git internals are excluded; unreadable paths, non-UTF-8 files and unfollowed symlinks are coverage gaps. If an index copy needs decoding, preserve original evidence and record the encoding assumption. Query results distinguish `wip`, `finalized` and `collection` material by its collection-relative path; the label is not proof of editorial review. “Complete” describes index coverage, not finalization.

Run from the private workspace, substituting the Python invocation, installed skill and configured locations:

```bash
python "<skill>/scripts/links.py" --db ".works/index.sqlite" index team --root "<readable tree>" --base "https://example.org/works/" --complete --snapshot "<source version or capture time>"
python "<skill>/scripts/links.py" --db ".works/index.sqlite" status
python "<skill>/scripts/links.py" --db ".works/index.sqlite" incoming "https://example.org/works/YYYY-MM-DD-slug/"
python "<skill>/scripts/links.py" --db ".works/index.sqlite" outgoing "https://example.org/works/YYYY-MM-DD-slug/"
python "<skill>/scripts/links.py" --db ".works/index.sqlite" search "work name"
```

- `--complete` asserts a full supplied inventory; only a successful complete pass removes missing files. It does not establish provider freshness. `--partial` upserts only, retaining omitted files and unresolved previous failures. Failed reads preserve earlier cached content with coverage warnings.
- Unchanged size/mtime reuse cached text. Use `--force` when those signals are unreliable. A complete pass still enumerates files; provider change listings can supply partial batches instead.
- Every query reports coverage, last complete indexing time, snapshot labels, failures and truncation. Indexing time is not capture time or current access. Unindexed followed collections are also gaps. A failed command is not a successful refresh.
- Search is phrase search over all indexed text. Incoming/outgoing include descendants of the supplied canonical address. Extraction covers inline/reference Markdown links and URL mentions outside code, not every Markdown/HTML syntax. Full-text searches and source review remain necessary.
- Non-Markdown attachments are not indexed. References are not checks of existence, headings, truth or authorization. `forget <collection>` removes its active cached content, not permissions or securely erased disk bytes. Never share the database or private follow lists.
