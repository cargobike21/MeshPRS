# MeshPRS: plan

## 1. Goal

Write down **one interface standard** for moving amateur station information between APRS and MeshCore, so that:
- any gateway (Kelly Page, a Pi, a repeater-side bridge, someone else's software) behaves the same way;
- the two networks never flood, loop or duplicate each other;
- the rules stay inside the AU amateur and LIPD licence conditions;
- APRS users (aprs.fi, APRSdroid, trackers) and MeshCore users each see the other side in a form their own tools already understand.

## 2. Scope

**In scope (candidates, to be confirmed: OPEN-QUESTIONS Q2):**
- position (MeshCore advert / telemetry location → APRS position report, and back)
- station identity: callsign ↔ MeshCore public key, SSID conventions, how a mesh node proves its callsign belongs to it
- messaging: APRS message ↔ MeshCore DM or channel text, ACKs, length limits
- telemetry: CayenneLPP / repeater status ↔ APRS telemetry (T#, PARM, UNIT, EQNS, BITS)
- status, objects / items (repeaters as APRS objects?), weather
- gateway behaviour: dedup, loop prevention, rate limits, which direction is allowed, the APRS q-construct, the tocall
- conformance: test vectors and what "MeshPRS compliant" means

**Out of scope (unless decided otherwise):**
- Meshtastic. It may get a sister profile later, but MeshCore comes first (OPEN-QUESTIONS Q3)
- changes to MeshCore firmware itself (the spec should work with stock firmware; anything needing firmware changes goes in a "future" annex)
- encrypted content of any kind on amateur RF

## 3. Phases

| Phase | Output | Done when |
|---|---|---|
| **0. Groundwork** | `research/` notes: prior art, the MeshCore packet facts, the APRS facts, regulatory notes | Every spec section has the facts it needs, with sources |
| **1. Architecture** | Spec §3-4: roles (gateway, iGate, digi-style bridge), directions, trust model; decision records for each | Q2-Q8 answered |
| **2. Mappings** | Spec §5-9: position, identity, messaging, telemetry, objects; field-by-field tables | Each mapping has a table plus test vectors |
| **3. Gateway rules** | Spec §10-11: dedup, loops, rate limits, failure behaviour, logging | Rules written as MUST/SHOULD, with vectors for every drop reason |
| **4. Reference implementation** | Kelly Page iGate brought to the spec (`js/igate.js`, `bridge/kelly_igate.py`) | Kelly passes every vector |
| **5. Field trial** | On-air trial on the SEQ mesh plus APRS-IS; a report | Agreed metrics met (Q12) |
| **6. Publish** | Spec 1.0, offered to MBUG and others | Alec signs off |

Phase 4 can start for the parts already settled. The current Kelly iGate is effectively a "version 0" of the position profile.

## 4. Who decides

Alec decides; nothing in the spec is settled until it has a decision record. Outside review is held on the published 1.0 Candidate (decision 0020): MBUG (channel and SEQ settings), the APRS-IS / aprs2.net operators (tocall and q-construct) and the MeshCore developers (data type).

## 5. Milestones

- [x] M0: framework set up (this folder)
- [x] M1: research notes complete (Phase 0)
- [x] M2: architecture decisions recorded (Phase 1)
- [x] M3: spec draft 0.1 with all mappings (Phase 2)
- [x] M4: every open question answered; spec published as the **1.0 Candidate**, layout frozen at header version 1 (decision 0020)
- [ ] M5: Kelly passes all vectors, including the still-to-write `inject.json`, `text.json` and stateful vectors (Phase 4)
- [ ] M6: field trial report (Phase 5)
- [ ] M7: review by MBUG, the APRS-IS operators and the MeshCore developers answered; spec 1.0 final (Phase 6)
