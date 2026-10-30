# 0013: Field-trial pass criteria

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q12
- **Spec sections affected:** design/test-plan.md §7

## Context

The trial must show MeshPRS is reliable and harmless. Sample sizes follow the two-sided 95 % Wilson interval (design/test-plan.md).

## Options

1. **Adopt test-plan.md §7:** delivery within 3 hops at least 90 % (lower bound at least 85 %, n at least 196); message round trip at least 95 %; exactly one APRS-IS copy per frame; zero loops; within the 0011 airtime budget; 95th-percentile latency at most 10 s.
2. **Looser, exploratory trial.**

## Decision

Option 1. Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

test-plan.md §7 loses its "proposed" status. A trial that misses a criterion is reported, and the spec changes before 1.0.
