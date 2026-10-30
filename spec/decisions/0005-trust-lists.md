# 0005: Callsign bindings come from the club's signed list plus each iGate owner's own list

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** OPEN-QUESTIONS Q6, Q7
- **Spec sections affected:** §4.3

## Context

A gateway must decide which node key may appear under which callsign. Kelly already has an owner whitelist and a club-signed list (`kelly-page/js/igate-wl.js`, ADMIN_KEYS). Byte-identical output across iGates (§10.3) works best when every iGate shares one binding source.

## Options

1. **Owner lists only:** each iGate trusts what its owner lists; against: two iGates can disagree about one station.
2. **Club signed list plus owner list:** the shared signed list is the common binding; an owner may add their own entries.
3. **A registry service:** against: a new piece of infrastructure.

## Decision

Option 2. The callsign in the frame must match the binding's base callsign; the SSID is taken from the frame, so one binding covers every SSID of that callsign for that key. Decided by Alec, 2026-10-29, on the lead agent's recommendation after the Phase 3 review.

## Consequences

§4.3 states the two sources and the base-call match. Kelly's existing profile-0 owner entries keep working for adverts; frame bindings are kept separate (igate-design Q-A6). The club list is the binding every Kelly shares.
