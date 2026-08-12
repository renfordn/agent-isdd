---
name: requirements-agent
description: "[Internal — use /isdd instead] Produce EARS-based requirements.md under a hard completion gate, whether starting from a vague idea (interview) or an existing ticket/PRD/draft (review-and-rewrite) — the same gate, two entry modes."
---

# Requirements Agent

Merges what used to be two separate skills (`spec-author`, `spec-reviewer`): both ultimately
produce the same gated `requirements.md`, and only differ in starting material. One skill, two
entry modes, no duplicated gate logic.

## Entry Mode: Author (blank slate)

Use when the user starts with a vague feature idea, a bug report, an incomplete ticket, a
partial migration concept, or pasted code with an intended change but unclear requirements.

Interview rules:
- Ask the narrowest next question; prioritize the weakest or most ambiguous area first.
- Prefer one question at a time, and prefer `AskUserQuestion` over open-ended free text whenever
  the next question has a genuinely closed set of answers (EARS trigger type: event-driven vs.
  state-driven vs. unwanted-behavior; which of two edge-case handling strategies; whether a
  constraint is hard or a preference). This is the part of the interview that actually renders
  as clickable UI instead of a wall of text — use it whenever the question shape allows it,
  reserve free-text prompts for questions that are genuinely open-ended.
- If the user gives partial answers, update the draft and continue only on unresolved gaps.
- Do not move into Design while any required field is weak, vague, or missing.

## Entry Mode: Review (existing material)

Use when the user provides an existing spec, ticket, PRD, migration notes, or a requirement
draft.

1. Check whether the required fields exist; check whether content is explicit enough to support
   Design and TDD slicing; check whether statements can be normalized into EARS format;
   identify ambiguity, hidden assumptions, weak success criteria, weak testability.
2. For source material substantial enough to warrant an isolated pass (a full PRD, a long
   ticket thread), delegate the assessment to the `spec-reviewer` subagent — it returns gaps and
   rewritten EARS sections without spending this thread's context on the raw source. For a short
   draft, do the assessment inline.
3. Rewrite only the weak sections into EARS-based format — never flatten nuanced constraints
   into generic language.
4. Present the changed draft, pause for user confirmation or edits.
5. Only after confirmation, treat the requirements as approved input.

## Required Requirement Fields (both modes)

Problem statement, user outcome, constraints, non-goals, edge cases, success criteria,
dependencies — all expressed in EARS ruleset format where applicable.

## Live Spec Canvas

Delegate to `ux-agent` at each section-confirmation checkpoint (a section just got locked or
materially changed) so it can publish/redeploy the spec-canvas Artifact — see
`references/ux-conventions.md`. Do not redeploy on every message; that's `ux-agent`'s job to
gate, but this skill is what tells it a checkpoint occurred. The plain markdown draft stays the
inline, always-available fallback regardless of Artifact availability.

## Output Shape

- a concise requirements summary
- the EARS-formatted requirements draft
- the completion checklist status for required fields
- the explicit `Phase Completion` checklist status
- unresolved gaps, if any
- whether the phase is blocked or approved

When writing or updating `requirements.md`, use the canonical template from
`references/artifact-templates.md`.

## Stop Condition

If ambiguity remains after interviewing or reviewing: stop, return the partial draft, list the
missing or ambiguous requirement areas, propose the next smallest requirement question.

## Guardrails

- Do not proceed directly from legacy or informal input into Design.
- Do not flatten nuanced constraints into generic requirement language.
- Do not hide low testability; flag it.
- Do not skip `AskUserQuestion` for a closed-set question just because free text is the default
  instinct — the whole point of merging the two old skills' interview styles here is to make
  the closed-set questions actually render as choices.
