# 0016: Kelly sends MeshPRS position frames as well as its advert

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** igate-design Q-A11
- **Spec sections affected:** none (implementation)

## Context

No application sends MeshPRS frames yet, so a receive-only iGate would have nothing to gate in the trial. Kelly already beacons its own position as a MeshCore advert (`igateui.js` own beacon). Sending frames needs `CMD_SEND_CHANNEL_DATA` (62), which Kelly does not have yet (decision 0010).

## Options

1. **Advert only:** no change; against: the trial needs a sender, and a phone app would have to be written first.
2. **Advert plus a MeshPRS position frame:** Kelly becomes a MeshPRS station, so one Kelly can beacon and another can gate it.

## Decision

Option 2. Kelly keeps its advert and also sends a Position frame (K set, spec §5) on the `#meshprs` channel, within the spec §5.5 smart-beaconing limits and the decision 0011 airtime budget. Decided by Alec, 2026-10-29.

## Consequences

Kelly work: implement command 62, a per-key seq counter kept across restarts (spec §9.3), and a setting to turn frame beaconing on. Where one station sends both, spec §5.4 applies (the frame is preferred and one per-station interval covers both).
