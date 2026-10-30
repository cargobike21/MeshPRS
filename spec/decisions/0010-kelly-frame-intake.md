# 0010: Kelly reads MeshPRS frames from the companion's channel-data messages, with raw-log decryption as fallback

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** igate-design Q-A2
- **Spec sections affected:** none (implementation)

## Context

Kelly logs received channel data (companion response 27) and discards it (`kelly-page/js/meshcore.js:376`), and doesn't implement `CMD_SEND_CHANNEL_DATA` (62). `mcdecode.js` can already decrypt channel packets from the raw RX log.

## Options

1. **Companion channel data:** add `#meshprs` to the companion and read `CHANNEL_DATA_RECV`; uses one channel slot.
2. **Decrypt the raw RX log** in the page; no channel slot, but depends on the raw log being on.

## Decision

Option 1 primary, option 2 as fallback. Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

Kelly work: handle response 27 for data type 0xFF4D; add the `#meshprs` channel on setup; implement command 62 when sending is built.
