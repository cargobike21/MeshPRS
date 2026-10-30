# 0004: A frame is gated to APRS-IS only if it carries the sender's key prefix (K)

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q18 (first half: optional vs mandatory; signed frames stay open)
- **Spec sections affected:** §4.3, §9.3

## Context

GRP_TXT/GRP_DATA carry no sender key (findings §1.5), so a callsign in a frame is self-asserted. The 4-byte node-key prefix (K flag) lets a gateway check the claim against the bound key. It is public, so it stops misconfiguration and casual spoofing, not a determined attacker. With K, the required VK4ABC position frame is 28 bytes, still inside the 29-byte AES step (37 B on air).

## Options

1. **Optional K** (draft 0.1): stations SHOULD set it; frames without it are mesh-only.
2. **K required for gating:** a station whose frames are to reach APRS-IS MUST set K; frames without K are never gated.

## Decision

Option 2. The one exception kept from the draft is the ack (§6.2): a gateway may gate an ack without K only when it matches a message that gateway itself delivered, and the ack's source callsign must still be bound. That keeps the ack in one AES block (21 B on air). Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

§4.3 item 1 becomes a MUST for stations that want to be gated. Gateways drop un-keyed frames as `no key` (except the ack case). Signed frames and periodic signed binding claims remain Q18.
