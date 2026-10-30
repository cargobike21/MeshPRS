# 0015: Kelly iGate settings for MeshPRS frames

- **Status:** accepted; the Q-A6 part replaced by 0019
- **Date:** 2026-10-29
- **Answers:** igate-design Q-A5, Q-A6, Q-A7, Q-A9, Q-A10
- **Spec sections affected:** none (implementation; Q-A7 follows decision 0005)

## Context

Decisions 0005 and 0008-0010 fixed where Kelly's MeshPRS iGate runs and how frames reach it. Five settings were still open in [design/igate-design.md](../../design/igate-design.md) §12 before the Kelly code could start.

## Options

Each question had a recommendation in igate-design §12:

1. **Q-A5 server:** `aunz.aprs2.net:14580`, with `rotate.aprs2.net` as fallback (spec §11), or keep `rotate` as the default.
2. **Q-A6 list entries:** keep profile-0 entries (owner-chosen SSID, symbol, comment) for adverts only and add frame bindings separately, or rebind existing entries to the frame's callsign-SSID.
3. **Q-A7 binding scope:** one binding per base callsign, or one per SSID.
4. **Q-A9 holds:** jitter 0-5 s, at most 10 s waiting for the rate limit, `expired` 15 s after receipt (spec §10.1); today's figures are 0-8 s and 30 s.
5. **Q-A10 recent advert:** require an advert from the bound key in the last 24 h before gating its frames (spec §4.3 item 5), or not.

## Decision

The recommendation in each case: `aunz.aprs2.net` with `rotate.aprs2.net` as fallback; frame bindings kept separate from profile-0 entries; bindings per base callsign, the SSID taken from the frame (as decision 0005 already says); the spec §10.1 hold times, tuned from the trial; and a 24 h recent-advert requirement in Kelly. Decided by Alec, 2026-10-29.

## Consequences

Kelly work: change the default server; add a frame-binding store beside `igateList`; set the Gate's jitter and wait defaults for frames to 5 s and 10 s and add the 15 s `expired` drop; keep a last-advert time per key and refuse frames from a key not heard in 24 h (counted as `untrusted`). Profile-0 advert gating is unchanged.
