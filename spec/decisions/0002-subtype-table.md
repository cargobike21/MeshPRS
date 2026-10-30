# 0002: One-byte MeshPRS service subtype table

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q2 (in part: which services have a code point; what 1.0 requires stays open)
- **Spec sections affected:** §5-9, Annex B

## Context

All MeshPRS frames share one GRP_DATA data type (decision 0001), so a subtype byte inside the blob selects the service. A version is needed so the format can change without breaking deployed gateways.

## Options

1. **Alec's proposed table, with reserved and experimental ranges.**
2. One GRP_DATA data type per service; against: uses up registry space, and the registry asks for small ranges.

## Decision

Option 1:

| Value | Service |
|---|---|
| 0x00 | Position |
| 0x01 | Message |
| 0x02 | Ack |
| 0x03 | Telemetry |
| 0x04 | Weather |
| 0x05 | Object / Item |
| 0x06 | Bulletin |
| 0x07 | Query |
| 0x08 | Neighbour report |
| 0x09 | Emergency / Status |
| 0x0A-0xDF | Reserved for future standard use |
| 0xE0-0xFE | Experimental / private |
| 0xFF | Reserved |

The subtype uses the whole byte, so the version cannot share it as a nibble: it is carried separately (a version byte, bits in another header byte, or the GRP_DATA data type itself). Which one is left to the spec draft, which must justify it. Decided by Alec, 2026-10-29.

## Consequences

The spec owns the field layouts for each subtype. Code-point values are fixed by this record; changing them needs a new record.
