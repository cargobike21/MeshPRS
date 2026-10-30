# 0009: Kelly's iGate runs in the Pi keeper for the trial; the bridge holds the passcode

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** igate-design Q-A1, Q-A3
- **Spec sections affected:** none (implementation)

## Context

Kelly's page decides what to gate and the bridge holds the one APRS-IS socket (igate-design §2). The page only runs while open, and today the APRS-IS passcode sits in clear in browser storage and is synced between a member's Kellys.

## Options

1. **Page only:** best effort; against: not 24/7.
2. **The Pi keeper** (a headless page on the Pi) for the trial, porting the gate into the bridge later if iGates are meant to run unattended.
3. **Port the gate into the bridge now.**

## Decision

Option 2 for where it runs. The passcode moves to the bridge only (a bridge config file or environment variable); the page sends just the call-SSID. Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

Kelly work: move the passcode out of `kelly.settings`/statesync; the bridge computes or reads it. A later record decides whether the gate moves into the bridge.
