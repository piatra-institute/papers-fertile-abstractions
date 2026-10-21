# Brief

## Question

When does learning an abstraction change what a bounded program-searching learner discovers next, by how much, and can that change be predicted from what the learner knows when it adopts the abstraction?

## Claim

1. Adding an abstraction defined from existing primitives never changes what can be expressed; it changes which behaviours a bounded search reaches, adding some and removing others.
2. The discovery value of an abstraction can be isolated by an early-, late- and no-access design in which the abstraction is present at the final test in both compared conditions; total value decomposes into direct value plus discovery value.
3. Discovery value is not determined by retrospective compression, frequency, direct value or first-round frontier statistics (constructed separation), and two abstractions can exchange their order by discovery value when verification cost rises, so no budget-independent score orders abstractions correctly at every cost.
4. In random simulated worlds, discovery value is large, two-signed and reliable; retrospective compression barely predicts it; a look-ahead on the learner's own curriculum predicts it partly in one domain and weakly in another; rankings change strongly with verification cost.

## Kind

Formal model with propositions and a simulation study in two domains. has_simulation: true; claims bound to simulation/output/results.json from the recorded run (verification/model.json) and to checked sources in claims.yaml.

## Strongest alternative

Library learning that selects abstractions by compression of past solutions is good enough: compressive abstractions are the fertile ones, and discovery value adds nothing beyond compression and direct utility. The simulations test this directly.

## Cornerstone literature

Macro-operators and the utility problem (Fikes, Hart and Nilsson; Korf; Iba; Laird, Rosenbloom and Newell; Minton; Tambe, Newell and Rosenbloom; Markovitch and Scott; Botea et al.; Sutton, Precup and Singh; Jong, Hester and Stone; Solway et al.). Universal search and self-improving solvers (Solomonoff; Levin; Schmidhuber OOPS and PowerPlay; Baxter). Library learning (Dechter et al.; Ellis et al. DreamCoder; Bowers et al. Stitch; Cao et al. babble; Cropper; Berlot-Attwell et al.). Self-improving agents (Wang et al. MetaSkill-Evolve; Feng et al. HMED). Human abstraction learning (Piantadosi, Tenenbaum and Goodman; Lake et al.; Zhao, Lucas and Bramley; Hernandez Cano et al.; Lieder and Griffiths). Creativity and novelty (Boden; Wiggins; Ritchie; Espírito Santo et al.; Schmidhuber; Tria et al.; Xu et al.). Fertility of theories (Carnap; Kuhn; Lakatos; McMullin).

## Discipline

Results are about the simulated learners and worlds. All world and learner parameters are assumptions; design and predictor definitions were settled on pilot worlds with other seeds before the recorded run. No claim about imagery, people or deployed systems.
