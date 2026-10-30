# 0020: Publish as the 1.0 Candidate, wire version 1, on GitHub under CC BY 4.0

- **Status:** accepted
- **Date:** 2026-10-30
- **Answers:** OPEN-QUESTIONS Q13 (review); also how and where to publish
- **Spec sections affected:** title block, §9.3 (version), §15, §16; README, PLAN, LICENSE

## Context

No standard for APRS over MeshCore exists, and Alec's own projects need one now. PLAN.md puts 1.0 after Phase 4 (Kelly passes every vector) and Phase 5 (field trial), and neither is done. Other people need a fixed layout to build to, and a licence that lets them.

## Options

1. **1.0 Candidate:** publish now, with the byte layout frozen and open for comment. It becomes 1.0 final after the trial, with clarifications only in between.
2. **1.0 final now:** quickest, but every fix the trial finds would need a new version.
3. **Draft 0.9:** the layout may still change, so fewer people would build to it.

For the header version: give the Candidate version 1 now, or stay on version 0 until 1.0 final.

Venue: a public GitHub repo, the MBUG wiki, or both. Licence: CC BY 4.0 with CC0 vectors, CC BY-ND 4.0, or CC0 throughout.

## Decision

Decided by Alec, 2026-10-30, taking the recommended option on each point:
- Publish as the **MeshPRS 1.0 Candidate**, with the frame layout frozen.
- Candidate frames carry header **version 1**. Version 0 (Draft 0.1) has the same layout, and receivers MAY accept it until 1.0 final.
- Publish in a **public GitHub repository of its own**, holding only the MeshPRS material, with issues open for comment. P25X and Kelly Page stay private.
- **Licence:** the spec, decision records and research notes under CC BY 4.0; the test vectors and code samples under CC0 1.0.
- **Review (Q13):** before 1.0 final, ask three groups:
  - MBUG, about the `#meshprs` channel and the SEQ settings;
  - the APRS-IS / aprs2.net operators, about the tocall (`APZKPG`, decision 0012) and the use of `qAO`;
  - the MeshCore developers, about the 0xFF4D data type and registering a value later.

## Consequences

- **Between the Candidate and 1.0 final** only clarifications and fixes the trial shows to be needed. Any change to the byte layout needs a decision record, and it is announced in the repository.
- **Version 1** changes every frame's first byte (`00` becomes `40`): the worked examples, the test vectors and both codecs.
- **1.0 final** needs:
  - every vector passed;
  - the trial criteria of decision 0013 met;
  - the three reviews asked for and answered or closed;
  - Alec's sign-off.
