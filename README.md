# Works

Preserve useful contributions as dated works, connected by ordinary citations. Keep evidence and uncertainty visible, look for later corrections, and publish to the right audience.

An [Agent Skills](https://agentskills.io) package for personal workspaces and shared collections. No hosted service, provider adapters or central knowledge registry.

## Install and start

In [pi](https://pi.dev):

```bash
pi install git:github.com/spoj/works
```

Open pi in an empty directory, load the skill and ask for setup:

```text
/skill:works setup here
```

The agent confirms the location, personal versus shared use, Git choice and any collections to follow before creating files. For other compatible agents, add `skills/works/` to the agent's skill search path and ask it to load **Works** and set up the current directory.

A personal workspace starts with `AGENTS.md`, `wip/` and `works/`. A shared collection starts with `README.md`; only completed dated works are added there. Draft elsewhere. Shared storage can be Git, a network folder, SharePoint or another location the agent can already access.

A person-owned folder deliberately shared with someone is an ordinary shared collection. Reading, technical write permission and authority to publish are separate. Sharing an existing works folder changes its audience, including potentially all future additions; private instructions, drafts, follow lists and indexes stay outside that boundary.

## Who owns the instructions?

| File | Owner and update behavior |
| --- | --- |
| [`SKILL.md`](skills/works/SKILL.md) | Upstream method: day-to-day principles, reading, publication and indexing. Updated with the installed skill. |
| [`SETUP.md`](skills/works/SETUP.md) | Upstream setup procedure and examples for new workspaces. |
| Workspace `AGENTS.md` | User-owned local rules, private follow list and access details. Generated once, editable afterward, never overwritten by skill updates. |
| Collection `README.md` | Collection-owned audience, custody, citation convention and publication procedure. |

Keep the reusable method in the skill rather than duplicating it in local instructions. Updating the skill does not migrate or rewrite existing workspaces. If a change needs local configuration updates, the agent should propose those separately.

## Discovery without a crawler

The bundled Python script indexes **all Markdown recursively**, not just `LOG.md`, into a private SQLite full-text and citation cache. The agent obtains readable files through existing access tools; the script knows nothing about the storage provider.

Canonical citation locations are separate from temporary download paths. Full snapshots and partial updates are explicit. Failed reads retain earlier cached material with coverage warnings; only a successful complete inventory removes missing files. Queries report coverage, freshness information and truncation.

The cache does not prove truth, source freshness, reader access or absence of corrections elsewhere. Extracted links are supplemented by full-text searches and source review. No remote URLs are fetched. See the skill for commands and limitations.

## Repository

```text
skills/works/
    SKILL.md
    SETUP.md
    scripts/links.py
tests/test_links.py
```

The instructions work without Python. The optional indexer requires Python 3.12+ with SQLite FTS5, with no third-party Python dependencies. From the repository root:

```bash
uv run --no-project python -B tests/test_links.py
```

Or run the same test file with an existing compatible Python interpreter. Tests use temporary directories, not real collections or remote services.
