# MeshPRS: test plan

How a MeshPRS implementation is shown to work, from byte-level vectors on a desk to a controlled field trial on the SEQ mesh and APRS-IS. The trial's pass criteria are the proposed answer to OPEN-QUESTIONS **Q12**. Nothing here is decided until Alec signs it off through a decision record.

The models and numbers behind this plan are in [reliability.md](reliability.md). Frame layouts belong to [../spec/MeshPRS-Spec.md](../spec/MeshPRS-Spec.md). The frame fields this plan relies on (seq, retry, the gating field's test value, the acked seq) are in spec §9.3; reliability.md §5 maps them (C1-C6).

Tests are run in stages, and each stage gates the next:

| Stage | What | Where | Gate to next stage |
|---|---|---|---|
| T1 | Encode/decode and gate logic against shared vectors | desk, no radio | every vector passes in every implementation |
| T2 | Simulated mesh, fault injection | desk (Kelly mesh sim) | retry/dedupe/fallback logic behaves |
| T3 | RF bench, attenuated, 1-2 hops | bench | per-hop delivery ≥ 99 % at good SNR |
| T4 | Hop chain 1-8 hops | bench or controlled outdoor chain | curve measured; ≤ 3-hop target met |
| T5 | Multi-iGate and APRS-IS, private server | bench + private aprsc | 0 duplicates after the server's dupe filter |
| T6 | Field trial on the live mesh + private aprsc | SEQ | Q12 criteria (§7) |
| T7 | Controlled live APRS-IS test | SEQ + live APRS-IS | short run, clean, Alec signs off |

---

## 1. T1: shared JSON test vectors

**Layout.** The spec (§15) owns the file names and the drop-reason strings; this plan uses them as written there. Spec §15.1 names four files: **`frames.json`** (encode and decode, all subtypes), **`gateway.json`** (frame → APRS line, or drop reason; also the dedupe, retry and sequence cases below), **`inject.json`** (APRS-IS → mesh) and **`text.json`** (compact text profile).

The model is `kelly-page/bridge/igate_vectors.json`. Every implementation (`js/igate.js` via `tests/igate-tests.html`, `bridge/kelly_igate.py` via `test_kelly_igate.py`) loads the same file and must pass every entry. Its conventions, kept:
- A top-level `"_"` string says what the file is and which test runners must pass it.
- Small pure functions get **compact tuple arrays**, `[input…, expected]`. For example `"passcode": [["VK4AZ", 19432], …]` and `"lat": [[-27.4545, 0, "2727.27S"], …]`. `null` as the expected value means "rejected".
- Larger cases get **objects** with named fields, and the expected value last (`"packet": [[{src, igate, lat, lon, sym, comment}, "VK4AZ-9>APZKPG,qAO,VK4AZ-10:!…"]]`).

MeshPRS adds the record form already given in [../test-vectors/README.md](../test-vectors/README.md): `id`, `spec` (section), `about`, `input`, `config`, `expect` (`{ "out": … }` or `{ "drop": "<reason>" }`, with the reason exactly as spec §9.5 / §10.1 names it).

**`frames.json`** (byte layouts come from the spec; these are the *kinds* of vector, not the bytes):
- `"encode"`: `[{subtype, fields…}, "hex blob"]`, one or more per subtype.
- `"decode"`: `["hex blob", {fields…}]`, and `["hex blob", null]` for every malformed case. Malformed cases to cover:
  - truncated blob (`short frame`)
  - unknown version (`unknown version`)
  - reserved subtype 0xFF (`unknown subtype`)
  - experimental subtype 0xE0-0xFE (`experimental subtype`)
  - reserved flag set (`unknown flag`); non-ASCII text (`bad text`)
  - a blob that crosses an AES boundary it should not
- `"onair"`: `[blob_len, path_hops, hash_size, on_air_bytes]`, checking the findings §1.4 formula. For example `[28, 0, 2, 37]`, `[30, 0, 2, 53]`, `[28, 6, 2, 49]`, `[83, 0, 2, 101]`.
- `"grp_data"`: full GRP_DATA packets (header, path_len, path, channel hash, MAC, ciphertext) under the MeshPRS channel key, so the AES-ECB, MAC and padding path is tested end to end. Keys must be the published test-channel key, never a private one.

**`gateway.json`, reliability cases:**
- Sequence handling across wrap and reboot (spec §9.3.1). A run of `{src, seq, retry, rxAt}` in, and accept or `{ "drop": "replayed" }` per row out, including the resync after two.
- The same frame via 2-3 paths and via flood then direct. Expect one output, then `{ "drop": "duplicate" }`.
- Two frames identical except `seq`: expect two outputs.
- Two frames identical except `retry`: expect one output, then `duplicate` (spec §10.2 ignores the retry field).
- Rendering: one frame rendered by iGate A and iGate B (different `igate` call, different `rxAt`). Expect byte-identical info fields (spec §10.3); only the `qAO,IGATE` part differs.
- Gating = 2 (test). Expect `{ "drop": "test" }` for a live-APRS-IS config and `{ "out": … }` for a test-server config. Gating = 1 or 3: `nogate`.
- Rate: a timed sequence against the gateway's limits. Expect `interval`, `queue full` and `rate` where spec §10.1 says. Over the reliability.md §4.4 airtime budget, expect `airtime` (IS→mesh, spec §6.5); a frame held past 15 s expects `expired` (spec §10.1 step 9).

**Pass:** 100 % of vectors in every implementation. Any change to a vector file needs the spec section it tests to change in the same commit.

## 2. T2: simulated mesh

`kelly-page/bridge/kelly_mesh_sim.py` (and its JS twin `js/meshcoresim.js`) is a companion-protocol simulator with fault injection: `ackloss=P`, `acklossfirst=N`, `acklatefirst=N`, `hang=S` and others. Extend it with a MeshPRS channel and GRP_DATA frames, then run:

- **Late ack:** `acklatefirst=1` with `acklatems=18700` (the delay measured 2026-10-24). Expect the late ack to be accepted for the earlier attempt, and no extra retry once it arrives.
- **Ack loss sweep:** `ackloss` = 0.1 / 0.3 / 0.5. Expect at most 2 retries, at 30 s and 60 s, each retry with a changed `retry` field, and a fallback to flood after one miss on a direct route (reliability.md §4.2).
- **Stale route:** the sim's `.moved` repeater. Expect the direct route to fail once, a flood to follow, and the path to be re-learned.

**Pass:** the expected sequence of sends, byte for byte, in each case. These are logic tests only; the sim has no RF model.

## 3. T3: RF bench, 1-2 hops

**Kit:**
- 2 companions (originator, sink) and 2-3 repeaters, all on 1.18.0, MBUG settings (923.125 / 62.5 / SF8 / CR5, `path.hash.mode 1`).
- SMA cables, fixed attenuators (10/20/30 dB) and one step attenuator, 2-way splitters.
- One shielded box per node, or as many as are available.
- Every node powered and logged from one PC, so all timestamps share one clock.

**Link design.**
- Run the radios at minimum power. SX1262 can go down to −9 dBm.
- Estimated sensitivity at SF8 / 62.5 kHz: about **−130 dBm** (noise floor −120 dBm with a 6 dB noise figure, plus the −10 dB SF8 demodulation floor) [model].
- For a "good" link aim at about −110 dBm (SNR about +10 dB): roughly **100 dB** of path loss between adjacent nodes at −9 dBm. For a "marginal" link, step it down to SNR 0 … −8 dB.
- **The hard part is leakage, not path loss.** Any route around the attenuators (through box seams, power and USB leads, the air) has to lose more than about 130 dB at −9 dBm, or non-adjacent nodes hear each other.
  - Cheap shield boxes give 60-90 dB (**UNVERIFIED** for the boxes we have).
  - Separate the boxes by a few metres, use ferrites or battery power on the leads, and **check every non-adjacent pair with TRACE and `GET_NEIGHBOURS` before trusting a run**.

**Tests:**
- **Per-hop delivery vs SNR:** send ≥ 400 frames per step (§4.3) at 4-5 SNR steps from +10 dB to −8 dB, for each frame class (21 / 37 / 53 / 69 B).
- **Relay collisions:** two repeaters hidden from each other (each attenuated away from the other) both feeding one sink. Tests the 0.64 hidden-pair overlap of reliability.md §2.2. Then repeat with them audible to each other (the listen-before-talk case).
- **Capture threshold:** the same setup with a level difference of 0 / 3 / 6 / 10 dB between the two relays.
- **Tx delay factor and `rx_delay_base`:** repeat the collision test at flood factor 0.5 / 1.0 / 2.0, and with `rx_delay_base` > 0. These are the bench-only experiments from reliability.md §4.3.

**Pass:** ≥ 99 % per hop (95 % lower bound ≥ 98 %) at SNR ≥ +5 dB. The SNR-vs-delivery curve and the collision results are recorded for reliability.md, replacing the model's values.

## 4. T4: hop chain, 1-8 hops

### 4.1 Building the chain

Three ways, in order of fidelity:

| Method | How | Tests | Limits |
|---|---|---|---|
| **A. Forced direct path on an open bench** | All nodes in one room. The sender uses `CMD_SEND_CHANNEL_DATA` with an explicit path of 1-8 repeater hashes; only the named next hop forwards a direct packet [source §2.2] | Hop-count logic, path growth, latency, ack return, direct-route fallback | Every node hears every hop, so no hidden-node or weak-link effects, and floods short-circuit to 1 hop. Logic only, not RF reliability |
| **B. Attenuated chain** | Nodes in boxes, adjacent pairs linked through attenuators/splitters, non-adjacent pairs isolated (§3). A flood can only travel the chain | Real flood hop count, real per-hop loss, collision effects (add a parallel branch) | Needs 8 repeaters + 2 endpoints and enough isolation; the most work |
| **C. Outdoor chain** | Low-power repeaters spaced out along a line (a road or a park). Then the real mesh, using known 3-6 hop routes such as VK4AZ ↔ VK4AB | Real terrain and real background traffic | Not controlled; background traffic varies; uses the live channel (keep within the reliability.md §4.4 budget) |

### 4.2 Verifying hop count

- **TRACE** before and after every run. A TRACE goes direct along a path and returns per-hop SNR; it works for repeaters and rooms only, and companions can't be traced (kelly-page `TRACE_ROUTE_PLAN.md`; memory note *Kelly Trace Route*).
- Use 2-byte trace hashes. Known gotchas: some nodes need 1-byte trace hashes (f8db), and some repeaters forward but never answer traces (c55d, 2026-10-24).
- The sink also logs each received copy's `path_len` and path hashes (the raw packet logger `scripts/meshcore_rx_logger.py` does this). **The hop count of a run is the received path length, not the intended one.**

### 4.3 Runs

- For n = 1 … 8 hops, for the 37-byte (position) and 69-byte (message) classes: send N frames from the originator, flood and direct.
- Measure delivery, the latency distribution, and (for messages) round-trip ack success.
- **N per point: ≥ 400** for a ±3 % 95 % interval at p ≈ 0.9 (§5.1). Use ≥ 140 for a quick ±5 % look.
- **Send interval:** ≥ 3 × the worst-case flood latency at that hop count, so frames don't queue behind each other (worst case 13.6 s at 8 hops, reliability.md §2.6, so ≥ 41 s). A 400-frame point at 8 hops therefore takes ~4.6 h; at 3 hops (≥ 17 s spacing) ~1.9 h.

**Output:** a measured delivery-vs-hops table to set against the reliability.md §2.1 model, per frame class and route type.

**Pass:** the ≤ 3-hop one-way delivery target in §7 is met on method B or C.

## 5. Measurement methods

### 5.1 Packet loss: sequence numbers and sample size

- Every frame carries a per-source sequence number and a retry counter (spec §9.3). The sink logs `(src, seq, retry, rxAt, path, snr, rssi)` for every copy it hears.
- **Delivery** = unique `(src, seq)` received ÷ `seq` values sent, taken from the originator's own send log. Don't infer the sent count from gaps in the received seq: a lost run at the end looks like no loss.
- **Sample size.** For a 95 % interval of ±E around p: `n = 1.96² · p(1−p) / E²`.

| True p | ±5 % | ±3 % | ±2 % |
|---|---|---|---|
| 0.5 (worst case) | 385 | 1 068 | 2 401 |
| 0.8 | 246 | 683 | 1 537 |
| 0.9 | 139 | 385 | 865 |
| 0.95 | 73 | 203 | 457 |

- **To show a floor** rather than estimate a value, use the lower end of the two-sided 95 % Wilson score interval (z = 1.96), computed by `wilson.py` with the observed proportion held exactly at its value. An observed 90 % needs **n ≥ 196** for the lower bound to reach 85 %; an observed 95 % needs **n ≥ 139** to reach 90 %. (A one-sided 95 % bound, z = 1.645, would need 138 and 98; this plan uses the two-sided figures.) With zero failures, `n = ln 0.05 / ln p` gives 29 frames to show p ≥ 0.90, 59 for 0.95 and 299 for 0.99.
- **To compare two settings** (for example tx delay factor 0.5 vs 1.0, or flood vs direct), detecting 80 % vs 90 % at α = 0.05 with 80 % power needs **199 frames per arm**. Interleave the arms (A, B, A, B …) so background traffic hits both alike.

### 5.2 Duplicates

- **Mesh side:** copies per unique `(src, seq)` at each listener. This is not a failure, just flood redundancy, but it is reported, together with the path of each copy.
- **Gateway side:** frames an iGate *submitted* more than once per `(src, seq)`. Must be 0; this is the iGate's own dedupe.
- **APRS-IS side:** packets the server *passed* for one `(src, seq)`, after its 30 s dupe filter. Must be 1. Packets *submitted* for it equals the number of iGates that heard it; this is reported, not failed.

### 5.3 Latency

- Measure on one clock. Originator and sink are logged by the same PC, or by PCs NTP-synced to < 50 ms (check with `chronyc tracking`).
- Never use the nodes' own clocks. MeshCore clocks are often wrong (OPEN-QUESTIONS Q15), and the frame needs no timestamp for this.
- Report the median, p95 and max per hop count. Mesh-to-APRS-IS latency is measured by a client connected to the (private) server, logged on the same clock.

### 5.4 Loops

- A loop shows up as the same `(src, seq)` arriving at the APRS-IS side via mesh → APRS → mesh → APRS, or as a frame re-entering the mesh from an iGate.
- Tag every iGate's mesh-bound output (it is direct and addressed, per reliability.md §4.4), and fail any run where an iGate gates a frame it injected itself.
- **Pass:** 0 loops.

### 5.5 Airtime

- Each node's tx airtime from its own logs (frames × ToA from reliability.md §1).
- Repeater counters from `GET_STATUS` (tx/rx airtime, flood/direct counters, duplicate counters [source §3.3]), read before and after each run on every repeater we can log in to.
- **Report:** MeshPRS airtime per hour per node, per iGate, and as a share of each logged repeater's tx and rx airtime. Compare with the reliability.md §4.4 budget.

### 5.6 Background load

At each iGate and trial repeater, log the channel for ≥ 2 h before the trial, as on 2026-10-25 (`meshcore_rx_logger.py`). That measures G for reliability.md §2.3 and gives the baseline the trial's added airtime is compared against.

## 6. T5 and the APRS-IS test path

**Why it needs care:**
- A `pass -1` (unverified) login cannot send: aprsc drops its packets [source §4.3], so it is not a sandbox.
- No official test server was found [source §4.3, UNVERIFIED that none exists].
- `srvr.aprs-is.net:8080` is "for testing" but feeds the live network.

### 6.1 Private aprsc, no uplink (T5, T6)

- aprsc runs on RiverReach as the `aprsc-test` service, server ID `MPRSTEST`, with **no uplink configured**, so nothing it accepts can leave (installed by `MeshPRS/tools/install-test-aprsc.sh`). Clients: `127.0.0.1:14580` on RiverReach, or RiverReach's Tailscale address; status page on port 14501 at the same addresses.
- iGates log in to it with their real call-SSID and passcode, exactly as they will in production. The login path is tested too.
- A listener client logs everything the server passes (full feed) on the trial clock. A local viewer (Xastir / YAAC, or a few lines of Python) replaces aprs.fi.
- **Firewall it:** no route from the private aprsc to any `*.aprs2.net` host. Before each run, check that the config has no uplink section.

**T5 multi-iGate dedupe test:**
- 2-3 iGates on the bench hear the same frames, with different path lengths to each iGate (method A or B).
- **Expect:** each `(src, seq)` is passed by the server exactly once; the info fields from all iGates are byte-identical (spec §10.3); the submitted count equals the iGate count.
- **Vary the arrival spread** by delaying one iGate's submission by 0 / 10 / 25 / 35 s. Below 30 s, expect 1 pass. At 35 s, expect 2: this documents the edge of APRS-IS's 30 s window, and is the reason for a spec rule on how late an iGate may still gate a frame. Note that a 35 s-late copy is a real duplicate on live APRS-IS.
- **Test gating (spec §9.3, gating = 2):** test frames reach the private server when the iGate is configured for it, and never when it is configured for live.

### 6.2 T7: controlled live test

Only after T5 and T6 pass.
- **Identity:** a dedicated SSID for the test source, not one in daily use. The iGate's own call-SSID, tocall `APZKPG` (experimental range, unallocated [source §4.4]), `qAO`.
- **Content:** the position is the station's real location. A status or comment says it is a MeshPRS test.
- **Rate and length:** ≤ 1 packet per 5 min per source, for ≤ 2 h, with a stated start and end. Alec is watching aprs.fi live with a stop switch: the iGate's gate-to-IS can be turned off without stopping the mesh side.
- **Pass:** each frame appears once on aprs.fi with the right source, symbol and position; no duplicates; nothing from the test flag leaks; the raw packets match the private-server run byte for byte, apart from the q-construct.

## 7. Pass criteria for the field trial (decision 0013)

Measured over T6 (the live mesh with a private aprsc), with at least 2 iGates and at least 1 mobile and 2 static originators, over ≥ 7 days.

| # | Metric | Proposed criterion | Sample |
|---|---|---|---|
| P1 | Originator → any iGate, one-way, ≤ 3 hops (the received path) | ≥ 90 % observed, 95 % lower bound ≥ 85 % | ≥ 196 frames per originator |
| P2 | Same, 4-6 hops | Reported, not failed; compared with the model | ≥ 140 |
| P3 | Message round trip (frame + ack, at most 2 retries at 30 s and 60 s), ≤ 3 hops | ≥ 95 % observed, lower bound ≥ 90 % | ≥ 139 messages |
| P4 | Duplicates passed by APRS-IS per `(src, seq)` | exactly 1, in 100 % of frames | all |
| P5 | Duplicate submissions by one iGate | 0 | all |
| P6 | Loops | 0 | all |
| P7 | MeshPRS airtime | within the reliability.md §4.4 budget per node and per iGate; ≤ 2 % added occupancy at each logged repeater, from `GET_STATUS` deltas | daily |
| P8 | Latency, mesh → APRS-IS, ≤ 3 hops | p95 ≤ 10 s | all delivered |
| P9 | No harm to other mesh traffic | logged repeaters' flood, dupe and error counters show no step change beyond normal day-to-day variation (baseline from §5.6) | before vs during |
| P10 | Vectors | the trial build passes 100 % of the T1 vectors | — |

If P1 or P3 fails, the report states the hop count and per-hop SNR (from TRACE) of the failing originators before anyone changes the protocol. The usual cause in SEQ is a weak link: in the 2026-10-24 test it was a repeater's power, not the protocol.
