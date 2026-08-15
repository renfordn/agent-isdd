---
name: design-author
description: "[Internal — use /isdd instead] Turns approved requirements into a testable design.md, grounded in agent-nelly's brief (if available) and planning-agent's codebase research."
---

# Design Author

## Use This Skill When

After Requirements are approved and before detailed task planning starts. Typical inputs:
approved `requirements.md`, a reviewed PRD/ticket that already passed the requirements gate, or
migration notes needing implementation-facing design.

## Research First

Before drafting, delegate to two subagents rather than relying only on what's already in
context:

1. `agent-nelly:nelly-orchestrator` — reuse the brief the caller passed down; call agent-nelly
   directly only per the re-fetch triggers defined in `spec-driven-development`'s Goal-Aware
   Memory section, when agent-nelly is available (per the Availability Check defined in
   `workflow-manager/SKILL.md`). When a fresh call is made, it returns a holistic brief (Intent,
   prior decisions, open risks, relevant past entries, Intent-alignment check). Seed
   `planning-agent` with it (whether reused or freshly fetched) so it isn't re-deriving project
   context the memory already has.
2. `planning-agent` — wide-fast then deep-focused codebase research for the actual touchpoints,
   interfaces, and constraints this design must respect. Reuse a still-valid `planning-agent`
   finding already fetched earlier in this same continuous stretch of phase work (per
   `spec-driven-development`'s extended brief-reuse convention and its three re-fetch triggers)
   instead of re-delegating for the same touchpoints. Record its findings in the `Research
   Basis` section of `design.md` (see `references/artifact-templates.md`) so a later reader can
   see the design is grounded, not guessed. Pass the caller's brief (including its `Relevant
   entries` section, which the orchestrator fetches with `surface relevant memory: true` before
   routing into this skill — see `spec-driven-development/SKILL.md`'s Goal-Aware Memory section)
   to `planning-agent` alongside the brief so it can skip re-deriving context nelly already
   gave. Do **not** make a separate pre-sweep `agent-nelly:nelly-orchestrator` call here — the
   relevant entries already in the brief serve this purpose. After `planning-agent` returns,
   take its "Nelly summaries to write (if any)" output and persist it via
   `agent-nelly:nelly-orchestrator`'s `new fact`/`new facts` input — `planning-agent` itself
   never writes it. If a specific summary describes a design approach already tried and rejected
   in this codebase (not just a fact about its current shape), persist that one via
   `error lesson` instead (see `INTEROP.md`'s "→ agent-nelly" section for the criterion).

## Design Gate

Move forward only when all of the following are true:
- requirement coverage is explicit
- architecture or code touchpoints are named, grounded in `planning-agent`'s findings
- interfaces or contracts that change are described
- edge-case handling is documented
- validation strategy is credible
- key tradeoffs are visible
- no unresolved contradiction remains
- when `agent-nelly:nelly-orchestrator` is available, its Intent-alignment check for this
  design is clean, or its flag has been surfaced to and resolved with the user
- no unresolved Security Finding remains unconfirmed by the user

If any of the above are weak or missing: stop, return a partial design draft, list the open
questions or contradictions, ask the next smallest clarifying question.

## Diagrams (`show_widget`)

When architecture, a data flow, or a state transition is genuinely clearer as a picture than as
prose or a table — not by default, and not for every design — render it with
`mcp__visualize__show_widget` (call `mcp__visualize__read_me` once first, silently, per its own
instructions). This is a lighter-weight, one-shot visual for explaining the design as you write
it; it is not the spec canvas (that's `agent-ux:ux-agent`'s redeployable Artifact over confirmed
requirements sections, a different artifact for a different phase). Reference the diagram from
`design.md` in prose (what it shows and why) rather than treating the widget itself as the
durable record — `design.md` stays the artifact of record.

## Required Output

- a concise design summary
- the `Research Basis` (wide-pass candidates, deep-pass findings, memory brief used)
- scope mapping back to approved requirements
- architecture or code touchpoints
- data contracts and interfaces
- states, flows, and edge-case handling
- validation strategy
- risks and tradeoffs
- the `Improvement Opportunities & Blast Radius` section (`Blast Radius`, `Security Findings
  (blocking)`, `Refactor & Reduction Opportunities (non-blocking)`, `Best-Practice Notes
  (non-blocking)`)
- the explicit `Phase Completion` checklist status
- open questions
- phase status: `blocked` or `approved`

When writing or updating `design.md`, use the canonical template from
`references/artifact-templates.md`.

## Guardrails

- Do not invent new product requirements in design.
- Do not move unresolved requirement ambiguity into design as if it were settled.
- Do not hide risky migrations or weak testability.
- Do not name a touchpoint or interface that `planning-agent` didn't actually surface or that
  wasn't otherwise verified — a design grounded in a guess is exactly the failure mode this
  research step exists to prevent.
- Never fold a security-relevant finding into the general (non-blocking) subsections silently —
  it always routes to `Security Findings` and triggers the Design Gate pause.
- Prefer the smallest coherent design that supports the current requirement slice.
- Do not render a diagram for a design simple enough to state in a sentence or two — `show_widget`
  is for when a picture removes real ambiguity, not decoration.
