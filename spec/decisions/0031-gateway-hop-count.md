# 0031: An H flag asks each gateway to fill in the hop count it saw, in telemetry and status

- **Status:** accepted
- **Date:** 2026-11-05
- **Answers:** OPEN-QUESTIONS Q40
- **Spec sections affected:** §7.2, §7.4 (new), §8.4, §10.3, §16.2

## Context

- **Alec wants to see how many repeaters a tracker's frames take to reach the iGate,** on aprs.fi: as a telemetry channel and in the status ("Hop count 2").
- **Only the gateway knows.** A flooded MeshCore packet collects one path hash per repeater. The receiver sees the count in path_len (low 6 bits; 0xFF = came direct), which Kelly already decodes (`kelly-page/js/meshcore.js` `hops()`, RESP 27 `CHANNEL_DATA_RECV`). The sender hears only its own frame echoed by the nearest repeater, which is always 1 hop.
- **§10.3 says gateways emit the frame's content only,** so that every gateway produces the same line and APRS-IS's duplicate filter merges copies.
- **The flag bits are there.** Telemetry mask bits 5-6 and status code bits 4-6 were reserved. A receiver drops a frame with a reserved bit set (§9.5), so gateways without this decision drop such frames.

## Options

1. **Gateway writes it, on the station's request (H flag):** the station opts in per frame. For: shows on aprs.fi, needs no new traffic. Against: one APRS-IS line per gateway that hears the frame; older gateways drop H frames.
2. **Gateway shows it locally only** (its own log / UI). For: no spec change. Against: not on aprs.fi.
3. **Station sends a stand-in it can measure** (repeaters that echoed). For: no spec change. Against: not the hop count to the gateway.
4. **Gateway replies with the count over the mesh,** and the station reports it next time. Against: airtime, a new subtype, and which gateway's count.

## Decision

Option 1, chosen by Alec (2026-11-05). Telemetry values: mask bit 5 = H, and the gateway puts its hop count (0-63, 0 = heard direct) in the first analog slot the mask leaves out. Status: code bit 4 = H, and the gateway adds " <hops>" to the text. A gateway that doesn't know the count leaves the slot empty or the text alone.

## Consequences

- §10.3's same-output rule has one exception, which the station opts into: each gateway's line can differ, so APRS-IS gets one per gateway.
- Gateways implementing 1.0 without this record drop H frames as `unknown flag`, so a station using H reaches only updated gateways.
- Vectors: `frames.json` bad-018 and bad-022 test the bits still reserved; bad-018h (H with all five analogs); `gateway.json` gw-hop-01 to 04 carry a per-vector `hops` in their config.
- Kelly Page: the page passes each copy's hop count into the gate and on to the bridge (`hops`); `meshprs.py` and `meshprs.js` render it.
- Mesh Buddy: telemetry sends A1, A3-A5 with H (A2 = Hops, `0,1,0`); the status goes with H, default text "Hop count".
