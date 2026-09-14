# v0 Result — Grow the Matrix First

## Question

Can a compact chemoaffinity-style developmental program grow a structured frozen connectivity matrix, and does destroying only the sender↔molecular-label assignment change the resulting geometry?

This is a calibration of the developmental instrument, not a claim that the model captures literal embryonic neural development.

## Predeclared matched arms

- **guided** — sender positional receptor codes remain attached to their original sender positions.
- **shuffled_labels** — the exact receptor-vector multiset is permuted across sender identities. Receiver ligands, soma positions, dendrites, growth grammar, growth-noise stream, and scalar label distributions are retained.
- **random_walk** — the chemoaffinity steering term is disabled while the rest of the growth grammar remains.

The canonical receipt uses seeds `0..15`.

## Frozen receipt

| metric, mean over 16 seeds | guided | shuffled labels | random walk |
|---|---:|---:|---:|
| connections | **8.000** | **8.000** | 2.750 |
| topographic error | **0.000** | 0.359375 | 0.0625 |
| mean wiring length | **0.626367** | 0.692969 | 0.800052 |
| effective rank | 8.000 | 8.000 | 2.750 |
| spectral radius | 0.960 | 0.960 | 0.955 |
| slow-mode separation | 0.000 | 0.000 | 0.005 |

For every canonical seed, guided uses less wiring than shuffled labels. The paired guided-minus-shuffled mean wiring-length delta is **−0.066602**. The paired topographic-error delta is **−0.359375**.

## What this actually says

The intact positional code and its exact-multiset shuffle build matrices with the **same connection count, the same effective rank, and the same frozen-operator spectral radius**, yet very different geometry. Guided development produces the identity-like topographic map; shuffling produces a permutation-like map. The developmental relation is therefore visible in *which sender reaches which receiver* and in wiring cost, not in these bulk spectral diagnostics.

That is useful because it is the intended control: the amount of molecular material and the gross matrix capacity are not enough to recover the organized map.

## Important negative / limitation

`slow_mode_separation` is exactly zero for guided and shuffled. With this v0 symmetric bipartite embedding, permutation-like full-rank maps produce paired eigenvalue magnitudes, so this particular metric cannot distinguish the two arms. It is retained rather than redefined after seeing the result.

The random-walk topographic error also needs careful interpretation. Random growth forms only 2.75 accepted connections on average, and the molecular compatibility threshold strongly filters which of those contacts survive. Its low mean topographic error therefore does **not** mean random growth made a good complete map.

## Wall sentence

> **A tiny positional chemoaffinity code can grow a complete topographic matrix with shorter wiring; exact label shuffling preserves connection count and bulk spectrum but destroys the sender↔receiver map.**

## What v0 has not tested

No dendrites grow. There is no activity-dependent refinement, Hebbian rule, soma credit, Oja learning, AnttisNeuron Gate-7 purification, membrane cable biophysics, AIS adaptation, or evolution. The next useful bridge is to let the grown anatomy become a richer physical AnttisNeuron substrate rather than immediately adding all of those mechanisms at once.
