# 0012: Trial identifiers: channel #meshprs, data type 0xFF4D, tocall APZKPG; register after a working demo

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q13, Q16, Q17
- **Spec sections affected:** §9.1, §11, §12.1

## Context

`#meshprs` (channel hash 0xBA) doesn't clash with existing chat; `#aprs` may already carry human chat. 0xFF4D is in the free development range (findings §1.6). APZKPG is unallocated in the APZ experimental range (findings §4.4); one tocall is shared by every MeshPRS gateway so APRS-IS dedupes across iGates.

## Options

1. **Use the development values for the trial, register after a working demo:** a 0100-FEFF data type by pull request to MeshCore's number_allocations.md, and a tocall via the aprs-deviceid repo.
2. **Register now:** against: both registries ask for a working implementation first.

## Decision

Option 1. MBUG is told about `#meshprs`. Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

§12.1's channel name is no longer proposed. Q13's review question (who reviews 1.0) stays open.
