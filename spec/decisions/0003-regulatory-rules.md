# 0003: Adopt the spec §13 regulatory rules; nothing to amateur RF in 1.0

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q9, Q10 (for 1.0)
- **Spec sections affected:** §13, §1.2

## Context

MeshCore in SEQ runs under the LIPD Class Licence 2025 (F2025L01047), not amateur; there is no amateur allocation in 915-928 MHz. The amateur class licence bans obscuring meaning (s13(2)(d)(iv)) and its "intercommunication" excludes contact with non-amateur stations. APRS-IS is amateur-only by APRS-IS policy, not ACMA law. See [research/00-findings.md](../../research/00-findings.md) §5.

## Options

1. **Adopt the §13 rules as written** (SA-5's R1-R8): gate to APRS-IS only callsigns bound to a node key, through a passcode-verified gateway, marked qAO; never gate DMs, private channels, room-server deliveries or (except 0006) request/response contents; nothing from the mesh to amateur RF in 1.0.
2. **Allow mesh → amateur RF now** for verified amateur callsigns in plaintext; against: legally untested, needs s12 identification and s13(4) unattended-operation rules.

## Decision

Option 1. The §13 rules are normative. Gating anything from the mesh onto amateur RF (VHF APRS 145.175 MHz, LoRa APRS 433.775 MHz) is out of scope for 1.0, so Q9 and Q10 are settled for 1.0 and stay open only for a later version. Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

§13 loses its "pending decision records" status. Gateways are APRS-IS-only in 1.0; no s12/s13(4) rules are needed yet. A later RF profile needs its own decision record.
