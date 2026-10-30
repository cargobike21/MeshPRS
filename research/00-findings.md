# MeshPRS Phase 0 findings

Verified facts that the MeshPRS design relies on. These notes are informative; the spec (`spec/MeshPRS-Spec.md`) is normative. Anything not confirmed is marked **UNVERIFIED**.

**MeshCore source:** github.com/meshcore-dev/MeshCore, commit `81dbae592ffad40b4212bc0b37e82b38da08f4bc` (2026-10-15). The tags `repeater-v1.18.0`, `companion-v1.18.0` and `room-server-v1.18.0` point at this same commit, so the 1.18.0 build running on the SEQ mesh is identical to main. Paths are relative to the MeshCore root.
**APRS spec:** APRS 1.2 draft C (`APRS12c.pdf`, WB2OSZ, github.com/wb2osz/aprsspec). It merges APRS101 with the 1.1 and 1.2 addenda and keeps APRS101's chapter and page numbers, so "Ch14 p.71" below is the same in both. aprs.org itself is behind Cloudflare.
**Fetched:** 2026-10-29.

---

## 1. MeshCore packet format

### 1.1 Header and framing

On the wire a packet is `[header 1][transport_codes 4, only for route types 0 and 3][path_len 1][path][payload]` (src/Packet.cpp:52-63, src/Dispatcher.cpp:148-189).

**Header byte** `0bVVPPPPRR` (src/Packet.h:8-12):

| Bits | Field | Notes |
|---|---|---|
| 0-1 | Route type | |
| 2-5 | Payload type | |
| 6-7 | Payload version | Only V1 (`0`) exists. A higher version is dropped on receive (Dispatcher.cpp:152) |

**path_len byte** (Packet.h:84-88):

| Bits | Field | Notes |
|---|---|---|
| 0-5 | Hop count | 0-63 |
| 6-7 | Hash size − 1 | 1, 2 or 3 bytes; the value `11` is rejected |

The path takes count × size bytes and must be ≤ 64 (`MAX_PATH_SIZE`). SEQ uses 2-byte hashes (MBUG `path.hash.mode 1`).

The source and destination hashes and the channel hash inside the payload are always **1 byte**, whatever the path hash size (`PATH_HASH_SIZE 1`, src/MeshCore.h:18).

**Transport codes** are only present on the TRANSPORT_* route types.
- `code[0]` = HMAC-SHA256(regionKey, type‖payload), truncated to 2 bytes. A public `#region` key is `sha256(name)` (src/helpers/TransportKeyStore.cpp:4-47).
- `code[1]` is always 0 for now.

### 1.2 Limits (src/MeshCore.h)

| Constant | Value |
|---|---|
| `MAX_PACKET_PAYLOAD` | 184 |
| `MAX_PATH_SIZE` | 64 |
| `MAX_TRANS_UNIT` | 255 |
| `CIPHER_BLOCK_SIZE` | 16 |
| `CIPHER_MAC_SIZE` | 2 |
| `MAX_ADVERT_DATA_SIZE` | 32 |

A payload larger than 184 bytes is dropped on receive (Dispatcher.cpp:180-183).

### 1.3 Type constants (src/Packet.h:14-32)

**Route types**

| Value | Name |
|---|---|
| 0x00 | TRANSPORT_FLOOD |
| 0x01 | FLOOD |
| 0x02 | DIRECT |
| 0x03 | TRANSPORT_DIRECT |

**Payload types**

| Value | Name | Value | Name |
|---|---|---|---|
| 0x00 | REQ | 0x08 | PATH |
| 0x01 | RESPONSE | 0x09 | TRACE |
| 0x02 | TXT_MSG | 0x0A | MULTIPART |
| 0x03 | ACK | 0x0B | CONTROL |
| 0x04 | ADVERT | 0x0C-0x0E | reserved |
| 0x05 | GRP_TXT | 0x0F | RAW_CUSTOM |
| 0x06 | GRP_DATA | | |
| 0x07 | ANON_REQ | | |

### 1.4 Maximum application bytes per candidate carrier

| Carrier | Plaintext layout | Max app bytes | Source |
|---|---|---|---|
| **GRP_DATA** | `data_type u16 LE, data_len u8, blob` | **165-byte blob** | `MAX_GROUP_DATA_LENGTH = 184−16−3`; MeshCore.h:21, BaseChatMesh.cpp:544-555 |
| GRP_TXT | `ts u32, txt_type u8, "name: text"\0` | **160 bytes, including the `name: ` prefix** | `MAX_TEXT_LEN 160`; BaseChatMesh.h:8, .cpp:518-531 |
| TXT_MSG (DM) | `ts u32, flags u8, text` | 160 | BaseChatMesh.cpp:453 |
| RAW_CUSTOM | raw bytes | 184; the companion requires at least 4 | Mesh.cpp:590; companion MyMesh.cpp:1563 |
| ADVERT app_data | `flags, [lat i32, lon i32], [feat1], [feat2], name` | 32 in total; a name can be 31 bytes, or 23 when lat/lon is included | Mesh.cpp:405; AdvertDataHelpers.cpp:4-29 |

**On-air size of a GRP_DATA packet carrying an N-byte blob:**

`1 (header) + 1 (path_len) + path + 1 (channel hash) + 2 (MAC) + 16·⌈(N+3)/16⌉`

Padding means the blob size grows in steps. These are the sizes that use the full space at each step:

| Blob N | Ciphertext | Payload | On air with no path yet (sender) |
|---|---|---|---|
| ≤ 13 | 16 | 19 | 21 |
| ≤ 29 | 32 | 35 | 37 |
| ≤ 45 | 48 | 51 | 53 |
| ≤ 61 | 64 | 67 | 69 |

Each repeater a flood passes through adds one path hash: 2 bytes per hop in SEQ.

**GRP_TXT length.** The 160-byte `MAX_TEXT_LEN` covers the `name: ` prefix plus the text and excludes the NUL. The NUL is written into the buffer, but the datagram length is `5 + prefix_len + text_len` (BaseChatMesh.cpp:519-531). The receiver relies on the zero padding of the last AES block to terminate the string.

**LoRa preamble.** 32 symbols at SF ≤ 8, 16 above: `preambleLengthForSF(sf) { return sf <= 8 ? 32 : 16; }` (src/helpers/radiolib/RadioLibWrappers.h:56, applied at RadioLibWrappers.cpp:30). At the MBUG setting of SF8 that is 32 symbols, the figure to use in time-on-air calculations.

The companion serial link carries a received channel-data blob of up to 167 bytes (`MAX_CHANNEL_DATA_LENGTH = 176−9`, companion MyMesh.cpp:106), so a 165-byte blob fits.

### 1.5 Encryption (src/Utils.cpp:85-175)

- **Cipher:** AES-128 in ECB mode, with the last block zero-padded.
- **MAC:** encrypt-then-MAC. HMAC-SHA256 over the ciphertext, truncated to 2 bytes and placed before the ciphertext.
- **ECB weakness:** under one key, identical 16-byte plaintext blocks produce identical ciphertext blocks. This is our own analysis, not something the source says.

**What travels in the clear:**

| Payload type | Clear fields |
|---|---|
| GRP_TXT / GRP_DATA | 1-byte channel hash: the first byte of `sha256(PSK)`, BaseChatMesh.cpp:918 |
| TXT_MSG / REQ / RESPONSE / PATH | 1-byte destination hash and 1-byte source hash. The key is the ECDH shared secret |
| ADVERT | The whole packet. It is signed (Ed25519, 64-byte signature) but **not encrypted** |
| ACK | The whole packet (a 4-byte CRC) |
| CONTROL | The whole packet |
| RAW_CUSTOM | The whole packet: "for applications with custom encryption" (Packet.h:32) |

**Channel keys:**
- The **Public** channel PSK is `izOH6cXN6mrJ5e26oRXNcg==`, which is hex `8b3387e9c5cdea6ac9e5edbaa115cd72` (companion MyMesh.cpp:114; MBUG publishes it too).
- A **hashtag** channel key is the first 16 bytes of `sha256("#name")`. The phone app derives it; the firmware only ever takes a PSK (docs/companion_protocol.md:461-468).
- So every channel is encrypted, but the Public and hashtag channels use keys anyone can work out.

### 1.6 GRP_DATA data-type registry (docs/number_allocations.md)

| Range | Use |
|---|---|
| 0000-00FF | MeshCore internal. `0x0000` is reserved and rejected |
| 0100-FEFF | Apps. Allocated by pull request, and a working app must be shown first |
| **FF00-FFFF** | **Free for development, no registration needed.** `0xFFFF` = `DATA_TYPE_DEV` |

Apps that already hold a 0100-FEFF allocation include MeshCore Open, Ripple, MCO Advanced, StreamSensor and Nelos.

### 1.7 MULTIPART is not general fragmentation

Byte 0 is `remaining<<4 | inner_type`. The only inner type implemented is ACK, used for the multi-ACK repeats (Mesh.cpp:300-322 and 574-587, with the comment "FUTURE: other multipart types??").

**No MeshCore payload type gives an application fragmentation.** MeshPRS must do its own, or avoid needing it.

---

## 2. Stock repeater forwarding (the key result)

`Mesh::onRecvPacket` (src/Mesh.cpp:41) checks the route type first, then the payload type. A direct packet whose path count is greater than 0 is forwarded by a generic next-hop branch that never looks at the payload:

```
Mesh.cpp:89   if (self_id.isHashMatch(pkt->path, pkt->getPathHashSize()) && allowPacketForward(pkt)) {
Mesh.cpp:102    if (!_tables->wasSeen(pkt)) { _tables->markSeen(pkt); removeSelfFromPath(pkt);
Mesh.cpp:106      return ACTION_RETRANSMIT_DELAYED(0, d);  // Routed traffic is HIGHEST priority
```

Flood packets reach the payload switch, and only the cases that call `routeRecvPacket` (Mesh.cpp:344-347) are flooded on:

```
Mesh.cpp:225  case PAYLOAD_TYPE_GRP_DATA:
Mesh.cpp:226  case PAYLOAD_TYPE_GRP_TXT: { ...
Mesh.cpp:248      action = routeRecvPacket(pkt);      // regardless of whether this node knows the channel
Mesh.cpp:292  case PAYLOAD_TYPE_RAW_CUSTOM: {
Mesh.cpp:293      if (pkt->isRouteDirect() && !_tables->wasSeen(pkt)) { ... onRawDataRecv(pkt);
Mesh.cpp:296      //action = routeRecvPacket(pkt);    don't flood route these (yet)
```

The repeater's `searchChannelsByHash` is the base stub that returns 0 (Mesh.cpp:37). **A repeater floods channel packets it cannot decrypt.**

### 2.1 What a stock repeater forwards

| Payload | Flood / transport flood | Direct (this node is next hop) |
|---|---|---|
| **RAW_CUSTOM** | **Never.** A flood RAW_CUSTOM isn't even handled locally (Mesh.cpp:292-296) | Yes (Mesh.cpp:89-106) |
| **GRP_DATA** | **Yes, without decrypting** (Mesh.cpp:225-248) | Yes |
| GRP_TXT | Yes, the same as GRP_DATA | Yes |
| TXT_MSG | Yes, unless the repeater is itself the destination (Mesh.cpp:133-193) | Yes |
| ACK | Yes | Yes, rebuilt with the optional extra ACKs (Mesh.cpp:93-99, 379) |
| MULTIPART | No (Mesh.cpp:318 is commented out) | Only when the inner type is ACK (Mesh.cpp:359-376) |
| ADVERT | Yes, if the signature is valid and hops < `flood.max.advert` (default 8) | Yes; seldom used |
| TRACE / CONTROL | No (the default case, Mesh.cpp:326-328) | TRACE yes; CONTROL 0x80 is zero-hop only |

### 2.2 Gates on forwarding

All of these are in `allowPacketForward`, examples/simple_repeater/MyMesh.cpp:434-459.

**Both route types:**
- `set repeat off` (`disable_fwd`) stops all forwarding.

**Flood only:**
- **Hop limits.** Hops ≥ `flood.max` (default 64), or `flood.max.unscoped` (64), or `flood.max.advert` (8) stop the packet (RoutingPolicy.h:15-22; MyMesh.cpp:906-908).
- **Path space.** `(n+1)·hash_size ≤ 64`. With SEQ's 2-byte hashes that is about 32 hops.
- **Unknown region.** A TRANSPORT_FLOOD whose region code is unknown is **not forwarded** (MyMesh.cpp:440). A code of 0 is the wildcard.
- **Loop detect** (default MINIMAL): the packet is dropped if this node's own hash already appears in the path 4 times (1-byte hashes), 2 times (2-byte) or 1 time (3-byte).

**Direct only:**
- The packet must not be in the seen-table.
- This node's hash must be the next hop.

### 2.3 Originating each carrier from a companion

**RAW_CUSTOM**
- Sent with `CMD_SEND_RAW_DATA` (25) as `[path_len][path][payload ≥ 4]`, and always sent direct.
- Flood is refused: "flood, not supported (yet)" (companion MyMesh.cpp:1557-1576).
- It has **no destination field**. Every node within range of the last hop delivers it, on a companion as `PUSH_CODE_RAW_DATA`.
- The sender must already know an explicit path.

**GRP_DATA**
- Sent with `CMD_SEND_CHANNEL_DATA` (62). Path value `0xFF` means flood; a real path means direct (companion :1198-1237).
- Data type `0x0000` is rejected.

**Flood scope (this settles the disagreement between SA-1 and SA-2)**
- The companion scopes a flood with its default scope key unless the app asks for unscoped (MyMesh.cpp:502-522).
- That key stays empty unless the build defines `DEFAULT_FLOOD_SCOPE_NAME` or the app sets one with `CMD_SET_DEFAULT_FLOOD_SCOPE` (63).
- No stock variant defines it, so floods go out **unscoped by default**.
- **UNVERIFIED:** whether the phone apps set a default scope.

### 2.4 Timing, priority and duplicates (inputs to the reliability analysis)

**Receive delay**
- An SNR-weighted rx delay exists, but `rx_delay_base = 0` turns it off by default (MyMesh.cpp:542-545, 892).

**Retransmit delay** (MyMesh.cpp:547-554, 893-894)
- `random(0, 5·t + 1)` ms, uniform, where `t = airtime(packet) × factor`.
- The factor is 0.5 for floods and 0.3 for direct.
- No SNR term.

**Queue priority**
- Direct relay is 0, the highest.
- Flood relay is the hop count, so priority falls with distance (Mesh.cpp:354).

**Airtime budget**
- `airtime_factor` defaults to 1.0, which is about 50% duty cycle over a 1-hour window (Dispatcher.cpp:26, 173).
- Transmission waits while the radio is receiving: retries every 120-480 ms, forced after 4 s.

**Duplicate suppression** (src/helpers/SimpleMeshTables.h:9; Packet.cpp:41-50)
- A ring of 160 entries, each holding the first 8 bytes of `SHA-256(payload_type ‖ payload)`.
- **Route bits, path and transport codes are not hashed.**
- So a packet that arrives by flood and again by direct is a duplicate, and so is one that arrives by two different paths.
- So are two *different* transmissions whose payload bytes happen to be identical.
- **Consequence for MeshPRS:** every frame needs a field that changes from one send to the next (a sequence number or timestamp). Without it, a repeated beacon is silently dropped. Because GRP_DATA is encrypted with ECB under a fixed channel key, the plaintext must differ for the ciphertext to differ.

---

## 3. Existing MeshCore features to reuse

### 3.1 Positions

**Adverts carry the only open (unencrypted) position.**
- Encoding: `ADV_LATLON_MASK 0x10`, int32 × 1e-6 degrees (AdvertDataHelpers.h:14).
- The node's `advert_loc_policy` decides what is sent (CommonCLI.cpp:170-181): `NONE`, `SHARE` (live GPS) or `PREFS` (a fixed position).
- An advert carries no course, speed or altitude.
- Adverts flood at most 8 hops by default.
- MBUG asks repeaters to send a flood advert only every ~3.5 days (`flood.advert.interval 83`).

**Positions from telemetry**
- Telemetry can carry a GPS fix (CayenneLPP `addGPS`, lat/lon/alt), but only inside an encrypted REQ/RESPONSE.

**Nothing else**
- No separate "share location" message type exists in the firmware.
- **UNVERIFIED:** whether the phone app has one of its own.

### 3.2 Telemetry: CayenneLPP

The request is `REQ 0x03 GET_TELEMETRY_DATA` and the reply is `[sender_ts 4][CayenneLPP]`. Code: repeater MyMesh.cpp:240-259, room server :181-198, sensor SensorMesh.cpp:148-162, companion MyMesh.cpp:641-680.

**What a reply contains:**
- Always channel 1: battery voltage.
- Channel 1 again: the MCU temperature, if the board supports it.
- Optional, behind permission bits (SensorManager.h:6-10):
  - `LOCATION` (0x02): GPS.
  - `ENVIRONMENT` (0x04): temperature, humidity, pressure, altitude, voltage, current, power and so on, on channels 2 and up (EnvironmentSensorManager.cpp:249-530).

**Who can ask:**
- Repeaters and room servers require a login. A guest gets the base data only.
- A companion answers any contact, filtered by its own per-node permission settings.

**Sensor firmware extras:**
- `GET_AVG_MIN_MAX` (0x04).
- `SUBSCRIBE` (0x08): the sensor pushes a reading when a value moves past a set change threshold (SensorMesh.cpp:213-240 and 1042-1065).
- Alerts sent with an ACK (`sendAlert`).

Every telemetry request and reply is **end-to-end encrypted**. Kelly already parses LPP (`kelly-page/js/meshcore.js:214-229`).

### 3.3 Repeater status, neighbours and discovery

**`GET_STATUS` (0x01)**
- Requires a login; a guest login is enough.
- Returns: battery mV, transmit queue length, noise floor, last RSSI and SNR, rx/tx counters, flood/direct counters, duplicate counters, tx and rx airtime, uptime and error counters (simple_repeater/MyMesh.h:44-61).

**`GET_NEIGHBOURS` (0x06)**
- Requires a login. A guest login looks to be enough, but that is **UNVERIFIED on air**.
- Returns `[pubkey prefix][heard secs ago u32][snr×4 i8]` for each neighbour (MyMesh.cpp:276-370).
- Only **zero-hop adverts from other repeaters** are recorded, so companions never appear.
- The list lives in RAM and is only compiled in when `MAX_NEIGHBOURS` is set.
- Kelly already parses it (`meshcore.js:237-238`).

**Open discovery: `CONTROL NODE_DISCOVER_REQ` (0x80)**
- Zero-hop, sent in the clear, no login needed.
- Each repeater that hears it answers `DISCOVER_RESP`, carrying **the SNR at which it heard the request** and its key.
- Limited to 4 answers per 2 minutes (MyMesh.cpp:786-860).

### 3.4 Room servers (examples/simple_room_server)

**Storage**
- A RAM ring of **32 posts**, each up to **151 bytes**. Longer text is truncated silently (MyMesh.h:68-90; MyMesh.cpp:57-62).
- **Posts are lost on reboot**: `memset` runs at startup (MyMesh.cpp:690). Only the ACL and prefs are saved to flash.
- **32 clients** at most (ClientACL.h:44-45).

**Login** (MyMesh.cpp:328-354)
- Sent as `ANON_REQ [ts][sync_since][password]`.
- Admin password: admin.
- Room password: read and write.
- Wrong password with `allow_read_only` on: guest, which can read but not post.
- Otherwise: no reply at all.

**Delivery** (MyMesh.cpp:1000-1040)
- Round-robin, one post per client at a time. Each post is a **TXT_MSG sent direct to that client**, encrypted with the client's shared secret, and waits for its ACK.
- ACK timeout: 4 s + 2 s per hop when a path is known, 12 s when the post is flooded.
- A client is skipped after 3 failed deliveries.
- One push every 1.2 s.
- A client's `sync_since` moves forward when it ACKs.

**For MeshPRS bulletins**
- The model fits: each bulletin is stored once and each subscriber gets one ACKed copy.
- The cost: airtime grows as clients × posts, the post limits above apply, and posts don't survive a reboot.
- An iGate would post a bulletin either as an ordinary room client or through the admin `room.post` system post (MyMesh.cpp:977).

### 3.5 Structured data in channel text

There is no community convention in the MeshCore source or docs for structured data inside channel text.

---

## 4. APRS and APRS-IS rules

### 4.1 Line format and callsigns (aprs-is.net/Connecting.aspx; aprsc source)

**Line format**
- TNC2 `SRC>DEST,PATH:info`, ending CR/LF.
- At most 512 bytes including CR/LF. aprsc enforces `PACKETLEN_MAX 512`.

**Callsigns**
- Alphanumeric, uppercase, at most 9 characters.
- One hyphen, then a **1-2 character alphanumeric SSID**. `-0` is not allowed.
- The base callsign is at least 3 characters.
- **Non-AX.25 SSIDs** such as `-AB` are legal on APRS-IS, but some Yaesu radios won't reply to them.
- RF needs a numeric SSID from 0 to 15.
- The source inside a third-party `}` header can be any 1-9 printable characters (Ch17 p.84).

### 4.2 q-constructs (aprs-is.net/q.aspx, IGateDetails.aspx)

A client may only generate **qAR** or **qAO**.

**qAO** is the receive-only iGate construct, and q.aspx explicitly names translated, non-APRS sources: *"translated packets where the station is not APRS capable (e.g. D-STAR station transmitting GPS strings translated via D-PRS spec to APRS by the IGate)."* **This is the basis for MeshPRS using qAO.**

**Path rules**
- iGates must not modify paths except to append `,qAR/qAO,IGATECALL`.
- q-constructs never go on RF.

**Packets not to gate to IS**
- Packets with TCPIP, TCPXX, NOGATE or RFONLY in the path.
- `}` packets whose inner header contains TCPIP.
- `?` queries.

aprsc drops NOGATE and RFONLY packets itself.

### 4.3 Login and testing

**Login line**
- `user CALL-SS pass NNNNN vers NAME VER filter ...`
- The gateway logs in with its own unique call-SSID.

**Passcode**
- The algorithm is not published officially (AE5PL). The common open-source hash is what `kelly-page/js/igate.js` uses.

**Unverified logins**
- **An unverified (`pass -1`) login cannot send.** The packets are dropped (aprsc `disallow_unverified = 1`), so it is not a test sandbox.

**Ports and hosts**
- Use port 14580 (user filter).
- Oceania host: `aunz.aprs2.net`. `rotate.aprs2.net` also works.

**Testing**
- **No official test server was found (UNVERIFIED that one exists).**
- `srvr.aprs-is.net:8080` is documented "for testing", but its traffic goes onto the live network.
- **Recommended test bed:** a private aprsc instance with no uplink.

### 4.4 TOCALL (github.com/aprsorg/aprs-deviceid)

**Experimental use**
- The experimental range is `APZ???`, with no registration needed.
- **`APZKPG` is unallocated today.**
- APZ calls already taken: APZ18, APZ186, APZ19, APZ247, APZG??, APZMAJ, APZMDR, APZTKP, APZWKR.

**Getting an official allocation**
- Open an issue on the aprs-deviceid repo, about a week's turnaround.
- Protocol converters and published software qualify.
- The precedent is `APM2A?`, "Meshtastic to APRS (mesh2aprs)", class `daemon`.

### 4.5 Formats (APRS12c)

**Data type identifier** (Ch6 p.23)

| | No timestamp | Timestamp |
|---|---|---|
| No messaging | `!` | `/` |
| Messaging | `=` | `@` |

Only zulu `DDHHMMz` timestamps should be transmitted.

**Uncompressed position** (Ch8 p.32-33)
- `!DDMM.mmN/DDDMM.mmE$comment`.
- Comment: 43 characters, or 36 after a course/speed or PHG extension.
- Altitude goes in the comment as `/A=nnnnnn` (feet).

**Compressed position** (Ch9 p.37-40)
- Always 13 characters: `/YYYYXXXX$csT`, base91 (ASCII − 33).
- Latitude: `380926·(90−lat)`. Longitude: `190463·(180+lon)`.
- The `cs` pair carries one of:
  - course `c·4` with speed `1.08^s − 1` knots
  - range (when `c` is `{`)
  - altitude `1.002^(c·91+s)` feet (when the GGA bits are set in T).

**Messages** (Ch14 p.71-73)
- `:ADDRESSEE:text{ID`, with the addressee padded to 9 characters.
- Text up to 67 characters, with no `{`.
- The ID is 1-5 alphanumerics; replies are `ack`/`rej` + ID.
- Reply-ack form: `{MM}AA`. **UNVERIFIED:** whether each half is limited to 2 characters.

**Bulletins** (Ch14 p.74-75)
- General: `:BLNn     :`.
- Announcement: `:BLNx     :` (a letter instead of a digit).
- Group: `:BLNnGROUP:` (group name up to 5 characters).
- Text up to 67 characters.

**Objects and items** (Ch11 p.58-59)
- Object: `;NAME_____*DDHHMMz<pos>`, a 9-character name with `*` for live or `_` for killed. Always timestamped.
- Item: `)NAME!<pos>` (`_` for killed). APRS12c marks items "not recommended".

**Status** (Ch16 p.80)
- `>text`: up to 62 characters, or 55 with a timestamp.

**Telemetry** (Ch13 p.68-70)
- `T#sss,a1,a2,a3,a4,a5,bbbbbbbb`. Decimal values are accepted.
- `PARM.`, `UNIT.`, `EQNS.` (a·v² + b·v + c, × 5) and `BITS.bbbbbbbb,Title` are sent as messages addressed to the station's own call.
- Base91 comment telemetry `|ss11…|`: values 0-8280, still "experimental" (he.fi/doc/aprs-base91-comment-telemetry.txt).

**Weather** (Ch12 p.65-66)
- `_` symbol, then `ddd/sss` (wind direction/speed), then:
  - `g` gust (mph)
  - `t` temperature (°F)
  - `r` / `p` / `P` rain: last hour, last 24 h, since midnight (hundredths of an inch)
  - `h` humidity (%, `00` = 100%)
  - `b` pressure (tenths of hPa, 5 digits)
  - optional `L`/`l` luminosity, `s` snow, `#` raw rain counter.
- Missing values are written as dots or spaces.

### 4.6 Duplicates and gating the other way (IS → RF)

**APRS-IS duplicate filter** (aprsc `dupecheck.c`)
- 30 s window.
- The hash covers source, destination (without its SSID) and the info field. **The path is not hashed.**
- So the same packet arriving through several iGates is a duplicate, which is good for MeshPRS. The catch is that a genuine repeat of identical info within 30 s is dropped too.

**Local duplicate checking at the iGate**
- No rule on aprs-is.net. It is common practice (Dire Wolf, aprx).

**IS → RF gating** (IGateDetails.aspx, IGating.aspx)

A message goes to RF only if all of these hold:
- the receiver was heard on RF recently ("within 1 hour (or less)");
- the sender was not heard on RF;
- the path has no TCPXX, NOGATE or RFONLY;
- the receiver was not heard via the internet.

After that, pass the sender's *next* position on to RF too.

**UNVERIFIED:** numeric IS → RF rate limits. aprs-is.net gives none; Dire Wolf's `IGTXLIMIT` is the usual reference.

**Third-party format on RF**
- `IGATE>APRS,PATH:}FROM>TO,TCPIP,IGATE*:data`, with q-constructs stripped.
- **Open point:** APRS12c Ch17 p.83 says the outer destination should be the gateway's own `APxxxx`, while aprs-is.net's example uses `APRS`.

**`?IGATE?` query**
- The iGate answers `<IGATE,MSG_CNT=n,LOC_CNT=n`.

---

## 5. Australian regulatory constraints

### 5.1 The LIPD class licence on 915-928 MHz

**The LIPD Class Licence 2015 has been repealed.** The instrument in force is the **Radiocommunications (Low Interference Potential Devices) Class Licence 2025, F2025L01047**, from 2025-09-05. Reference: legislation.gov.au/F2025L01047/latest/text.

The band appears in three items:

| Item | Device class | Max EIRP | Condition |
|---|---|---|---|
| Sch 1 item 20 | Any transmitter | 3 mW | none |
| Table 8 item 1 | Frequency hopping | 1 W | at least 20 hop channels (cl 39) |
| Table 8 item 6 | Digital modulation | 1 W | power spectral density ≤ 25 mW per 3 kHz (cl 43) |

- **LoRa** on a single 62.5 kHz channel (SF8, CR5) most likely falls under **item 6**. That is **UNVERIFIED**: "digital modulation transmitter" isn't defined and LoRa isn't named. Industry practice (LoRaWAN AU915) treats it as item 6.
- **The PSD limit may bind narrow LoRa.** Spread flat, 25 mW per 3 kHz × 62.5 kHz ≈ 520 mW (27 dBm). How it is measured is **UNVERIFIED**.
- **There is no duty-cycle limit** in 915-928 MHz, unlike the EU's 1% / 10%.
- Encryption is allowed and no callsign is required.
- s7 Note 4: an antenna other than the one supplied may breach the conditions.

### 5.2 Amateur Stations Class Licence 2023 (F2023L01648)

**Bands**
- **There is no amateur allocation in 915-928 MHz.** Schedule 2 goes from 430-450 MHz straight to 1240-1300 MHz.
- A MeshCore node at 923 MHz is therefore never an amateur station, even when a licensed amateur runs it (Interpretation Determination 2025, F2025L00362: an amateur station "operates on amateur frequencies").
- The one overlap is 433.05-434.79 MHz, where LIPD item 19 (25 mW) sits inside the amateur band. **UNVERIFIED:** which authorisation applies to a given transmission there.

**Encryption**
- s13(2)(d)(iv) bans signals "encoded, for the purpose of obscuring the meaning".
- The only exceptions (s13(3)) are space station control, control of an unattended amateur station, and emergency services operations and training.

**Identification**
- s12(1): the callsign at the start and end of every transmission and at least every 10 minutes.

**Purpose**
- s13(1) allows operation for an "amateur purpose" only.
- The Interpretation Determination, "intercommunication" Note 1: *communication between a station in the amateur service and a station that is not in the amateur service is not intercommunication.*
- There is no explicit third-party traffic clause.
- s13(2)(a) and (d) ban financial gain and advertising.

**Unattended operation**
- s13(4) requires a computer-controlled or automatic mode **and** a timer that shuts the transmitter down after 10 minutes of unintended transmission.

**Repeaters**
- s13(2)(b): an "amateur repeater station" needs an apparatus licence, not the class licence.
- A repeater is defined as receiving radio signals from an amateur station *and* retransmitting them automatically.
- An RF → RF digipeater probably counts. A transmitting iGate fed from the internet or the mesh arguably doesn't. **UNVERIFIED:** how ACMA and the WIA treat either in VK.

**Retransmitting content from non-amateur LIPD users on 145.175 MHz**
- Not expressly banned, but hard to fit under "amateur purpose" given intercommunication Note 1.
- **UNVERIFIED and legally untested.** The conservative reading is: only plaintext, only from verified amateur callsigns, and identified by the gateway's own callsign.

### 5.3 APRS-IS

- No ACMA instrument governs what goes into an internet network.
- The amateur-only rule is **APRS-IS policy**: passcodes exist "to aid in keeping APRS-IS restricted to amateur radio use only" (Connecting.aspx).
- "Any special gating to RF should be done with the utmost consideration of the effect to other Amateurs" (IGating.aspx).

### 5.4 Airtime guidance

**MBUG** (wiki.mbug.com.au/en/Meshcore/Settings, updated 2026-08-23)
- Sets 923.125 MHz, 62.5 kHz bandwidth, SF8, CR5.
- Sets `path.hash.mode 1`, `multi.acks 1` and `flood.advert.interval 83` ("if anyone wants to avoid floods, it's Brisbane").
- Asks for no floods on #Public.
- Gives **no numeric airtime budget.**

MeshPRS must set its own budget.

### 5.5 Candidate rules (SA-5's recommendations, not decisions)

| # | Rule |
|---|---|
| R1 | Gate to APRS-IS only packets carrying a valid callsign, through a passcode-verified gateway, marked qAO. Never gate anonymous LIPD users |
| R2 | Gate only callsigns the gateway has bound to a mesh public key, for example through a node-name offer or a signed claim |
| R3 | Never gate DMs or private-channel content. Gate only adverts and the MeshPRS channel, and only on the originator's opt-in |
| R4 | To amateur RF: plaintext only, only from a verified amateur callsign, third-party format, gateway callsign as source, no commercial content |
| R5 | A gateway transmitting unattended on amateur RF must meet s13(4) |
| R6 | No APRS RF → mesh → APRS RF chains without a repeater apparatus licence |
| R7 | APRS-IS → mesh is legal under LIPD, but must be rate-limited to a per-gateway airtime budget, never flood #Public, and honour NOGATE/RFONLY |
| R8 | Cite LIPD 2025, not 2015, and note the clause 43 PSD point |

---

## 6. What this means for the Tier A carrier

| Option | Floods on stock repeaters? | Verdict |
|---|---|---|
| **RAW_CUSTOM** | **No.** It only travels direct, needs a known source route, has no destination, and companions refuse to flood it | Unusable for beacons, and for anything sent to "whatever iGate is nearby". It might suit iGate ↔ known-node unicast, but GRP_DATA direct does that too |
| **GRP_DATA on a dedicated channel** | Yes, without decrypting; also direct-routable | **The only binary carrier that stock repeaters will flood.** Blob up to 165 bytes, sized in 16-byte steps; data types FF00-FFFF free for development |
| **GRP_TXT, compact APRS text** | Yes | Works with stock phone apps, and people can read it. The cost is the `name: ` prefix inside a 160-byte limit and a self-asserted sender. Bytes are higher than binary but still well under 160 for a position |
| ADVERT | Yes, up to 8 hops | Already carries an open position, but only 32 bytes of app data, and MBUG limits its rate. Kelly's iGate already reads it ("version 0") |

**Constraints any choice must handle:**
- Each frame needs a field that changes on every send, or the duplicate table drops repeats (§2.4).
- MeshPRS has to fragment for itself or avoid it (§1.7).
- Channel encryption is AES with a published key. That is fine on LIPD, but the content must be sent to amateur RF only as decoded plaintext (§5.2).
- Region-scoped floods die at any repeater that doesn't know the region (§2.2), so MeshPRS should flood unscoped, or with a region every SEQ repeater carries.
