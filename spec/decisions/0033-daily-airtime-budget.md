# 0033: The per-node airtime budget is a 24 h average; a moving station may beacon at its smart-beaconing rate inside it

- **Status:** accepted; amends 0011
- **Date:** 2026-11-06
- **Answers:** OPEN-QUESTIONS Q42
- **Spec sections affected:** §5.5, §12.3; `design/reliability.md` §4.4; `design/test-plan.md` §7 (P7)

## Context

- **Decision 0011** set a per-node budget of at most 1 flooded frame per 10 min on average (burst 3) and 10 s/h of own transmit time, but it didn't say what period the average is over.
- **§5.5 lets a moving station beacon every 120 s,** or every 60 s in patchy coverage (decisions 0024, 0027). That is up to 30 or 60 floods an hour, so read hour by hour the two rules contradict each other.
- **Measured on VK4AZ-12, 2026-11-06,** with Mesh Buddy 1.5 (`../../design/field-trial-log.md` §3): about 35 frames and 14 s of own airtime in a riding hour; 57 frames and about 2.2 s/h over 10.4 h.
- **A tracker moves for a small part of the day.** Its riding hours are dense and the rest is sparse, which is what smart beaconing is for.

## Options

1. **A 24 h average per node:** at most 144 flooded frames and 240 s of own transmit time a day. A moving station may go up to its §5.5 rate as long as the day stays inside the budget. For: matches real use, and one number is easy to measure from a gateway log. Against: a station could, in principle, spend its whole day's budget in a few hours.
2. **Hourly, plus a mobile allowance,** for example 30 floods and 15 s/h while moving. For: easy to check in any one hour. Against: a second set of numbers, and a normal commute sits right at the cap.
3. **Strict hourly for every station.** For: simplest. Against: a mobile could beacon only every 10 min, which can't draw a usable track.

## Decision

Option 1. Decided by Alec, 2026-11-06, taking the recommendation.

## Consequences

- **The budget, per originating node:**
  - **at most 144 flooded MeshPRS frames per 24 h** (1 per 10 min on average), retries and track history included;
  - **at most 240 s of own MeshPRS transmit time per 24 h** (10 s/h on average);
  - the burst limit of 3 back-to-back floods still applies;
  - inside the day, a moving station is bounded by §5.5's minimum interval, not by an hourly figure.
- **What it rules out:** riding all day at a 60 s minimum (up to 1 440 frames) is far over. A station that moves for hours SHOULD use the 120 s default, and keep 60 s for short spells in patchy coverage.
- **The spec:** §5.5's mobile bullet and §12.3 cite the 24 h figures.
- **Design notes:** `reliability.md` §4.4 states the period. Test plan criterion P7 measures each node's frames and airtime per 24 h from the gateway log (§10.4) and seq.
- **The measured day:** VK4AZ-12 on 2026-11-06 used about 40 % of the frame budget and about 10 % of the airtime budget.
- **Left open:** at boot Mesh Buddy sends 4 telemetry definitions and a value frame 6 s apart. That is a burst of 5, over the burst limit of 3. It happens once per power-on, but it is noted in the field-trial log for a firmware follow-up.
