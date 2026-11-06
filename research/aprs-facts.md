# APRS facts the spec relies on

| Fact | Source |
|---|---|
| Receive-only iGates use `qAO` for everything they gate, including translated non-APRS sources | aprs-is.net/q.aspx (cited in `kelly-page/js/igate.js`) |
| The APZ tocall range is experimental; Kelly uses `APZKPG` | `igate.js`; aprs-deviceid *(to check: registration)* |
| A position with `!` means the station doesn't do messaging; `=` means it does | APRS 1.01 ch. 8 *(to check: page)* |
| Message text is at most 67 characters; the `{nn` suffix requests an ACK | APRS 1.01 ch. 14 *(to check)* |
| Telemetry: `T#` with 5 analog channels and 8 bits, defined by PARM / UNIT / EQNS / BITS messages to itself | APRS 1.01 ch. 13; `igate.js` tlm* |
| The APRS-IS passcode is a hash of the base callsign | `igate.js` passcode |
| APRS-IS servers do not rate-limit senders (a tracker beaconing every 5 s is accepted). The aprs.fi *API* rate-limits clients pulling data, and the aprs.fi map marks positions under 5 s apart as "rate limited"; neither limits what a gateway sends | Alec, 2026-11-03; aprs.fi/page/api *(to check: page)*; decision 0029 |
| VK frequencies: 145.175 MHz (VHF APRS), 433.775 MHz (LoRa APRS) | `loraaprs.js` header *(VHF: to check)* |
| Timestamps come in three formats: DHM `DDHHMMz` (zulu) or `DDHHMM/` (local), HMS `HHMMSSh` (zulu, no day) and MDHM (positionless weather only). "It is recommended that future APRS implementations only transmit zulu format on the air" | APRS12c (= APRS101 page numbering) ch. 6 p.22, "Time Formats" (checked 2026-11-04 from github.com/wb2osz/aprsspec `APRS12c.pdf`) |
| A report without a timestamp is "real-time, current" and the receiver records when it heard it; a report with one "may or may not be real-time, and may possibly be (very) old". Data type `/` = timestamped position without messaging, `@` = with messaging | APRS12c ch. 6 p.23, "Use of Timestamps" (checked 2026-11-04) |
| aprs.fi uses packet timestamps to detect delayed and out-of-order packets: "They prevent the station tracks from jumping back and forth to old positions due to delayed packets" (OH7LZB). Its raw-packet view labels such packets "[Delayed or out-of-order packet (timestamp)]" and does not use them for the track; a station's timestamped packets were "quite consistently discarded" when another source sent newer valid ones. A timestamped position older than one aprs.fi already has is therefore expected to reach the raw log but not the map track. **UNVERIFIED** for an older timestamped position following an untimestamped one (whether aprs.fi compares against the earlier packet's receive time); to be checked on a ride | groups.google.com/g/aprsfi/c/zCnWPKLESYQ (H. Hannikainen, 2025-06-20); groups.google.com/g/aprsfi/c/mqSsYPCoB8s (2016-07, raw logs quoted in the thread); aprs.fi/doc/guide/aprsfi-troubleshooting.html ("aprs.fi tries hard to filter old positions") |
| aprs.fi (2008 design note) discards a position arriving within 5 s of the station's previous one and one implying more than 500 km/h from arrival times; the same 5 s threshold is the map's "rate limited" label | blog.aprs.fi/2008/03/on-duplicate-and-delayed-packets.html; decision 0029 |
