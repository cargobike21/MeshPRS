# MeshPRS: field trial log

A record of the on-air testing behind MeshPRS: what was sent, what arrived, what it cost the mesh, and what was changed as a result. Informative, not normative. The rules are in the spec and the decision records it cites.

**The test station is a real tracker on a real push bike.**
- VK4AZ-12 is a RAK4631 with RAK12500 GNSS running Mesh Buddy (`tools/mesh-buddy` in the reference implementation's repo), the MeshPRS reference tracker. It rides daily commutes and evening rides in Brisbane.
- One Kelly Page iGate, VK4AZ-10, gates it live to APRS-IS (`aunz.aprs2.net`) and keeps the 24 h per-frame log of spec §10.4.
- All traffic is on the SEQ MeshCore network on MBUG settings (spec §12.3): unscoped floods of GRP_DATA on `#meshprs`, shared with everyone else's traffic.

**Privacy.** This log gives no coordinates, suburbs, routes or bearings. The tester's home and workplace stay private, and the iGate's privacy zone (Kelly Page) hides the home on APRS-IS. The raw logs are kept privately and can be shown to MBUG on request.

**How the numbers are measured.**
- **Frames sent** come from the header seq (spec §9.3). Every new frame of any subtype takes the next seq, heard or not, so seq gaps count lost frames exactly. Retries reuse their seq, so they are not in "frames sent".
- **Heard** means received by the one iGate, directly or through any number of repeaters. Another iGate might have heard more.
- **Own airtime** is estimated at about 0.4 s per frame, the 37-53 byte range of spec §5.5's table at SF8 / 62.5 kHz. Each repeater that relays a flood spends about that much again.

---

## 1. Settings over time

Every change made the tracker send less, or made what it sends count for more.

| Date | Tracker version | Change | Why |
|---|---|---|---|
| 2026-10-31 | v3 | First ride: smart beaconing, 60 s minimum, flooded; status every 30 min | Baseline |
| 2026-10-31 | 1.1 | Status and telemetry definitions every **12 h** instead of 30 min (decision 0028) | Parked, they were about half the tracker's airtime |
| 2026-11-01 | 1.2 | GPS quality gate: no position without a 3D fix, PDOP ≤ 5, HDOP ≤ 3, accuracy ≤ 50 m and ≥ 5 satellites | No positions from a poor fix |
| 2026-11-03 | 1.2 | Smart beaconing: 60 s minimum, 50 m move threshold | Track detail while riding |
| 2026-11-04 | 1.3 | One retry of a position with no repeater echo; track history (decision 0030); hardware watchdog | Recover lost positions instead of sending more often |
| 2026-11-05 | 1.4 | Hop count to the iGate on aprs.fi (decision 0031) | Measure the path without sending traces |
| 2026-11-05 | 1.5 | Telemetry every **30 min** moving and **60 min** parked; minimum interval **120 s** (the spec default); move threshold **500 m** | A traffic review showed the bike was the busiest single source the iGate's node heard (§3) |
| 2026-11-06 | 1.5 | Parked position at most **hourly** (`max 3600`) | GPS drift while parked made about 20 extra positions a day (§4) |
| 2026-11-06 | iGate | Late or duplicate track history entries no longer go to APRS-IS (decision 0032) | They drew spikes back along the track |
| 2026-11-06 | 1.6 | Parked, telemetry waits for a position that drew an echo (3 h at most); parked position every **30 min** (`max 1800`) | Parked indoors, 0 of ~9 hourly telemetry frames and 0 first transmissions arrived (§4) |

Not done, on purpose: no padding of the flood path to cap hop count. MeshCore has no sender hop limit, and padding would add 54 bytes to every transmission for everyone (`reliability.md`).

## 2. Rides

| Date | Ride | Tracker | Frames sent | Heard by the iGate | Notes |
|---|---|---|---|---|---|
| 2026-10-31 | 92 min loop | v3, 60 s min | 68 | 47 (69 %) | All 28 gated frames appeared once on aprs.fi. Losses at the first hop, clustered (decision 0027) |
| 2026-11-05 | Morning commute, 33 min | 1.4, 60 s / 50 m | 36 | 10 (28 %) | A known weak area for the first hop |
| 2026-11-05 | Three evening rides | 1.4, 60 s / 50 m | ~49 | 94 %, 72 %, 94 % | |
| 2026-11-06 | Morning commute, 34 min | 1.5, 120 s / 500 m | 20 | 17 (85 %) | 2 of the 3 lost positions recovered by track history: 19 of 20 known |
| 2026-11-06 | Afternoon ride, 19 min | 1.5 | 8 | 7 (88 %) | 3 positions got through only by their retry |

Latency from mesh to APRS-IS on the first ride: median 4 s, maximum 6 s (decision 0027).

## 3. What the tracker costs the mesh

**Transmission rate, from seq.**

| | 2026-11-05 (1.4) | 2026-11-06 (1.5) | Change |
|---|---|---|---|
| Moving | ~64 frames/h | ~35 frames/h | −45 % |
| Parked (a working day) | ~9 frames/h | ~2.7 frames/h | −70 % |
| Whole day | ~157 frames in 13 h (1 per 5 min) | 57 frames in 10.4 h (1 per 11 min) | about half |
| Own airtime, day average | ~4.8 s/h | ~2.2 s/h | |
| Own airtime, riding hour | ~26 s/h | ~14 s/h | |

**Against the budget** (decisions 0011 and 0033, `reliability.md` §4.4: per node at most 144 floods and 240 s of own airtime per 24 h, burst 3):
- **The whole day is now within it:** about 1 frame per 11 min and 2.2 s/h.
- **A riding hour is denser:** about 35 frames and 14 s at the spec's 120 s minimum. Decision 0033 makes the budget a 24 h average (144 floods, 240 s), so the day is what counts: about 40 % of the frame budget and 10 % of the airtime budget on 2026-11-06.

**Share of what the iGate's node hears.** In riding hours, the bike's frames were 15-22 % of the flood packets the iGate's node heard (for example 17 of 76 in the 06:00 hour on 2026-11-06, 31 of 194 in the 17:00 hour on 2026-11-05). That overstates its share across the network:
- the node sits near the start of the routes, so it hears the bike far better than a distant repeater does;
- early morning is the quietest time on the mesh, so the share is highest then.

It is still the reason for 1.5's reductions.

## 4. Lessons that changed the design

- **Losses happen at the first hop, and they cluster** (decision 0027). Sending more often doesn't fill a hole. A late retry and a track history do (decision 0030).
- **An echo is a good test of the first hop, not of delivery.** The tracker treats a repeater echo as delivered. Twice the iGate received a retry that no repeater echoed back to the tracker, so the tracker kept the position for history and it was sent again (decision 0032). In one weak area a repeater echoed positions that never reached the iGate. The iGate now drops the duplicates. Whether the tracker should also change is still open.
- **A track history always arrives after a newer live position.** On a map that draws positions in arrival order, its entries made spikes back along the track: 1.2 km, 480 m and 500 m on 2026-11-06. They now stay in the iGate's log, which has the complete track, and go to APRS-IS only when newer than every live position already sent (decision 0032).
- **GPS drift moves a parked tracker.** With a 50 m move threshold, a tracker parked indoors at work sent about 20 drift positions in a day (altitude wandering 32-193 m). A 500 m threshold and an hourly parked position stopped that. The spec's default is now 500 m (decision 0034).
- **Parked indoors, fewer frames means fewer chances.** At work the only path to the iGate is one marginal repeater link, 2-3 hops.
  - On 2026-11-05 (1.4, 50 m threshold) the tracker sent about 81 frames while parked, most of them drift positions, and about 40 % were heard.
  - On 2026-11-06 (1.5, hourly position) it sent about 24 and 4 were heard (17 %). All 4 were positions that got through only on their retry. No first transmission and none of the hourly telemetry frames, which have no retry, got through.
  - The drift positions had worked as extra attempts. A track history can't help a parked tracker: its entries expire after 30 min, positions are an hour apart, and it waits for an echo that seldom comes there.
- **Status and definitions are cheap to repeat rarely.** At 30-min repeats they were half of a parked tracker's airtime (decision 0028).

## 5. Next

- **Boot burst:** at power-on Mesh Buddy sends 4 telemetry definitions and a value frame 6 s apart, a burst of 5 against the limit of 3 (decision 0033). To be spread out in firmware.
- **A second iGate.** The field-trial criteria (test plan §7) need at least 2 iGates, 3 originators and 7 days. So far there is one iGate and one tracker.
- **Repeater counters.** Logging `GET_STATUS` deltas on the nearest repeaters would measure added occupancy directly (criteria P7, P9), not estimate it.
