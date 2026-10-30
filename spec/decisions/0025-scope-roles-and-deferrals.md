# 0025: Gateway roles and directions confirmed; Meshtastic, neighbours on IS, profile registry and island links deferred

- **Status:** accepted
- **Date:** 2026-10-30
- **Answers:** OPEN-QUESTIONS Q3, Q4, Q5, Q21, Q28, Q29, Q30
- **Spec sections affected:** §1.2, §3.2, §4.2, §5.6, §6.5, §7.2, §8.3, Annex C

## Context

To publish the 1.0 Candidate (decision 0020), every scope question has to be either settled or explicitly deferred.

## Options

For each question: settle it as drafted, or widen 1.0. Widening 1.0 means designing and testing new rules before publishing.

## Decision

Decided by Alec, 2026-10-30, taking the recommendation each time.
- **Q4 + Q5, directions and roles:** confirmed as drafted.
  - There are three roles: iGate (mesh to APRS-IS), messaging gateway (adds APRS-IS messages into the mesh, sent direct, never flooded), and object server.
  - One box MAY hold several roles.
  - 1.0 covers APRS-IS only. APRS RF (145.175 MHz, LoRa APRS 433.775 MHz) is left to a later version, after the regulatory work (decision 0003).
- **Q3, Meshtastic:** out of scope for 1.0. A Meshtastic sister profile may follow later.
- **Q21, neighbour reports:** never gated to APRS-IS. They are for the mesh, MQTT and maps only.
- **Q28, telemetry profile registry:** not in 1.0, and kinds 0x05 and 0x10 stay `not gated` (decision 0017). Kelly's `PRESETS` can seed a later registry, kept in the MeshPRS repository.
- **Q29, sender positions into the mesh:** not in 1.0 (§5.6). This is future work.
- **Q30, island-to-island messaging through APRS-IS:** not in 1.0. The §6.5 loop rule stays, and a safe rule for it is future work.

## Consequences

- §3.2 states the roles as normative, without citing Q5.
- §1.2, §5.6, §6.5 and §8.3 drop their open-question references.
- A "Future work" list in §16 names the deferred items: RF gating, Meshtastic, signed frames, the profile registry, sender positions, island-to-island messaging, and the bulletin agent.
