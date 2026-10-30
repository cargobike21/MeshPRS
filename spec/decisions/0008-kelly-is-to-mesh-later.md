# 0008: Kelly's first MeshPRS release does not gate APRS-IS into the mesh

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q4 (for Kelly's first release); igate-design Q-A4
- **Spec sections affected:** §6.5 (implementation note only)

## Context

APRS-IS → mesh is the direction that can cost mesh airtime and loop. The spec allows it (direct only, never flooded, §6.5), but nothing has been tested.

## Options

1. **Receive-only first:** the trial proves mesh → APRS-IS; then messages only.
2. **Messages in the first release,** off by default.

## Decision

Option 1. Kelly's first MeshPRS release is receive-only (qAO). Messages-only APRS-IS → mesh, direct and never flooded, follows after the field trial. Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

The spec's §6.5 is unchanged (it defines the messaging-gateway profile for when it is built). The test plan's inject.json stage runs on the private aprsc only until then.
