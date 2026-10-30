# 0001: Tier A carries MeshPRS frames in GRP_DATA on a dedicated channel

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q8 (mesh-side transport, for mesh-originated APRS traffic)
- **Spec sections affected:** §3, §9, §12, Annex C

## Context

Stock MeshCore 1.18.0 repeaters flood GRP_DATA and GRP_TXT without decrypting them, but never flood RAW_CUSTOM; RAW_CUSTOM only travels a known source route, and companions refuse to flood it. MULTIPART carries only ACKs. GRP_DATA carries a blob of up to 165 bytes under a 16-bit data type, with FF00-FFFF free for development. See [research/00-findings.md](../../research/00-findings.md) §2 and §6.

## Options

1. **RAW_CUSTOM:** no channel overhead and unencrypted; against: never flooded, needs a known path, no destination. Unusable for beacons.
2. **GRP_DATA on a dedicated channel:** flooded and direct-routable on stock repeaters, sendable from stock companion firmware (`CMD_SEND_CHANNEL_DATA`); against: AES padding to 16-byte blocks, needs a data type, stock phone apps don't decode it.
3. **GRP_TXT compact APRS text:** works in every phone app; against: `name: ` prefix in a 160-byte limit, self-asserted sender, more bytes.

## Decision

Option 2: GRP_DATA on a dedicated MeshPRS channel, using a development data type in FF00-FFFF until a range is registered. GRP_TXT compact text remains a fallback profile for stock phone apps. Decided by Alec, 2026-10-29.

## Consequences

The spec defines one GRP_DATA data type for MeshPRS and a binary frame inside it. Binary encoding needs app or gateway changes only, not modified firmware, so Tier B narrows to what the app layer cannot do (Annex C). Every frame needs a field that changes per send, because repeaters' duplicate table hashes only the payload. Floods SHOULD be unscoped, because region-scoped floods die at repeaters without that region.
