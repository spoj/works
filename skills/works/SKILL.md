---
name: works
description: Retain, find, cite, finalize and adapt dated contributions in collections of folders.
---

# Works

A collection is a growing list of dated works whose evidence serves as documentation across time and people. Preserve contributions; later findings build on or correct them through new works and citations.

Works applies independently of how the folders are stored or shared. The agent must understand the surrounding access, visibility and authorization sufficiently to apply it appropriately.

## Layout

Use the chosen collection folder directly, including a repository root:

```text
README.md
AGENTS.md                  # optional, user-owned
_wip_some-question/LOG.md   # created on demand
YYYY-MM-DD-some-finding/LOG.md
```

Read README for owner, audience (intended readers), locations and contribution rules. Respect AGENTS; updates must not overwrite local policy. For setup or migration, read [SETUP.md](SETUP.md).

Use relative paths locally and `[label](@name/path)` across collections. README prose identifies referenced collections and nicknames; names belong to the citing collection. These are agent-resolved references, not browser links.

**WIP** holds ongoing investigation, calculations, scripts, evidence and preparation of business outputs. A **draft** is an unfinished artifact within it. Keep code, evidence and source receipts together. WIPs are not stable citations; review them without automatically deleting them.

## Finalize

A **work** is a finalized, dated, citable contribution. Useful negative results and inconclusive checkpoints qualify; finalized does not mean correct or conclusive.

Exercise editorial judgment: decide what is worth retaining and for whom. Write `LOG.md` as a synthesis of the question, finding, significance, reasoning, evidence, scope and uncertainty—not an activity log. Link lengthy support. Distinguish observations from interpretations and retain material counterevidence.

Check content and links, then rename to `YYYY-MM-DD-slug/` and resolve WIP-path references. Renaming is the last step, not the substance. Never overwrite a work.

The folder date records this edition's finalization. State applicable evidence and analysis dates in `LOG.md`. Unchanged copies retain their date; a new shared edition does not make old evidence new.

Preserve works and addresses. Changed claims, evidence, reasoning or material caveats require a new work citing the earlier one. Meaning-preserving fixes and brief dated sharing notes may be added in place; preserve original evidence bytes.

## Read and reuse

Read `LOG.md`, supporting evidence, earlier foundations and later citations or corrections across followed collections. Citations may disagree or repeat a source; recency and citation counts do not prove truth. WIP references remain unfinished.

When copying or adapting a work for other readers, review its contents, supporting files and citations. Copy unchanged only when these remain appropriate; otherwise finalize a self-contained **shared edition** without changing the original. Readers need access to its evidence. Reconcile reference names with the destination README and verify the resulting files and links through the destination's read route.

Recheck changing facts before consequential use. Report coverage, freshness and access gaps; “not found” does not mean “absent.” For the private index, read [INDEX.md](INDEX.md). Index all collection Markdown, not just logs; the cache is disposable, not evidence.

## Operating context

Check actual storage permissions and task authorization before writing or copying; reading does not authorize redistribution. If uncertain, ask rather than probe by writing. WIP names and README text do not set storage permissions. Keep personal follows, caches and machine-specific details in suitably private storage; never expose live credentials or access-token-bearing URLs. Use existing provider procedures and applicable retention rules. Do not broaden permissions to repair citations or push Git without authorization.
