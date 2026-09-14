# GrowingAnttisNeuron

> **Grow the matrix first. Then ask what computation its physics makes possible.**

GrowingAnttisNeuron is a deliberately small developmental bridge into [AnttisNeuron](https://github.com/anttiluode/AnttisNeuron). Instead of handing a neuron system a finished connectivity matrix, v0 lets branching axons grow through a two-dimensional developmental sheet toward fixed dendritic arbors under a continuous chemoaffinity-style positional code. Synapses appear only when geometry and molecular compatibility both permit them. The anatomy is then frozen and measured as an operator.

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

The wall sentence is:

> **A tiny positional chemoaffinity code can grow a complete topographic matrix with shorter wiring; exact label shuffling preserves connection count and singular spectrum but destroys the sender↔receiver map.**

See [`docs/RESULTS_V0.md`](docs/RESULTS_V0.md) and [`results/v0.json`](results/v0.json).

## Run it

```bash
python -m pip install -e ".[test]"
pytest -q
python experiments/run_v0.py --seeds 16 --out /tmp/v0-full.json
```

The CLI emits the full deterministic per-seed receipt. `results/v0.json` freezes the canonical 16-seed aggregate used in the writeup.

CI runs Python 3.11 and 3.12, unit/invariant tests, exact control checks, the frozen aggregate regression, a JavaScript syntax check for the Pages microscope, and a scientific smoke run. No preferred scientific sign is required by CI.

## What is physical and what is still abstract

The developmental geometry is explicit: somata, dendritic sample points, growing axon branches, path length and synapse capture all exist in 2-D space. Molecular identity is represented by continuous positional coordinates rather than unique neuron IDs.

The post-development operator is still abstract. It is a stable symmetric bipartite embedding of the grown sender→receiver matrix; it does **not** yet contain compartment capacitance, leak, axial conductance, active dendritic channels, or an AIS output boundary. Those are exactly where this repo can later meet AnttisNeuron more deeply.

## Next bridge, not another pile of mechanisms

v0 establishes that we can grow a matrix under a matched developmental control. The next useful experiment is to replace the simple neuron-level frozen operator with an AnttisNeuron-like physical substrate and ask whether the *grown* geometry changes mode visibility, local adaptation, or purification cost.

Free dendritic growth, activity-dependent refinement, inherited developmental evolution, and 3-D development remain deferred until that bridge earns them.

## Project documents

- [`docs/superpowers/specs/2026-09-14-developmental-anttisneuron-design.md`](docs/superpowers/specs/2026-09-14-developmental-anttisneuron-design.md) — pre-implementation design.
- [`docs/superpowers/plans/2026-09-14-developmental-anttisneuron-v0.md`](docs/superpowers/plans/2026-09-14-developmental-anttisneuron-v0.md) — implementation plan.
- [`docs/RESULTS_V0.md`](docs/RESULTS_V0.md) — interpretation of the frozen receipt.

Experimental computational-development code; scientific failures are kept rather than tuned away.
