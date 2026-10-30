# 0018: The per-station interval is kept per station and service

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** none (found while building Kelly's gate)
- **Spec sections affected:** §10.1 step 6, §15.2

## Context

Spec §10.1 step 6 applies one interval (Kelly: 2 min) per station. Applied literally, it drops three of the four telemetry definition frames (PARM, UNIT, EQNS, BITS) a station sends together (§7.3), and every object but one from an owner with several (§8.2).

## Options

1. **One interval per station:** simple; against: definitions and multi-object owners lose frames every time.
2. **One interval per station and service:** the key is (source, subtype), plus the telemetry kind for telemetry and the object name for objects.

## Decision

Option 2. Messages, acks and emergencies (codes 7 and 9) stay exempt. Decided by Alec, 2026-10-29, on the lead agent's recommendation.

## Consequences

§10.1 step 6 names the key. Kelly's `js/meshprs.js` Gate already uses it (`ivKey`). A station's position and its telemetry no longer hold each other back.
