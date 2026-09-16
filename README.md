# Works

Preserve useful contributions as dated works, connected by ordinary citations. Keep evidence and uncertainty visible, look for later corrections, and publish to the right audience.

An [Agent Skills](https://agentskills.io) package. No hosted service, provider adapters or central knowledge registry.

## Install and start

In [pi](https://pi.dev):

```bash
pi install git:github.com/spoj/works
```

Open pi in the intended workspace and ask:

```text
/skill:works setup here
```

For other compatible agents, add `skills/works/` to their skill search path. The agent confirms the collection location, audience, Git choice and private follows before writing.

## One layout, personal or shared

```text
works/
    README.md
    AGENTS.md                         # optional, user-owned
    _wip_some-question/LOG.md          # created on demand
    YYYY-MM-DD-finished-work/LOG.md
```

A person's shared OneDrive folder and a team SharePoint folder are ordinary collections. Drafts inherit the collection's audience. Review a finished WIP before renaming it to a dated folder; corrections become new works. Shared drafts are not a private staging area.

Reading, effective write permission and authority to contribute are separate. Keep private follow lists and SQLite caches outside shared folders. Sharing an existing collection can expose its WIPs and future additions too.

## Instruction ownership

- [`SKILL.md`](skills/works/SKILL.md): upstream day-to-day method, reading, publication and indexing.
- [`SETUP.md`](skills/works/SETUP.md): upstream setup procedure and examples.
- Collection `README.md`: locally owned audience, custody, citation and publication rules.
- Optional `AGENTS.md`: user-owned local instructions. Personal setup adds one only when no applicable file exists; updates never overwrite it.

Keep general guidance in the skill rather than copying it into local files. Changes requiring local migration should be proposed separately.

## Private discovery cache

The bundled script indexes **all Markdown recursively**, including supporting files and WIPs, into SQLite full-text and citation indexes. Results label WIP references as unpublished rather than completed contributions. The agent supplies readable files and canonical addresses through existing access tools; the script does not access providers.

Complete inventories and partial updates are explicit. Failed reads retain earlier cached material with coverage warnings; only a successful complete inventory removes missing files. Queries report coverage, freshness and truncation. Extracted links are supplemented by full-text searches and source review; the cache cannot prove truth, current permissions or absence of corrections elsewhere.

The instructions work without Python. The optional indexer requires Python 3.12+ with SQLite FTS5 and no third-party Python dependencies. From this repository root:

```bash
uv run --no-project python -B tests/test_links.py
```

Tests use temporary directories, not real collections or remote services.
