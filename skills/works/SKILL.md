---
name: works
description: Retain, find, cite, finalize and adapt dated contributions in collections of folders.
---

# Works

A collection holds dated contributions. Preserve evidence and connections for later reuse, qualification and correction.

## Layout

Use the chosen collection folder directly, including a repository root:

```text
README.md
AGENTS.md                  # optional, user-owned
_wip_some-question/LOG.md
YYYY-MM-DD-some-finding/LOG.md
```

Read README for owner, audience, locations and contribution rules. Respect user-owned AGENTS. For setup or migration, read [SETUP.md](SETUP.md).

Use relative links locally and `[label](@name/path)` across collections. Names come from the citing collection's README, not Git remotes. Say why each citation matters.

A **WIP** holds investigation, calculations, scripts, evidence and output preparation—not just drafts. Create on demand; keep related materials together. WIPs are unfinished references; review without automatically deleting them.

## Finalize

A **work** is a finalized, citable contribution, not necessarily correct or conclusive. Useful negative results and inconclusive checkpoints qualify.

Write `LOG.md` as a synthesis of question, finding, significance, reasoning, evidence, scope and uncertainty—not an activity log. Separate observations from interpretations; retain material counterevidence. Link lengthy support. Enable understanding, reuse and correction, not exhaustive reproduction.

A work may record an external change, such as launching a project or intake folder: capture date, intention, owner and stable location. The live system owns its evolving state; do not mirror it routinely.

Check content and links, then rename to `YYYY-MM-DD-slug/` and fix WIP-path references. The date records finalization; state evidence and analysis dates. Unchanged copies retain their date.

Preserve works and addresses. Meaning-preserving edits, including navigation citations, may be made in place without post-note labels. Material changes to findings, methods, reasoning, evidential basis or caveats require a new work. Cite the affected work beside the changed claim and state what changes. Preserve original evidence bytes.

## Read and reuse

Find and read Markdown with ordinary tools. **Before relying on a work, run `citations.py in COLLECTION WORK` and inspect all incoming citations. Do not filter citations.** Read relevant citing sources for qualifications and corrections. See [INDEX.md](INDEX.md) for commands; scan all collection Markdown, including support and WIPs. Report coverage, freshness and access gaps: no indexed citation does not prove no correction.

Follow evidence and foundations to the depth the task requires. Recency, finalization and citation counts do not prove truth. Recheck changing facts before consequential use.

Cite unchanged foundations rather than copying them. Include enough current context to do the task. Consolidate when actual work reveals costly fragmentation or conflict—not on a schedule or for hypothetical future needs.

For another audience, review contents, evidence and citations. Copy unchanged only when appropriate; otherwise finalize a self-contained shared edition. Preserve the original. Readers need evidence access. Reconcile collection names and verify files and links through the destination's read route.

## Access

Check actual storage permissions and task authorization before writing or copying; reading does not authorize redistribution. Ask when uncertain; do not probe by writing. README prose does not grant permissions. Keep personal follows, caches and machine-specific details private; never expose live credentials or token-bearing URLs. Use existing provider procedures and retention rules. Do not broaden permissions or push Git without authorization.
