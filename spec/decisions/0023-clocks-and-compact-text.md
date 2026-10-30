# 0023: Receive time is authoritative; compact text stays mesh-only under `MPRS`

- **Status:** accepted
- **Date:** 2026-10-30
- **Answers:** OPEN-QUESTIONS Q15, Q22
- **Spec sections affected:** §5.3, §8.2, §9.7, §10.3, §14

## Context

**Clocks.** MeshCore node clocks are often wrong: a repeater restarts at May 2024 (F§3.1). The draft judges freshness and replays by the gateway's receive time and seq. It uses the sender's TS only to time-stamp APRS objects, and only when TS lies within ±1 h of the receive time, so that every gateway renders the same line.

**Compact text.** GRP_TXT lines starting `MPRS` let stock phone apps read and type MeshPRS traffic. A GRP_TXT packet carries no sender key, so even the weak key-prefix check (§4.3) is impossible.

## Options

- **Q15:**
  - the rule as drafted;
  - or never use the sender's TS, even for objects. That is simpler, but gateways would then disagree at minute boundaries and produce duplicate APRS-IS lines.
- **Q22:**
  - keep `MPRS` and mesh-only;
  - choose another marker;
  - or drop the text profile.

## Decision

Decided by Alec, 2026-10-30, taking the recommendation each time.
- **Q15:** as drafted. The gateway's receive time is authoritative. TS is informative, apart from the ±1 h object-time rule.
- **Q22:** the marker stays `MPRS`. Compact text frames are never gated to APRS-IS in 1.0. Gating them could be looked at again only once signed frames exist (decision 0026).

## Consequences

Q15 and Q22 are no longer cited as open in §5.3, §8.2 and §9.7. No byte changes.
