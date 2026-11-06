# 0032: A track history entry behind the live track, or already sent live, is not gated

- **Status:** accepted
- **Date:** 2026-11-06
- **Answers:** OPEN-QUESTIONS Q41
- **Spec sections affected:** §5.8 (gateway conversion, "On aprs.fi"), §16.2

## Context

- **A track history always arrives after a newer live position** (§5.8): the station sends it only once a later frame draws an echo.
- **On a map that draws positions in arrival order,** its entries make a spike back along the track and forward again. On 2026-11-06 VK4AZ-12's entries jumped back 1.2 km, about 480 m and about 500 m (`../../design/field-trial-log.md` §4).
- **An echo tests the first hop, not delivery.** On the evening of 2026-11-05, 4 of the 6 history entries VK4AZ-12 sent had already been gated: the iGate had received each one's retry, but no repeater echo reached the tracker, so it kept the position. Each was gated twice, the second time minutes late.
- **aprs.fi may keep a timestamped late position off its track,** but this is unverified for a timestamped position that follows an untimestamped one (`../../research/aprs-facts.md`). Other APRS-IS clients may not.

## Options

1. **Gate only the entries that are newer than every live position already gated for the station, and never one already gated live.** The rest stay in the gateway's diagnostic log (§10.4). For: no spikes, no double lines. The log still holds the full track. Against: APRS-IS loses the backfill for short holes, the common case.
2. **Keep gating every entry, timestamped,** and rely on clients to use the timestamp. For: APRS-IS gets the full track. Against: spikes on clients that plot in arrival order, and double lines.
3. **A per-gateway switch,** off by default. For: owners choose. Against: different gateways give different output for the same frame, against §10.3.

## Decision

Option 1. Decided by Alec, 2026-11-06, taking the recommendation.

## Consequences

- **The spec, §5.8, gateway conversion:**
  - a gateway MUST NOT gate an entry whose position is exactly one it gated live for the same station in the last 1800 s (`duplicate`);
  - it SHOULD NOT gate an entry older than the newest live position it has gated for that station (`late`), and logs it instead (§10.4).
  - Entries newer than every live position gated still go, so a long hole with no live position is still filled.
- **The "On aprs.fi" note** no longer applies in the common case. A gated entry is now always the newest position the gateway has sent for that station.
- **Determinism (§10.3):** what is gated now depends on what the gateway has already gated for the station. Two gateways with different histories can gate different entries. APRS-IS's duplicate filter still merges any entry both of them gate, because each entry renders the same.
- **Test vectors:** none. The vectors are one frame each, and this rule depends on the frames before it. The reference iGate's tests cover it (`kelly-page/bridge/test_kelly_igate.py`, "hist late").
- **Implementations:** Kelly Page's bridge, `kelly_igate.py` `_hist`, live on the VK4AZ-10 iGate from 2026-11-06.
- **Left open:** whether the station should change how it decides a position was delivered. A first-hop echo is the only signal it has.
