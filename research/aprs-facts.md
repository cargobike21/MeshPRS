# APRS facts the spec relies on

| Fact | Source |
|---|---|
| Receive-only iGates use `qAO` for everything they gate, including translated non-APRS sources | aprs-is.net/q.aspx (cited in `kelly-page/js/igate.js`) |
| The APZ tocall range is experimental; Kelly uses `APZKPG` | `igate.js`; aprs-deviceid *(to check: registration)* |
| A position with `!` means the station doesn't do messaging; `=` means it does | APRS 1.01 ch. 8 *(to check: page)* |
| Message text is at most 67 characters; the `{nn` suffix requests an ACK | APRS 1.01 ch. 14 *(to check)* |
| Telemetry: `T#` with 5 analog channels and 8 bits, defined by PARM / UNIT / EQNS / BITS messages to itself | APRS 1.01 ch. 13; `igate.js` tlm* |
| The APRS-IS passcode is a hash of the base callsign | `igate.js` passcode |
| VK frequencies: 145.175 MHz (VHF APRS), 433.775 MHz (LoRa APRS) | `loraaprs.js` header *(VHF: to check)* |
