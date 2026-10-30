# 0019: Kelly's frame bindings come from the enabled entries on the owner's list

- **Status:** accepted
- **Date:** 2026-10-29
- **Answers:** igate-design Q-A6 (replaces that part of 0015)
- **Spec sections affected:** none (implementation)

## Context

Decision 0015 said Kelly would keep frame bindings in a store separate from its profile-0 list entries. When it was built, the simpler form turned out to meet the same aim: each list entry (the owner's own, a node-name offer, or the signed club list) already binds a node key to a base callsign, which is all a binding is (decision 0005).

## Options

1. **A separate frame-binding store:** a key can be bound for frames without being gated for adverts; against: a second list to manage, and a second copy of the club list.
2. **Bindings from the enabled list entries:** the key and base callsign only; the entry's SSID, symbol and comment stay for adverts and are never used for frames.

## Decision

Option 2. Decided by Alec, 2026-10-29, on the lead agent's recommendation.

## Consequences

Profile-0 gating is unchanged. A node cannot be bound for frames without its adverts also being on the list; if that is ever needed, a "frames only" flag on an entry is the way to add it.
