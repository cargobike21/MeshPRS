# Prior art

What already exists that MeshPRS must fit with or learn from. Mark each entry **verified** (read the source or saw it on air, with a date) or **to check**.

## In this repo

- **Kelly Page APRS iGate**, verified 2026-10-24, released in Kelly 0.4.34.
  - Files: `kelly-page/js/igate.js` (core: gate rules, packet format, telemetry mapping), `kelly-page/bridge/kelly_igate.py` (APRS-IS connection), shared vectors in `kelly-page/bridge/igate_vectors.json`, club whitelist in `kelly-page/js/igate-wl.js`.
  - Behaviour: MeshCore positions from whitelisted keys go to APRS-IS, receive-only, as `qAO` with tocall `APZKPG`. Nothing goes from APRS-IS to RF; no message text, channel data or anything encrypted is carried.
  - This is effectively MeshPRS version 0 for positions.
- **Kelly LoRa APRS driver**, verified 2026-10-17. `kelly-page/js/loraaprs.js` talks to CA2RXU LoRa APRS trackers and iGates (KISS and TNC2, BLE and USB) on 433.775 MHz.
- **The gateway's Nearby APRS**: `tools/p25x-fault-finding-page/aprs-nearby.js` (APRS-IS parse and filter).
- **The P25X APRS gateway**: `scripts/p25x_aprs_gateway.py`, the club's one APRS-IS connection point, for P25 GPS (LRRP / SDM).
- **MeshCore on-air facts**: `kelly-page/js/meshcore.js` (companion protocol), `kelly-page/js/mcdecode.js` (raw packet decoder), and the 2026-10-25 air capture (memory: no trackers on MeshCore in SEQ; telemetry is end-to-end encrypted).

## Elsewhere

- **D-PRS** (D-STAR GPS-A to APRS): the naming model, and the precedent for "translated non-APRS source → qAO". *To check:* the exact D-PRS gateway rules.
- **APRS-IS q-construct**: aprs-is.net/q.aspx (qAO for receive-only iGates). *Verified*, cited in `igate.js`.
- **APRS 1.01 spec and 1.2 addenda** (aprs.org): position, message, telemetry and object formats. *To check:* which version is the baseline.
- **Tocall registry** (aprs-deviceid, github.com/aprsorg/aprs-deviceid): how to register a tocall instead of the experimental APZ range. *To check.*
- **Existing MeshCore ↔ APRS bridges** (community projects, firmware forks): *to check* whether any exist and what they chose.
- **Meshtastic ↔ APRS efforts**: *to check*, for lessons only (Q3).
- **MBUG guidelines** (wiki.mbug.com.au): the SEQ mesh etiquette the mesh side must respect. *Verified* 2026-10-22, see `docs/lora-mesh-gap-analysis.md` §5.7.
