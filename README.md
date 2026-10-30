# MeshPRS

**An interface standard between APRS and MeshCore.** MeshPRS defines how amateur station information (positions, messages, telemetry, objects, status) is carried on a MeshCore LoRa mesh, and how gateways move it to and from APRS-IS. The rules make sure the two networks never flood, loop or duplicate each other, and that both sides' licence conditions are kept. Any gateway can implement it.

The name follows D-PRS, D-STAR's position reporting into APRS. It stands for *Mesh Position Reporting System*.

## Status: 1.0 Candidate

This is the **MeshPRS 1.0 Candidate**, open for public comment.
- The frame layout is frozen: header version 1, GRP_DATA data type 0xFF4D on the `#meshprs` channel.
- Between now and 1.0 final, changes are limited to clarifications and to fixes the field trial shows to be needed. Any change to the layout gets a decision record and is announced here.
- 1.0 final follows once:
  - the reference implementation passes every test vector;
  - the field trial meets its pass criteria (decision 0013);
  - review comments from MBUG, the APRS-IS operators and the MeshCore developers are answered.

Comments, questions and implementation reports are welcome as [issues](https://github.com/cargobike21/MeshPRS/issues) on [github.com/cargobike21/MeshPRS](https://github.com/cargobike21/MeshPRS).

## Start here

| Path | What it is |
|---|---|
| [spec/MeshPRS-Spec.md](spec/MeshPRS-Spec.md) | **The standard.** Normative, RFC 2119 style (MUST / SHOULD / MAY) |
| [spec/decisions/](spec/decisions/) | One record per decision: the context, the options and the choice made |
| [test-vectors/](test-vectors/) | Shared JSON vectors (input, then expected output or drop reason). Every implementation must pass them |
| [research/](research/) | The facts the spec relies on, with sources. [00-findings.md](research/00-findings.md) is the baseline (MeshCore 1.18.0 source, APRS 1.2, aprs-is.net, LIPD 2025) |
| [design/](design/) | Informative design notes: airtime and multi-hop delivery ([reliability.md](design/reliability.md)), the field trial ([test-plan.md](design/test-plan.md)), the reference iGate ([igate-design.md](design/igate-design.md)) |
| [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) | Every question raised so far, each with the decision that answered it |
| [PLAN.md](PLAN.md) | Phases and milestones |

## In one paragraph

A MeshCore station sends a compact binary frame (24-53 bytes on air for most services) as GRP_DATA on the `#meshprs` channel. It carries an amateur callsign in M17 base-40 encoding and, for anything to be gated, the first 4 bytes of the station's node key. A gateway gates the frame to APRS-IS only when that callsign is bound to that key in its trust lists, and every gateway renders the same frame to a byte-identical APRS-IS line, so APRS-IS's own duplicate filter merges copies. APRS-IS traffic reaches the mesh only as messages to stations heard on the mesh, sent direct and never flooded. Nothing crosses from the mesh (LIPD/ISM) to amateur RF in 1.0. Stock phone apps can read and type a human-readable text form (`MPRS ...`), which stays mesh-only.

## Implementations

- **Kelly Page** (VK4AZ): the reference implementation. A JavaScript and Python codec passing the vectors, a receive-only iGate and a position sender. Its earlier advert-based iGate is MeshPRS *profile 0*.

To list another implementation, open an issue.

Paths starting `kelly-page/` in the research and design notes (for example `kelly-page/js/igate.js`) refer to Kelly Page's source code, which is not public. They are cited so each claim can be traced to the code that proved it.

## Licence

- The specification, decision records, research and design notes are licensed under [CC BY 4.0](LICENSE). You may copy, adapt and implement them, with credit to "MeshPRS, Alec Swinton VK4AZ".
- The test vectors and code samples in [test-vectors/](test-vectors/) are dedicated to the public domain under [CC0 1.0](test-vectors/LICENSE), so any implementation can embed them freely.
