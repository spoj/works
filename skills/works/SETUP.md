# Setup

The skill must already be installed. Setup arranges folders within existing storage; it does not configure sharing or install another copy of the skill. General instructions stay upstream; the collection README and optional AGENTS belong to their local owners. Updates do not silently rewrite either file. Propose existing-collection changes separately.

## Confirm the plan

Inspect the current directory, its contents and enclosing Git worktree. Ask one short batch, skipping answered questions:

1. Which folder is the collection? Show the resolved path. Use it directly, including when it is the repository root; do not add a containing `works/` folder unless requested.
2. Who owns it, who can read it, and who may contribute under what conditions?
3. Use Git? Reuse an existing worktree; do not nest another repository.
4. For a personal workspace, any collections to follow, and where should private instructions and the rebuildable index live?

Use the storage's existing access procedures to check actual permissions and task authorization. Local sync access does not establish server permissions. Record useful provider-specific procedures in local instructions; writing into a synced folder may expose content immediately.

Confirm before writing. Preserve existing files; a nonempty directory needs a scoped migration plan. Do not install software, create remotes, push, change sharing permissions or access unrelated sources as part of collection setup.

## The same scaffold everywhere

Create the chosen collection folder if needed and its `README.md`. Do not create a WIP directory, sample work, nested `works/`, index or scripts as part of the scaffold.

```text
<collection>/
    README.md
```

New `_wip_<slug>/LOG.md` and `YYYY-MM-DD-slug/LOG.md` folders are created as work develops. Personal, person-to-person and team collections have the same structure. An entire repository may itself be the collection if the user chooses that location; do not impose another containing workspace.

Write a short README using confirmed facts:

```markdown
# <Collection name> — Works

Contributions and dated checkpoints for <audience>.
Owner: <person or team>.
Location: <owner-provided collection location>.
Contribution rules: <who may contribute and what approval/disclosure rules apply>.

Create `_wip_<slug>/` on demand for ongoing work, not only draft writing.
WIPs are not stable citations.
Finalize through editorial review, then rename to `YYYY-MM-DD-slug/`.
The folder date records finalization; `LOG.md` states the finding, evidence,
applicable dates and uncertainty. Finalized does not mean validated.
Preserve works; material changes belong in new works citing the affected finding.
Meaning-preserving edits, including navigation citations, may be made in place.
Review WIPs without automatically deleting them; consolidate only when needed.
```

Replace placeholders; omit irrelevant fields. Identify referenced collections and their nicknames in ordinary README prose, using owner-provided locations. References use `[label](@name/path)`; do not repoint a name to another collection. Referencing does not imply following or access. The README describes policy, not a grant or verification of permission.

## Optional personal instructions

For personal setup, preserve and use an applicable existing `AGENTS.md`. If none exists, add one at the chosen workspace root, or in the collection when that is itself the workspace. Do not create a competing nested AGENTS merely because the collection has a README.

Keep it user-owned and short:

```markdown
# Local instructions

Load the installed `works` skill for this collection.
This file contains local instructions; skill updates must not overwrite it.

<Only local execution/disclosure rules and collection locations.>
```

Keep personal follows, cache locations and machine-specific access details in private local instructions, separate from reference declarations. Non-sensitive provider procedures may live with the collection. An owner may choose collection-level instructions; setup does not automatically add another AGENTS there.

The default private cache is `<private workspace>/.works/index.sqlite`, never a shared collection's cache. Agree its exclusion from Git before creating it. Do not invent additional evidence exclusions. If Git was requested, commit only the agreed scaffold; no remote or push.

## Existing collections

Migrate an existing separate WIP tree to collection-root `_wip_<slug>/` folders without discarding contributions. Update active callers and links. Preserve works and evidence; report historical pointers that cannot be changed without rewriting finished records. There is no legacy WIP container or alias kept after migration.

If the task also changes a folder's sharing, check what the storage will expose—including nested WIPs, instructions and caches—and update local guidance. Where adaptation is needed, retain a new self-contained edition rather than editing the original.

## Follow and index

Read followed collections' READMEs through existing tools. Identify shared targets across different names and supply source-scoped bindings to the indexer. The agent follows references as needed; the script neither interprets prose nor walks collections. Missing access is a gap, not a setup blocker. Obtain readable trees through existing tools, preserving collection-relative paths. A URL root is optional and only valid where URLs map directly to paths.

Scan all Markdown, including WIP. Read [INDEX.md](INDEX.md) for `citations.py scan`, `references`, `in`, `out` and `resolve`. Ordinary tools handle finding and reading files; before relying on a work, inspect all incoming citations with `in`. Ask before a potentially large initial retrieval. Use bounded `--partial` scan batches when needed; `--complete` requires a complete snapshot, never a selected download folder. Citation results themselves are never limited or ranked. Keep source capture/version information distinct from scanning time.

Keep the follow list independent of SQLite so missing collections remain visible and the cache is rebuildable. Finish by reporting created/migrated files, Git choice, follows, index coverage and unresolved permissions. Do not claim provider synchronization merely from local presence.
