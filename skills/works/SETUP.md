# Setup

The skill must already be available to the agent. Setup creates a workspace or collection, not another copy of the skill or its scripts.

The installed skill owns the reusable method. Generated `AGENTS.md` belongs to the user: initialize it once, then let the user and authorized agents edit local instructions. Skill updates change the method, not this file. Keep general guidance in the skill rather than copying it into local instructions. Template changes apply to new setups; propose any existing-workspace change separately. A shared collection's `README.md` similarly belongs to its custodian.

## Ask before writing

Inspect the current directory, its contents and any enclosing Git worktree. Ask one short batch, omitting questions already answered:

1. Set up here (`<absolute cwd>`), or somewhere else?
2. A personal working workspace, or a shared completed-work collection? Default proposal: personal.
3. Use Git? Reuse an existing worktree rather than nesting another repository.
4. For a personal workspace, which shared collections should it follow, if any? Names and paths or URLs are enough to start.

For a shared collection, establish its intended readers, custodian, canonical location, who may publish under what conditions, and how effective read/write permissions are checked. Its custodian may be a person or a team. Obtain these from local policy or the user; do not infer them from the current agent's access. Confirm that writing into a synced folder may publish immediately.

Confirm the plan before scaffolding. Preserve existing files; a nonempty directory requires a scoped plan, not replacement. Do not install software, create remotes, push, change permissions or access unrelated sources as part of setup.

## Personal workspace

Create:

```text
AGENTS.md
wip/
works/
```

Write a short `AGENTS.md` using the confirmed answers, along these lines:

```markdown
# Works

Load the installed `works` skill when working with dated contributions here.
This file contains user-owned local instructions; skill updates must not overwrite it.
Keep these instructions, WIP, follow list and index private to <owner>.

## Local rules

<Only environment-specific execution, disclosure and access instructions.>

## Collections

- My works: `works/`. Audience: <initially owner only>. Canonical root: <location>.
- <Name>: <canonical shared root>. Read via <path or existing tool>.
  Check reader access using <established policy/procedure>.

The private, rebuildable index is `.works/index.sqlite`.
```

Use plain English, not a new configuration schema. Omit unused sections and placeholder entries; say explicitly when canonical addresses, access or freshness have not yet been established. A private local collection may use a `file://` directory URL; it is not a portable shared citation address.

Keep follow lists private even when they point to several teams. Do not create a merged published timeline, copy shared collections into personal works, or put personal access details in a shared README.

If Git was requested, initialize it only when needed. Agree to exclude `.works/` from version control because it caches other collections' content; do not invent additional evidence exclusions. Add empty `.gitkeep` files in `wip/` and `works/` so cloning preserves the scaffold. Commit only the agreed scaffold, without a remote or push.

## Shared collection

Create only `README.md`; dated work folders appear when actual contributions are published. No WIP, index database, follow list, scripts or `AGENTS.md` belong here. Hidden Git metadata is optional if explicitly requested.

Write the README in plain language for people and agents:

```markdown
# <Collection name>

Completed contributions and dated checkpoints for <audience>.
Maintained by <person, team or other custodian>.

Canonical location: <location and citation convention>.
Reader access: <provider-managed boundary and how to verify it>.
Publication: <who may contribute, approval and disclosure requirements>.
Write access: <how to verify effective provider permission and publish>.

Each `YYYY-MM-DD-slug/` folder has a `LOG.md` entry point with the
question, finding, significance and links to supporting evidence.
Inclusion means worth retaining, not independently validated.
Keep finished works and their addresses stable. Publish substantive
corrections as new works citing the earlier conclusions.

Draft elsewhere. Publish only material authorized for these readers;
citations and necessary evidence must remain accessible to them.
Do not depend on material inaccessible to these readers.
Write permission alone does not authorize a contribution or rewriting finished works.
```

Replace placeholders with confirmed facts. Missing information is unknown, not permission. The README states the procedure; it does not itself verify or grant access rights.

A person-to-person share is the same kind of collection. If the user wants to share an existing `works/` folder, review its content and citations for the new audience rather than recreating it. Explain that future additions may inherit the sharing permissions. Keep private instructions, WIP, follow lists and indexes outside the shared boundary. If some works are unsuitable, prepare a separate shared collection with authorized versions; do not silently edit finished originals or change permissions during setup.

## Following and first indexing

Read each followed collection's README through an existing access route. Keep read access separate from authority to publish or redistribute. Missing access need not block personal scaffolding; record the unresolved location instead of claiming it was checked.

The indexer consumes a local readable tree, whether obtained from Git, a mounted drive, sync, export or another existing tool. It has no provider adapters. Establish a path-addressable canonical directory URL independently of that local tree. Preserve all collection-relative paths, and supply source version/capture information when known.

Initialize the personal database by indexing the empty local `works/` collection as a complete snapshot. Use the command examples in `SKILL.md`. For followed collections, ask before a potentially large initial retrieval. Index all Markdown, but allow bounded batches with `--partial` so setup need not wait for the entire history. Only use `--complete` for a full snapshot, never for a selected download directory.

Record the private follow list independently of the database so the index can be rebuilt. Collections not yet indexed remain explicit gaps; compare the follow list with index status during retrieval. Do not silently treat the registered database collections as the entire followed set.

Finish by reporting the created files, Git choice, followed collections, indexing coverage and unresolved access questions. Do not publish a sample work merely to demonstrate setup.
