---
name: tdd-planner
description: "[Internal — use /isdd instead] Convert approved requirements and design into phased tasks optimized for safe TDD execution and agent handoff, grounded in planning-agent's codebase research."
---

# TDD Planner

## Purpose

Use this skill after Requirements are approved and the Design phase is coherent enough to plan
implementation.

## Research Before Slicing

Delegate to `planning-agent` (seeded with `design.md`'s existing `Research Basis` so it isn't
repeating work `design-author` already did) whenever the design didn't already pin down exactly
which files a task touches — slicing against a guessed file boundary is how oversized or
wrongly-scoped tasks happen. If `design.md`'s research is already concrete enough, skip
re-research and slice directly from it.

## Phase Model

Reinforces Requirements → Design → Tasks. `Tasks` should be phased and small enough to support
Red-Green-Refactor execution.

## Task Slicing Rules

Target one behavior change and/or one file or module touched if possible. If a task is too
large: propose a smaller slice, ask for confirmation, continue only after confirmation.

## Required Task Output

For each phase: phase objective, Risk Tier, ordered tasks, test intent, validation target,
dependency notes, what the phase enables next, task readiness checklist status.

## Risk Tier Assignment

Set each task's Risk Tier to `high-risk` only when `design.md`'s Risks And Tradeoffs section
names a risk touching that task's files/module, or the task is itself a high-risk migration.
Otherwise `standard`. This is the trigger `spec-driven-development`'s Implementation Handoff
uses to decide whether to spawn `agent-tdd:test-author` before `agent-tdd:agent-TDD` instead of
`agent-tdd:agent-TDD` writing the test itself (see `INTEROP.md` at the repo root) — do not mark
a task `high-risk` speculatively; it must trace to a specific named risk or migration, not
general caution.

When writing or updating `tasks.md`, use the canonical template from
`references/artifact-templates.md`.

## Tasks File Style

Optimize for agent handoff: direct execution language, minimal prose, observable validation
steps, no vague "investigate more" placeholders unless paired with a concrete question or exit
condition.

## Flagged Conditions

Pause instead of advancing when any of these are present: unresolved ambiguity, conflicting
constraints, weak testability, high-risk migration, tasks too large for safe TDD slicing.
