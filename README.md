# GrowingAnttisNeuron

> **Grow the matrix first. Then ask what computation its physics makes possible.**

GrowingAnttisNeuron is a deliberately small developmental bridge into [AnttisNeuron](https://github.com/anttiluode/AnttisNeuron). v0 lets branching axons grow through a two-dimensional developmental sheet toward fixed dendritic arbors under a continuous chemoaffinity-style positional code. v1 compiles those developed contacts into explicit passive receiver cables. v2 then gives receiver addresses four genuinely different passive dendritic phenotypes and asks what happens when the exact address→operator relation is shuffled while the grown anatomy is held fixed.

This is **not** a literal model of embryonic neurodevelopment and it is not evidence for a new biological growth law. It is an instrument for asking what changes when the matrix itself is a developmental product.

**Live developmental microscope:** https://anttiluode.github.io/GrowingAnttisNeuron/

## v0 in one picture

```text
continuous positional cues
          ↓
sender receptor coordinates
          ↓
branching axon growth cones ─── fixed dendritic arbors
          ↓                         ↓
          └──── proximity + compatibility
                         ↓
                      synapses
                         ↓
                  freeze anatomy
                         ↓
                 connectivity W
                         ↓
               operator diagnostics
```

There is no lifetime learning, Hebbian refinement, soma reward, GA, evolution, or activity-dependent pruning in v0. Fixed dendrites and growing axons make the first causal question identifiable.

## Controls

The important control is not “less growth.” `guided` and `shuffled_labels` use the same somata, fixed dendrites, growth grammar, seeded growth-noise generator, receptor-vector multiset and ligand-vector multiset. The shuffle changes only which sender carries which receptor vector. `random_walk` removes chemoaffinity steering while retaining the growth machinery.

A regression test explicitly proves that label shuffling itself does not consume or shift the growth-noise generator: when chemoaffinity strength is set to zero, guided and shuffled axon trajectories are byte-identical. Once chemoaffinity is active the trajectories can diverge, so later random draws need not remain event-for-event paired; v0 does not claim a pre-generated common random tape.

## Frozen v0 result — 16 seeds

| mean metric | guided | shuffled labels | random walk |
|---|---:|---:|---:|
| connections | **8.000** | **8.000** | 2.750 |
| topographic error | **0.000** | 0.359375 | 0.0625 |
| mean wiring length | **0.626367** | 0.692969 | 0.800052 |
| effective rank | 8.000 | 8.000 | 2.750 |
| spectral radius | 0.960 | 0.960 | 0.955 |
| slow-mode separation | 0.000 | 0.000 | 0.005 |

The exact-label shuffle is the useful part. Guided and shuffled both make all eight connections and both produce effective rank 8, but shuffling breaks the sender↔receiver topographic relation and costs more wire. Mean paired guided-minus-shuffled topographic error is **−0.359375** and mean wiring-length delta is **−0.066602**.

The operator spectral radius is primarily a **stability invariant** here: the bipartite block is normalized before the fixed leak/coupling transform, so any nonempty full-strength map is driven to the same top stability scale. It is not evidence that guided and shuffled have the same detailed dynamics. The more meaningful spectral fact in v0 is that identity-like and permutation-like full maps have the same singular values/effective rank. `slow_mode_separation` is also exactly zero in guided and shuffled and is retained as an honest uninformative diagnostic rather than redefined after seeing the result.

The v0 wall sentence is:

> **A tiny positional chemoaffinity code can grow a complete topographic matrix with shorter wiring; exact label shuffling preserves connection count and singular spectrum but destroys the sender↔receiver map.**

See [`docs/RESULTS_V0.md`](docs/RESULTS_V0.md) and [`results/v0.json`](results/v0.json).

## v1 physical bridge

v1 does not change the developmental grammar. Instead it asks what the grown contacts mean when the fixed receiver morphology is made physically explicit.

Each receiver is compiled into a passive soma+dendrite cable. The seven existing dendritic sample points and soma are connected by a deterministic Euclidean minimum-spanning tree. Segment area sets capacitance and leak; segment length sets axial conductance. The continuous system is

```text
C dv/dt = -G v + B u
```

and generalized cable modes are measured through the capacitance-whitened operator `C^-1/2 G C^-1/2`.

A developed synapse becomes a point-current input at the nearest dendritic compartment of its receiver. The critical control is exact: for the same seed, `guided` and `shuffled_labels` have **identical cable geometry, capacitance, conductance, system matrices and generalized eigenvalues**. Development can therefore change only the input address and its projection onto the fixed physical modes.

### Frozen v1 result — 16 seeds

| mean metric | guided | shuffled labels | guided − shuffled |
|---|---:|---:|---:|
| synapse count | 8.000000 | 8.000000 | 0.000000 |
| visible-mode effective count | 4.914812 | 4.921359 | −0.006547 |
| slow target decay | 0.120859 | 0.120859 | ≈0 |
| next decay gap | 0.003016 | 0.003016 | 0.000000 |
| purification time to 95% | 675.857100 | 679.522568 | −3.665468 |
| soma transfer resistance | 0.005213 | 0.003968 | +0.001245 |

This is a **mixed, sparse input-placement effect**, not a broad spectral advantage. The paired medians for visibility, purification time and soma transfer are essentially zero. Four of sixteen seeds (`0`, `5`, `9`, `12`) place the guided input at a physically different relative dendritic port; in those seeds the input excites slightly fewer non-uniform modes, reaches 95% slow-subspace purity about **14.6619** normalized time units sooner, and has about **0.004979** greater soma DC transfer. Most seeds remain permutation-equivalent.

The cable spectrum itself does not change: slow target decay and the next decay gap are equal by construction and control. That is the point. v1 separates **changing the physical basis** from **changing where a signal enters the basis**.

The v1 wall sentence is:

> **With identical passive dendrites, development cannot change the cable spectrum; it can only choose where the input enters that spectrum. In v1 that placement effect is sparse: four of sixteen seeds shift visibility, purification time, and soma transfer, while most seeds remain permutation-equivalent.**

See [`docs/RESULTS_V1.md`](docs/RESULTS_V1.md) and [`results/v1.json`](results/v1.json).

## v2 developmental operator codebook

v2 changes the physical basis itself, but does so in the smallest controlled way possible. Receiver somata stay fixed while dendritic offsets are scaled by one of four phenotype values:

```text
0.70, 0.90, 1.20, 1.45
```

That scaling changes segment length and membrane area, so capacitance, leak, axial conductance and the capacitance-whitened passive operator are recomputed. The four phenotype labels therefore correspond to genuinely different physical operators.

The crucial matched control is stronger than v0/v1: **one guided anatomy is grown per seed and reused exactly in both v2 arms**. Same axons. Same synapses. Same weights. Same contact coordinates. Same phenotype inventory. Only which receiver address carries which physical phenotype is changed.

`coded_operator` repeats the four-entry address→phenotype map. `shuffled_operator` permutes the exact same phenotype multiset among those receiver addresses. v2 is an oracle/calibration layer: the coded arm defines the desired operator family and therefore has perfect match by construction.

### Frozen v2 result — 16 seeds

| mean metric | coded operator | shuffled operator | coded − shuffled |
|---|---:|---:|---:|
| synapse count | 8.000000 | 8.000000 | 0.000000 |
| phenotype match fraction | **1.000000** | 0.281250 | **+0.718750** |
| normalized operator-target error | **0.000000** | 0.099527 | **−0.099527** |
| visible-mode effective count | 4.648693 | 4.610102 | +0.038591 |
| slow target decay | 0.120918 | 0.120918 | ≈0 |
| next decay gap | 0.003465 | 0.003485 | −0.000019 |
| purification time to 95% | 705.601098 | 696.050177 | +9.550921 |
| soma transfer resistance | 0.027298 | 0.029664 | −0.002366 |

The clean result is the operator relation itself: exact phenotype shuffling drops mean address/operator match from **1.0 to 0.28125** and produces **0.099527** mean normalized operator-target error without altering the grown anatomy or the phenotype inventory.

But this is not a functional win. The paired median changes in modal visibility, gap, purification time and soma transfer are essentially zero, and purification differences change sign across seeds. v2 therefore proves only that a developmental address can stand in for a physical operator family in this toy system. It does **not** show that the chosen codebook is computationally privileged.

The v2 wall sentence is:

> **A four-entry developmental address can name four genuinely different passive dendritic operators on the exact same grown network; shuffling only that address→operator relation breaks operator compatibility, but does not confer a broad purification advantage.**

See [`docs/RESULTS_V2.md`](docs/RESULTS_V2.md) and [`results/v2.json`](results/v2.json).

## Run it

```bash
python -m pip install -e ".[test]"
pytest -q
python experiments/run_v0.py --seeds 16 --out /tmp/v0-full.json
python experiments/run_v1.py --seeds 16 --out /tmp/v1-full.json
python experiments/run_v2.py --seeds 16 --out /tmp/v2-full.json
```

All three CLIs emit deterministic receipts. `results/v0.json`, `results/v1.json` and `results/v2.json` freeze the canonical 16-seed runs used in the writeups.

CI runs Python 3.11 and 3.12, unit/invariant tests, exact control checks, frozen receipt regressions, a JavaScript syntax check for the Pages microscope, and v0/v1/v2 scientific smoke runs. No preferred scientific sign is required by CI.

## What is physical and what is still abstract

The developmental geometry is explicit: somata, dendritic sample points, growing axon branches, path length and synapse capture all exist in 2-D space. Molecular identity is represented by continuous positional coordinates rather than unique neuron IDs.

v1 adds an explicit passive compartment substrate: membrane capacitance, leak, axial conductance, implicit cable dynamics, generalized decay modes, point-current synaptic inputs, soma DC transfer, and an oracle passive-purification diagnostic. v2 adds real morphological/operator heterogeneity by scaling dendritic geometry and recompiling that substrate. The parameters are normalized rather than fitted to a particular biological neuron.

Still absent are active dendritic channels, spiking, AIS dynamics, activity-dependent plasticity, reward and evolution. Most importantly, v2 still **assigns** phenotype identity through an oracle codebook. The signals do not yet cause the dendrite to become the operator it needs to be.

## Next bridge: let statistics grow the operator

v0 grew the wiring relation. v1 showed what a developed input address means inside a repeated physical basis. v2 proved that developmental identity can also be coupled to genuinely different physical bases, but its particular codebook has no broad functional advantage.

The next clean experiment therefore removes the phenotype ID. Every receiver begins physically identical. Equal-power input processes with different temporal correlation statistics drive the same local growth/shrinkage rule. The rule sees only a local voltage statistic and a fixed homeostatic setpoint—not sender ID, desired phenotype, eigenspectrum, soma reward or task loss.

The target causal chain is:

```text
signal statistics
      ↓
local dendritic voltage statistics
      ↓
local growth / shrinkage
      ↓
different morphology
      ↓
different passive operator
```

If distinct statistics reliably produce distinct frozen operators while same-statistics and temporal-order-destroyed controls collapse that diversity, then the matrix has begun manufacturing **different kinds of matrix elements** from experience rather than receiving their identities from an oracle.

## Project documents

- [`docs/superpowers/specs/2026-09-14-developmental-anttisneuron-design.md`](docs/superpowers/specs/2026-09-14-developmental-anttisneuron-design.md) — v0 pre-implementation design.
- [`docs/superpowers/plans/2026-09-14-developmental-anttisneuron-v0.md`](docs/superpowers/plans/2026-09-14-developmental-anttisneuron-v0.md) — v0 implementation plan.
- [`docs/RESULTS_V0.md`](docs/RESULTS_V0.md) — v0 interpretation.
- [`docs/superpowers/specs/2026-09-14-v1-physical-bridge-design.md`](docs/superpowers/specs/2026-09-14-v1-physical-bridge-design.md) — v1 design.
- [`docs/superpowers/plans/2026-09-14-v1-physical-bridge.md`](docs/superpowers/plans/2026-09-14-v1-physical-bridge.md) — v1 implementation plan.
- [`docs/RESULTS_V1.md`](docs/RESULTS_V1.md) — v1 interpretation.
- [`docs/RESULTS_V2.md`](docs/RESULTS_V2.md) — v2 operator-codebook calibration and its negative functional result.

Experimental computational-development code; scientific failures are kept rather than tuned away.
