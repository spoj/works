# Works

A growing list of dated contributions, connected by ordinary citations. Prior works and their evidence serve as documentation across time and people. Preserve them; later findings build on or correct them through new works, not revisions of the past.

Works applies independently of how these folders are stored or shared. The agent must understand the surrounding access, visibility and authorization sufficiently to apply it appropriately; Works defines no sharing workflow or permission model.

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

## Collection layout

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
- When adapting a work for other readers, retain a self-contained **shared edition** without changing the original. Review supporting evidence and preserve what references mean in the destination context.
- Preserve works and their addresses. Substantive corrections belong in new works citing them. Meaning-preserving fixes and brief dated sharing notes may be added in place.

Check actual storage permissions and task authorization before writing or copying. WIP names and README text do not set storage permissions. Keep personal follows, caches and machine-specific details in suitably private storage; provider-specific procedures belong in local instructions.

## Instruction ownership

- [`SKILL.md`](skills/works/SKILL.md): core method, finalization and reuse; roughly 1,000 tokens.
- [`SETUP.md`](skills/works/SETUP.md): read only for setup or migration.
- [`INDEX.md`](skills/works/INDEX.md): read only for private indexing or queries.
- Collection `README.md`: locally owned audience, owner, citation and contribution rules.
- Optional `AGENTS.md`: user-owned local instructions. Personal setup adds one only when no applicable file exists; updates never overwrite it.

Keep general guidance in the skill rather than copying it into local files. Changes requiring local migration should be proposed separately.

## References and private index

Use ordinary relative links locally and `[label](@name/path)` across collections. Each collection's README identifies its referenced collections and nicknames in prose. Names belong to the citing collection; personal follows and machine-specific access details stay in local instructions. Copying a work must preserve what its names identify in the destination context. Named references are agent-resolved, not browser-clickable links.

The agent supplies local snapshots and source-scoped bindings to [links.py](skills/works/scripts/links.py); it neither reads provider services nor interprets declarations or walks the graph. `set-references B --reference research=D --reference lab=D` replaces B's complete mapping. C may use another name for D. `incoming D` finds both sources, even before D is indexed. Run `--help` for examples or read [INDEX.md](skills/works/INDEX.md).

The script indexes **all collection Markdown**, including supporting files and WIPs. Query states `wip`, `finalized` and `collection` are path-based labels, not proof of review. Target status distinguishes cached, missing, unchecked, unbound and invalid references. URL roots are optional; logical identity is independent of provider paths.

Complete inventories and partial updates are explicit. “Complete” describes index coverage, not finalization. Failed reads retain earlier cached material with warnings; only a successful complete inventory removes missing files. Queries report coverage, freshness and truncation. Supplement extracted links with full-text searches and source review; the cache cannot prove truth, current permissions or absence of corrections elsewhere.

The method works without Python. The optional indexer requires Python 3.12+ with SQLite FTS5 and no third-party dependencies. Choose the Python invocation for the local environment. From this repository root:

```bash
python -B tests/test_links.py
```

Tests use temporary directories, not real collections or remote services.
