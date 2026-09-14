# Developmental AnttisNeuron v0 Design

## Purpose

Build the smallest developmental substrate that can grow a neuronal connectivity matrix before AnttisNeuron-style operator measurements are applied. The experiment must separate developmental wiring from lifetime learning and from evolutionary search.

The central question is:

> Can a compact chemoaffinity-style developmental program grow structured axonal connectivity whose frozen graph has measurably different mapping and modal properties from matched random or label-shuffled controls?

This is a computational morphogenesis instrument, not a literal model of embryonic neurodevelopment.

## Scope

Version 0 contains fixed target dendritic arbors and genuinely growing branching axons. Dendrites do not remodel. There is no Hebbian refinement, no soma reward, no GA, no evolution, no activity-dependent pruning, and no learned alignment map.

The grown network is frozen before operator analysis begins.

## Developmental world

The world is a two-dimensional unit square. Somata are placed on two strips: senders on the left and receivers on the right. Each receiver owns a short fixed dendritic tree represented by line segments and sample points near its soma.

Two smooth cue fields provide positional information:

- `cue_x(x, y) = x`
- `cue_y(x, y) = y`

Each sender has a molecular receptor vector derived from its soma position. Each receiver/dendrite has a ligand vector derived from its target position. These are continuous coordinates, not unique neuron IDs.

## Axonal growth

Each sender begins with one growth cone at its soma. At every developmental step each active tip evaluates candidate directions. Candidate score is a weighted sum of:

1. chemoaffinity improvement: move toward a location whose cue vector better matches the sender receptor target,
2. local persistence: weak preference for the previous direction,
3. crowding penalty: avoid occupied axonal segments,
4. small seeded noise.

The highest-scoring legal direction is taken. Tips may branch stochastically under a fixed branch probability and branch budget. A branch inherits the sender molecular identity but receives an independent deterministic random stream.

Axons stop when their length budget is exhausted or all tips terminate.

## Synapse formation

When an axonal segment passes within `capture_radius` of a dendritic sample point, a synapse is eligible. Eligibility is accepted only when molecular compatibility exceeds `compatibility_threshold`.

Compatibility is:

`exp(-||receptor - ligand||^2 / (2 * compatibility_sigma^2))`.

At most one synapse is created for a sender-receiver pair in v0. The synapse weight is the compatibility value. This prevents geometry alone from silently turning dense contact into arbitrarily large weight.

## Controls

Every experiment uses the same somata, dendrites, branch budgets, growth noise seeds, receptor multiset, and ligand multiset.

Three arms are required:

- `guided`: intact mapping between sender receptor vectors and their developmental target coordinates.
- `shuffled_labels`: exact receptor-vector multiset is permuted across sender identities before growth. Scalar distributions are unchanged while pairing information is destroyed.
- `random_walk`: chemoaffinity term is disabled; all other growth and capture rules remain.

The primary scientific comparison is `guided` versus `shuffled_labels`; `random_walk` is a weaker structural null.

## Frozen operator

After development, construct a directed weighted neuron-level matrix `W` where `W[i, j]` is the synaptic weight from sender `i` to receiver `j`.

For operator analysis, row-normalize nonempty sender rows and define a stable recurrent block:

`A = (1 - leak) * I + coupling * S(W)`

where `S(W)` is a symmetric bipartite embedding of the sender-receiver matrix into a square matrix. Coupling is chosen so the spectral radius remains below one; the implementation must validate this rather than assume it.

Measure:

- connection count,
- mean wiring length,
- topographic error: mean absolute difference between sender normalized y-coordinate and receiver normalized y-coordinate over formed synapses,
- singular values of `W`,
- effective rank from singular-value entropy,
- spectral radius of `A`,
- slow-mode separation: difference between the two largest eigenvalue magnitudes of `A`.

No claim is made that these are yet AnttisNeuron task performance. They are developmental/operator diagnostics.

## Determinism and invariants

For a fixed seed and arm, development must be byte-for-byte deterministic at the JSON receipt level.

Required invariants:

- every axon point stays within the unit square,
- every synapse references an existing sender and receiver,
- no sender-receiver pair appears twice,
- guided and shuffled arms use identical receptor and ligand multisets,
- shuffled arm changes only sender-to-receptor assignment,
- operator spectral radius is strictly below one,
- all reported metrics are finite.

## v0 success and failure

Version 0 succeeds as an instrument if it grows nontrivial branching axons, forms synapses, produces deterministic receipts, and the shuffle is exact.

The scientific result is recorded rather than required by CI. A useful positive signal would be lower topographic error for `guided` than `shuffled_labels` across a small seed ensemble. If no such difference appears, that is retained as a developmental null rather than tuned away.

## Browser companion

GitHub Pages should show one deterministic embryo developing in real time. The page exposes arm selection (`guided`, `shuffled labels`, `random walk`), seed reset, pause/resume, and a final operator summary.

The visualization is explanatory. Scientific claims come from the Python implementation and frozen receipts, not from eyeballing the browser animation.

## Deferred work

Explicitly deferred until v0 is stable:

- free dendritic growth,
- activity-dependent stabilization/pruning,
- membrane capacitance/leak/axial conductance per dendritic compartment,
- AnttisNeuron Oja learning on the grown graph,
- Gate-7 physical purification length,
- AIS/load homeostasis,
- evolutionary mutation/selection of the developmental genome,
- 3-D development.
