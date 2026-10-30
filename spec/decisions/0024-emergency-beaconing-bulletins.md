# 0024: Emergency local alert, 120 s minimum beacon interval, bulletin schedule

- **Status:** accepted
- **Date:** 2026-10-30
- **Answers:** OPEN-QUESTIONS Q20, Q25, Q26
- **Spec sections affected:** §5.5, §6.6, §8.4, §9.3 (seq)

## Context

- **Emergencies (Q20).** MeshPRS drops Mic-E, so an emergency reaches APRS-IS as a position report whose comment starts `EMERGENCY`. Gateways already give it priority. APRS software may not flag it as an emergency.
- **Beaconing (Q25).** The draft's smart-beaconing defaults (100 m, 15°, 30 min, 60 s minimum) are the usual tracker values. On a shared flood mesh, every beacon costs airtime once per repeater (`design/reliability.md`).
- **Bulletins (Q26).** The draft proposed a 30 min repeat and a 4 h stop, with Room Server posting as an optional MAY.

## Options

- **Q20:**
  - as drafted, plus a local operator alert;
  - exactly as drafted;
  - or also send a separate `>EMERGENCY` status line.
- **Q25:**
  - same triggers with a 120 s default minimum;
  - as drafted;
  - or more conservative: 250 m / 30° / 30 min / 180 s.
- **Q26:**
  - keep the figures and add no new role;
  - or define a bulletin-agent role now.

## Decision

Decided by Alec, 2026-10-30, taking the recommendation each time.
- **Q20:**
  - Rendering and gateway priority stay as drafted.
  - On a code 7 (emergency) or code 9 (cancelled) frame, a gateway SHOULD also alert its own operator locally, and MAY show it on its own map or log.
  - The spec says plainly that APRS clients may not flag a non-Mic-E emergency.
- **Q25:**
  - The triggers stay at 100 m, 15° and 30 min.
  - The **default minimum interval becomes 120 s**; the 30 s floor stays.
  - A moving station therefore sends at most 30 position frames an hour by default.
- **Q26:**
  - The bulletin figures become the rule: senders SHOULD NOT repeat a bulletin more often than every 30 min, and SHOULD stop after 4 h unless it is renewed.
  - Room Server posting stays an optional MAY.
  - A defined bulletin-agent role is left to a later version.

## Consequences

- §5.5's default table changes.
- §9.3's "why 8 bits" arithmetic now uses 120 s: 256 frames take 8.5 h, well past the 2.7 h duplicate horizon.
- Kelly is a fixed station: its own beacon already has a 15-minute minimum (`OWN_MIN_MIN` in `js/igate.js`), so it needs no change. A mobile station's sender has to default to a 120 s minimum.
- §8.4 gains the local-alert rule. §6.6 states the bulletin figures as normative.
