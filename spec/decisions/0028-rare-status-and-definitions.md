# 0028: An unchanged status and telemetry definitions are repeated rarely; only a new status is retried

- **Status:** accepted
- **Date:** 2026-10-31
- **Answers:** OPEN-QUESTIONS Q37
- **Spec sections affected:** §7.3, §8.4, §10.2

## Context

The aprs.fi raw log for VK4AZ-12 (Mesh Buddy 1.0, parked at home on 2026-10-31) showed how much of a parked tracker's
airtime went on text that never changes:
- **Status:** sent every 30 min, each with the §8.4 retry 75 s later, so about 96 LoRa frames a day for one fixed line.
- **Definitions:** PARM, UNIT, EQNS and BITS (4 frames) every 6 h, the most often §7.3 allowed: 16 frames a day. Several
  sets that day were incomplete on air (UNIT or BITS lost).
- **The rest:** about 48 positions (smart beaconing, 30 min maximum) and 48 telemetry value frames a day.
- **aprs.fi keeps a station's last status and definitions** and shows them until new ones arrive, so a frequent repeat
  adds nothing for a viewer. The repeats only help a gateway that has just started; it shows unscaled values until it
  hears the next definitions.
- **A status and its retry both reached APRS-IS** (14:27:02 and 14:27:57). The Kelly page holds the §10.2 duplicate
  keys, and the page was reloaded around then; the bridge, which holds the one APRS-IS connection, had no check of its own.

Alec, 2026-10-31: "I want to be as packet efficient as I can."

## Options

1. **Keep 30 min status and 6 h definitions:** simple; for: a new gateway gets everything soon; against: half the
   parked airtime is repeats.
2. **Repeat rarely, retry only what's new (chosen):** status and definitions at start, on change and on query, an
   unchanged status no more often than every 6 h and definitions no more often than every 6 h, 12 h recommended for a
   battery station; the 60-90 s status retry only for a new status. For: about half the parked airtime (about 208 ->
   106 frames a day); against: a gateway started mid-session shows unscaled values for up to 12 h, unless it sends query 0x04.
3. **Send once at start only:** least airtime; against: a gateway that misses the start never gets them without a
   query, and most gateways won't query.

## Decision

Option 2, decided by Alec on 2026-10-31.

## Consequences

- **§7.3:** definitions at start, on change, on query 0x04; repeated no more often than every 6 h; a battery station
  SHOULD use 12 h.
- **§8.4:** a plain status at start and on change; an unchanged status no more often than every 6 h (12 h for a battery
  station); the retry only for a new status.
- **§10.2:** the duplicate check belongs where the APRS-IS line is sent, so a restarted or second front end can't send a
  frame twice.
- **Implementations:** Mesh Buddy 1.1 (`tools/mesh-buddy`: status 720 min default, 360 minimum, definitions every
  12 h, retry only for a new status); Kelly's bridge `kelly_igate.py` (10-min (originator, seq) check); Kelly's
  profile-0 telemetry definitions every 6 h instead of 2 h (`igateui.js`; internet only, no airtime).
- **Test vectors:** none change (timing, not bytes).
