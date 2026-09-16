# Setup

The skill must already be installed. Setup creates a collection, not another copy of the skill or its scripts. General instructions stay upstream; the collection README and optional AGENTS belong to their local owners. Updates do not silently rewrite either file. Propose existing-collection changes separately.

## Confirm the plan

Inspect the current directory, its contents and enclosing Git worktree. Ask one short batch, skipping answered questions:

1. Which folder is the collection? Show the resolved path. Use it directly, including when it is the repository root; do not add a containing `works/` folder unless requested.
2. Who owns it, who can read it, and who may contribute under what conditions?
3. Use Git? Reuse an existing worktree; do not nest another repository.
4. For a personal workspace, any collections to follow, and where should private instructions and the rebuildable index live?

For shared storage, establish canonical addresses, the existing read/write route and how effective provider permissions are checked. Writing into a synced folder may share immediately. Do not infer audience or contribution authority from the current user's ability to open a file.

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
Canonical location and citation convention: <location>.
Contributions and sharing: <who may contribute and what approval/disclosure rules apply>.
Access: <how effective provider read/write rights are checked>.

Create `_wip_<slug>/` on demand for ongoing work, not only draft writing.
WIPs have this collection's audience and are not stable citations.
Finalize through editorial review, then rename to `YYYY-MM-DD-slug/`.
The folder date records finalization; `LOG.md` states the finding, evidence,
applicable dates and uncertainty. Finalized does not mean validated.
Preserve works; substantive corrections belong in new works citing them.
Meaning-preserving fixes and brief dated sharing notes may be added in place.
Review WIPs without automatically deleting them.
```

Replace placeholders; omit irrelevant fields rather than inventing infrastructure. Unknown access remains unknown. The README describes policy, not a grant or verification of permission.

## Optional personal instructions

For personal setup, preserve and use an applicable existing `AGENTS.md`. If none exists, add one at the chosen workspace root, or in the collection when that is itself the workspace. Do not create a competing nested AGENTS merely because the collection has a README.

Keep it user-owned and short:

```markdown
# Local instructions

Load the installed `works` skill for this collection.
This file contains local instructions; skill updates must not overwrite it.

<Only local execution/disclosure rules and collection locations.>
```

Put private follows and index location here only if this location is private. Record followed collection names, canonical roots, local read routes and permission-checking instructions in ordinary prose, not a new configuration schema. Use an existing personal instruction file elsewhere if the collection is shared. Shared setup does not automatically add AGENTS; an owner may choose collection-level instructions without private machine details.

The default private cache is `<private workspace>/.works/index.sqlite`, never a shared collection's cache. Agree its exclusion from Git before creating it. Do not invent additional evidence exclusions. If Git was requested, commit only the agreed scaffold; no remote or push.

## Existing collections and changed audiences

Migrate an existing separate WIP tree to collection-root `_wip_<slug>/` folders without discarding contributions. Update active callers and links. Preserve works and evidence; report historical pointers that cannot be changed without rewriting finished records. There is no legacy WIP container or alias kept after migration.

Sharing existing works also shares their WIPs and potentially future additions. Review content and citations for the new audience. Keep private instructions, follows and caches outside the sharing boundary. If unsuitable, prepare authorized shared editions in a separate shared collection rather than editing finished originals or assuming broader access.

## Follow and index

Read followed collections' READMEs through existing tools. Missing access need not block personal scaffolding; record the gap. Obtain readable trees from Git, drives, sync, export or other existing tools while preserving collection-relative paths. Establish canonical URLs independently of local download paths.

Index all Markdown, including WIP. See the commands and limits in `SKILL.md`. Ask before a potentially large initial retrieval. Use bounded `--partial` batches when needed; `--complete` requires a complete snapshot, never a selected download folder. Keep source capture/version information distinct from indexing time.

Keep the follow list independent of SQLite so missing collections remain visible and the cache is rebuildable. Finish by reporting created/migrated files, Git choice, follows, index coverage and unresolved permissions. Do not claim provider synchronization merely from local presence.
