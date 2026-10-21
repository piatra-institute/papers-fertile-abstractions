# Research

Findings, tiered by source proximity. See the workspace docs (`papers docs`): research-pipeline.md §2.
T1 primary · T2 authoritative secondary · T3 reference · T4 general web (leads only).
A claim that reaches the paper rests on a T1 or T2 source.

## Findings

### Corrections and checks of the origin material

- The four 2026 items named in the origin material exist and match their descriptions (checked 2026-10-21): arXiv 2605.09985 (Hernandez Cano et al., Prospective Compression in Human Abstraction Learning, submitted 11 May 2026, under review at NeurIPS 2026), arXiv 2607.05297 (Wang et al., MetaSkill-Evolve, 6 July 2026), arXiv 2610.07979 (Feng et al., HMED, 6 October 2026), and EACL 2026 long paper 163 (Berlot-Attwell, Sesterhenn, Rudzicz and Si), pp. 3534-3568, DOI 10.18653/v1/2026.eacl-long.163.
- The origin material's toy calculation (uniform sampling, $b^\ell$ attempts) is replaced in the paper by exact length-lexicographic enumeration with per-candidate cost; Proposition 1 states the corresponding exact bounds.
- The origin material's parent-removal design is not used; the paper adopts the early/late/no-access design in which the abstraction is present at evaluation in both compared conditions.
- The origin material's "imaginative reproduction number" is not used.
- Zhao, Lucas and Bramley appeared online in 2023; the issue is Nature Human Behaviour 8(1):125-136, 2024, cited as 2024.
- Lieder and Griffiths, Behavioral and Brain Sciences 43, e1, published online 2019, cited as 2020.
- Jong, Hester and Stone 2008: abstract checked on the authors' publication page; standard ways of adding temporal abstraction help only in limited contexts, linked to exploration.
- Levin 1973: record checked via Math-Net.ru listing (English translation Problems of Information Transmission 9(3):265-266; Russian original pp. 115-116).
- Dechter et al. 2013: IJCAI 2013 proceedings index, pp. 1302-1309.

### Primary sources (T1), what each supports

- [T1] Fikes, Hart, Nilsson 1972, AI 3:251-288: generalized plans (macro-operators) in STRIPS. Crossref.
- [T1] Korf 1985, AI 26:35-77: macro-operators as a weak method; macro tables for permutation puzzles. Crossref.
- [T1] Iba 1989, ML 3:285-317: heuristic discovery and filtering of macro-operators. Crossref.
- [T1] Laird, Rosenbloom, Newell 1986, ML 1:11-46: chunking in Soar. Crossref.
- [T1] Minton 1990, AI 42:363-391: the utility problem quantified. Crossref.
- [T1] Tambe, Newell, Rosenbloom 1990, ML 5:299-348: expensive chunks. Crossref.
- [T1] Markovitch and Scott 1993, ML 10:113-151: information filtering, selection mechanisms. Crossref.
- [T1] Botea et al. 2005, JAIR 24:581-621: Macro-FF; abstract read.
- [T1] Sutton, Precup, Singh 1999, AI 112:181-211: options. Crossref.
- [T1] Solway et al. 2014, PLoS Comput Biol 10:e1003779: optimal behavioural hierarchy; abstract read.
- [T1] Solomonoff 1964, Information and Control 7:1-22; Levin 1973; Schmidhuber 2004 (OOPS, abstract read), 2013 (PowerPlay, abstract read), 2010 (formal theory of creativity, abstract read); Baxter 2000 (abstract read).
- [T1] Dechter et al. 2013 (IJCAI); Ellis et al. 2021 (PLDI, abstract read) and 2023 (Phil Trans A, abstract read); Bowers et al. 2023 (PACMPL 7 POPL, abstract read: library quality measured by compressivity); Cao et al. 2023 (babble, abstract read); Cropper 2020 (AAAI, abstract read).
- [T1] Berlot-Attwell et al. 2026 (EACL): abstract read on the ACL Anthology; gains vanish or reverse once compute is accounted for; no evidence of direct reuse of LEGO-Prover's learned lemmas.
- [T1] Wang et al. 2026 and Feng et al. 2026: arXiv abstracts read.
- [T1] Piantadosi, Tenenbaum, Goodman 2016 (abstract read); Lake et al. 2015 (summary read); Zhao, Lucas, Bramley 2024 (abstract read: four experiments, n = 570); Hernandez Cano et al. 2026 (arXiv abstract read); Lieder and Griffiths 2020 (abstract read).
- [T1] Boden 1998, Wiggins 2006, Ritchie 2006 (Crossref records; standard content); Espírito Santo, Wiggins, Cardoso 2024 (arXiv abstract read); Tria et al. 2014 (abstract read); Xu et al. 2020 (arXiv abstract read).
- [T1/T2] Carnap 1950 (requirements for an explicatum, ch. I §3), Kuhn 1977 (five characteristics of a good theory), Lakatos 1970 (progressive problem shifts), McMullin 1976 (fertility of theory): identities checked; content standard.
- [T1] Udupa et al. 2013, Albarghouthi, Gulwani, Kincaid 2013, Gulwani, Polozov, Singh 2017: enumerative synthesis with observational-equivalence pruning; cited for the limitation that our search does not prune.
- [T1] Sutton 1990 (Dyna); Rissanen 1978 (MDL).

### Computations (this paper)

- Propositions 1-3 proved in text; Propositions 2 and 3 verified by exact enumeration in simulation/constructions.py (checks separation_matched, separation_differs, reversal_high_order, reversal_low_order).
- Simulation (recorded run verification/model.json, 13 checks): 300 worlds per domain, 8 candidates per world, discovery verification costs 1, 2, 4, 8; 12-family curriculum check in the list domain.
- Pilot: worlds from numpy default_rng(seed), seeds 0-39, used to settle design (curriculum enlarged from 12 to 24 families; frontier gain added; canonical evaluation order added). The recorded run uses default_rng([20261021, seed]).
