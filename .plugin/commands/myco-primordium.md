---
description: "Author a 3-round craft proposal under docs/primordia/ via the primordium subagent, then run myco winnow to gate the shape"
argument-hint: "<topic-phrase>"
---

The user wants you to author a 3-round craft proposal for the topic: $ARGUMENTS

Use the **primordium** subagent (defined at `.claude/agents/primordium.md`) to do this work. The subagent has the full protocol baked in (frontmatter shape, 3-round structure, R-rules, winnow gating).

Pass the topic to the subagent as its only dynamic input. The subagent will:

1. Run `myco hunger` for substrate state.
2. Run `myco sense` for prior art on the topic.
3. Compute the canonical filename via `myco fruit --topic "<topic>" --kind <inferred-or-design> --dry-run`.
4. Compose the full claim → 1.5 self-rebuttal → 2 refinement → 3 decision draft.
5. Land the draft as DRAFT status at `docs/primordia/<slug>_<kind>_<date>.md`.
6. Run `myco winnow --proposal <path>` to gate.
7. Report a single structured paragraph: drafted path, winnow result, deferred sub-tasks, recommended next user action.

When primordium returns, relay its report verbatim to the user. Do NOT add your own opinion about the craft's merit — the user reviews. Your only role here is invocation orchestration.

If primordium reports the winnow gate failed and could not be self-corrected within the subagent's two-revision limit, do NOT attempt further fixes; report the failure to the user with the diagnosis primordium provided.
