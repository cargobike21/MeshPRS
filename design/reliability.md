# MeshPRS: reliability analysis

Why delivery over a MeshCore flood falls away after a few hops, what MeshPRS can do about it, and what it should ask of repeater owners and iGate operators. This is a design note: informative, not normative. Proposals here become spec text only through a decision record (see [../spec/decisions/](../spec/decisions/)).

**What is measured and what is modelled.** Every figure is labelled:
- **[source]**: a verified fact from [../research/00-findings.md](../research/00-findings.md) (MeshCore 1.18.0, commit `81dbae5`).
- **[measured]**: seen on air in SEQ, with the date and the log.
- **[model]**: arithmetic from a stated assumption. A model shows which way a setting pushes and roughly how far; it is not a prediction of the SEQ mesh.
- **UNVERIFIED**: an input nobody has checked yet.

All numbers come from `calc.py` / `calc2.py` / `wilson.py` (throwaway scripts, kept out of the repo); the formulas are given inline so anyone can recompute them.

**Frame sizes** are the spec's ([../spec/MeshPRS-Spec.md](../spec/MeshPRS-Spec.md) owns the layouts): position blob 24-28 B (37 B on air with no path), ack 13 B (21 B), message 16 B + text (a 67-character message is an 83-byte blob, 101 B on air). On-air size = `1 + 1 + path + 1 + 2 + 16·⌈(N+3)/16⌉` for an N-byte blob [source, §1.4].

---

## 1. Time on air

**Radio:** 923.125 MHz, BW 62.5 kHz, SF8, CR 4/5 (MBUG) [source, §5.4]. Explicit header, CRC on.

- **Symbol time** `Tsym = 2^SF / BW = 256 / 62 500 = 4.096 ms`.
- **Low-data-rate optimise is off.** RadioLib turns it on when `Tsym > 16 ms` (SF11/12 at 125 kHz, SF10+ at 62.5 kHz). 4.096 ms is well under.
- **Preamble: 32 symbols.** MeshCore 1.18.0 sets `preambleLengthForSF(sf) = sf <= 8 ? 32 : 16` (src/helpers/radiolib/RadioLibWrappers.h:56, applied at RadioLibWrappers.cpp:30; findings §1.4). Older firmware used 16. The 16- and 8-symbol columns are shown for comparison. (`kelly-page/js/mesh-bridge-rules.js:48` still assumes 8, which understates every packet by 98 ms.)
- **Formula** (Semtech AN1200.13): `ToA = (Npre + 4.25)·Tsym + (8 + max(⌈(8·PL − 4·SF + 28 + 16)/(4·SF)⌉·5, 0))·Tsym`.

| On-air bytes | What it is (assumed) | Payload symbols | ToA, 32-sym preamble | 16-sym | 8-sym |
|---|---|---|---|---|---|
| 21 | ack, blob ≤ 13 | 38 | **304 ms** | 239 | 206 |
| 37 | position, blob 24-28 | 58 | **386 ms** | 321 | 288 |
| 53 | telemetry, or a message of ≤ 29 characters (blob ≤ 45) | 78 | **468 ms** | 402 | 370 |
| 69 | message of ≤ 45 characters (blob ≤ 61) | 98 | **550 ms** | 484 | 452 |
| 101 | maximum message, 67 characters (blob 83) | 138 | **714 ms** | 648 | 615 |
| 160 | near-maximum frame | 213 | **1021 ms** | 955 | 923 |

The fixed overhead (preamble plus header) is 151 ms at 32 symbols, half the time of the smallest frame. Each payload byte beyond that costs about 2 ms (5 symbols per 4 bytes at CR 4/5).

**Path growth.** Each repeater adds a 2-byte hash [source, §1.4], so a flood gets longer as it travels. With 2-byte hashes, ToA steps up 20.5 ms every 2 hops (one 4-byte symbol group):

| Start size | 0 hops | 2 | 4 | 6 | 8 |
|---|---|---|---|---|---|
| 21 B | 304 | 325 | 345 | 366 | 386 ms |
| 37 B | 386 | 407 | 427 | 448 | 468 ms |
| 69 B | 550 | 570 | 591 | 611 | 632 ms |

**The AES step matters more than any one byte.** A 30-byte position blob lands in the 53-byte class (468 ms), 21 % longer than a 29-byte one (386 ms). Keeping each subtype's common case inside a 13/29/45/61 boundary is the single biggest airtime lever the spec controls.

---

## 2. Why 5-6+ hops degrade

### 2.1 Per-hop success compounds [model]

If each hop delivers with probability *p* independently, a single chain of *n* hops delivers `p^n`:

| Hops | p = 0.99 | 0.95 | 0.90 | 0.85 | 0.80 | 0.70 |
|---|---|---|---|---|---|---|
| 1 | 0.99 | 0.95 | 0.90 | 0.85 | 0.80 | 0.70 |
| 2 | 0.98 | 0.90 | 0.81 | 0.72 | 0.64 | 0.49 |
| 3 | 0.97 | 0.86 | 0.73 | 0.61 | 0.51 | 0.34 |
| 4 | 0.96 | 0.81 | 0.66 | 0.52 | 0.41 | 0.24 |
| 5 | 0.95 | 0.77 | 0.59 | 0.44 | 0.33 | 0.17 |
| 6 | 0.94 | 0.74 | 0.53 | 0.38 | 0.26 | 0.12 |
| 7 | 0.93 | 0.70 | 0.48 | 0.32 | 0.21 | 0.08 |
| 8 | 0.92 | 0.66 | 0.43 | 0.27 | 0.17 | 0.06 |

Anything that needs a reply needs both directions. Frame and ack together deliver `p^(2n)`; with up to 3 tries, `1 − (1 − p^(2n))^3`:

| Hops | p = 0.95: once / 3 tries | p = 0.90 | p = 0.80 |
|---|---|---|---|
| 1 | 0.90 / 1.00 | 0.81 / 0.99 | 0.64 / 0.95 |
| 3 | 0.74 / 0.98 | 0.53 / 0.90 | 0.26 / 0.60 |
| 6 | 0.54 / 0.90 | 0.28 / 0.63 | 0.07 / 0.19 |
| 8 | 0.44 / 0.82 | 0.19 / 0.46 | 0.03 / 0.08 |

**Where the model is pessimistic:** a flood is not one chain. Every repeater that hears it relays it once, so where the mesh is wide a packet has many parallel chances.
**Where it is optimistic:** SEQ is largely a chain of long hilltop links with weak cut-edges, and at a cut-edge there is no parallel path. Hops are also not independent (one busy hilltop affects several hops at once), and the two directions are not symmetric.

**[measured] 2026-10-24/26, VK4AZ ↔ VK4AB** (memory note *VK4AZ↔VK4AB mesh link*; scripts `_scratch/ts/mc_e2e.py`, `mc_trace.py`):
- Alec → Rob DMs arrived reliably over 5-6 hops.
- Rob → Alec floods, ACKs and path returns often did not; the routes differed each way.
- One link (a698 ↔ f8db) traced at only 1-4 dB SNR before a698's power was raised from 10 to 22 dBm.
- 0 of 6 pinned (direct) DMs over 4-7 hop routes arrived on 2026-10-26.
- An ACK arrived 18.7 s after the send, after the sender had given up.

This is the round-trip table's 6-hop row in practice: one-way works, the ack does not.

### 2.2 Relays colliding with each other

When a flood is heard by *k* repeaters at the same moment, each waits `random(0, 5t + 1)` ms, uniform, with `t = ToA × 0.5` for floods (0.3 for direct). There is no SNR weighting, because `rx_delay_base = 0` [source, §2.4]. The random window is therefore **W = 2.5 × ToA** for a flood and 1.5 × ToA for direct.

Two cases, depending on whether the relays can hear each other:

**Relays that hear each other.** The later one finds the radio busy and waits, retrying every 120-480 ms and forcing a send after 4 s [source, §2.4]. They collide only if both start within the detection latency δ, the time before a receiver flags a preamble.
- **UNVERIFIED:** δ. Assumed here to be 8 symbols (33 ms).
- Pair overlap is `1 − (1 − δ/W)²`: 0.067 at 37 B, 0.047 at 69 B, 0.026 at 160 B [model].
- With 2-6 such relays, a downstream receiver gets a clean copy 93-99.6 % of the time (Monte Carlo, no capture).
- In this case a **longer** packet collides *less*, because the window grows with ToA and δ doesn't.

**Relays that cannot hear each other but share a receiver** (hidden nodes: two hilltops either side of a ridge). There is no listen-before-talk protection, so they collide whenever their starts are less than one ToA apart.
- **The pair overlap is `1 − (1 − ToA/W)² = 1 − (1 − 0.4)² = 0.64`, whatever the packet size.** W and the vulnerable window both scale with ToA, so the ratio is fixed. The Monte Carlo gives the same answer for a 1 s and a 0.3 s packet [model].
- With *k* hidden relays all heard by one receiver, P(at least one clean copy) is 1.00, 0.37, 0.42, 0.26, 0.16 and 0.09 for k = 1-6, before capture.
- LoRa capture (the stronger copy survives if it is several dB above the other) recovers some of these. **UNVERIFIED:** the threshold for SX126x at SF8, commonly quoted as about 6 dB.

**What this means:**
- Shrinking frames does **not** reduce relay-on-relay collisions. Those are set by the delay *factor*, not by the size.
- Raising the flood factor does reduce them, but costs latency:

| Flood factor | W | Hidden pair overlap | Mean added delay per hop (37 B) | Extra over 6 hops vs 0.5 |
|---|---|---|---|---|
| 0.3 (direct default) | 1.5 T | 0.89 | 0.29 s | −1.2 s |
| **0.5 (flood default)** | 2.5 T | 0.64 | 0.48 s | 0 |
| 1.0 | 5 T | 0.36 | 0.97 s | +2.9 s |
| 2.0 | 10 T | 0.19 | 1.93 s | +8.7 s |

### 2.3 Background traffic and hidden transmitters

A hop also fails when some unrelated station, which the receiver hears but the sender doesn't, transmits during the packet. As pure-ALOHA, P(hit) = `1 − exp(−λ(T + Tb))`, with background load G (the fraction of time the receiver hears hidden traffic) and Tb = 427 ms (a 43-byte background packet) [model]:

| Hidden load G | 21 B | 37 B | 69 B | 160 B | 6-hop survival, 37 B / 160 B |
|---|---|---|---|---|---|
| 1 % | 1.7 % | 1.9 % | 2.3 % | 3.3 % | |
| 2 % | 3.4 % | 3.7 % | 4.5 % | 6.6 % | 0.80 / 0.66 |
| 5 % | 8.2 % | 9.1 % | 10.8 % | 15.6 % | 0.56 / 0.36 |
| 10 % | 15.7 % | 17.3 % | 20.4 % | 28.8 % | |

**This is where smaller packets help:** the vulnerable window is `T + Tb`, so a shorter frame is exposed for less time, and the gain compounds per hop.

**[measured] 2026-10-25, 2 h passive capture at VK4AZ** (`_scratch/meshcap/rx-riverreach.jsonl`, 117 packets): the airtime heard was 71 s, **1.0 % of the time**. A hilltop repeater hears more than a home node; G of 2-5 % at a busy Brisbane hilltop is plausible but **UNVERIFIED**. Repeater `GET_STATUS` returns tx/rx airtime counters [source, §3.3], so it can be measured (test plan §5.6).

### 2.4 Flood priority falls with hop count

A queued flood relay has priority equal to its hop count; direct relays are priority 0 [source, §2.4]. On a busy repeater, a packet that has already come 6 hops waits behind every nearer flood and every direct packet. The radio also defers while receiving, and `airtime_factor` paces the transmitter [source, §2.4].
- **UNVERIFIED:** the queue's depth and what it drops when full.

Distant traffic is the first to be delayed. That is a further reason an ack can arrive after the sender has given up (§2.1).

### 2.5 The 160-entry duplicate table

- **Size isn't the problem.** The table holds 160 payload hashes [source, §2.4], so its horizon is 160 / (unique packets per second). The VK4AZ capture saw about 1 unique packet per minute, a 2.7-hour horizon. Even a channel 100 % busy with 37-byte frames (2.6 per second) gives 62 s, longer than any flood takes to settle (§2.6). Eviction is not a delivery risk [model].
- **The hash ignores path and route type,** so the long horizon cuts the other way: **a retry with identical bytes is silently dropped** by every repeater that saw the first try, for hours. MeshPRS retries and repeated beacons must change at least one plaintext byte (findings §2.4; spec §9.3 has the seq and retry fields for this, see §5 below).
- **Measured multi-copy:** 7 of 110 unique payloads were heard twice at VK4AZ. The rest were heard once, mostly via `fbae` (95 of 117).

### 2.6 Latency [model]

Per hop, the cost is ToA plus the random wait, with mean `1.25 ToA` (flood) or `0.75 ToA` (direct). This ignores queueing and listen-before-talk waits, so it is a floor.

| Hops | Flood: mean / worst random | Direct: mean / worst |
|---|---|---|
| 1 | 1.8 / 2.8 s | 1.4 / 2.0 s |
| 3 | 3.7 / 5.7 s | 2.9 / 4.1 s |
| 6 | 6.6 / 10.3 s | 5.2 / 7.4 s |
| 8 | 8.7 / 13.6 s | 6.8 / 9.7 s |

APRS-IS drops duplicates within 30 s [source, §4.6], so copies from several iGates of one flood normally fall inside the window. A heavily queued path could spread them past it.

### 2.7 How far floods travel in SEQ [measured]

Hop counts of floods heard at VK4AZ on 2026-10-25 (one malformed 60-hop PATH packet excluded):

| Hops | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11+ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Packets | 4 | 8 | 19 | 20 | 19 | 19 | 7 | 3 | 5 | 4 | 4 |

- 73 % had come 4 or more hops, and 38 % 6 or more.
- 80 distinct 2-byte repeater hashes appeared in paths (plus 51 3-byte and 18 1-byte, which partly overlap the same repeaters).

So **a flood in SEQ is retransmitted by dozens of repeaters**, R ≈ 30-80 [model, from the hash count].

---

## 3. What a flood costs

**Network airtime of one flood** ≈ ToA × (1 + R), summed over every transmitter. A 37-byte position frame (mean ToA over 0-5 hops: 417 ms) flooded to R = 30 costs **12.9 s** of transmitter time; to R = 60, **25.4 s**.

That is spread over the whole region. What one site actually sees is ToA × A, where A is the number of copies it can hear.

### 3.1 Smart beaconing against fixed intervals [model]

**Assumed region:** 10 static stations and 5 mobiles.
- **Mobiles drive 1.5 h a day:** 0.6 h in town at 40 km/h with a corner peg every 3 min, and 0.9 h on the highway at 100 km/h.
- **SmartBeaconing settings:** fast 60 s at ≥ 90 km/h; slow 1800 s at ≤ 5 km/h; in between, `60·90/v`.

| Scheme | Frames / day | Saving | Gap between fixes at 100 km/h | Site occupancy, A = 3 | Network airtime, flood R = 30 |
|---|---|---|---|---|---|
| Fixed 60 s | 21 600 | | 1.7 km | 31 % | impossible |
| Fixed 120 s | 10 800 | | 3.3 km | 15.6 % | impossible (161 %) |
| Fixed 300 s | 4 320 | | 8.3 km | 6.3 % | 65 % |
| Fixed 600 s | 2 160 | | 16.7 km | 3.1 % | 32 % |
| **Smart, static every 30 min** | **1 115** | 74 % vs 300 s, 90 % vs 120 s | 1.7 km | 1.6 % | 600 s/h (17 %) |
| Smart, static and parked hourly | 762 | | 1.7 km | 1.1 % | 410 s/h (11 %) |
| Smart mobiles, statics by advert only | 522 | | 1.7 km | 0.8 % | 281 s/h (8 %) |
| Same 1 115 frames, **direct to an iGate 3 hops away** | 1 115 | | 1.7 km | (path only) | 77 s/h (2 %) |

**Conclusions:**
1. Fixed-interval flooding is not viable at SEQ's flood reach. Even smart beaconing, flooded everywhere, would use a tenth or more of the network's transmitter time for 15 stations.
2. **Static stations should not beacon positions on the MeshPRS channel at all, or only rarely.** Their advert already carries a fixed position, and the Kelly v0 iGate already gates it [source, §3.1; prior-art].
3. **Direct routing to a known iGate is about 8× cheaper than flooding to R = 30,** and better than 15× against R = 60.

---

## 4. Recommendations

These are proposals; each needs Alec's decision, and some need MBUG's.

### 4.1 Topology: an iGate within 3 hops

- **Target:** every MeshPRS originator's traffic reaches at least one iGate in **≤ 3 hops**. At p = 0.9 that is 73 % one-way, against 53 % at 6 hops. Round trip with 3 tries is 90 %, against 63 %.
- **Where to put iGates:** sites already heard by many repeaters, measured by flood reach, not by map. Brisbane hilltops first, then the Gold and Sunshine Coasts and Ipswich. A home-node iGate (like VK4AZ, which hears most traffic via one repeater, `fbae`) is a leaf, not a hub.
- **More than one iGate is good,** not a problem: APRS-IS removes the duplicates provided every iGate renders **byte-identical** APRS text for the same frame (spec §10.3).

### 4.2 Routing: direct after first contact, flood as the fallback

1. **First frame floods** (unscoped [source, §2.3]) so it can find an iGate. The iGate's reply carries the path back, as MeshCore's PATH return does today.
2. **Later frames go direct** to that iGate. Direct relays have priority 0 and a shorter wait [source, §2.4], and the cost scales with hops, not with R.
3. **Flood again after one missed ack,** and re-learn the path. Pinned routes went stale in the field: 0/6 on 2026-10-26, and a stale direct route on 2026-10-29 (memory note *VK4AZ Work*). Never pin a route without a fallback.
4. **Beacons that don't need an ack** (positions) go direct to the last known iGate path with a periodic flood, for example every Nth frame, or every 30 min, so a new or moved iGate is found. **UNVERIFIED:** best N; the test plan measures it.

### 4.3 Repeater settings

| Setting | Recommendation | Basis |
|---|---|---|
| `path.hash.mode` | **1** (2-byte), as MBUG sets | [source, §5.4] |
| `multi.acks` | **1**, as MBUG sets. Helps DM ACKs only; MeshPRS acks are GRP_DATA frames and get no multi-ACK | [source, §2.1, §5.4] |
| `flood.max` / `flood.max.unscoped` | Leave at **64** for now. MeshPRS should not *depend* on more than 6 hops. A lower network-wide cap is MBUG's call, because it affects all traffic | [source, §2.2] |
| `flood.max.advert` | Leave at **8** | [source, §2.2] |
| Loop detect | At least **MINIMAL** (the default). With 2-byte hashes it drops a packet whose path already holds this node twice | [source, §2.2]. Names of the other modes: **UNVERIFIED** |
| `rx_delay_base` | Leave at **0** on the live mesh. An SNR-weighted rx delay might let the best-placed relay go first; try it on the bench chain first | [source, §2.4]; effect **UNVERIFIED** |
| tx delay factors (flood 0.5, direct 0.3) | Leave the defaults on the live mesh. Raising the flood factor to 1.0 roughly halves hidden-relay overlap (0.64 → 0.36) for about +3 s over 6 hops; test on the bench (§2.2) | [source, §2.4] for the defaults; CLI names **UNVERIFIED** |
| `airtime_factor` | Leave at **1.0** | [source, §2.4] |
| `flood.advert.interval` | **83**, as MBUG sets | [source, §5.4] |
| Tx power / antenna | Fix weak cut-edges first: a698 went from 1.3 to 9-11 dB by raising it from 10 to 22 dBm. Mind the LIPD PSD point | [measured] 2026-10-24; [source, §5.1] |

### 4.4 Airtime budget (proposed)

LIPD 915-928 MHz has **no duty-cycle limit** [source, §5.1] and MBUG sets no number [source, §5.4], so MeshPRS must set its own. The figure to protect is the channel at a busy site (A copies audible). Measured background at VK4AZ is about 1 %.

**Per originating node:**
- **Flooded MeshPRS frames:** ≤ **1 per 10 min** on average, burst ≤ 3.
- **Direct frames to an iGate:** ≤ **1 per 60 s** while moving (SmartBeaconing fast rate), ≤ 1 per 30 min while parked.
- **Own transmit time:** ≤ **10 s/h**, about 25 position frames.
- **Retries:** at most 2 per message, at 30 s and 60 s after the first send (so at most 3 sends). Both gaps exceed the longest round trip seen (§2.1's 18.7 s ACK).

**Per iGate, APRS-IS → mesh:**
- **Direct only,** to a station heard on the mesh in the last hour (the APRS IS→RF rule [source, §4.6]).
- **Never flooded.** A station with no known path is not reached from APRS-IS.
- **Own transmit time:** ≤ **36 s/h** (1 %), shared by all mesh-bound traffic. That is about 93 position-class or 65 message-class frames.

**Per region, total MeshPRS:** keep it under **2 %** occupancy at any one site. At A = 3 this allows about 1 100 37-byte frames a day, the "smart, static every 30 min" row of §3.1. Every flooded frame costs ~13-25 s of network airtime, so floods are the budget's main consumer.

These sit alongside the Kelly iGate's existing gate-side limits (1 per 5 s, burst 3, per-station 2 min, 30 s floor when moving; OPEN-QUESTIONS Q11), which govern what goes to APRS-IS, not what goes on air.

### 4.5 Frame design (for the spec owner)

1. **Keep each subtype's common case inside an AES boundary.** The spec already does: position 24-28 B blob (37 B on air) and ack 13 B (21 B). One byte past 29 would cost +82 ms (+21 %).
2. **Smaller frames help hidden-traffic hits and total airtime,** not relay-on-relay collisions (§2.2, §2.3). Don't trade robustness fields away for bytes that land in the same AES block anyway.
3. **No fragmentation in the common path** (findings §1.7): a 2-fragment message delivers `p_frame²`.

---

## 5. Frame fields this analysis needs, and where the spec has them

All six were requested by this analysis and are now in the spec; listed here so the reasoning stays with the numbers.

| # | Need | Spec | Why |
|---|---|---|---|
| C1 | A per-originator sequence number in every frame, incremented on every new frame | §9.3: `seq`, u8 per originator identity | Repeaters' dupe table drops repeats with identical bytes (§2.5); also the loss-measurement key (test plan §5.1) |
| C2 | A retry counter that changes on each retry while seq stays the same | §9.3: 2-bit retry field in the header | So a retry isn't dropped as a duplicate, and gateways can still collapse retries to one APRS-IS line |
| C3 | A test marking that iGates never pass to live APRS-IS | §9.3: gating field, value 2 = test (`test` drop reason) | Lets trials run on the live mesh without polluting APRS-IS (test plan §6) |
| C4 | Byte-identical APRS rendering at every iGate | §10.3 (normative) | APRS-IS dedupe hashes source, destination and info (findings §4.6), so multi-iGate copies collapse only if identical |
| C5 | Seq wrap and reboot handling | §9.3.1 (10-minute window, `replayed`, resync after two) | An 8-bit counter restarts at power-up; a gateway must not drop a fresh frame as an old one for long |
| C6 | Acks carry the acked seq and stay in the smallest class | §6: ack 13-byte blob (21 B on air) | The ack is the weak direction (§2.1) |
