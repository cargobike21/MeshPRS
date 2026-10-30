# 0021: Wire format kept: big-endian callsigns, 24-bit positions, 8-bit telemetry

- **Status:** accepted
- **Date:** 2026-10-30
- **Answers:** OPEN-QUESTIONS Q19, Q23, Q24
- **Spec sections affected:** §4.1, §5.1, §7.2, §7.3

## Context

The 1.0 Candidate freezes the byte layout (decision 0020). These three questions are about layout, so they have to be settled before it is published.

## Options

- **Q24, callsign byte order:**
  - keep big-endian, byte-identical to M17, as the codecs and vectors already do;
  - or little-endian like every other field, which would mean redoing the codecs, vectors and examples.
- **Q19, position precision:**
  - keep 24-bit lat/lon (1-2 m, against APRS's ≈ 18 m);
  - or add a 32-bit option now.
- **Q23, telemetry range:**
  - 8-bit analog values only, as in classic APRS `T#`;
  - or add a 16-bit or decimal values kind now.

## Decision

Decided by Alec, 2026-10-30, taking the recommendation each time:
- **Q24:** callsigns stay big-endian.
- **Q19:** lat/lon stay 24-bit. Position pflags bit 7 stays reserved, so that a later version can use it to signal a higher-precision position.
- **Q23:** telemetry analog values stay 8-bit in 1.0. Wider values may later be added as a new telemetry kind from the reserved range.

## Consequences

- No byte changes.
- The spec no longer lists these as open. It names pflags bit 7 and the reserved telemetry kinds as the extension points.
- Under §9.5, a receiver that finds pflags bit 7 set already stops at that point and does not gate the frame (`unknown flag`), so a later 32-bit option stays safe for 1.0 receivers.
