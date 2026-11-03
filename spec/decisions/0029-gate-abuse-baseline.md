# 0029: Gate-side limits are an abuse baseline: 5 s per station and service, 1 line/s with a burst of 10

- **Status:** accepted
- **Date:** 2026-11-03
- **Answers:** OPEN-QUESTIONS Q38
- **Spec sections affected:** §5.5, §8.4, §10.1 steps 6 and 8, §15.2, §16.2; `design/igate-design.md` §1, §3; `design/test-plan.md` §6.2; `design/reliability.md` §4.4

## Context

- **APRS-IS does not rate-limit senders.** A tracker beaconing every 5 s is accepted. The only limits nearby are on the pull side: the aprs.fi *API* for fetching data is rate-limited, and the aprs.fi map marks positions less than 5 s apart as "rate limited". Neither applies to what a gateway sends.
- The gate-side limits (§10.1 steps 6 and 8) were justified as protecting APRS-IS: one position per station and service per 2 min (30 s floor when moved more than 500 m), and a token bucket of 1 line per 5 s, burst 3. Those were the Kelly iGate's defaults (decision 0015, keyed per decision 0018).
- **The 2-min interval cost track.** On the 2026-10-31 bike ride, 19 of the 47 frames heard were held by the per-station interval, not lost on air (decision 0027).
- A gateway still needs a ceiling: a broken or hostile station, or a bug in a gateway, could otherwise turn into an unbounded stream of APRS-IS lines.
- The air side is a separate question. LoRa airtime is bounded at the station (§5.5 minimums, decisions 0011, 0024, 0028) and on the IS → mesh side (§13, `design/igate-design.md` §6); none of that changes here.

## Options

1. **Keep the 2-min interval and 1 per 5 s, burst 3:** proven on the ride; against: it rests on an APRS-IS limit that does not exist, and drops real positions.
2. **No gate-side limits:** simplest; against: nothing stops a runaway station or gateway bug.
3. **A loose baseline against abuse and bugs:** 5 s per station key (the aprs.fi map's own threshold) and 1 line per 1 s, burst 10, globally.

## Decision

Option 3. Decided by Alec, 2026-11-03.
- **Per-station interval (step 6):** a gateway MUST NOT gate more than one position per station key per **5 s**, the key as in decision 0018 (source, subtype, plus telemetry kind or object name). There is no distance-based floor. Messages, acks and emergency codes 7 and 9 stay exempt. Reason `interval`.
- **Global limit (step 8):** a token bucket of **1 line per 1 s, burst 10**. A frame waits at most **10 s** for a token, then is dropped as `rate`.
- **Unchanged:** the 0-5 s jitter, the bounded queue, the 15 s `expired` hold (it rests on APRS-IS's 30 s duplicate window, F§4.6) and §10.2 duplicate suppression.
- Both limits are there to stop abuse and runaway bugs, not to meet an APRS-IS requirement.

## Consequences

- **The spec:** §10.1 steps 6 and 8 state the values as the rule; §8.4 keeps emergencies under the global limit as an abuse guard; §5.5's case for a 60 s mobile minimum rests on LoRa airtime and loss, not on the gateway interval; §15.2 and §16.2 follow.
- **Replaces** the interval and rate figures of decision 0015 (Kelly defaults) and the 2-min figure quoted in 0018's context; 0018's key stays. **Replaces** the T7 rate in 0027 (Q34): one position per 2 min was the gateway interval, and the gateway interval no longer bounds a test, so T7 runs at the station's own §5.5 minimum.
- **Kelly:** the Gate's per-station interval becomes 5 s with no moved-distance floor, and the page and bridge buckets 1 per 1 s, burst 10, with a 10 s wait.
- **Test vectors:** `gateway.json` covers only the stateless steps 1-4, so it is unaffected; the stateful tests in `kelly-page/tests/meshprs-tests.html` follow Kelly.
- **Rules out:** citing APRS-IS as the reason for a gate-side limit.
