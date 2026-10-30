# 0017: Four rendering gaps found while writing the test vectors

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** none (gaps found while writing `test-vectors/gateway.json`)
- **Spec sections affected:** §7.2, §8.4, §10.1, §10.3, §15.2

## Context

Byte-identical output across gateways (§10.3) needs a rule for every case. Writing the gateway vectors turned up four cases the draft did not settle.

## Options

For each, either define the behaviour now or leave the case undefined until the trial. Leaving it undefined means two implementations may render differently, which breaks APRS-IS duplicate merging.

## Decision

1. **Telemetry with no digital byte** (mask bit 7 clear): the APRS `T#` bits field is `00000000`, as Kelly's profile-0 telemetry already writes.
2. **Emergency / status codes 0-7 and 9 with a position:** the position report uses the symbol `/>`, as the spec's own example does. The frame has no symbol field.
3. **Status code 8 with a position:** rendered as `>text`; the position is not rendered.
4. **Telemetry kinds 0x05 (profile ID) and 0x10 (CayenneLPP):** dropped as `not gated` until the profile registry (Q28) exists.

Decided by Alec, 2026-10-29, on the lead agent's recommendation.

## Consequences

The spec states the four rules; `test-vectors/gateway.json` gw-032 (absent analogs, bits present), gw-034 (profile ID) and gw-051 (emergency symbol) cover them, with vectors for cases 1 and 3 added alongside. Item 2 may change if Q20 (emergencies on APRS-IS) adds a symbol field.
