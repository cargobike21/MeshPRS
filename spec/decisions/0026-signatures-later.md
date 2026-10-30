# 0026: No signed frames in 1.0

- **Status:** accepted
- **Date:** 2026-10-30
- **Answers:** OPEN-QUESTIONS Q18 (second half; the first half is decision 0004)
- **Spec sections affected:** §4.3, §14

## Context

The 4-byte key prefix (decision 0004) catches misconfiguration and casual spoofing only, because anyone who hears an advert can copy it. Real proof needs an Ed25519 signature. At +64 bytes, that would roughly triple a position frame's airtime.

## Options

1. **Later version:** no signatures in 1.0. Trust rests on gateway bindings (decision 0005).
2. **Periodic signed claim:** an occasional signed frame saying "this key is VK4xxx-n", defined in 1.0.

## Decision

Option 1. Decided by Alec, 2026-10-30, on the recommendation. A signed frame or signed binding claim would later take a subtype from the reserved range 0x0A-0xDF, so 1.0 needs no header bit for it.

## Consequences

- §4.3 and §14 say that 1.0 has no cryptographic proof of identity, and that gateway bindings are the trust model.
- Gating compact text (decision 0023) depends on this future work.
