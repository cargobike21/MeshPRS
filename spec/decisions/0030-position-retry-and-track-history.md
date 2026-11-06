# 0030: A position with no echo is retried once at 40-50 s; positions still missed go later in a track history (0x0A)

- **Status:** accepted
- **Date:** 2026-11-04
- **Answers:** OPEN-QUESTIONS Q39
- **Spec sections affected:** §5.3, §5.7 (new), §5.8 (new), §9.2, §9.3 (retry field), §9.4, §9.5, §10.1 steps 6 and 8, §10.2, §10.3, §15, §15.2, §16.1, §16.2

## Context

- **Loss is clustered and mostly at the first hop.** On the 2026-10-31 ride 69 % of position frames were heard. P(lost | previous lost) was 48 %, against 31 % overall, and 46 of the 47 arrivals came in 3 hops or fewer (decision 0027). The 2026-11-04 rides heard about a third to a half of positions while moving (`tools/mesh-buddy/TRACKER-IMPROVEMENTS.md`).
- **A tracker can tell when a frame was probably lost.** When a repeater relays a flooded frame, its sender hears the copy, which has the same packet hash because the hash covers the payload only (F§2.4). Mesh Buddy already listens for this "echo" for 20 s after each frame, for its Echo% telemetry (`research/meshcore-facts.md`).
- **Positions have no retry rule.** Messages are retried until acked (§6.3) and a new plain status once at 60-90 s (§8.4, decision 0027), but a lost position is simply gone. Raising the beacon rate does not help inside a coverage hole, and every extra flood costs everyone airtime (decision 0011).
- **Gateways already collapse retries.** The duplicate key is (originator identity, seq), ignoring the retry field and the subtype (§10.2), so a retried position gives one APRS-IS line.
- **Node clocks can't be trusted** (decision 0023). A late position therefore can't carry its own wall-clock time. It can carry its age, measured on the station's own uptime clock, and the gateway can subtract that from its receive time.
- **APRS timestamps** (APRS12c ch. 6 p.22-23, in `research/aprs-facts.md`):
  - DHM zulu `DDHHMMz` carries the day and is the format APRS recommends on air;
  - HMS `HHMMSSh` has seconds and no day;
  - a timestamped report "may possibly be (very) old"; data type `/` (or `@` with messaging) marks it.
- **aprs.fi** uses timestamps to keep delayed packets out of a station's track ("They prevent the station tracks from jumping back and forth to old positions due to delayed packets", OH7LZB, 2025-06-20). It labels such packets "[Delayed or out-of-order packet (timestamp)]" in the raw view (`research/aprs-facts.md`). History entries always arrive after a newer live position, so aprs.fi will most likely list them as raw packets but not draw them on the track. This is unverified for a timestamped position following an untimestamped one.
- **The 100-byte limit.** Mesh Buddy builds frames in a 100-byte buffer (`MPRS_MAX_BLOB`). The GRP_DATA limit is 165 (§9.1).

## Options

Alec was asked how Mesh Buddy should recover positions that drew no echo:

1. **Retry only:** resend a position once when its echo window closes with no echo. For: simple, no new subtype, gateways need no change (§10.2), and the APRS-IS line is a live position, which aprs.fi draws. Against: inside a long hole the retry is lost too, because losses cluster.
2. **Track history only:** keep the missed positions and send them later, in one frame, once back in coverage. For: recovers positions lost in long holes. Against: a new subtype and gateway rule; the entries are timestamped and late, so aprs.fi may keep them off the map track; a short hole costs a whole history frame.
3. **Both:** retry first, which recovers short holes as live positions; a history frame carries whatever the retry did not recover.

## Decision

Option 3, both. Decided by Alec, 2026-11-04.

**A. Position retry (§5.7).**
- A position whose 20 s echo window closes with no echo is sent once more: same bytes and seq, retry field 1, after a further random **20-30 s** delay, so **40-50 s** after the original.
  - A window cut short by the station's next frame does not count.
- **Only:**
  - when flooding;
  - when quiet (the station's 5 s gap between frames);
  - when no newer position has been sent, and no new beacon is due within 10 s.
- **Never more than once.**
- **Why 40-50 s:**
  - The retry has to get out of the bad spot: at 60 s after a lost frame the loss rate was still 48 % (decision 0027), so an immediate retry would mostly be lost as well.
  - It has to come before the next beacon (60-120 s, §5.5), or it is pointless. 40-50 s is the latest that still leaves room for the 10 s skip rule at a 60 s minimum.
  - The random spread keeps two stations that collided from retrying into each other.
  - Losses are mostly at the first hop, so a retry no repeater hears costs only the tracker's own transmission.
  - The ride data can't say how much better 45 s is than 60 s. Kelly's received-packet log keeps seq and retry per frame (spec §10.4, decision 0027), so the next ride measures it.

**B. Track history (§5.8, subtype 0x0A).**
- **Subtype 0x0A**, the first value of "reserved for future standard use" (0x0A-0xDF, decision 0002). It is a standard service, so it does not go in the experimental range: gateways MUST NOT gate 0xE0-0xFE (§9.5).
- **The tracker keeps** a position when neither the frame nor its retry, if one was sent, drew an echo:
  - at most **8**, oldest dropped;
  - nothing older than **30 min**.
- **When a later frame does draw an echo**, the tracker sends one history frame with its new seq (not a retry), then forgets the entries.
- **Layout:** symbol 2, hflags 1 (ALT, ambiguity, MSG), count 1, then per entry `age` u16 s, `lat` i24, `lon` i24 and `alt` i16 if ALT.
  - `age` is the time from taking the position to sending the frame, on the tracker's own uptime clock. That is how it squares with decision 0023: no node clock is needed, and the gateway's receive time stays authoritative.
  - Absolute i24 positions reuse §5.1, and each entry stands alone.
  - The largest frame (8 entries, altitude, K) is N = 97, inside Mesh Buddy's 100-byte buffer. It takes 7 AES blocks, 117 bytes on air, about 800 ms at SF8, once per return to coverage.
- **Gateway rendering:** each entry becomes `/DDHHMMz` (`@` with MSG) + position + `/A=`, timestamped ⌊receive time⌋ − age, truncated to the minute.
  - **DHM zulu, not HMS:** it carries the day, it is APRS's recommended on-air format, and objects already use it (§8.2).
  - Most of all, gateways whose receive times differ by a second or two still produce the same line, so APRS-IS merges their copies. HMS seconds would split them.
- **Gateways:**
  - MUST apply the same per-station privacy and abuse rules to each entry as to a live position;
  - MUST NOT let entries change live-position state (the 0x00 interval, jump or plausibility references, the last known position), because entries are older than the live position;
  - send the frame through replay and duplicate checks by its own seq;
  - drop entries aged 0 or over 1800 s (`stale`) and at 0,0 (`0,0`), and the frame when none is left (`stale`).
- **Rate** (relates to decision 0029):
  - The frame has its own interval key (source, 0x0A). Entries bypass the per-station interval against each other and against live positions: the interval is an abuse guard against a runaway station, and the history frame's own key already bounds that.
  - Each entry line takes a token from the global bucket, so 8 entries use 8 of the burst of 10 and wait for tokens like any frame.

## Consequences

- **The spec:**
  - §5.7 (position retry) and §5.8 (track history) are new.
  - §9.4 lists 0x0A, and the reserved range starts at 0x0B.
  - §9.3's retry note, §9.5's field-order and subtype rows, §10.1 steps 6 and 8, §10.2, §10.3's timestamp row, §15 (0x0A optional), §15.2 (`stale` and `0,0` cover entries), §16.1 and §16.2 follow.
- **Test vectors:**
  - `frames.json`: history encode and decode (`hst-001` to `hst-004`) and seven invalid frames (`bad-hst-*`). The reserved-subtype vector `bad-007` moves to 0x0B.
  - `gateway.json`: rendering, timestamps, minute truncation, age limits, 0,0 entries, ambiguity, no K and G = 1 (`gw-hst-001` to `gw-hst-009`), and a Mesh Buddy-layout position retry rendering the original's line (`gw-hst-010`).
  - A track history's `out` is a **list** of lines.
  - The stateful cases (retry collapse, interval and rate for entries) are in `kelly-page/tests/meshprs-tests.html`.
- **Implementations:**
  - Kelly's iGate (`js/meshprs.js`, `bridge/meshprs.py`, `bridge/kelly_igate.py`) gates 0x0A. The bridge applies the privacy zone per entry, never consults or updates its jump guard with entries (it checks them against each other only), and writes one RxLog record per entry (`"k": "hist"`, t = receive time − age, the frame's seq).
  - Mesh Buddy 1.3 retries and sends track history (`mprs retry on|off`, `mprs hist on|off`).
- **Known limit:** aprs.fi will probably show history entries in the raw packet list and not on the map track (Context). The next ride checks it. If aprs.fi drops them from the track, they still serve other APRS-IS clients and each gateway's own log and KML.
- **Rules out:**
  - more than one position retry;
  - retrying zero-hop positions;
  - gateways rendering history entries from a node's clock;
  - HMS timestamps for history entries.
