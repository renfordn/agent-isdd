---
name: tdd-planner
description: "[Internal — use /isdd instead] Converts approved requirements+design into phased TDD tasks.md, grounded in planning-agent's research."
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
re-research and slice directly from it. Before delegating, also check whether a still-valid
`planning-agent` finding for the same touchpoints was already fetched earlier in this same
continuous stretch of phase work (per `spec-driven-development`'s extended brief-reuse
convention and its three re-fetch triggers) and reuse it instead of re-delegating.

## Phase Model

Reinforces Requirements → Design → Tasks. `Tasks` should be phased and small enough to support
Red-Green-Refactor execution.

## Task Slicing Rules

Target one behavior change and/or one file or module touched if possible. If a task is too
large: propose a smaller slice, ask for confirmation, continue only after confirmation.

## Required Task Output

For each phase: phase objective, Risk Tier, ordered tasks, test intent, validation target, a
structured `Depends On` task-id list (see `references/artifact-templates.md`; bare ids only, no
prose — a narrative dependency stays in `Prerequisites`), what the phase enables next, task
readiness checklist status.

## Risk Tier Assignment

Risk Tier assignment is defined once, in `agents/tdd-planner.md`'s Risk Tier Assignment section
— see there for the exact rule rather than restating it here.

When writing or updating `tasks.md`, use the canonical template from
`references/artifact-templates.md`.

## Tasks File Style

Optimize for agent handoff: direct execution language, minimal prose, observable validation
steps, no vague "investigate more" placeholders unless paired with a concrete question or exit
condition.

## Flagged Conditions

Pause instead of advancing when any of these are present: unresolved ambiguity, conflicting
constraints, weak testability, high-risk migration, tasks too large for safe TDD slicing.
