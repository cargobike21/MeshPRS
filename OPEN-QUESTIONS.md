# MeshPRS: open questions

Numbered so decision records and the spec can refer to them. When one is answered, add **→ Decided in NNNN** and keep the question. Every question below is answered for the 1.0 Candidate (decision 0020). New questions raised in public review go at the end, from Q32.

## Naming and scope

- **Q1. Name.** **→ Decided in 0014** (MeshPRS). Is "MeshPRS" final? What does it stand for (working expansion: *Mesh Position Reporting System*, after D-PRS)? Is it only positions, or the whole interface?
- **Q2. Scope of 1.0.** **→ Decided in 0007** (code points in 0002). Which of these are in 1.0: position, identity, messaging, telemetry, status, objects, weather? A position-only 1.0 would ship sooner.
- **Q3. Meshtastic.** **→ Decided in 0025** (out of 1.0; a sister profile may follow). Out of scope, or a sister profile in the same spec?

## Architecture and direction

- **Q4. Directions.** **→ Decided in 0025** (both, APRS-IS only; RF later; 0003, 0008). APRS → MeshCore, MeshCore → APRS, or both? And over which APRS side: APRS-IS only, or RF too (VHF 145.175, LoRa APRS 433.775)?
- **Q5. Gateway roles.** **→ Decided in 0025** (iGate, messaging gateway, object server; one box may hold several). Which kinds of gateway exist? Candidates: receive-only iGate (today's Kelly), two-way messaging gateway, an "object server" that puts repeaters on the APRS map. Can one box be several?
- **Q6. Trust and identity.** **→ Decided in 0005** (club signed list plus owner list; K required for gating, 0004). How does a MeshCore key earn the right to appear under a callsign? Options: an owner's whitelist (today), a signed claim in the node name or advert, the club-signed list (`igate-wl.js` ADMIN_KEYS), a registry.
- **Q7. Where it's decided.** **→ Decided in 0005.** Is the gate decision made per gateway (each owner's list) or network-wide (one shared list)?
- **Q8. Transport on the mesh side.** **→ Decided in 0001** (GRP_DATA on a dedicated channel; GRP_TXT compact text as fallback; APRS → mesh direct only, §6.5). For APRS → MeshCore: a public channel, a dedicated hashtag channel (e.g. `#aprs`), DMs only, or a room server?

## Regulatory

- **Q9. ISM → amateur.** **→ Settled for 1.0 in 0003** (nothing from the mesh to amateur RF). MeshCore traffic is on LIPD/ISM and some of it is encrypted (DMs, private channels). What may an amateur gateway put on amateur RF? Plaintext channel and advert data only? Does third-party traffic need a control operator?
- **Q10. Callsign identification.** **→ Not needed for 1.0 (0003).** s12(1) requires a callsign at the start and end of each transmission and every 10 minutes. How does that apply to a gateway's RF transmissions, and to a mesh node that carries a callsign?

## Behaviour

- **Q11. Rate limits.** **→ Decided in 0011.** Keep the Kelly iGate defaults (1 per 5 s, burst 3, per-station 2 min, 30 s floor when moving), or set network-wide figures with MBUG? Floods on the mesh side: when, if ever?
- **Q12. Trial success.** **→ Decided in 0013.** What does the field trial have to show: delivery rate, duplicates, no loops, airtime cost?
- **Q13. Review.** **→ Decided in 0020** (MBUG, APRS-IS operators and MeshCore developers; tocall in 0012). Who reviews before 1.0 (MBUG, APRS-IS operators, MeshCore developers)? Do we ask for a registered tocall instead of `APZKPG`?
- **Q14. Message length and ACKs.** **→ Decided in 0022** (refuse over 67, never truncate or split; end-to-end acks). APRS messages are 67 characters with `{nn` ACKs; MeshCore DMs are longer, with their own ACKs. Do we truncate, split or refuse? Whose ACK counts?
- **Q15. Clocks.** **→ Decided in 0023** (receive time authoritative; TS only for object times within ±1 h). MeshCore clocks are often wrong (a repeater restarts at May 2024). Today the receive time is used, never the node's own time. Is that the rule for the standard?

## Raised by the first spec draft (2026-10-29)

Section references (§) are to `spec/MeshPRS-Spec.md`.

- **Q16. Channel name.** **→ Decided in 0012** (`#meshprs`). `#meshprs`, `#aprs`, or another? Should MBUG be asked to list it?
- **Q17. Data type.** **→ Decided in 0012.** Keep 0xFF4D while in development. When, and with what demonstrator, should a 0100-FEFF value be requested?
- **Q18. Callsign proof.** **→ Decided in 0004 and 0026** (K required for gating; no signed frames in 1.0). Should the 4-byte key prefix stay optional or become mandatory? Should an optional signed frame (Ed25519, +64 bytes) or a periodic signed binding claim be defined for Tier A?
- **Q19. Position precision.** **→ Decided in 0021** (24-bit; pflags bit 7 reserved for later). Is 24-bit lat/lon (about 1-2 m) right, or is a 32-bit option needed?
- **Q20. Emergencies on APRS-IS.** **→ Decided in 0024** (comment prefix and priority, plus a local operator alert). How should a non-Mic-E emergency appear (comment prefix, status, both)? Should gateways prioritise or alert on it?
- **Q21. Neighbour reports.** **→ Decided in 0025** (never on APRS-IS). Publish them anywhere APRS-side (status, objects), or mesh, MQTT and map only?
- **Q22. Compact text profile.** **→ Decided in 0023** (`MPRS`; never gated in 1.0). Is `MPRS` the right marker? Should compact text ever be gated to APRS-IS (§9.7), and if so, what would bind its sender?
- **Q23. Telemetry range.** **→ Decided in 0021** (8-bit only in 1.0). 8-bit analog only, or also APRS 1.2 decimal or 16-bit values?
- **Q24. Callsign byte order.** **→ Decided in 0021** (big-endian, M17 parity). Keep big-endian for byte-exact M17 parity, or go little-endian like everything else?
- **Q25. Beaconing defaults.** **→ Decided in 0024** (100 m, 15°, 30 min, 120 s minimum, 30 s floor). Are the smart-beaconing defaults (100 m, 15°, 30 min, 60 s minimum) right against the network airtime budget (`design/reliability.md`)?
- **Q26. Bulletins.** **→ Decided in 0024** (30 min repeat, 4 h stop; no bulletin-agent role in 1.0). The repeat schedule, and whether a room-server bulletin agent is a defined role.
- **Q27. Gatewayed-in frames.** **→ Decided in 0022** (derivation and clash rule kept; G = 1 senders shown as unverified). Is deriving seq and msgno from SHA-256(source:ID) right? Is the 1-in-32,768 msgno clash rule acceptable? Should a station that receives a G = 1 frame trust it, given that anyone can set G?
- **Q28. Telemetry profiles.** **→ Decided in 0025** (no registry in 1.0; kinds 0x05/0x10 stay not gated). Should there be a registry of telemetry profile IDs (kind 5), where would it live, and should it start from Kelly's `PRESETS`?
- **Q29. Sender positions into the mesh.** **→ Decided in 0025** (future work). Should a later version pass an APRS message sender's next position into the mesh, as IS → RF iGates do, and if so, how is it encoded?
- **Q30. Mesh island to island.** **→ Decided in 0025** (future work; the §6.5 loop rule stays). Should two separate meshes be able to message each other through APRS-IS?
- **Q31. Profile-0 polled telemetry.** **→ Decided in 0006.** Accept the narrow exception in §7.1 (a gateway's own polls of its owner's own nodes) or drop it?

## Raised by the first bike ride (2026-10-31)

- **Q32. Minimum beacon interval for mobiles.** **→ Decided in 0027** (120 s default; 60 s allowed for a mobile in patchy coverage). §5.5 said 60 s, 0024 said 120 s; the ride showed 60 s fills APRS-IS gaps at 69 % delivery.
- **Q33. Status retry.** **→ Decided in 0027** (one retry at 60-90 s). A plain status has no ack; 2 of 4 were lost on the ride.
- **Q34. T7 live-test rate.** **→ Decided in 0027** (the gateway's per-station interval). 1 per 5 min can't show a mobile track.
- **Q35. Gateway log.** **→ Decided in 0027** (SHOULD keep a per-frame log for 24 h, §10.4). Should gateways keep a standard per-frame record?
- **Q36. First-hop coverage.** **→ Decided in 0027** (measured ranges in reliability.md §2.8). How far does a mobile reach its first repeater?

## Raised by the parked tracker (2026-10-31)

- **Q37. How often to repeat an unchanged status and the telemetry definitions.** **→ Decided in 0028** (at start, on change and on query; otherwise no more often than every 6 h, 12 h for a battery station; the status retry only for a new status). A parked Mesh Buddy 1.0 spent about half its airtime repeating them.
