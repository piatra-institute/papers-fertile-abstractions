# Audit

Dated log of editorial passes and verification runs. Newest first.
See the workspace docs (run `papers docs`): writing-pipeline.md §7 and refresh-pipeline.md.

## 2026-10-21 — publication

Status set to published and PDF rebuilt (zero missing-character warnings). All 20 pages rendered at 100 dpi are pixel-identical to the inspected build; visual-review.json moved from 00d1b20c7a1f to 28ef94054040. Manuscript unchanged, so the claims ledger and editorial review still cover it. PDF synced to the website repository (public/papers), ownPapers entry added to app/papers/page.tsx (the website repository is left uncommitted for the editor), published-stage check run, GitHub repository created and initial signed commit pushed.

## 2026-10-21 — mathematical corrections after review

Scope: two mathematical fixes from review; no code change, so the recorded run (verification/model.json) stands.
Changes:
  - Proposition 1(iii): hypothesis now "no shortest program for h over L plus a contains a, and l_L(h) >= 2"; proof rewritten (pi remains the first program for h, every earlier candidate stays earlier, and the one-token program a adds positive cost); the false sentence about same-length programs containing a was dropped; the follow-on sentence in Section 3.1 now matches the hypothesis.
  - Proposition 3: history {a3b, b1a, ab} = {01233210, 32101012, 0123210} stated (as in simulation/constructions.py), with three non-overlapping occurrences each and savings 3 and 5; sets moved to displayed equations.
  - claims.yaml: new claims p1-iii and computation claims for the savings in Propositions 2 and 3 (222 claims, 156 computation), rebound to the new manuscript hash.
  - editorial.md: correction recorded.
Verification:
  - exhaustive scan (scratch, not part of the recorded run) of list-domain programs up to length 4 for four added tokens: 0 violations of corrected 1(iii) in 687 cases; 5 counterexamples to the old hypothesis.
  - claims: PASS; refs: PASS; voice: OK
  - build: 20 pages, 0 missing-character warnings
  - check --stage local => PASS

## 2026-10-21 — initial local completion

Scope: first complete version of the paper (manuscript, simulation, references, claims, records).
Changes:
  - simulation: engine (bounded search, compression, discovery), two domains (lists, maze), early/late/no-access experiment, exact constructions, analyses; recorded run verification/model.json (13/13 checks); an earlier receipt from before a figure-layout change is retained.
  - paper: Sections 1-6, Propositions 1-3 with corollary, Table 1, Figures 1-4, 46 references.
Verification:
  - voice: OK (0 editorial candidates); lint: no outliers
  - refs: PASS (46 entries, all cited)
  - claims: PASS (schema 1, bound to final manuscript hash)
  - build: 20 pages, 0 missing-character warnings
  - check --stage local => PASS
Limitations: older classics checked at the level of Crossref/Open Library records and standard content; results concern the simulated learners and worlds only.

<!--
## YYYY-MM-DD — <pass name>
Scope: <the bounded list of changes>
Changes:
  - ...
Verification:
  - voice: <errors / warns>
  - refs: <missing / unused>
  - claims: <reconciliation result>
  - build: <pages, missing-char warnings>
  - check => PASS/FAIL
-->
