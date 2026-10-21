# Fertile Abstractions

Measuring How a Learned Idea Changes Later Discovery.

A learner that searches over programs and names recurring pieces of its solutions can find that one named piece changes what it discovers afterwards. The paper defines the discovery value of an abstraction through an early-, late- and no-access design in which the abstraction is available at the final test in both compared conditions, proves that discovery value is not determined by compression of past solutions, direct usefulness or the immediate effect on search, and proves that rankings by discovery value can reverse when verification becomes more expensive, so no budget-independent score orders abstractions correctly at every cost. In 300 simulated worlds in each of two domains, list programs and navigation between rooms, discovery value is larger in spread than direct value, takes both signs and is reliable across test families; compression of past solutions barely predicts it, direct value predicts it with the wrong sign, and a costly look-ahead on the learner's own curriculum recovers about a third of the attainable benefit in one domain and little in the other. Rankings at verification costs eight times apart are nearly unrelated.

## Build

```bash
uv run build.py          # -> paper/PAPER.pdf  (vendored canonical recipe)
```

Requires `pandoc` and `xelatex` on PATH. From the workspace you can also run `papers build fertile-abstractions`.

## Simulation

```bash
cd simulation && uv run run_all.py   # -> output/results.json and output/figures/*.png, 13 checks
```

`engine.py` holds the search, compression and discovery loop; `lists.py` and `maze.py` the two domains and world generators; `experiment.py` the early/late/no-access design and predictors; `constructions.py` exact checks of the two propositions; `analyses.py` and `stats.py` the reported statistics. The recorded run is `verification/model.json`.

Part of [piatra-papers](https://github.com/piatra-institute). See the workspace docs for the research and writing pipelines.
