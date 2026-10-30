# 0011: MeshPRS airtime budget: 10 s/h of transmit time and one flood per 10 min per node

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q11
- **Spec sections affected:** §5.5, §10.1, §12.3

## Context

LIPD 2025 sets no duty-cycle limit in 915-928 MHz and MBUG publishes no number (findings §5.1, §5.4). A flood reaches roughly 30-80 SEQ repeaters (design/reliability.md), so each flooded frame costs that many retransmissions.

## Options

1. **Adopt reliability.md §4.4:** per node at most 10 s/h of MeshPRS transmit time, at most one flooded frame per 10 min, at most 2 retries per message; per region at most 2 % added occupancy at any site.
2. **No budget, rate limits only.**

## Decision

Option 1, offered to MBUG as MeshPRS's figures. The APRS-IS → mesh gateway budget (igate-design Q-A8) waits for 0008's follow-up. Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

The spec's §12.3 cites these as the network figures; the `airtime` drop reason enforces them on the gateway side. The test plan measures against them.
