# 0022: End-to-end acks; frames from APRS-IS are shown as unverified

- **Status:** accepted
- **Date:** 2026-10-30
- **Answers:** OPEN-QUESTIONS Q14, Q27
- **Spec sections affected:** §6.4, §6.5, §9.3 (G)

## Context

A messaging gateway passes APRS-IS messages into the mesh direct (§6.5). The APRS sender has to know whether the message arrived.

A G = 1 frame's seq and msgno come from `SHA-256(source ":" ID)`, so every gateway builds the same bytes, with a 1-in-32,768 msgno clash rule. Anyone on the channel can set G = 1, though, so a G = 1 frame proves nothing about where it came from.

## Options

- **Q14, whose ack counts:**
  - end-to-end, where `ackID` goes to APRS-IS only when the mesh addressee acks;
  - or the gateway acks once it has transmitted.
- **Q27:**
  - keep the derivation and clash rule, and add a receive-side rule that G = 1 senders are shown as unverified;
  - or keep the derivation with no receive-side rule.

## Decision

Decided by Alec, 2026-10-30, taking the recommendation each time.
- **Q14:** acks are **end-to-end**. A gateway MUST NOT send `ackID` to APRS-IS until the mesh addressee's ack frame arrives. Messages over 67 characters are refused (`bad text`), never truncated or split, as the draft already said.
- **Q27:** keep the SHA-256 derivation and the clash rule.
  - A station SHOULD show the sender of a G = 1 frame as having come via APRS-IS and unverified.
  - It MUST NOT treat a G = 1 frame as proof that the sender is on the mesh.
  - The existing rule stays: a gateway never gates a G = 1 frame back to APRS-IS (`looped`).

## Consequences

The spec's §6.4 and §6.5 state the ack rule as normative. A display rule for G = 1 senders is added to §9.3. No byte changes.
