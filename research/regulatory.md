# Regulatory notes (informative)

These notes are informative. The regulator's text governs, and anything here should be checked against the current instruments before the spec relies on it.

## Amateur side: Radiocommunications (Amateur Stations) Class Licence 2023

- **s13(2)(d)(iv):** no encoding to obscure meaning, with narrow exceptions (satellite and unattended-station control, emergency services). This is why Reticulum was rejected for amateur RF (decision 2026-10-20).
- **s12(1):** a callsign at the start and end of each transmission, and at least every 10 minutes.
- Third-party traffic, unattended operation (s13(4)), repeaters (s13(2)(b)) and retransmitting LIPD-originated content: see [00-findings.md](00-findings.md) §5.2.

## Mesh side: LIPD class licence (915-928 MHz ISM)

- Not amateur. Encryption is allowed, and no callsign is required. Power and duty limits apply.
- The instrument in force is the **LIPD Class Licence 2025 (F2025L01047)**; the 2015 licence is repealed. 915-928 MHz: 1 W EIRP for digital modulation (Table 8 item 6, PSD <= 25 mW / 3 kHz), no duty-cycle limit. Details and clause numbers: [00-findings.md](00-findings.md) §5.1.

## What follows (questions Q9 and Q10)

- Mesh → APRS-IS (internet only) puts nothing on amateur RF, so it is the easy direction. Today's Kelly iGate stops here.
- Mesh → amateur RF, or APRS RF → mesh: needs rules on content (plaintext only), identification and control. Not decided.
