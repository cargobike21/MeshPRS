# 0027: First ride: 120 s default with 60 s for mobiles, one status retry, T7 rate, gateway log, first-hop ranges

- **Status:** accepted
- **Date:** 2026-10-31
- **Answers:** OPEN-QUESTIONS Q32, Q33, Q34, Q35, Q36
- **Spec sections affected:** §5.5, §8.4, §9.3 (retry field, seq), §10.4 (new), §10.5; `design/test-plan.md` §5.1, §6.2; `design/reliability.md` §2.8 (new), §4.1

## Context

The first on-air test with a real mobile ran on 2026-10-31.
- **Setup:**
  - VK4AZ-12, a RAK4631 bike tracker (`tools/meshprs-tracker`, firmware v3);
  - smart beaconing with a 60 s minimum, flooded;
  - 92 min through Bulimba and Hawthorne;
  - gated live to aunz.aprs2.net by one home-node iGate, VK4AZ-10 (the Kelly keeper).
- **The data:**
  - the gateway's in-memory MeshPRS history: every frame heard, with path, hops, SNR / RSSI and the §10.1 verdict;
  - the aprs.fi raw log for VK4AZ-12.
- **The full report is private** (it shows a home location): `_scratch/meshprs-ride-2026-10-31/` in the P25X repo.

Findings:
- **Delivery and gating:**
  - 68 frames sent (from seq), 47 heard (69 %).
  - 28 were gated and all 28 appeared on aprs.fi once.
  - 19 were held by the 2-min per-station interval.
  - Delay from mesh to APRS-IS: median 4 s, maximum 6 s.
- **Where frames were lost:** losses were at the first hop. 46 of 47 arrivals came in 3 hops or fewer.
- **Losses cluster:** P(lost | previous lost) = 48 %, against 31 % overall.
- **Beacon interval:**
  - Replaying the gate over the heard frames reproduces the day exactly: 26 positions, with the longest gap 13.75 min.
  - With every other frame removed (a 120 s minimum) and the same losses, 19-21 positions would have reached APRS-IS, with 6-8 gaps over 5 min instead of 4.
- **Status:** 2 of the 4 plain status frames were lost, so the status went 90 min without a refresh.
- **Text out of step with 0024:** §5.5 still said the default minimum was 60 s, contradicting decision 0024 (120 s) and §9.3.
- **Test plan conflict:** test plan T7 caps a live test at 1 packet per 5 min, below what the spec's own gateway passes for a mobile. This ride also ran live before T5 and T6.
- **No standard log:** the analysis was only possible because the gateway still had the frames in memory. The bridge kept no log.

## Options

- **Q32, minimum interval:**
  - 120 s default (as 0024) with 60 s allowed for mobiles in patchy coverage;
  - 60 s default, replacing 0024;
  - 120 s with no exception.
- **Q33, status retry:**
  - one retry at 60-90 s;
  - one retry at 30 s, as message retries;
  - no retry.
- **Q34, T7 rate:**
  - the gateway's per-station interval;
  - keep 1 per 5 min.
- **Q35, gateway log:**
  - SHOULD keep a per-frame log for 24 h, JSON lines RECOMMENDED;
  - leave it to implementations.
- **Q36, first-hop ranges:** record the measured ranges in `design/reliability.md`, and add first-hop coverage to the topology advice.

## Decision

Decided by Alec, 2026-10-31, each time taking the recommendation.
- **Q32:**
  - The default minimum stays **120 s** (0024), and §5.5 now says so.
  - A moving station MAY use **60 s** in patchy coverage. The extra frames fill gaps without adding APRS-IS lines.
- **Q33:**
  - A plain status SHOULD be sent once more, as a retry (retry field 1, same seq), **60-90 s** after the first, and never more than once.
  - It is 60-90 s, not 30 s, because losses cluster.
- **Q34:** T7's rate becomes the gateway's per-station interval (one position per source per 2 min), keeping the ≤ 2 h limit and the stop switch.
- **Q35:** a gateway SHOULD keep a per-frame diagnostic log for at least 24 h (spec §10.4), never holding the passcode.
- **Q36:** recorded as `reliability.md` §2.8 [measured], with a first-hop line in §4.1.

## Consequences

- **The spec:**
  - §5.5 is consistent with §9.3 and 0024.
  - §8.4 gains the status retry.
  - §9.3's retry-field note lists it.
  - §10.4 (diagnostic log) is new; the summary moves to §10.5.
- **Test vectors:** nothing new is needed. Retries already collapse under §10.2, and the gate vectors cover a retry of one seq.
- **Implementations:**
  - The tracker firmware (v4) retries the status at 30 s and must move to 60-90 s.
  - Its minimum interval is a setting (`mprs min`), 60 or 120 per the rule above.
  - Kelly's iGate needs a diagnostic log: the keeper / bridge writing §10.4 records to disk.
- **The ride itself:** counts as an early T7 run. The next live test waits for T5 and T6 on the private aprsc.
- **Ruled out:**
  - a 30 s status retry;
  - more than one status retry;
  - a 5-min T7 cap for mobiles.
