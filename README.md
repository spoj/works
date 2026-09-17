# Works

A growing list of dated contributions, connected by ordinary citations. Prior works and their evidence serve as documentation across time and people. Preserve them; material changes belong in new works citing the affected findings. Meaning-preserving edits, including navigation citations, may be made in place.

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
- Preserve works and their addresses. Material changes belong in new works citing the affected claim. Navigation links need no special post-note label when they preserve meaning.
- Reuse unchanged foundations through citations. Consolidate when actual work exposes costly fragmentation or conflict, not on a schedule.
- A work can record the launch of an external project or intake folder: capture its date, purpose, owner and stable location. Read the live system for evolving state rather than routinely mirroring it.

Check actual storage permissions and task authorization before writing or copying. WIP names and README text do not set storage permissions. Keep personal follows, caches and machine-specific details in suitably private storage; provider-specific procedures belong in local instructions.

## Instruction ownership

- [`SKILL.md`](skills/works/SKILL.md): core method, finalization and reuse; roughly 1,000 tokens.
- [`SETUP.md`](skills/works/SETUP.md): read only for setup or migration.
- [`INDEX.md`](skills/works/INDEX.md): read only for private indexing or queries.
- Collection `README.md`: locally owned audience, owner, citation and contribution rules.
- Optional `AGENTS.md`: user-owned local instructions. Personal setup adds one only when no applicable file exists; updates never overwrite it.

Keep general guidance in the skill rather than copying it into local files. Changes requiring local migration should be proposed separately.

## References and private citation lookup

Use ordinary relative links locally and `[label](@name/path)` across collections. Each collection's README identifies its referenced collections and nicknames in prose. Names belong to the citing collection, not Git remotes. Personal follows and machine-specific access details stay private. Copying a work must preserve what its names identify in the destination context. Named references are agent-resolved, not browser-clickable links.

Find and read Markdown with ordinary tools. **Before relying on a work, inspect all indexed incoming cross-work citations. Do not filter citations.** A later contradiction must remain visible even if it has no incoming citations or matching search terms of its own.

The agent supplies readable snapshots and source-scoped bindings to [citations.py](skills/works/scripts/citations.py). It does not fetch, search, rank, traverse the graph or publish anything. From this repository root:

```bash
python skills/works/scripts/citations.py references add local research team
python skills/works/scripts/citations.py scan local --root ./local-snapshot --complete --snapshot 'capture time or revision'
python skills/works/scripts/citations.py in local 2026-01-01-study/
python skills/works/scripts/citations.py out local 2026-01-01-study/
python skills/works/scripts/citations.py resolve --from local '@research/2026-01-01-study/LOG.md'
python skills/works/scripts/citations.py coverage
```

`in` groups every incoming occurrence by citing work and source filename, with line numbers and full citing paragraphs/list items. `out` lists distinct cited works and destination paths. Within-work navigation is separate from cross-work citations. There are no result limits, context clipping or ranking adjustments. Default output is text; `--json` returns structured records. Run `--help` or read [INDEX.md](skills/works/INDEX.md).

Scan **all collection Markdown**, including supporting files and WIPs. Complete inventories and partial updates are explicit. Failed reads retain earlier citation context with warnings; only a successful complete scan removes missing files. Every query reports coverage and snapshot dates. Compare coverage with private follows: the cache cannot prove truth, current access or absence of unlinked/unavailable corrections. If a shell truncates output, save it and read the remainder.

The tool requires Python 3.12+ with SQLite and no third-party dependencies. Schema 2 requires rebuilding older caches from readable snapshots; source works and evidence do not change. Test from the repository root:

```bash
python -B -m unittest discover -s tests -v
```

Tests use temporary directories, not real collections or remote services.
