# MeshCore facts the spec relies on

Each fact with its source. Add to this as the spec needs more. Don't re-derive what Kelly's code already proves; point at it.

| Fact | Source |
|---|---|
| Adverts carry the node's key, name, type (companion / repeater / room / sensor), optional lat/lon (int32 × 1e-6) and the sender's own timestamp | `kelly-page/js/meshcore.js` parseContact; `mcdecode.js` |
| Node clocks are often wrong: a repeater restarts at 15 May 2024 after a power-off | `meshrepeaters.js` header; bench 2026-10-21 |
| DMs, telemetry requests and responses are end-to-end encrypted. Public and hashtag channels use a known shared key | `mcdecode.js`; air capture 2026-10-25 |
| Path hashes are 1, 2 or 3 bytes of each repeater's key. SEQ uses 2 (MBUG) | `meshcore.js`; MBUG wiki |
| Floods are passed on by every repeater; direct routes are learned from replies and go stale when a node moves | trace work 2026-10-24 and 2026-10-29 |
| A wrong repeater password gets silence, not a refusal | `meshrepeaters.js` header |
| *(payload size limits: to check against firmware)* | |
| *(CayenneLPP channel / type list used by common sensors: to check)* | |
