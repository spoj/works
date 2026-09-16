# Works

A growing list of dated contributions, connected by ordinary citations. Prior works and their evidence serve as documentation across time and people. Preserve them; later findings build on or correct them through new works, not revisions of the past.

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

For other compatible agents, add `skills/works/` to their skill search path. The agent confirms the collection folder, audience, Git choice and private follows before writing.

## One layout, personal or shared

Use the chosen collection folder directly, including a repository root:

```text
README.md
AGENTS.md                         # optional, user-owned
_wip_some-question/LOG.md          # created on demand
YYYY-MM-DD-some-finding/LOG.md
```

- **WIP** holds ongoing work: investigation, calculations, scripts, evidence and preparation of business outputs. A **draft** is an unfinished artifact within it.
- **Finalize** through editorial review of claims, evidence, scope, uncertainty and links; only then rename the WIP to a dated folder. A **work** is the retained, dated, citable contribution. Finalized does not mean correct or conclusive.
- The folder date records when that edition was finalized. `LOG.md` states the dates or periods to which its evidence and analysis apply. An unchanged copy retains its date; a new shared edition does not make old evidence new.
- **Share** means making material available to another **audience** (intended readers). Review the whole work; copy it unchanged when suitable, otherwise prepare a self-contained **shared edition** without changing the original.
- Preserve works and their addresses. Substantive corrections belong in new works citing them. Meaning-preserving fixes and brief dated sharing notes may be added in place.

A person's shared folder and a team's shared folder are ordinary collections. WIPs inherit the collection's audience; shared WIPs are not private staging areas. Reading, effective write permission and authority to contribute are separate. Keep private follows and caches outside shared boundaries. Sharing a collection can expose its WIPs and future additions too.

## Instruction ownership

- [`SKILL.md`](skills/works/SKILL.md): upstream method, finalization, sharing and indexing.
- [`SETUP.md`](skills/works/SETUP.md): upstream setup procedure and examples.
- Collection `README.md`: locally owned audience, owner, citation and contribution rules.
- Optional `AGENTS.md`: user-owned local instructions. Personal setup adds one only when no applicable file exists; updates never overwrite it.

Keep general guidance in the skill rather than copying it into local files. Changes requiring local migration should be proposed separately.

## Private discovery cache

The bundled script indexes **all Markdown recursively** in supplied collection trees, including supporting files and WIPs, into SQLite full-text and citation indexes. Query states are `wip`, `finalized` and `collection`; these are path-based labels, not proof of review. The agent supplies readable files and canonical addresses through existing tools, excluding and reporting runtime/cache boundaries. The script does not access providers.

Complete inventories and partial updates are explicit. “Complete” describes index coverage, not finalization. Failed reads retain earlier cached material with warnings; only a successful complete inventory removes missing files. Queries report coverage, freshness and truncation. Supplement extracted links with full-text searches and source review; the cache cannot prove truth, current permissions or absence of corrections elsewhere.

The method works without Python. The optional indexer requires Python 3.12+ with SQLite FTS5 and no third-party dependencies. Choose the Python invocation for the local environment. From this repository root:

```bash
python -B tests/test_links.py
```

Tests use temporary directories, not real collections or remote services.
