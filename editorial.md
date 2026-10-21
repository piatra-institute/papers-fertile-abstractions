# Editorial record

Status: full read of the final manuscript completed 2026-10-21; claims, references and figures checked against the recorded run.

## Contribution and reader

For researchers in program synthesis, library learning, planning with macro-operators and computational models of concept learning. The paper answers, for bounded program-search learners with greedy library learning: how large is the effect of having an abstraction during later discovery, separately from its use as a tool; can retrospective compression, direct value or cheap frontier statistics predict it; and does the answer depend on the cost of verification. Confidence: the propositions are proved and checked by exact enumeration; the empirical answers hold for the two simulated domains and the learner as specified.

## Material worth preserving

- The early/late/no-access design with the abstraction present at evaluation in both compared conditions, and the identity V_total = V_direct + V_disc (Section 3.2, Table 1).
- Proposition 1(iii): adding a definable token strictly delays every behaviour that needs at least two tokens and has no shortest program using the new token; Figure 1 shows a single abstraction gaining and losing about 1,300 behaviours each at the experimental budget.
- Proposition 2, the symmetric construction in which history, direct uses and first-round discovery are exchanged by a relabelling and only later demands differ.
- Proposition 3 and its corollary: no budget-independent score orders abstractions correctly at every verification cost.
- The empirical pattern: discovery value larger in spread than direct value, two-signed, reliable, negatively related to direct value, weakly predicted, and strongly budget-dependent.

## Reverse outline

1. Two abstractions with the same record: the puzzle, the question, the four contributions, scope.
2. Prior work: macro-operators and the utility problem (direct value and branching cost); library learning and self-improving search (the loop exists; compute-matched evaluation; matched-state comparisons); human abstraction learning (bootstrapping, prospective compression); creativity and usable information (definable additions change access); fertility of theories (the philosophical counterpart).
3. Framework: expressibility versus accessibility with Proposition 1 and Figure 1; discovery process, compressor and the three values.
4. Constructions: separation (Proposition 2), reversal and corollary (Proposition 3), predictor ladder derived from the two observations (exchangeability, mediation through the learned set).
5. Experiments: domains and protocol; size, sign and reliability of discovery value; mechanism (descendants and redirections); predictor agreement and choice gain; verification cost.
6. Limits and interpretation: learner simplicity, what is and is not supported, results that would change the conclusion, relation to fertility of theories, practical implication.

## Strongest rival

Compression-based library learning (Stitch, babble, DreamCoder's refactoring) treats compressivity as the measure of library quality. If compressive abstractions were the fertile ones, discovery value would add nothing beyond compression and direct value. The simulations test this directly: history compression correlates with discovery value at 0.11 and 0.08 at cost 1 and at $-0.02$ in the list domain at cost 4. A second rival is that discovery value is test noise; split-half reliability (0.64 and 0.47) and the matched-pair replication across test quarters (0.57 and 0.30) rule that out for these learners. A third is that a richer learner (equivalence pruning, a learned search policy) would make compression predictive; this is not tested and is named in Section 6 as a result that would narrow the claim.

## Decisions and remaining checks

- Framing: imagination is mentioned only as scope (Section 1). The origin material's grand framing, toy uniform-sampling calculation, reproduction number and parent-removal design are not used.
- Design decisions settled on pilot worlds (other seeds): curriculum 24 families (12 reported as a check), frontier gain added, canonical evaluation order for learned tokens. The recorded run uses fresh seeds.
- Rounding corrections after binding claims: frontier gain 0.13 (not 0.14), navigation mean discovery value 0.007, 12-family direct value $-0.13$, negative share 41.8%.
- Prose: abstract shortened to about 250 words; contribution list split into numbered sentences; mechanism paragraph marked as observed in inspected worlds.
- Correction after review (2026-10-21): Proposition 1(iii) originally assumed only that adding the token leaves the description length unchanged; a shortest program using the new token can then come earlier, and the proof's claim that no same-length program containing the token precedes the old first program was false. The hypothesis now requires that no shortest program over the extended library contains the token, and the proof was rewritten. An exhaustive scan of programs up to length 4 in the list domain found 5 counterexamples to the old statement and none among 687 cases of the corrected one. Proposition 3 now states its history and derives the savings 3 and 5 used in the corollary.
- Verified: claims.yaml bound to the recorded results (all computation claims PASS), references resolve (46 entries, all cited), voice OK, build with no missing glyphs, all pages inspected.
- Source support for older classics (Fikes et al., Korf, Iba, Laird et al., Minton, Tambe et al., Markovitch and Scott, Boden, Wiggins, Ritchie, Carnap, Kuhn, Lakatos, McMullin) is checked at the level of the Crossref or Open Library record and the standard content; abstracts were not available from the APIs used. Claims citing them are restricted to that content.
