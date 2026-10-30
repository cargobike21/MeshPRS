# 0006: A gateway may gate telemetry it polled itself from its owner's own nodes

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q31
- **Spec sections affected:** §7.1, §13

## Context

§13 forbids gating request/response contents. Kelly's released profile-0 iGate already gates telemetry it polls, with its own login, from nodes bound to the Kelly owner (encrypted `GET_TELEMETRY_DATA` / `GET_STATUS`, findings §3.2-3.3).

## Options

1. **Allow the narrow exception:** the owner is the one consenting, and it is today's released behaviour.
2. **Frames only:** polled telemetry stops at 1.0.

## Decision

Option 1, limited exactly as §7.1 states: only telemetry the gateway polled itself, with its own login, from a node bound to the gateway's owner, using the owner's mapping. Never any other node's responses, and never a response it did not request. Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

§7.1's exception becomes part of the standard; §13's request/response ban names it as the one exception. Vectors for it go in `gateway.json`.
