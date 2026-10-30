# MeshPRS: APRS ↔ MeshCore Interface Standard

**1.0 Candidate** (2026-10-30), open for public comment. The frame layout is frozen at header version 1 (§9.3). 1.0 final follows the field trial and review (decision [0020](decisions/0020-publish-1-0-candidate.md)), with clarifications only in between. Every choice in this document has a decision record in [decisions/](decisions/); §16 lists them, with the work left for later versions. `Qn` refers to [OPEN-QUESTIONS.md](../OPEN-QUESTIONS.md), where each question names the decision that answered it. Facts cited as "F§n" are in [research/00-findings.md](../research/00-findings.md).

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be read as in RFC 2119.

**Reading order:** §9 (frame format) defines the common header that every subtype in §5-8 starts with.

---

## 1. Introduction

### 1.1 Purpose

APRS (APRS-IS and RF) and MeshCore (a LoRa mesh on 915-928 MHz LIPD in Australia) both carry station positions, short messages and telemetry, with no common rules between them. Without rules, gateways flood each side with the other's traffic, loop packets back, and put duplicate or unverified stations on aprs.fi. MeshPRS defines:

- a compact binary frame for APRS-style information on a MeshCore mesh (Tier A, stock firmware);
- a human-readable text fallback for stock phone apps (§9.7);
- how a gateway converts between those frames and APRS, and the rules that keep the two networks from flooding, looping or breaking either side's licence conditions.

The name stands for *Mesh Position Reporting System* (decision 0014).

### 1.2 Scope

**Kept from APRS:** the station model (callsign-SSID), position reports with symbols and comments, messages with IDs and acks, bulletins, objects and items, telemetry (T#, PARM, UNIT, EQNS, BITS), weather, status, and queries.

**Dropped:** AX.25 addressing (the mesh frame carries one source callsign and, where needed, one addressee, nothing else), digipeater paths and `WIDEn-N` aliases (the mesh does its own flooding), KISS and HDLC framing, the AX.25 destination field as a carrier of data (Mic-E), and the q-construct on the mesh side.

**Out of scope:**
- tunnelling raw AX.25 frames or TNC2 lines through the mesh;
- gating to or from amateur RF (VHF 145.175 MHz, LoRa APRS 433.775 MHz) (decisions 0003, 0025);
- Meshtastic, which may get a sister profile later (decision 0025);
- anything that needs modified MeshCore firmware (Tier B, Annex C).

Which subtypes 1.0 requires is in §15 (decision 0007). Every subtype in decision 0002 is fully defined, required or not.

### 1.3 Profile 0 (the advert profile)

Kelly Page's receive-only iGate (`kelly-page/js/igate.js`, released in Kelly 0.4.34) gates MeshCore **adverts** from whitelisted keys to APRS-IS as `CALL-SSID>APZKPG,qAO,IGATECALL:!DDMM.mmS/DDDMM.mmE>comment`. MeshPRS calls this **profile 0**, the advert profile. The name is chosen so it does not clash with header version 0 (§9.3).

Profile 0 stays valid (§5.4), and this specification stays compatible with it: same tocall, q-construct, position text format, gate order and drop-reason model.

---

## 2. Terminology

- **APRS side:** APRS-IS. APRS RF is out of scope (§1.2).
- **Mesh side:** a MeshCore network with the settings in §12.
- **Station:** a MeshCore node (normally a companion with a phone or PC app) that sends or receives MeshPRS frames under an amateur callsign.
- **Gateway:** software that moves information between the APRS side and the mesh side. An **iGate** is a gateway that carries mesh → APRS-IS only (receive-only, `qAO`). Roles are in §3.
- **Frame:** one MeshPRS unit: the **blob** of one GRP_DATA packet (§9.1), or the text of one GRP_TXT packet in the compact text profile (§9.7).
- **Subtype:** byte 1 of a frame. It selects the service (decision 0002, §9.4).
- **MeshPRS channel:** the MeshCore group channel that carries MeshPRS frames (§12.1).
- **Node key:** a MeshCore Ed25519 public key (32 bytes). A **key prefix** is its first *n* bytes. A **path hash** is its first 1, 2 or 3 bytes; SEQ uses 2 (F§1.1).
- **Binding:** a gateway's record that a callsign-SSID belongs to a node key (§4.3).
- **Tier A:** what works on stock MeshCore 1.18.0 firmware, with app or gateway changes only. **Tier B:** what would need firmware changes (Annex C).
- **N:** the blob length in bytes. **On-air size:** the whole LoRa packet, header to MAC and ciphertext (§9.2).

---

## 3. Architecture, tiers and gateway roles

```
 MeshCore station                MeshCore mesh (LIPD, 923.125 MHz)          Gateway                 APRS-IS
 (app + stock companion)  --GRP_DATA flood, MeshPRS channel-->  repeaters  -->  decode, trust,  --qAO-->  aunz.aprs2.net
                          <--GRP_DATA (G=1), messages only----  repeaters  <--  IS->mesh rules  <--filter-
```

### 3.1 Tiers

- **Tier A** (normative): GRP_DATA on the MeshPRS channel, sent with the companion's `CMD_SEND_CHANNEL_DATA`, with the compact GRP_TXT text profile (§9.7) as the fallback for stock phone apps. Stock repeaters flood both without decrypting them (F§2, F§2.1; decision 0001).
- **Tier B** (optional, informative): Annex C.

### 3.2 Gateway roles

There are three gateway roles (decision 0025). One box MAY hold several.

| Role | Mesh → APRS-IS | APRS-IS → mesh | Notes |
|---|---|---|---|
| **iGate** (receive-only) | Positions, objects, weather, telemetry, status, bulletins, messages and acks from bound stations | Nothing | Today's Kelly iGate role. `qAO` (§11) |
| **Messaging gateway** | As the iGate | Messages and acks addressed to stations heard on the mesh, sent direct only, never flooded (§6.5) | Acks are end-to-end (§6.5) |
| **Object server** | Objects it owns (repeaters, EOCs, evacuation centres) | Nothing | §8.2 |

A gateway MUST NOT carry anything onto the mesh that this section does not list for its role. In particular, a gateway MUST NOT put general APRS-IS positions onto the mesh (no IS → mesh flooding).

---

## 4. Identity and trust

### 4.1 Callsign encoding

Every callsign in a frame (source, addressee, ack target, query target) is a **6-byte base-40 callsign**:

- **Alphabet:** value 0 = space (padding), 1-26 = `A`-`Z`, 27-36 = `0`-`9`, 37 = `-`, 38 = `/`, 39 = `.`.
- **Value:** `Σ c[i]·40^i` for the characters `c[0]..c[k-1]` of the text, first character least significant, so the padding never appears in the value.
- **Storage:** the value as a 48-bit **big-endian** unsigned integer.
- **Range:** 1-9 characters, so values are below 40⁹ = 262,144,000,000,000 < 2⁴⁸. A receiver MUST reject a callsign field whose value is 0 or ≥ 40⁹.

This is the M17 address encoding, chosen so implementations can reuse M17 code and so the full APRS-IS callsign shape (up to 9 characters, alphanumeric SSID) fits in 6 bytes.
- **Verified** against the M17 specification (github.com/M17-Project/M17_spec, `M17_spec.tex` Appendix "Address Encoding", commit `d3995d3`, 2026-10-16): the same 40-character alphabet in the same order, the first character in the least significant position, and the 6-byte address stored big-endian ("network byte order").
- **Check:** the script reproduces M17's own worked example, `AB1CD` = `0x9FDD51`.
- **Divergences:** M17 also defines `0xFFFFFFFFFFFF` as BROADCAST and `0xEE6B28000000`-`0xFFFFFFFFFFFE` as an application range. MeshPRS rejects all values ≥ 40⁹ instead.
- **Byte order:** it is the one big-endian field in MeshPRS; every other multi-byte integer is little-endian, like MeshCore's own. Big-endian is kept so the bytes match M17 exactly.

Examples (verified by script): `VK4ABC` = `00 00 12 9F 5D 8E`; `VK4AZ-9` = `00 23 3A DD DD 8E`.

### 4.2 Callsign rules

- A station MUST use its own amateur callsign as the source. The SSID SHOULD be numeric 1-15. `-0` MUST NOT be used; no SSID is allowed.
- Before gating to APRS-IS, a gateway MUST check that the source is a valid APRS-IS callsign: at most 9 characters, an amateur base callsign (Kelly's `validBase`: 1-3 prefix characters, a digit, 1-4 letters, at most 6 in all), then optionally `-` and a 1-2 character alphanumeric SSID (F§4.1). A gateway MUST drop a frame that fails (`bad callsign`).
- Frames injected from APRS-IS (G = 1, §9.3) carry the APRS source unchanged. It can be any valid APRS-IS callsign up to 9 characters, including alphanumeric SSIDs.
- APRS RF needs a numeric SSID 0-15. That only matters once a later version brings RF gating into scope.

### 4.3 Binding a callsign to a node key

A GRP_DATA packet carries no sender identity: only a 1-byte channel hash in the clear, then ciphertext under a key anyone can derive (F§1.5). The callsign in a frame is therefore **self-asserted**. MeshPRS ties it to a node key like this:

1. **Key prefix in the frame.** A station whose frames are to be gated to APRS-IS MUST set the header's K flag (decision 0004); other stations SHOULD and include the **first 4 bytes of its own node key** (§9.3). The first 1-3 of those bytes equal the station's path hash, so a gateway can cross-check against adverts and paths.
2. **Binding at the gateway.** A gateway keeps bindings of callsign-SSID → full node key. Each gateway keeps its own bindings, from its owner's list and from a club-signed list (decision 0005).
3. **Gate rule.** A gateway MUST NOT gate a frame to APRS-IS unless the source callsign is bound to a node key and the frame's key prefix matches that key (drop reasons `untrusted`, `no key`, `key mismatch`). A frame without K is therefore mesh-only. This is default deny, as in profile 0, and finding R2 (F§5.5).
4. **Not authentication.** A 4-byte prefix is public: anyone who has heard a station's advert can copy the prefix along with the callsign. The prefix catches misconfiguration and casual spoofing only. Real proof needs a signature. An Ed25519 signature is 64 bytes, which would roughly triple a position frame. 1.0 defines no signed frame: trust rests on the gateway's bindings (decision 0026). A later signed frame would take a subtype from the reserved range.
5. A gateway MAY also require that it has heard an advert from the bound key recently (for example within 24 hours) before gating that station's frames.

---

## 5. Position (subtype 0x00)

### 5.1 Layout

After the common header (§9.3: 9 bytes, or 13 with K):

| Field | Type | Size | Units / scaling | Range / notes |
|---|---|---|---|---|
| lat | i24 LE | 3 | degrees = v × 90 / 2²³ | −90 to +89.99999°. Resolution 1.07×10⁻⁵° ≈ 1.19 m |
| lon | i24 LE | 3 | degrees = v × 180 / 2²³ | −180 to +179.99998°. Resolution 2.15×10⁻⁵° ≈ 2.39 m at the equator |
| symbol | 2 × ASCII | 2 | APRS symbol table/overlay, then symbol code | Table `/`, `\`, or overlay `0`-`9` `A`-`Z`. Code 0x21-0x7E |
| pflags | u8 | 1 | bit 0 ALT, bit 1 CSE, bit 2 TS, bits 3-5 ambiguity 0-4 (5-7 reserved), bit 6 MSG, bit 7 reserved | |
| alt | i16 LE | 2 if ALT | metres | −32768 to 32767 |
| course | u8 | 1 if CSE | degrees = v × 360 / 256 (0 = north) | 1.4° steps |
| speed | u8 | 1 if CSE | km/h | 0-254; 255 = 255 km/h or more |
| ts | u32 LE | 4 if TS | sender's Unix time, s | Informative only (§5.3) |
| comment | ASCII | rest of blob | printable 0x20-0x7E, no `\|` or `~` | 0-43 bytes. The gateway truncates to fit APRS (§10.3) |

- **MSG** set means the station can receive MeshPRS messages. The gateway then uses APRS `=` instead of `!`.
- **Ambiguity** follows APRS (F§4.5; Kelly `fmt`): 1-4 blank the hundredths, tenths, units and tens of minutes. A sender that sets ambiguity SHOULD also round lat/lon itself, because a gateway that is not MeshPRS-aware would show the full precision.
- **Precision vs bytes:** 24-bit lat/lon gives about 1-2 m, already better than APRS's uncompressed 0.01′ (≈18 m), in 6 bytes against the 8 of an advert's int32 × 10⁻⁶. Position pflags bit 7 stays reserved, so that a later version can signal a higher-precision position (decision 0021).
- **Size budget.** A full-length 43-byte comment is allowed, but it costs a frame of up to N = 73 (5 blocks).
  - A station beaconing with its normal settings (K set, the options it uses) MUST keep N ≤ 45. With K and no options, that is a comment of at most 23 bytes; with K and every option, 15.
  - It SHOULD keep N ≤ 29, which allows a 7-byte comment with K and no options, or 11 without K.
  - A longer comment SHOULD be sent only occasionally, for example on every 10th beacon or after a change.
- **Encoding (stations):** `v = sign(x) · ⌊|x| · 2²³ / 90 + 0.5⌋` for latitude (`/ 180` for longitude): round half away from zero, clamped to the i24 range. −27.4680 encodes to −2560203.

### 5.2 Worked example (required)

VK4ABC at −27.4680, 153.0235, car symbol `/>`, comment "Mobile", K set, seq 0x2A. The node key is illustrative: its prefix comes from `sha256("MeshPRS illustrative node key VK4ABC")`.

```
00: 50 00 2A 00 00 12 9F 5D 8E 02 F9 52 3D 35 EF D8
10: 14 D1 6C 2F 3E 00 4D 6F 62 69 6C 65
```

| Bytes | Field | Value |
|---|---|---|
| `50` | header | version 1, G 0, K 1, gating 0, retry 0. A first retry would be `51`, with every other byte the same |
| `00` | subtype | Position |
| `2A` | seq | 42 |
| `00 00 12 9F 5D 8E` | source | VK4ABC |
| `02 F9 52 3D` | key prefix | (illustrative) |
| `35 EF D8` | lat | −27.467998° |
| `14 D1 6C` | lon | 153.023500° |
| `2F 3E` | symbol | `/>` |
| `00` | pflags | no options, no ambiguity, not messaging-capable |
| `4D 6F 62 69 6C 65` | comment | "Mobile" |

- **Blob:** N = 28 (2 AES blocks). Without K it is 24, still 2 blocks.
- **On air:** 37 bytes from the sender, plus 2 per repeater hop in SEQ.
- **APRS equivalent:** info field `!2728.08S/15301.41E>Mobile` is 26 bytes. The gated line `VK4ABC>APZKPG,qAO,VK4AZ-10:!2728.08S/15301.41E>Mobile` is 53 bytes plus CR/LF.
- **Compact text (§9.7):** `VK4ABC Mobile: MPRS VK4ABC !2728.08S/15301.41E>Mobile` is 53 bytes of the 160, and 69 bytes on air.

**Second example**, with K, ALT 45 m, CSE 90° at 60 km/h, no comment, from VK4ABC-9: `50 00 2B 05 80 A6 53 5D 8E 02 F9 52 3D 35 EF D8 14 D1 6C 2F 3E 03 2D 00 40 3C`.
- Blob N = 26, 37 bytes on air.
- APRS: `!2728.08S/15301.41E>090/032/A=000148` (36 bytes).

### 5.3 Mesh → APRS conversion

- The output is `SRC>TOCALL,qAO,IGATE:` followed by `!` (or `=` when MSG is set), then the uncompressed position, the CSE extension, the altitude and the comment.
- Every part is rendered by the normative rules in §10.3, so every gateway emits the same line.
- **TS:** a gateway MUST NOT use it to judge freshness or to build an APRS timestamp, because MeshCore clocks are often wrong (decision 0023; F§3.1). Freshness is the receive time, and replay is judged by seq (§9.3.1).
- **Validity checks:** the same as Kelly's `checkPosition`: no fix, out of range, `0,0`, stale.

### 5.4 Adverts (profile 0) and frames together

- A gateway MAY keep gating advert positions as in profile 0.
- When a bound station sends both, the per-station interval (§10) applies across both sources, so the station appears once per interval.
- A gateway SHOULD prefer the MeshPRS frame, because it carries the station's chosen SSID, symbol and comment.

### 5.5 Smart beaconing

A station sending position frames SHOULD beacon when any one of these holds since its last sent position:

| Trigger | Default | Notes |
|---|---|---|
| Moved more than | 100 m | Great-circle distance from the last **sent** position |
| Heading changed by more than | 15° | Only while speed ≥ 5 km/h; GPS heading is noise when stopped |
| Time since last beacon | 30 min | The maximum interval; also the beacon rate when stationary |

Rules on top of the triggers:
- **Minimum interval:** a station MUST NOT beacon more often than its minimum interval. The default is 60 s, and it MUST NOT be set below 30 s. A trigger inside the minimum interval waits until the interval expires.
- **Configurable:** all four values SHOULD be configurable.
- **Fixed stations:** a station that does not move SHOULD rely on its advert position (§5.4) and SHOULD NOT send position frames, apart from one in reply to a query (§6.7) or when it changes symbol or comment. Adverts already flood and are already gated in profile 0, so a beacon frame only adds airtime (SA-8, `../design/reliability.md`).

**Airtime, for context.** At SF8, 62.5 kHz, CR 4/5 with MeshCore's 32-symbol preamble (F§1.4):

| On air | Airtime |
|---|---|
| 21 bytes | 304 ms |
| 37 bytes | 386 ms |
| 53 bytes | 468 ms |
| 101 bytes | 714 ms |

A flood costs that once per repeater that relays it. The network-wide budget is decision 0011, and the defaults above are decision 0024; `../design/reliability.md` has the full table.

### 5.6 APRS → mesh

APRS-IS positions MUST NOT be put onto the mesh in 1.0 (§3.2). That includes a message sender's next position: the IS → RF practice of passing it on (F§4.6) is left for a later version (decision 0025).

---

## 6. Messaging

### 6.1 Message (subtype 0x01)

| Field | Type | Size | Notes |
|---|---|---|---|
| header | | 9 / 13 | Source = sender |
| addressee | base-40 callsign | 6 | §4.1 |
| msgno | u8 | 1 | 1-127. 0 = no ack wanted (an APRS message with no `{ID`). 128-255 reserved; bit 7 is the rej flag in acks |
| text | ASCII | rest, 1-67 | Printable 0x20-0x7E. MUST NOT contain `{`, `\|` or `~` |

**Example:** VK4ABC → VK4AZ-9, msgno 7, "Meet at Ipswich 1300".

```
00: 40 01 2C 00 00 12 9F 5D 8E 00 23 3A DD DD 8E 07
10: 4D 65 65 74 20 61 74 20 49 70 73 77 69 63 68 20
20: 31 33 30 30
```

- **Blob:** N = 36 (3 blocks), 53 bytes on air. Text up to 13 characters keeps N ≤ 29; up to 29 characters keeps N ≤ 45.
- **APRS:** `:VK4AZ-9  :Meet at Ipswich 1300{7` (33 bytes); the gated line is 60 bytes.
- **Maximum message:** 67 characters gives N = 83 and 101 bytes on air, which is well inside the 165-byte blob limit.

### 6.2 Ack (subtype 0x02)

| Field | Type | Size | Notes |
|---|---|---|---|
| header | | 9 / 13 | Source = the station acknowledging |
| acked seq | u8 | 1 | The header seq of the acknowledged message frame |
| msgno / kind | u8 | 1 | bits 0-6: the message's msgno (1-127); bit 7: 0 = ack, 1 = rej |
| to hash | 2 bytes | 2 | The first 2 bytes of SHA-256 of the message sender's 6-byte encoded callsign (§4.1) |

Without K an ack is 13 bytes: **one AES block, 21 bytes on air**.
- **Why a hash:** the sender's full callsign would cost 4 more bytes and a second block.
- **The cost:** a gateway can only render an ack for a message it has itself seen, either one it gated to APRS-IS or one it injected. It recovers the full callsign and the original APRS ID from its own record of (acked seq, msgno, to hash). An ack matching no record is dropped (`unknown ack`), which is harmless: a gateway that never saw the message never gated it.
- **Trust exception to §4.3:** a gateway MAY gate an ack without K when it matches such a record and its source is that message's addressee. The exception waives **only the key-prefix check**: the ack's source callsign MUST still be bound (§4.3 step 2), otherwise it is dropped (`untrusted`). An ack only confirms delivery, and requiring K would push every ack to 17 bytes.
- **Re-acks:** when a station acks another copy of the same message (§6.3), it sends a **retry of its first ack frame** (same seq, retry field incremented), not a new frame.

**Example:** VK4AZ-9 acks VK4ABC's msgno 7, sent with seq 0x2C (§6.1): `40 02 11 00 23 3A DD DD 8E 2C 07 75 E7`.
- Blob N = 13 (1 block), 21 bytes on air.
- APRS: `:VK4ABC   :ack7` (15 bytes); the gated line is 43 bytes.

### 6.3 IDs, retries and duplicates

- **Message numbers:** a sender allocates msgno per addressee and SHOULD increment it for each new message, skipping 0.
- **Retries:** a station that wants an ack MAY retry at most twice, at 30 s and 60 s after the first send (at most 3 sends), and stops when the ack arrives. The limit keeps to the airtime budget in `../design/reliability.md`.
  - A retry is the same frame with the header retry field incremented (§9.3): same seq, msgno and text.
  - Repeaters therefore pass it on, while gateways still see one message (§10.2).
- **The receiver:**
  - MUST ack every copy it receives, including repeats, because the earlier ack may have been lost.
  - SHOULD show a message once, treating (source, msgno, text) within 30 min as one message.
- **Privacy:** messages travel on the MeshPRS channel, whose key is public (§12.1). Every station on the channel can read them. Applications MUST NOT present them as private.

### 6.4 Length and fragmentation

- **Length:** message text MUST be at most 67 characters, the APRS limit (F§4.5).
- **No fragmentation.** MeshPRS defines none, because:
  - (a) MULTIPART carries only ACKs, so MeshCore gives applications no fragmentation (F§1.7);
  - (b) each fragment of a flood is delivered or lost on its own, so a two-fragment message reaches a station with roughly the square of the single-frame delivery rate, and needs its own reassembly timers and partial-loss acks;
  - (c) the longest APRS message already fits one frame (N = 83).
- **Longer text:** an application with longer text MUST send it as separate messages, each with its own msgno.
- **Over-long messages:** a gateway MUST NOT truncate or split a message. A messaging gateway refuses an over-long APRS-IS message (`bad text`, §6.5; decision 0022).

### 6.5 Messages across the gateway

**Mesh → APRS-IS**
- Output: `SRC>TOCALL,qAO,IGATE::ADDRESSEE:text{ID`, with the addressee padded to 9 characters and ID = msgno in decimal (`7`). When msgno is 0 there is no `{ID`.
- A rej becomes `rejID`.
- An ack frame becomes `:TO       :ackID`, with TO and ID recovered from the gateway's record of the message (§6.2).

**APRS-IS → mesh (messaging gateway only)**
- A gateway MAY inject an APRS-IS message as a message frame with G = 1 only when all of these hold:
  - the addressee has sent a MeshPRS frame that this gateway heard on the mesh within the last hour (else `addressee not heard`);
  - the APRS sender has not been heard on the mesh in that hour (else `sender on mesh`);
  - the addressee has not been heard via APRS-IS in that hour, as a source on APRS-IS other than in a MeshPRS-gated line (else `addressee on IS`);
  - the path has no `TCPXX`, `NOGATE` or `RFONLY` (else `path excluded`);
  - the line is not itself MeshPRS output: a line whose destination is the MeshPRS tocall and whose path contains `qAO` MUST NOT be injected (`looped`);
  - sending it keeps the gateway within its APRS-IS → mesh airtime budget (decision 0011, `../design/reliability.md`) (else `airtime`).
  The first four mirror the IS → RF rules (F§4.6). The fifth stops loops.
- **The loop rule's cost:** two mesh islands, each with its own gateway, cannot message each other through APRS-IS in 1.0. A safe rule for that is left for a later version (decision 0025).
- **Direct only:** an injected frame MUST be sent **direct** (GRP_DATA with the addressee's known path, §12.2) and MUST NOT be flooded. If the gateway has no path to the addressee, it does not send (`no path`). APRS-IS never causes a mesh flood.
- **Text:** an APRS message whose text contains any byte outside 0x20-0x7E, or `|`, `~` or `{`, is not injected (`bad text`). It is never transliterated, so every gateway makes the same decision. Text over 67 characters is likewise refused (`bad text`).
- **Byte-identical frames.** The frame MUST be identical whichever gateway builds it (§9.3 G). Let `H = SHA-256(APRS source ‖ ":" ‖ APRS ID)`, with the source in uppercase text as on APRS-IS:
  - seq = `H[0]`;
  - msgno = `H[1] & 0x7F`, or 1 if that is 0;
  - for a message with no ID, `H = SHA-256(APRS source ‖ ":" ‖ text)`, and msgno = 0.
- **ID record:** the gateway keeps (seq, msgno, to hash) → (APRS source, APRS ID) for at least 30 min, so it can turn the mesh ack back into `ackID` with the original 1-5 character ID. A collision between two live messages to the same addressee is possible but rare (1 in 32,768 per pair). The gateway MUST then not inject the second until the first is acked or expired (`id clash`).
- **Reply-ack:** a reply-ack `{MM}AA` is treated as message ID `MM` plus an ack of `AA`. **UNVERIFIED:** whether each half is limited to 2 characters (F§4.5).
- **No positions:** the sender's position is not injected in 1.0 (§5.6).
- **Retries:**
  - A gateway injects the first copy of an APRS message.
  - It MAY re-inject at most **2** APRS-side retries of the same (source, ID) while no mesh ack has been seen. Each re-injection sets the retry field to 1, then 2.
  - It then drops further copies of that ID for 30 min (`duplicate`).
  - Gateways following the same APRS-IS stream reach the same count, so their retries stay identical.
- **Example:** VK2XYZ-7 on APRS-IS sends "See you at the hamfest" to VK4ABC, ID `AB12`. Every gateway builds the same frame:
  - Frame: `60 01 A7 05 34 EB 0D B7 0E 00 00 12 9F 5D 8E 4B` followed by the text. Header `60` (version 1, G = 1), seq 0xA7, msgno 75. N = 38, 53 bytes on air.
  - VK4ABC's ack: `40 02 2E 00 00 12 9F 5D 8E A7 4B 1A F7` (13 bytes), which a gateway renders as `:VK2XYZ-7 :ackAB12`.
- **Whose ack counts:** end to end. A gateway MUST NOT send `ackID` to APRS-IS until the mesh addressee's ack frame arrives (decision 0022).

### 6.6 Bulletin (subtype 0x06)

| Field | Type | Size | Notes |
|---|---|---|---|
| header | | 9 / 13 | |
| glen | u8 | 1 | bits 0-2: group name length 0-5 (6-7 invalid: `bad field`); bits 3-7 reserved |
| id | ASCII | 1 | `0`-`9` = bulletin, `A`-`Z` = announcement (`BLNn` / `BLNx`) |
| group | ASCII | glen | Group name, 0-5 characters |
| text | ASCII | rest, 1-67 | As for messages |

**Example:** VK4ABC, BLN1, "Net tonight 1930 on 147.000": `40 06 31 00 00 12 9F 5D 8E 00 31` followed by the text.
- Blob N = 38, 53 bytes on air.
- APRS: `:BLN1     :Net tonight 1930 on 147.000` (38 bytes); the line is 65 bytes.

**On the channel**
- A bulletin frame is a broadcast: only stations listening at the time get it.
- Senders SHOULD NOT repeat a bulletin more often than every 30 min, and SHOULD stop after 4 h unless it is renewed. A Room Server bulletin agent as a defined role is left for a later version (decision 0024).

**Store-and-forward through a Room Server (Tier A, optional)**

A station or gateway MAY also post a bulletin to a MeshCore Room Server, so stations that were away receive it when they next sync. The room server's limits shape what it can be used for (F§3.4):
- **32 posts.** The store is a RAM ring of 32 posts, so the oldest drop off. A poster SHOULD NOT use more than a few slots of a shared room.
- **151 bytes.** Longer text is truncated silently, so a poster MUST keep each post within 151 bytes. The compact text form `BLN1: <text>` (§9.7 syntax, without the `MPRS <SRC>` prefix, since the room records the poster) is the recommended content.
- **RAM only.** Posts are lost on reboot. A poster SHOULD re-post its live bulletins when it sees that the room has restarted, or at least every few hours.
- **Encrypted delivery.** Each post reaches each client as an encrypted, ACKed TXT_MSG. Airtime grows as clients × posts, and the delivered copies are DMs: a gateway MUST NOT gate room-server deliveries to APRS-IS (§13). Only the channel frame or the APRS-IS original may be gated.

Durable storage would need firmware changes (Annex C).

### 6.7 Query (subtype 0x07)

| Field | Type | Size | Notes |
|---|---|---|---|
| header | | 9 / 13 | |
| q | u8 | 1 | bits 0-6 query type; bit 7 = directed (a target follows) |
| target | base-40 callsign | 6 if directed | |

| Type | Meaning | APRS analogue | Reply |
|---|---|---|---|
| 0x00 | Stations, send your position | `?APRS?` | Position frame |
| 0x01 | Position of the target | `?APRSP` (directed) | Position frame |
| 0x02 | Gateways, identify | `?IGATE?` | Status frame (code 8) from each gateway: role and counts |
| 0x03 | Send your neighbour report | none | Neighbour report |
| 0x04 | Send your telemetry definitions | none | Telemetry kinds 1-4 |
| 0x05 | Send your status | `?APRSS` | Status frame |
| 0x06-0x7F | Reserved | | |

The APRS analogues are for orientation only. `?APRS?` and `?IGATE?` come from the findings (F§4.2, F§4.6); `?APRSP` and `?APRSS` are **UNVERIFIED** (not yet in the research notes).

**Examples:**
- Directed position query from VK4AZ-9 to VK4ABC: `40 07 12 00 23 3A DD DD 8E 81 00 00 12 9F 5D 8E`. N = 16, 37 bytes on air. Compare `:VK4ABC   :?APRSP` (17 bytes).
- `?IGATE?`: `40 07 13 00 23 3A DD DD 8E 02`. N = 10 (1 block), 21 bytes on air.

**Rules**
- A responder to an undirected query MUST wait a random 0-30 s before replying.
- It SHOULD NOT reply if it sent the requested frame type in the last 5 min.
- It MUST NOT reply to the same query type more than once per 10 min.
- A directed query is answered only by the target.
- Queries MUST NOT be gated to APRS-IS, since `?` queries are not gated (F§4.2).
- APRS-IS queries MUST NOT be put onto the mesh. A gateway MAY answer APRS-IS `?IGATE?` itself (F§4.6).

---

## 7. Telemetry (subtype 0x03)

### 7.1 Choice of form

A **compact 5-analog + 8-bit form** is the mandatory form, mapping 1:1 onto APRS `T#`. Raw CayenneLPP is an optional second kind.

**Why the compact form:**
- APRS telemetry *is* 5 analog values (0-255 in APRS 1.0) and 8 bits, and Kelly's iGate already reduces a node's readings to that shape (`igate.js` `tlmValues`).
- It costs 1 byte per value; CayenneLPP needs a channel byte, a type byte and 2-4 value bytes per reading.
- Its scaling travels separately in definition frames, which change rarely, so every value frame stays small.

**Why LPP stays as an option:** it is what MeshCore sensors already produce (F§3.2), but it can only reach APRS through a mapping, and §7.3 requires that mapping to come from the station.

**Definitions come from the station.** The meaning and scaling of a station's channels (PARM, UNIT, EQNS, BITS) MUST come from the station: either its definition frames (kinds 1-4) or a profile ID (kind 5). A gateway MUST NOT invent definitions or use its owner's local mapping for a station's MeshPRS frames, because two gateways would then publish different definitions for one station. Kelly's per-owner mapping (`igate.js` `tlm*`) applies only to profile-0 telemetry, polled with an encrypted request, which is not a MeshPRS frame.

**Profile-0 polled telemetry exception (decision 0006).** §13 forbids gating REQ/RESPONSE contents. Kelly's profile-0 telemetry is exactly that: a response to the gateway's own encrypted `GET_TELEMETRY_DATA` or `GET_STATUS` poll (F§3.2, F§3.3). The one exception is:
- A gateway MAY gate telemetry that it **polled itself, with its own login**, from a node **bound to the gateway's owner** (the owner's own nodes), using the owner's mapping.
- It MUST NOT gate any other node's responses, or any response it did not request.


### 7.2 Layout

After the header, a **kind** byte selects the body:

| kind | Body | Notes |
|---|---|---|
| 0x00 | values | Below |
| 0x01 | `PARM` text | ASCII after `PARM.`: up to 13 comma-separated names. Per-field length limits as in Kelly `igate.js` (`A_LEN` 7,7,6,6,5; `B_LEN` 6,5,4,4,4,3,3,3, from APRS 1.0.1). **UNVERIFIED** against APRS12c (not yet in the findings) |
| 0x02 | `UNIT` text | ASCII after `UNIT.` |
| 0x03 | `EQNS` text | ASCII after `EQNS.`: 15 comma-separated coefficients |
| 0x04 | `BITS` text | ASCII after `BITS.`: `bbbbbbbb,Title` |
| 0x05 | profile ID | u16 LE: a registered telemetry profile that fixes PARM, UNIT, EQNS and BITS (and, for LPP, which reading goes in which slot). 1.0 has no registry (decision 0025), so only kinds 1-4 define channels |
| 0x10 | CayenneLPP | Bytes in MeshCore's telemetry-reply format, without the 4-byte sender timestamp (F§3.2). Gated only when the station has announced a profile ID that maps it |

Until a profile registry exists, a gateway MUST NOT gate kinds 0x05 and 0x10 (`not gated`, decision 0017).
| others | reserved | |

**Values body (kind 0):**

| Field | Type | Size | Notes |
|---|---|---|---|
| mask | u8 | 1 | bits 0-4: A1-A5 present; bit 7: digital byte present; bits 5-6 reserved |
| A1..A5 | u8 each | 1 per bit set in 0-4 | Raw 0-255, in order |
| bits | u8 | 1 if bit 7 | B1 = bit 7 (MSB) … B8 = bit 0 |

**Example:** VK4ABC-3, A1-A5 = 156, 34, 0, 200, 99, bits `10000000`: `40 03 2A 04 9B C4 93 5D 8E 00 9F 9C 22 00 C8 63 80`.
- Blob N = 17 (2 blocks), 37 bytes on air.
- APRS: `T#042,156,034,000,200,099,10000000` (34 bytes); the line is 63 bytes.

**Definition example (kind 1):** `PARM` text "Battery,Noise,TX air,RSSI,SNR,LowBat".
- Blob N = 46, 69 bytes on air.
- APRS: `:VK4ABC-3 :PARM.Battery,Noise,TX air,RSSI,SNR,LowBat` (52 bytes).

### 7.3 Rules

- The APRS `T#` sequence is the header seq as three decimal digits (000-255). Every gateway therefore produces the same line, so APRS-IS's duplicate filter merges copies (§10.3).
- A gateway converts kinds 1-4 into the APRS messages a station sends to itself: `:SRC      :PARM.…`, with the source padded to 9 characters (F§4.5).
- A station SHOULD send its definitions (or profile ID) when it starts, when they change, in reply to query 0x04, and otherwise at most every 6 h.
- A gateway passes a station's definitions on to APRS-IS as received. Until it has received them, it gates the values only, which APRS shows unscaled.
- Analog values are 8-bit (decision 0021). Wider values may come later as a new kind from the reserved range.

---

## 8. Weather, objects, neighbours and status

### 8.1 Weather (subtype 0x04)

After the header comes a 16-bit presence mask (u16 LE), then each present field in bit order:

| Bit | Field | Type | Size | Units | APRS field (F§4.5) |
|---|---|---|---|---|---|
| 0 | position | i24 lat, i24 lon | 6 | As §5.1 | Positional weather `!…/_` |
| 1 | wind direction | u8 | 1 | × 360/256° | `ddd` |
| 2 | wind speed | u8 | 1 | × 0.5 m/s | `/sss` (mph) |
| 3 | gust | u8 | 1 | × 0.5 m/s | `gGGG` (mph) |
| 4 | temperature | i16 | 2 | × 0.1 °C | `tTTT` (°F) |
| 5 | humidity | u8 | 1 | % (1-100) | `hHH` (`00` = 100 %) |
| 6 | pressure | u16 | 2 | × 0.1 hPa | `bBBBBB` (tenths of hPa) |
| 7 | rain, last hour | u16 | 2 | × 0.1 mm | `rRRR` (hundredths of an inch) |
| 8 | rain, last 24 h | u16 | 2 | × 0.1 mm | `pPPP` |
| 9 | rain since midnight | u16 | 2 | × 0.1 mm | `PPPP` |
| 10 | luminosity | u16 | 2 | W/m² | `Lnnn` / `lnnn` |
| 11-15 | reserved | | | | |

**Example:** VK4ABC-13 at −27.6150, 152.7600 (illustrative), wind 90° at 3.0 m/s gusting 5.5, 24.5 °C, 65 %, 1013.2 hPa, no rain in the last hour.

```
00: 40 04 05 B7 1F D7 53 5D 8E FF 00 AF B9 D8 1C A1
10: 6C 40 06 0B F5 00 41 94 27 00 00
```

- **Blob:** N = 27 (2 blocks), 37 bytes on air.
- **APRS:** `!2736.90S/15245.60E_090/007g012t076r000h65b10132` (48 bytes); the line is 78 bytes.

**Conversion**
- Units: m/s × 2.236936 → mph; °C × 9/5 + 32 → °F; mm ÷ 0.254 → hundredths of an inch. Each is rounded.
- Missing fields: wind direction and speed are written as `.../...`; any other missing field is left out.
- **Without a position:** in 1.0 a weather frame **without** bit 0 is mesh-only, and gateways MUST NOT gate it (`no position`).
  - Borrowing the station's last position would differ between gateways.
  - APRS positionless weather (`_MMDDHHMM…`) would need a receive-time stamp, and its format is **UNVERIFIED** (not in the findings).
  - Fixed weather stations therefore include their position: 6 bytes.
- **Range limits:** humidity outside 1-100 gives `bad field`.
- **Symbol:** `/_`.

### 8.2 Object / Item (subtype 0x05)

| Field | Type | Size | Notes |
|---|---|---|---|
| header | | 9 / 13 | Source = the object's owner |
| oflags | u8 | 1 | bit 0 live (1) / killed (0); bit 1 item (1) / object (0); bit 2 TS present; bit 3 reserved; bits 4-7 name length 1-9 (0 and 10-15 invalid: `bad field`; an item of 1-2 characters likewise) |
| name | ASCII | 1-9 | Printable. Objects 1-9 characters, items 3-9 |
| lat, lon | i24, i24 | 6 | As §5.1 |
| symbol | 2 × ASCII | 2 | e.g. `/r` repeater, `/o` EOC |
| ts | u32 LE | 4 if TS | The owner's Unix time when it last set the object, in s |
| comment | ASCII | rest, 0-43 | e.g. frequency and offset for a repeater |

**Example:** VK4ABC owns the live object "IPSRPT", symbol `/r`, comment "147.000MHz -060" (illustrative).

```
00: 40 05 30 00 00 12 9F 5D 8E 61 49 50 53 52 50 54
10: AF B9 D8 1C A1 6C 2F 72 31 34 37 2E 30 30 30 4D
20: 48 7A 20 2D 30 36 30
```

- **Blob:** N = 39, 53 bytes on air.
- **APRS:** `;IPSRPT   *291030z2736.90S/15245.60Er147.000MHz -060` (52 bytes); the line is 79 bytes.

**Conversion**
- **Timestamp source.** Objects are always timestamped on APRS (F§4.5).
  - When TS is set and lies within ±1 h of the gateway's receive time, the gateway MUST use TS as `DDHHMMz` UTC, truncated to the minute. A sender clock is the same for every gateway, so the line comes out identical (§10.3).
  - Otherwise, when TS is absent or implausible (MeshCore clocks are often wrong, decision 0023), the gateway uses its receive time, truncated to the minute. Gateways can then differ at a minute boundary.
  - Owners with a good clock (GPS or phone time) SHOULD set TS.
- Items become `)NAME!pos` (live) or `)NAME_pos` (killed). APRS12c marks items "not recommended", so owners SHOULD use objects.

**Refresh and kill**
- An owner SHOULD resend a live object every 30-60 min, and at most every 10 min.
- To remove one, it sends the frame with live = 0 three times about 1 min apart, then stops.
- A gateway MUST only gate objects whose owner (the header source) is bound (§4.3).
- Any gateway owner MAY run an object server role for objects they are responsible for (decision 0025).

### 8.3 Neighbour report (subtype 0x08)

"Who can hear me" data for coverage maps. It has no APRS equivalent.

| Field | Type | Size | Notes |
|---|---|---|---|
| header | | 9 / 13 | |
| nflags | u8 | 1 | bits 0-4: entry count 0-31; bits 5-6: prefix size − 1 (1-3 bytes; value 3 reserved); bit 7: direction (0 = I heard them, 1 = they heard me) |
| entries | | count × (prefix + 2) | Each entry: prefix (key prefix = path hash of the neighbour), SNR (i8, dB × 4, MeshCore's own encoding), age (u8, minutes since heard; 255 = 255 or more) |

**Example:** VK4ABC heard four neighbours, with 2-byte prefixes (illustrative):

| Prefix | SNR | Age |
|---|---|---|
| 9B80 | +6.25 dB | 1 min |
| FBAE | −3.5 dB | 4 min |
| A698 | −10.5 dB | 12 min |
| 582A | +2.0 dB | 30 min |

```
00: 40 08 32 00 00 12 9F 5D 8E 24 9B 80 19 01 FB AE
10: F2 04 A6 98 D6 0C 58 2A 08 1E
```

- **Blob:** N = 26 (2 blocks), 37 bytes on air.
- **Size limit:** the count is limited so that N ≤ 165 (31 entries of 3-byte prefixes without K).

**Data sources** (F§3.3)

Direction 0 (I heard them):
- zero-hop adverts the station heard;
- the last hop of floods it received;
- a repeater's own `GET_NEIGHBOURS` list, which needs a login and contains repeaters only.

Direction 1 (they heard me): `DISCOVER_RESP`, which carries the SNR at which each repeater heard the station's `NODE_DISCOVER_REQ`. Discovery is zero-hop and limited to 4 answers per 2 min, so a station MUST NOT send discovery requests just to fill reports faster than that.

**Rules**
- A station SHOULD NOT send a neighbour report more than every 30 min, except in reply to query 0x03.
- Neighbour reports map to nothing on APRS: in 1.0, gateways MUST NOT gate them to APRS-IS (`not gated`). They MAY publish them elsewhere, such as a map or MQTT. This is final for 1.0 (decision 0025).

### 8.4 Emergency / Status (subtype 0x09)

| Field | Type | Size | Notes |
|---|---|---|---|
| header | | 9 / 13 | |
| code | u8 | 1 | bits 0-3 status code (below); bits 4-6 reserved; bit 7 = position follows |
| lat, lon | i24, i24 | 6 if bit 7 | As §5.1 |
| text | ASCII | rest, 0-62 | Status text (APRS limit 62, F§4.5) |

**Status codes**
- 0-7 follow the Mic-E standard messages: 0 Off duty, 1 En route, 2 In service, 3 Returning, 4 Committed, 5 Special, 6 Priority, 7 **Emergency**. This list is from APRS101 ch. 10 and not yet in the research notes (UNVERIFIED).
- 8 = plain status (no code).
- 9 = emergency cancelled.
- 10-15 are reserved.

**Examples:**
- Plain status "Net control tonight": `40 09 33 00 00 12 9F 5D 8E 08` followed by the text.
  - N = 29 (2 blocks), 37 bytes on air.
  - APRS `>Net control tonight` (20 bytes).
- Emergency with position: `40 09 34 00 00 12 9F 5D 8E 87 35 EF D8 14 D1 6C` followed by "Vehicle rollover".
  - N = 32, 53 bytes on air.

**Conversion**
- Code 8 becomes `>text`. A position in a code 8 frame is not rendered (decision 0017).
- Codes 0-7 and 9 with a position become a position report with the symbol `/>` (the frame carries none; decision 0017), whose comment starts with the code's name in capitals, for example `!2728.08S/15301.41E>EMERGENCY Vehicle rollover` (46 bytes). Without a position they become `>NAME text`.
  - **UNVERIFIED:** whether APRS clients recognise an emergency outside Mic-E at all. Mic-E carries emergency in the destination field, which MeshPRS drops (§1.2). The comment prefix makes the emergency readable by people, though APRS software may not flag it (decision 0024).

**Emergency handling**
- A station in emergency SHOULD send the frame every 60 s for 5 min, then every 5 min until it sends code 9.
- **Gateway priority:**
  - A gateway MUST exempt code 7 and 9 frames from the per-station interval.
  - It MUST queue them ahead of all other traffic, and MUST NOT drop one for `queue full` while it holds any lower-priority frame (it drops that frame instead).
  - It MUST still apply the global rate limit, so that a flood of fake emergencies cannot flood APRS-IS.
- **Local alert:** on a code 7 or code 9 frame, a gateway SHOULD also alert its own operator locally, and MAY show it on its own map or log (decision 0024).
- **Mesh priority:** stations relaying nothing do nothing different. MeshCore has no priority field for group packets, so mesh-side priority would need firmware changes (Annex C).

---

## 9. Frame format, encodings and limits

### 9.1 Carrier

- **Packet:** a Tier A frame is the blob of a MeshCore **GRP_DATA** packet (payload type 0x06) on the MeshPRS channel (§12.1), plaintext `data_type u16 LE, data_len u8, blob` (F§1.4).
- **Data type:** **0xFF4D**, bytes `4D FF` on the wire. It is a development value in the unregistered FF00-FFFE range (F§1.6), chosen because it is not 0xFFFF (`DATA_TYPE_DEV`, which every experimenter uses by default). It is **provisional**: a registered value in 0100-FEFF replaces it once a working implementation can be shown (decision 0012).
- **Collisions:** another project may use the same development value on the same channel. A receiver MUST therefore validate every frame (§9.5) before acting on it.
- **Size:** the blob is at most 165 bytes (`MAX_GROUP_DATA_LENGTH`, F§1.4).

### 9.2 Size

On-air size of a GRP_DATA packet with an N-byte blob (F§1.4):

`1 (header) + 1 (path_len) + path + 1 (channel hash) + 2 (MAC) + 16·⌈(N+3)/16⌉`

| Blob N | AES blocks | On air from the sender (no path) |
|---|---|---|
| ≤ 13 | 1 | 21 |
| ≤ 29 | 2 | 37 |
| ≤ 45 | 3 | 53 |
| ≤ 61 | 4 | 69 |

- **Steps:** the steps are 13, 29, 45 and 61 bytes. Each repeater hop adds a path hash (2 bytes in SEQ).
- **Targets:**
  - An ack without K MUST fit N ≤ 13 (it is fixed at 13).
  - Telemetry values MUST fit N ≤ 29 (at most 22 with K).
  - A position beacon with its normal settings MUST fit N ≤ 45, and SHOULD fit N ≤ 29. A longer comment is allowed occasionally (§5.1).
  - Weather and neighbour frames SHOULD fit N ≤ 29.
  - A message is 16 bytes plus its text (20 with K): it fits N ≤ 45 for up to 29 characters, and longer text up to 67 characters is allowed (§6.4).

### 9.3 Common header

Every frame starts with:

| Byte | Field | Notes |
|---|---|---|
| 0 | hdr | bits 7-6 **version** (0-3); bit 5 **G**; bit 4 **K**; bits 3-2 **gating**; bits 1-0 **retry** |
| 1 | subtype | Decision 0002 (§9.4) |
| 2 | seq | u8, per-originator sequence number (below) |
| 3-8 | source | base-40 callsign (§4.1) |
| 9-12 | key prefix | Only when K = 1: the first 4 bytes of the sender's node key (§4.3) |

The header is 9 bytes, or 13 with K. MeshPRS defines no hop count: the MeshCore path length already gives one.

**Version.** The version is the top 2 bits of byte 0. This layout is version **1**, frozen at the 1.0 Candidate. Version 0 was the Draft 0.1 experimental layout: it is byte-identical apart from the version bits, and a receiver MAY accept it as version 1 until 1.0 final. Stations MUST send version 1. Version 2 is spare. Version 3 is reserved as an escape: a version byte follows the header, to be defined by the version that first uses it. Why this choice:
- Decision 0002 gives the subtype the whole of byte 1, so the version can't share it.
- A separate version byte costs a byte on every frame, and the frame needs a flags byte anyway (G, K, gating, retry).
- Using the GRP_DATA data type as the version would spend a registry allocation per version, and the registry asks for small ranges (F§1.6). The data type identifies MeshPRS; it is not a version counter.
- 2 bits plus the escape is enough for a format that changes rarely, and frees the bits needed for gating and retry without a second flags byte.

**G (gatewayed in from APRS-IS).** G is set only by a gateway, on a frame it built from APRS-IS. It is the mesh-side loop marker: a gateway MUST NOT gate a G = 1 frame to APRS-IS (`looped`). Stations MUST send G = 0. A G = 1 frame MUST be byte-identical whichever gateway builds it: it carries no gateway identity and nothing derived from a gateway's clock. Its seq and msgno come from the APRS sender and message ID (§6.5), so the mesh's duplicate table drops a second gateway's copy.

**K (key prefix present).** §4.3.

**Gating (2 bits):**

| Value | Meaning | APRS analogue |
|---|---|---|
| 0 | Normal: may be gated | |
| 1 | **Do not gate.** Gateways MUST NOT gate the frame anywhere (`nogate`) | `NOGATE` |
| 2 | **Test.** Gateways MUST NOT pass the frame to live APRS-IS (`test`); a gateway MAY pass it to a test server (§11) | |
| 3 | Reserved; receivers treat it as 1 | |

The two flags share one 2-bit field instead of two bits because they are mutually exclusive outcomes of one decision (where the frame may go). "Test but may go live" and "do not gate but test" mean nothing, so a field rules out the contradictory combinations, and the fourth value is spare for a later rule.

**Retry (2 bits).** 0 on the first send of a frame, incremented on each retransmission of that same frame. Stations retry at most twice (§6.3) and gateways re-inject at most twice (§6.5), so value 3 is never sent in 1.0; receivers treat it like any other retry.
- Every other byte of a retry is identical to the original, seq included.
- The retry field exists because repeaters' duplicate table hashes only the payload (F§2.4), and on the SEQ mesh it remembers a payload for about 2.7 h at measured load (SA-8, `../design/reliability.md`). Without the field, a retry would never get past the nodes that carried the first copy.
- The retry value MUST NOT affect any APRS-IS output, and gateways ignore it when removing duplicates (§10.2). Every retry of one frame therefore collapses to one APRS-IS line.

**seq.** The sequence space belongs to the **originator identity**: the node key when K is set, otherwise the source callsign.
- A sender keeps one counter per originator identity, so a node sending under several SSIDs with K set uses **one** counter for all of them.
- It increments the counter (mod 256) by 1 for each new frame, of any subtype. A retry keeps its frame's seq.
- A sender MUST either always or never set K for a given source callsign, so that its identity does not switch between key and callsign. G = 1 frames take a derived seq instead (§6.5). The counter serves as:
- the field that makes otherwise-identical frames differ. With AES-ECB under a fixed channel key, identical plaintext gives identical ciphertext (F§1.5), so without it a stationary station's repeated beacon would be dropped silently as a duplicate;
- the gateways' duplicate key (§10.2);
- the APRS telemetry `T#` sequence (§7.3);
- the replay check (§9.3.1).

**Why 8 bits:**
- A counter repeats only after 256 new frames. At the 120 s default minimum beacon interval (§5.5) that is 8.5 h, longer than the 2.7 h duplicate horizon.
- At the 30 s floor it is 2.1 h. A repeat then also needs every other byte to be identical, which a moving station's position never is.
- A timestamp was rejected because node clocks are unreliable (decision 0023). A 16-bit counter would cost a byte on every frame.
- A sender SHOULD keep its counter across reboots (in flash or app storage). One that can't MUST start at a random value.

#### 9.3.1 Sequence wrap, reboot and replay

A gateway keeps, for each originator identity (§9.3), the last accepted seq and when it was accepted. For a new frame, let `d = (seq − last) mod 256` (serial-number arithmetic, as in RFC 1982):

| d | Meaning | Action |
|---|---|---|
| 0 | The same frame, or one of its retries | Duplicate (§10.2) |
| 1-127 | Newer | Accept; `last = seq` |
| 128-255 | Older | If `last` was accepted less than 10 min ago: drop (`replayed`). Otherwise accept and resync (a wrap or reboot after a quiet spell) |

**Reboot inside 10 min.** A node that reboots within 10 minutes and restarts at a random seq looks "older" about half the time. To recover, a gateway that drops two consecutive `replayed` frames from one originator, where the second is newer than the first (`1 ≤ d ≤ 127` between them), MUST resync to the second and accept it. A rebooted node therefore loses at most one frame. Frames with `d = 0` whose body differs from the stored frame (ignoring retry) are treated as "older".

**Limits.** Senders MUST NOT send more than 127 new frames per originator in any 10 minutes, so "newer" stays unambiguous. This replay check stops casual replays only (§14).

### 9.4 Subtypes

As fixed by decision 0002:

| Value | Service | Layout |
|---|---|---|
| 0x00 | Position | §5.1 |
| 0x01 | Message | §6.1 |
| 0x02 | Ack | §6.2 |
| 0x03 | Telemetry | §7.2 |
| 0x04 | Weather | §8.1 |
| 0x05 | Object / Item | §8.2 |
| 0x06 | Bulletin | §6.6 |
| 0x07 | Query | §6.7 |
| 0x08 | Neighbour report | §8.3 |
| 0x09 | Emergency / Status | §8.4 |
| 0x0A-0xDF | Reserved for future standard use | |
| 0xE0-0xFE | Experimental / private | |
| 0xFF | Reserved | |

### 9.5 Receive validation, versioning and extension

A receiver MUST drop the frame, counting the named reason, when any of these holds:

| Condition | Reason |
|---|---|
| Data type is not MeshPRS's | (not counted: not ours) |
| N < 9, or < 13 with K, or shorter than the subtype's fixed fields | `short frame` |
| Version not implemented | `unknown version` |
| Source or another callsign field invalid (§4.1) | `bad callsign` |
| Subtype 0xFF, or reserved 0x0A-0xDF not implemented | `unknown subtype` |
| A field outside its defined values (bulletin glen 6-7, object name length 0 or 10-15, neighbour prefix size 4, humidity 0 or > 100) | `bad field` |

Further rules:
- **Experimental subtypes:** subtypes 0xE0-0xFE MAY be used by private agreement. A conforming gateway MUST NOT gate them to APRS-IS (`experimental subtype`).
- **Unknown subtypes:** a receiver MUST NOT gate or answer a subtype it does not implement. It MAY show or log it.
- **Field order:** every subtype lays out its fields in this order: fixed fields, then optional fields in the order of their flag bits, then at most one variable tail (comment or text) running to the end of the blob. New optional fields may only use flag bits that are reserved now, and sit before the tail.
- **Reserved flag set:** a receiver that finds a reserved flag set in a subtype's flags or mask byte cannot find the tail. It MAY use the fields before that point, MUST NOT gate the frame, and SHOULD count it (`unknown flag`).
- **Integers:** all multi-byte integers are little-endian two's complement, except callsigns (§4.1).

### 9.6 Text and limits

- **Text fields:** printable ASCII (0x20-0x7E) only, because APRS is 7-bit and gateways must produce identical bytes. A sender MUST NOT put UTF-8 into a frame. A gateway MUST drop (`bad text`) rather than transliterate a frame that breaks this. Comments MUST NOT contain `|` or `~`, as in Kelly's `clean`.
- **APRS-IS line:** at most 512 bytes including CR/LF (F§4.1). No MeshPRS conversion comes near it; the longest example here is 107 bytes.
- **MeshCore limits:** a blob is at most 165 bytes (GRP_DATA), and a compact text line at most 160 (GRP_TXT, F§1.4).

### 9.7 Compact text profile (GRP_TXT fallback)

For stock phone apps that can send and show channel text but not GRP_DATA. Frames are GRP_TXT messages on the MeshPRS channel. The app shows them as `name: text`, where `name` is the sender's node name.

**Syntax** (the text after `name: `):

```
MPRS[.KKKKKKKK] SP SRC SP INFO
```

- `MPRS` marks a MeshPRS text frame. Text not starting with it is ordinary chat and MUST be ignored by gateways.
- `.KKKKKKKK` is optional: the first 4 bytes of the sender's node key in uppercase hex. It is the text form of the K flag.
- `SRC` is the source callsign (§4.2).
- `INFO` is an APRS info field (F§4.5) of one of these types:
  - `!`, `=`, `/`, `@`: positions, uncompressed or compressed;
  - `:`: message, ack, rej, bulletin, telemetry definitions;
  - `;` object, `)` item, `>` status, `T#` telemetry, `_` positionless weather.
  
  Any other type MUST be dropped (`bad text`), including `?` queries, `}` third-party, `` ` `` and `'` Mic-E, and `$` NMEA.
- **Length:** `name: ` prefix plus text MUST NOT exceed 160 bytes; the NUL terminator is not counted (BaseChatMesh.cpp:519-531, F§1.4). With a 31-byte node name and a 9-character SRC, that leaves 112 bytes for INFO, or 103 with the key token. That is enough for a 67-character message with a 5-character ID (84 bytes).
- **No seq needed:** GRP_TXT's plaintext starts with a 4-byte sender timestamp, so repeats differ from one second to the next (F§1.4).
- **Not gated in 1.0:** gateways MUST NOT gate compact text frames to APRS-IS (`text profile`).
  - A GRP_TXT packet carries no sender key, and the key token is self-asserted text that anyone can type, so even the weak binding check of §4.3 is impossible.
  - The profile exists so that MeshPRS traffic is readable, and can be typed, in stock phone apps on the mesh.
  - Gating it would need signed frames, which a later version may define (decisions 0023, 0026).
- **Cost:** the required position example takes 53 bytes and 69 on air, against 37 for the binary frame (§16.1).

---

## 10. Gateway behaviour

### 10.1 Pipeline

Every gateway MUST process each mesh-side frame in **this order**. The order is normative, because it decides which reason a frame is counted under, and the test vectors depend on that. It is Kelly's profile-0 order with the frame steps added. Each drop has a named reason and is counted.

1. **Decode and validate** (§9.5): `short frame`, `unknown version`, `bad callsign`, `unknown subtype`, `bad field`, `experimental subtype`, `unknown flag`, `bad text`.
2. **Loop and gating checks** (§9.3):
   - G = 1 gives `looped`;
   - gating 1 or 3 gives `nogate`;
   - gating 2 gives `test`, unless this gateway is connected to a test server;
   - subtypes 0x07 and 0x08, telemetry kinds 0x05 and 0x10 (§7.2), and weather without a position, give `not gated` / `no position`;
   - compact text frames give `text profile`.
3. **Trust** (§4.3): `untrusted`, `no key`, `key mismatch`, `unknown ack`.
4. **Replay** (§9.3.1): `replayed`. **Validity**, for subtypes with a position: `no fix`, `out of range`, `0,0`, `stale`, and `replayed (older advert)` for adverts.
5. **Duplicate suppression** (§10.2): `duplicate`.
6. **Per-station interval**, kept per station and service: the key is (source, subtype), plus the telemetry kind for telemetry and the object name for objects (decision 0018). Kelly: 2 min, down to a 30 s floor when the station has moved more than 500 m. Messages, acks and emergencies are exempt: `interval`.
7. **Queue and jitter** (a bounded queue with a random delay of 0-5 s, so gateways hearing one frame don't all send at once): `queue full`.
8. **Global rate limit** (Kelly: token bucket, 1 per 5 s, burst 3). A frame that would exceed it waits in the queue, but at most 10 s: `rate`.
9. **Maximum hold:** a frame not sent within **15 s** of its receipt MUST be dropped (`expired`).
   - The figure is jitter (5 s) plus the longest wait (10 s).
   - It keeps every gateway's line for one frame inside APRS-IS's 30 s duplicate window (F§4.6), so copies still merge.
   - Emergencies (§8.4) are held to the same limit.

The numbers are the network-wide figures of decision 0011.

### 10.2 Duplicates

- **Mesh side:** the duplicate key is (originator identity, seq) (§9.3), **ignoring the retry field**. Subtype is not part of the key, because one counter covers every subtype. A gateway MUST treat a frame matching a key it accepted in the last 10 min as a duplicate (`duplicate`), so all retries of one frame give at most one APRS-IS line. The 127-frames-per-10-minutes limit (§9.3.1) keeps the key unambiguous.
- **APRS side:** a gateway MUST NOT send an APRS line with the same source, destination and info as one it sent in the last 30 s, which is the APRS-IS window (F§4.6).

### 10.3 Deterministic output (normative)

APRS-IS removes duplicates only when source, destination and info match (F§4.6). So that several gateways hearing one flood collapse into one APRS-IS packet, every gateway MUST render a given frame to the same bytes. Hence:
- **One tocall:** all MeshPRS gateways MUST use the same tocall (§11).
- **Output from the frame alone:** the callsign-SSID claim, symbol and comment are all taken from the frame (§5.1). A gateway's local lists decide *whether* it gates, never *what* it emits.
- **Fixed rendering rules** for every field, below. They are written in integer arithmetic, where `⌊x⌋` is floor division, so that floating-point rounding cannot differ between implementations.

**The rendering rules** (the script check is in Annex A):

| Item | Rule |
|---|---|
| Position format | Always **uncompressed** `DDMM.mmH` / `DDDMM.mmH`. Compressed positions are never emitted, for readability, ambiguity support and profile-0 compatibility |
| Latitude | From the raw i24 `v`: `hm = ⌊(|v|·540000·2 + 2²³) / 2²⁴⌋` hundredths of a minute (half-up). Degrees = `⌊hm/6000⌋` (2 digits), minutes = `hm mod 6000` written as `MM.mm`. The carry at 60.00′ happens by itself (−27.99999° gives `2800.00S`). `S` if `v < 0`, else `N` |
| Longitude | The same with `|v|·1080000·2`, 3-digit degrees, `W`/`E` |
| Ambiguity | Then blank the trailing digits as §5.1 |
| Course | `c` raw byte: `⌊(c·720 + 256) / 512⌋`; 0 becomes `360`; 3 digits |
| Speed | km/h `s` to knots: `⌊(s·2000 + 1852) / 3704⌋`, 3 digits |
| Altitude | m `a` to feet: `⌊(|a|·20000 + 3048) / 6096⌋` with the sign of `a`; written `/A=` and 6 characters (`-` plus 5 digits when negative). The i16 maximum, 32767 m, gives 107503 ft, which fits. A negative value below −99999 ft is clamped to `-99999` |
| Order after the symbol code | CSE extension, then `/A=`, then the comment |
| Text | Frames are printable ASCII already (§9.6; frames that aren't are dropped, never mapped). The gateway trims leading and trailing spaces, truncates so that the whole text after the symbol code (extension, altitude, comment) is at most 43 characters, then trims trailing spaces again. Message text: at most 67 characters; bulletins likewise; status at most 62 characters |
| Wind speed and gust | Raw `u` (0.5 m/s units) to mph: `⌊(u·3600000 + 1609344) / 3218688⌋`, 3 digits |
| Wind direction | As course. **UNVERIFIED:** whether APRS weather writes north as `360` or `000` |
| Temperature | Raw `t` (0.1 °C) to °F: `⌊(2·(9t + 1600) + 50) / 100⌋`, 3 characters (`-05` style when negative), clamped to −99 to 999 |
| Rain | Raw `r` (0.1 mm) to hundredths of an inch: `⌊(200r + 254) / 508⌋`, 3 digits, clamped to 999 |
| Humidity | 100 written `00`, otherwise 2 digits |
| Pressure | Tenths of a hPa as is, 5 digits (the u16 maximum, 65535, fits) |
| Luminosity | Below 1000 W/m²: `L` + 3 digits. 1000-1999: `l` + 3 digits of (value − 1000). 2000 and over: clamped to `l999`. **UNVERIFIED:** the `L`/`l` split (the findings name the fields only) |
| Weather field order | `_ddd/sss` (or `.../...`), `g`, `t`, `r`, `p`, `P`, `h`, `b`, `L`/`l`; absent fields left out |
| Timestamps | Objects per §8.2: the frame's TS when plausible, otherwise receive time, truncated to the minute |
| Telemetry | `T#` + seq (3 digits) + the five analogs (3 digits each, empty when absent) + 8 bits (`00000000` when the frame has no digital byte; decision 0017) |

A frame received either side of a minute boundary, when its timestamp comes from receive time, can still produce two lines; this is accepted.

### 10.4 Summary

The full iGate design is in [`../design/igate-design.md`](../design/igate-design.md). In summary, a MeshPRS gateway:
- logs in to APRS-IS with its own callsign-SSID and passcode, and never with `pass -1`, which cannot send (F§4.3);
- marks every gated packet `qAO`;
- uses the tocall `APZKPG` (provisional, §11);
- removes duplicates as in §10.2;
- puts nothing from APRS-IS onto the mesh except what its role allows (§3.2, §6.5), and never general positions or floods.

---

## 11. APRS-IS specifics

- **Login:** `user CALL-SS pass NNNNN vers NAME VER filter …` on port 14580. Use `aunz.aprs2.net`, falling back to `rotate.aprs2.net` (F§4.3).
- **q-construct:** gated packets are `SRC>TOCALL,qAO,IGATECALL:info`. qAO is the receive-only construct and explicitly covers translated non-APRS sources (F§4.2).
  - A gateway MUST NOT add any other path element.
  - Its own packets (status, `?IGATE?` replies) go as `IGATECALL>TOCALL,TCPIP*:` without qAO, as Kelly's `statusPacket` does.
- **Tocall:** **one tocall for all MeshPRS gateways**, whoever wrote them, because APRS-IS's duplicate hash includes the destination (F§4.6, §10.3). It is `APZKPG`, from the unregistered experimental `APZ` range and currently unallocated (F§4.4).
  - It is provisional. A registered tocall for MeshPRS is to be requested from aprs-deviceid before 1.0 final (decisions 0012, 0020). The precedent is `APM2A?` for mesh2aprs.
  - Implementations identify themselves in their login `vers` string, not in the tocall.
  - A line whose destination is the MeshPRS tocall and whose path contains `qAO` is MeshPRS output, and MUST NOT be injected into the mesh (§6.5).
- **Filter (messaging gateway):** a filter that brings messages for the callsigns heard on the mesh, for example `g/` with those callsigns. It MUST NOT be a range filter feeding positions to the mesh.
- **Packets never gated to APRS-IS:** frames from G = 1, room-server deliveries, anything from a DM or a private channel (§13).
- **Testing:** test against a private aprsc instance with no uplink, not the live network (F§4.3). Frames with gating = 2 (test) MAY go only to such a server. A gateway MUST NOT send them to any server that has an uplink to APRS-IS.

---

## 12. Mesh-side specifics

### 12.1 The MeshPRS channel

Tier A frames travel on one dedicated **hashtag channel**, so the key is public and derivable by anyone:

- **Name:** `#meshprs` (decision 0012). `#aprs` was not chosen because it may already carry human chat.
- **Key:** the first 16 bytes of `sha256("#meshprs")` = `650fa1fd5d2c0bc01449a964a130ea1c`.
- **Channel hash:** the first byte of `sha256(key)` = `0xBA`. The Public channel's is `0x11`. The `#aprs` alternative would be key `910a190e741c01e20043ef8e74db9400`, hash `0xE7`.
- **Collisions:** a 1-byte channel hash collides with roughly 1 in 256 other channels. The firmware's MAC check and §9.5 validation separate them.
- **Not Public:** MeshPRS traffic MUST NOT be sent on the Public channel, as MBUG asks (F§5.4; R7).

### 12.2 Routing

- **Floods:** broadcasts (positions, objects, bulletins, status, queries, neighbour reports) are sent as FLOOD GRP_DATA, path `0xFF` in `CMD_SEND_CHANNEL_DATA` (F§2.3).
- **Unscoped:** floods SHOULD be unscoped (no transport code), because a region-scoped flood dies at any repeater that does not know the region (F§2.2; decision 0001).
- **Direct, from APRS-IS:** everything a gateway injects from APRS-IS (G = 1) MUST be sent direct, on the addressee's known path, and MUST NOT be flooded. With no known path, the gateway does not send (§6.5).

### 12.3 Radio settings and etiquette

- **Radio:** MBUG settings: 923.125 MHz, BW 62.5 kHz, SF8, CR 4/5, `path.hash.mode 1` (2-byte hashes), `multi.acks 1`, `flood.advert.interval 83` (F§5.4).
- **Adverts:** MeshPRS does not change advert behaviour.
- **Airtime:** MBUG gives no numeric budget, so MeshPRS sets one (decisions 0011, 0024). Meanwhile the smart-beaconing minimums (§5.5), the query back-off (§6.7) and the report interval (§8.3) bound a station's output.

---

## 13. Regulatory considerations

*Informative where it describes the law; the regulator's text governs.* See F§5. Decision 0003 settles it for 1.0: nothing from the mesh goes to amateur RF.

The rules below are normative (decision 0003). They come from the regulatory research's recommendations R1-R8 (F§5.5).

- **The mesh is not amateur.** MeshCore at 915-928 MHz operates under the **Radiocommunications (Low Interference Potential Devices) Class Licence 2025 (F2025L01047)**, not the repealed 2015 instrument. There is no amateur allocation in that band, so a mesh node is never an amateur station, even when an amateur runs it (F§5.1, F§5.2).
  - LIPD allows encryption and needs no callsign, so GRP_DATA under a public channel key is lawful there.
  - The applicable LIPD item for LoRa (Table 8 item 6, and the clause 43 PSD limit) is UNVERIFIED.
- **Never gate private content.** A gateway MUST NOT gate DMs (TXT_MSG), private-channel content, room-server deliveries, or telemetry request/response contents to APRS-IS or anywhere else, except the polled-telemetry exception of §7.1 (decision 0006). Only MeshPRS-channel frames and adverts may be gated (R3).
- **Verified amateur callsigns only.** A gateway MUST gate to APRS-IS only frames from a valid amateur callsign bound to a node key (§4.2, §4.3), through a passcode-verified login, marked qAO (R1, R2). Anonymous LIPD users are never gated. This is APRS-IS policy, not ACMA law (F§5.3).
- **Plaintext only on amateur RF.** Gating to amateur RF is out of scope (§1.2). If a later version allows it, everything put on amateur RF MUST be the decoded plaintext APRS form, never a MeshCore packet or ciphertext. This follows the Amateur Stations Class Licence 2023 s13(2)(d)(iv) ban on encoding to obscure meaning (R4).
  - It MUST come only from verified amateur callsigns, in third-party format, with the gateway's callsign as the source.
  - It MUST meet s12(1) identification and, if unattended, s13(4) (R5).
  - APRS RF → mesh → APRS RF chains MUST NOT be built without a repeater apparatus licence (R6).
  - The 433.05-434.79 MHz overlap between LIPD and amateur is UNVERIFIED.
- **No commercial content.** A gateway MUST NOT gate financial-gain or advertising content to APRS-IS.
  - This is **APRS-IS policy**: APRS-IS is kept to amateur use (F§5.3). It is not law: s13(2)(a) and (d) of the Amateur Stations Class Licence govern amateur stations, and APRS-IS is not one.
  - Those clauses would apply directly only to content put on amateur RF.
- **APRS-IS → mesh** is lawful under LIPD, but it MUST:
  - be rate-limited to the gateway's airtime budget;
  - be sent direct only, never flooded (§6.5);
  - not use #Public;
  - honour `NOGATE`, `RFONLY` and `TCPXX` (R7).

---

## 14. Security and privacy considerations

- **Callsign spoofing.**
  - The callsign and key prefix in a frame are self-asserted and copyable (§4.3).
  - Default-deny binding stops unknown stations reaching APRS-IS, but not someone copying a bound station's prefix within radio range of a gateway. The requirement that the gateway heard the bound key's advert recently (§4.3 item 5) narrows this.
  - 1.0 defines no signed frames (decision 0026). Firmware-level sender authentication is Annex C.
- **Replay.**
  - A recorded frame replayed later carries an old seq and old content. The 10-minute duplicate window catches only short-term replays.
  - The seq check (§9.3.1) rejects a replay only while the station has sent within the last 10 min; after a quiet spell a replayed frame resyncs the gateway and is gated as if current, because the stale check uses receive time.
  - Full replay protection needs trustworthy clocks or signatures (decisions 0023, 0026).
- **Location privacy.**
  - Stations opt in by sending frames, and gateways gate only bound stations.
  - Ambiguity (§5.1) and sender-side rounding (Kelly `roundPos`) are available.
  - Anyone can read positions sent on the MeshPRS channel.
- **Channel confidentiality.**
  - The channel key is public (§12.1), and ECB shows identical blocks (F§1.5).
  - Nothing on the MeshPRS channel is confidential, and no application may suggest that it is (§6.3).
- **Abuse.** A gateway SHOULD support a blocklist by node key and by callsign, with drops counted (`blocked`). A blocklist SHOULD be able to override a binding.
- **Resource exhaustion.**
  - Every gateway queue is bounded (§10.1).
  - Responders back off on queries (§6.7).
  - A sender is limited to 127 new frames per 10 min (§9.3.1) and by the beaconing minimums (§5.5).

---

## 15. Conformance

MeshPRS 1.0 requires the subtypes position (0x00), message (0x01), ack (0x02), telemetry (0x03), object/item (0x05) and status (0x09); weather (0x04), bulletin (0x06) and neighbour report (0x08) are optional, and query (0x07) must be parsed but need not be answered (decision 0007). The profiles:

| Profile | MUST implement |
|---|---|
| **Station** | §9 header and validation; sending position (§5) with smart beaconing (§5.5); receiving messages and acks if it sets MSG |
| **iGate** | §9.5 validation; §4.3 trust; §10 pipeline; §11; conversion of every subtype it gates; never gating 0x07, 0x08 or compact text |
| **Messaging gateway** | iGate, plus §6.5 APRS-IS → mesh |

### 15.1 Test vector files

Conformance is proven by the shared vectors in [`test-vectors/`](../test-vectors/), following the `kelly-page/bridge/igate_vectors.json` pattern. The examples in this specification were checked by script (Annex A). The file names are fixed here so other documents can copy them:

| File | Contents |
|---|---|
| `frames.json` | Encode and decode: field values ↔ blob hex, for every subtype, including the invalid frames of §9.5 |
| `gateway.json` | Mesh → APRS-IS: a frame (or advert) plus gateway state → the exact APRS-IS line, or a drop reason |
| `inject.json` | APRS-IS → mesh: an APRS-IS line plus gateway state → the exact G = 1 blob and its routing, or a drop reason |
| `text.json` | Compact text profile: GRP_TXT text → parsed fields, or a drop reason |

### 15.2 Drop reasons

These are the only drop-reason names. Implementations and vectors MUST use these exact strings.

| Reason | Where | Meaning |
|---|---|---|
| `short frame` | §9.5 | Blob shorter than the header or the subtype's fixed fields |
| `unknown version` | §9.5 | Header version not implemented |
| `bad callsign` | §4.1, §4.2, §9.5 | Invalid callsign field, or not a valid APRS-IS amateur callsign |
| `unknown subtype` | §9.5 | Subtype 0xFF, or a reserved subtype not implemented |
| `bad field` | §9.5 | A field outside its defined values |
| `experimental subtype` | §9.5 | Subtype 0xE0-0xFE |
| `unknown flag` | §9.5 | A reserved flag set in a subtype's flags or mask byte |
| `bad text` | §6.5, §9.6, §9.7 | Text outside printable ASCII, a forbidden character, over-long text, or a disallowed APRS type |
| `looped` | §9.3, §6.5 | G = 1 frame offered to APRS-IS, or a MeshPRS-output line offered to the mesh |
| `nogate` | §9.3 | Gating field 1 or 3 |
| `test` | §9.3 | Gating field 2 on a gateway with no test server |
| `not gated` | §6.7, §7.2, §8.3 | Query, neighbour report, or telemetry kind 0x05 / 0x10 |
| `no position` | §8.1 | Weather without a position |
| `text profile` | §9.7 | Compact text frame (not gated in 1.0) |
| `untrusted` | §4.3 | Source callsign not bound |
| `no key` | §4.3 | No key prefix |
| `key mismatch` | §4.3 | Key prefix does not match the binding |
| `unknown ack` | §6.2 | Ack matching no message record |
| `replayed` | §9.3.1 | Older seq within 10 min |
| `replayed (older advert)` | profile 0 | Advert timestamp older than the last |
| `no fix` | §5.3 | Profile 0 validity check |
| `out of range` | §5.3 | Profile 0 validity check |
| `0,0` | §5.3 | Profile 0 validity check |
| `stale` | §5.3 | Profile 0 validity check |
| `duplicate` | §10.2, §6.5 | Same (identity, seq) within 10 min, or an extra APRS retry |
| `interval` | §10.1 | Per-station interval (per station and service) |
| `queue full` | §10.1 | Queue bound reached |
| `rate` | §10.1 | Global rate limit |
| `expired` | §10.1 | Not sent within 15 s of receipt |
| `addressee not heard` | §6.5 | APRS → mesh: addressee has sent no MeshPRS frame heard here in the last hour |
| `sender on mesh` | §6.5 | APRS → mesh: the APRS sender was heard on the mesh in the last hour |
| `addressee on IS` | §6.5 | APRS → mesh: the addressee was heard via APRS-IS in the last hour |
| `path excluded` | §6.5 | APRS → mesh: `TCPXX`, `NOGATE` or `RFONLY` in the path |
| `airtime` | §6.5 | APRS → mesh: over the gateway's airtime budget |
| `blocked` | §14 | Blocklist |
| `no path` | §6.5, §12.2 | APRS → mesh: no known direct path (never flooded) |
| `id clash` | §6.5 | Derived msgno already live for that addressee |

---

## 16. Open questions

### 16.1 Size summary

All figures were verified by script (Annex A). On air is from the sender with no path; add 2 bytes per SEQ hop.

The compact text columns use the node name `VK4ABC Mobile` (13 characters) on every row, with the row's own SRC. They are informative only, since compact text is not gated in 1.0 (§9.7).

| Subtype (example) | Blob N | On air | APRS info | APRS-IS line | Compact text | Text on air |
|---|---|---|---|---|---|---|
| 0x00 Position, K (required example) | 28 | 37 | 26 | 53 | 53 | 69 |
| 0x00 Position, no K | 24 | 37 | 26 | 53 | | |
| 0x00 Position, K + alt + course/speed | 26 | 37 | 36 | 65 | 65 | 85 |
| 0x01 Message, 20 characters | 36 | 53 | 33 | 60 | 60 | 85 |
| 0x01 Message, 67 characters | 83 | 101 | 80 | 107 | | |
| 0x02 Ack | 13 | 21 | 15 | 43 | 43 | 53 |
| 0x01 Message injected from APRS-IS (G = 1) | 38 | 53 | | | | |
| 0x02 Ack of the injected message | 13 | 21 | 18 | 45 | | |
| 0x03 Telemetry values | 17 | 37 | 34 | 63 | 63 | 85 |
| 0x03 Telemetry PARM | 46 | 69 | 52 | 81 | | |
| 0x04 Weather with position | 27 | 37 | 48 | 78 | 78 | 101 |
| 0x05 Object | 39 | 53 | 52 | 79 | 79 | 101 |
| 0x06 Bulletin | 38 | 53 | 38 | 65 | 65 | 85 |
| 0x07 Query, directed | 16 | 37 | 17 | 45 | | |
| 0x07 Query, `?IGATE?` | 10 | 21 | 7 | 35 | | |
| 0x08 Neighbour report, 4 entries | 26 | 37 | | | | |
| 0x09 Status | 29 | 37 | 20 | 47 | 47 | 69 |
| 0x09 Emergency with position | 32 | 53 | 46 | 73 | | |

**Text on air** is `5 + 16·⌈(5 + L)/16⌉` for L bytes of `name: text` (4-byte timestamp + 1-byte type + text; the NUL is not counted, F§1.4).

### 16.2 Decisions

Every question in [OPEN-QUESTIONS.md](../OPEN-QUESTIONS.md) is answered. The records:

| Record | Decides |
|---|---|
| 0001 | Tier A carrier: GRP_DATA on a dedicated channel, GRP_TXT compact text as fallback |
| 0002 | Subtype table |
| 0003 | Regulatory: nothing from the mesh to amateur RF in 1.0 |
| 0004 | K (key prefix) required for gating |
| 0005 | Trust lists: owner's list plus club-signed list, per gateway |
| 0006 | Profile-0 polled-telemetry exception |
| 0007 | Scope of 1.0 (required and optional subtypes) |
| 0011 | Airtime budget and rate limits |
| 0012 | Trial identifiers: `#meshprs`, data type 0xFF4D, tocall `APZKPG` |
| 0013 | Field-trial pass criteria |
| 0014 | Name |
| 0017 | Rendering gaps found while writing the vectors |
| 0018 | Interval per service |
| 0020 | 1.0 Candidate, header version 1, publication, licence and review |
| 0021 | Wire format: big-endian callsigns, 24-bit positions, 8-bit telemetry |
| 0022 | End-to-end acks; G = 1 senders shown as unverified |
| 0023 | Receive time authoritative; compact text `MPRS`, mesh-only |
| 0024 | Emergency local alert, 120 s minimum beacon interval, bulletin schedule |
| 0025 | Gateway roles and directions; deferrals |
| 0026 | No signed frames in 1.0 |

Records 0008-0010, 0015, 0016 and 0019 are about the reference implementation (Kelly Page), not the standard.

### 16.3 Future work

Left for later versions. Each one is an extension: the reserved values they would use stay reserved in 1.0.

- Gating to and from amateur RF (145.175 MHz, LoRa APRS 433.775 MHz), with its identification rules (decisions 0003, 0025).
- Signed frames or signed binding claims, and with them gating compact text (decisions 0023, 0026).
- A higher-precision position, signalled by pflags bit 7 (decision 0021).
- Wider telemetry values, and a telemetry profile registry that would enable kinds 0x05 and 0x10 (decisions 0021, 0025).
- Passing an APRS message sender's position into the mesh, and messaging between mesh islands through APRS-IS (decision 0025).
- A Room Server bulletin-agent role (decision 0024).
- A Meshtastic sister profile (decision 0025).
- A registered GRP_DATA data type and tocall (decision 0012).
- Tier B firmware features (Annex C).

---

## Annex A: Verification of the examples

Every hex dump, byte count, on-air size, APRS line length, channel key and hash in this specification was produced by one throwaway script, and every frame was decoded back (round trip). The script was run 2026-10-29 with CPython 3.14. The examples are the first entries of `test-vectors/frames.json` (§15). When the header moved to version 1, every example was checked again against those vectors on 2026-10-30, by both reference codecs (`meshprs.js` and `meshprs.py`). The script is not kept in the repository.

The script also checks:
- that every hex run printed in this document is a byte sequence of one of the frames it built;
- the M17 example `AB1CD` = `0x9FDD51`;
- that the integer rendering rules of §10.3 match floating-point rendering on 20,002 random positions;
- airtime with MeshCore's 32-symbol preamble.

Caveats:
- The node key prefix `02 F9 52 3D` and the neighbour prefixes are illustrative, not real nodes.
- The weather and object coordinates are illustrative.
- Examples without K (the message, telemetry and weather frames, among others) are shown short for clarity. Under §4.3 they would be mesh-only.
- **Seq values are illustrative.** VK4ABC's position (0x2A) and VK4ABC-9's (0x2B) both set K with one key, so they are consecutive in that key's single sequence space. VK4ABC-3's telemetry (0x2A) has no K and so has its own space.

## Annex B: Field mapping tables

| Frame field | APRS field | Conversion |
|---|---|---|
| source (header) | TNC2 source | Text as encoded; validated (§4.2) |
| (none) | destination | Tocall `APZKPG` (§11) |
| (none) | path | `qAO,IGATECALL` |
| Position lat/lon | `DDMM.mmH` / `DDDMM.mmH` | Integer rule of §10.3 (same output as Kelly `fmtLat` / `fmtLon`), with ambiguity blanking |
| Position symbol | Table and code characters | Unchanged |
| pflags MSG | DTI `!` or `=` | MSG set → `=` |
| course, speed | `ccc/sss` | §10.3: course 0 → 360; km/h → knots |
| alt | `/A=nnnnnn` | §10.3: m → feet, 6 characters |
| comment | Comment | §10.3: extension + altitude + comment ≤ 43 |
| Message addressee, msgno, text | `:ADDRESSEE:text{ID` | Addressee padded to 9; ID = decimal msgno; no `{ID` when msgno is 0 |
| Ack to, msgno, kind | `:TO       :ackID` / `rejID` | |
| Telemetry values | `T#sss,a1,…,a5,bbbbbbbb` | sss = header seq; a = 3 digits; empty slot for a missing analog |
| Telemetry kinds 1-4 | `:SRC      :PARM.` / `UNIT.` / `EQNS.` / `BITS.` | Text unchanged |
| Weather fields | `_ddd/sssgGGGtTTTrRRRpPPPPPPhHHbBBBBB` | Units per §8.1 |
| Object name, live, position, symbol, ts, comment | `;NAME_____*DDHHMMz…` / `_` | Name padded to 9; time per §8.2 (TS when within ±1 h of receive time, otherwise receive time), UTC, truncated to the minute |
| Item | `)NAME!…` / `)NAME_…` | |
| Bulletin id, group, text | `:BLNn[GROUP]:text` | Name field padded to 9 |
| Status code 8, text | `>text` | ≤ 62 |
| Status codes 0-7 and 9 | Position comment or status prefixed with the code name | §8.4 |
| Query, neighbour report | Never gated | |

## Annex C: Tier B: future work needing MeshCore firmware changes

Optional and informative. Stock companions already send binary GRP_DATA (Tier A), so Tier B covers only what the app layer cannot do:

- **RAW_CUSTOM flooding.** Stock repeaters never flood RAW_CUSTOM, and companions refuse to send it flooded (F§2.1, F§2.3). A firmware change allowing it would remove the 3-byte channel overhead and the 16-byte padding, and would be cleartext on the air. Frames would keep the §9.3 header.
- **Sender authentication in group packets.** A firmware-level sender key, or signature, on GRP_DATA, so a gateway can prove which node sent a frame (§4.3, decision 0026).
- **Persistent room-server posts.** Flash-backed posts, more than 32 slots and longer than 151 bytes, so bulletins survive reboots (§6.6; F§3.4).
- **Multipart fragmentation.** MULTIPART inner types other than ACK, for payloads larger than one frame (F§1.7). MeshPRS 1.0 deliberately needs none (§6.4).
- **Open position and telemetry.** An unencrypted, unsolicited CayenneLPP or GPS beacon type, so trackers need no app layer.
