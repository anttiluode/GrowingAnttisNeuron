# GrowingAnttisNeuron v1 — Developed Cable Physical Bridge

**Status:** approved direction. The user explicitly said “ok go” after the proposed next step: take the v0 grown anatomy, replace the deliberately crude frozen operator with AnttisNeuron-like passive compartments, and ask whether development changes mode visibility and purification cost.

## Goal

v0 established a clean developmental fact: intact chemoaffinity-style positional matching can grow a complete topographic sender→receiver map with shorter wiring, while exact receptor-label shuffling preserves connection count and bulk singular spectrum but destroys the relation.

v1 asks the next narrower question:

> When that developed connectivity is compiled into an explicit passive cable substrate, does the *placement of the developed inputs* change which physical modes are visible and how much passive time/depth is required to purify the slowest excited non-uniform mode?

The important design constraint is that receiver dendritic geometry stays fixed in v1. Therefore guided and shuffled organisms must have the same passive cable matrices. Only the sender→synapse input map is allowed to differ. A change in cable eigenvalues between those arms is a bug, not a result.

## Non-goals

v1 does **not** add free dendritic growth, conductance learning, Oja learning, AIS homeostasis, activity-dependent refinement, evolutionary search, reward, spikes, active channels, or biological units. Those remain later gates.

The purpose is to isolate the first physical bridge before adding another mechanism.

## Approaches considered

1. **Install AnttisNeuron as a dependency.** Rejected for v1 because it would couple two experimental repos operationally and make frozen reproduction more fragile.
2. **Copy AnttisNeuron’s cable module wholesale.** Rejected because most of that module concerns Gate-5 local conductance adaptation, which is intentionally out of scope.
3. **Recommended: a small native physical adapter.** GrowingAnttisNeuron gets a focused `physical.py` implementing the same passive cable mathematics needed here, but it compiles compartments directly from `DevelopmentResult`. This keeps the repo self-contained while preserving the mathematical bridge.

## Physical compilation

### Receiver compartments

Each receiver is compiled independently into one passive tree:

- node 0: receiver soma,
- nodes 1..N: the existing fixed dendritic sample points belonging to that receiver.

The tree topology is a deterministic Euclidean minimum-spanning tree over the soma and dendritic points. The MST is used only to turn the already-present geometric cloud into a connected cable without inventing a hand-tuned branch graph.

Tie breaking is deterministic by node index.

### Passive parameters

The model uses normalized physical units. Parameters are explicit and fixed in a frozen `PassiveCableConfig`.

For each dendritic child segment of length `ell`:

- membrane area is proportional to `pi * diameter * ell`, with a positive minimum segment length for numerical safety,
- capacitance is `capacitance_density * area`,
- leak conductance is `leak_density * area`,
- axial conductance is `axial_scale * diameter^2 / ell`.

The soma has a fixed positive area. No parameter depends on developmental arm or scientific outcome.

For one receiver,

`C dv/dt = -G v + B u`,

where `C` is positive diagonal and

`G = G_leak + L_axial`.

`G` is symmetric positive definite because leak is positive.

A stable discrete simulator uses implicit Euler:

`(C + dt G) v[t+1] = C v[t] + dt B u[t]`.

This gives

`A = (C + dt G)^-1 C`

and an input map

`U = (C + dt G)^-1 dt B`.

The experiment does not tune `dt`; it is a fixed integration parameter.

## Developed synapses become physical input ports

Each v0 synapse is assigned to the nearest dendritic sample point of its receiver in world coordinates. The assignment is deterministic. Current v0 synapses already record the contact coordinate, sender, receiver, weight, and axonal path length.

For modal analysis, a synaptic current injected at compartment `j` has continuous whitened forcing proportional to

`C^(-1/2) e_j * synapse_weight`.

The sender input map is therefore a consequence of development. Guided and shuffled arms use identical receiver cable physics but generally different sender→receiver/contact assignments.

Soma voltages are the bounded observations for transfer diagnostics.

## Modal analysis

Because capacitance is non-uniform, v1 does not diagonalize `G` naively. It analyzes the symmetric whitened operator

`H = C^(-1/2) G C^(-1/2)`.

This is equivalent to the generalized eigenproblem

`G phi = lambda C phi`.

The cable’s uniform voltage mode has decay `leak_density / capacitance_density` and is excluded from the purification analysis. It is identified by maximal overlap with the capacitance-weighted uniform vector rather than by eigenvector index.

Near-degenerate eigenvalues are treated as eigenspaces. Metrics must not depend on an arbitrary rotation of eigenvectors inside a degenerate subspace.

### Input-mode visibility

For a synapse at compartment `j`, initial non-uniform modal amplitudes are the projections of the whitened input vector onto the physical eigenmodes.

v1 records:

- **visible-mode effective count** — entropy effective number of non-uniform modal-energy components at injection,
- **slow target subspace decay** — the smallest decay eigenvalue among excited non-uniform modes,
- **next distinct decay gap** — the gap from that target subspace to the next faster excited eigenspace,
- **soma transfer resistance** — the DC transfer from the synaptic compartment to the receiver soma, `e_soma^T G^-1 e_j`.

### Passive purification cost

The target is the slowest *excited non-uniform eigenspace*, not a hand-selected biological feature.

For distinct non-uniform eigenspaces `r`, let initial energy be `E_r(0)`. Then

`E_r(t) = E_r(0) exp(-2 lambda_r t)`.

Purity of the slow target subspace is

`P(t) = E_target(t) / sum_r E_r(t)`.

`purification_time_95` is the smallest non-negative continuous time for which `P(t) >= 0.95`, found by a deterministic monotone bracket + bisection. If the input already exceeds 0.95, the cost is zero. If there is no non-uniform energy, the diagnostic is undefined and recorded explicitly rather than coerced to zero.

This is the many-mode physical analogue of AnttisNeuron Gate 7’s two-mode growth-to-purity calculation. It remains an oracle diagnostic, not a local developmental stopping rule.

## Scientific comparison

The canonical experiment runs the same seeds and developmental arms as v0:

- `guided`,
- `shuffled_labels`,
- `random_walk`.

The primary paired comparison remains **guided minus shuffled** because it preserves the exact molecular multisets and growth machinery while destroying only the sender↔receptor assignment.

For each arm and seed, v1 aggregates synapse-level physical diagnostics. The canonical receipt records mean/median/min/max and defined-count for each metric.

No scientific sign is required by CI.

A useful positive result would be a reproducible guided-vs-shuffled difference in input-mode visibility or purification cost despite identical passive cable spectra. A useful negative result would be that the current fixed, translation-equivalent dendritic morphology makes the physical diagnostics permutation-equivalent too. That negative would directly motivate the next experiment: heterogenous or developmentally grown dendrites.

## Required invariants and controls

Tests must prove:

1. every receiver cable is a connected tree with `n_nodes - 1` edges,
2. capacitances and conductances are finite and positive,
3. `G` is symmetric positive definite,
4. implicit-Euler `A` has spectral radius below one,
5. guided and shuffled receiver `C`, `G`, eigenvalues, and compartment geometry are exactly equal for the same seed,
6. label shuffling still does not perturb the growth-noise stream,
7. synapse→compartment assignment is deterministic and remains inside the matching receiver,
8. degenerate-subspace purity is invariant to basis rotations,
9. purification purity is monotone non-decreasing when a strictly slower target subspace is excited,
10. the frozen v1 aggregate exactly matches the canonical deterministic run.

## Files

Planned additions:

- `growing_anttis_neuron/physical.py` — cable compilation and physical diagnostics,
- `experiments/run_v1.py` — matched ensemble and receipt,
- `tests/test_physical.py` — mathematical/physical invariants,
- `tests/test_v1_receipt.py` — deterministic aggregate and frozen receipt,
- `results/v1.json` — canonical aggregate,
- `docs/RESULTS_V1.md` — interpretation including negative results,
- README v1 section.

The existing v0 development engine is not rewritten unless a test exposes a bug needed by this bridge.

## Pages

The browser microscope remains a visualization of developmental geometry. v1 will not duplicate the physical solver in JavaScript. After the Python result is frozen, the page may receive a small static v1 result panel sourced from the frozen receipt, with the existing statement that Python receipts are authoritative.

## Success boundary

v1 is complete when the developed geometry can be deterministically compiled into passive receiver cables, the input-placement modal diagnostics are frozen across the canonical ensemble, all controls are green on Python 3.11 and 3.12, and the result is documented without tuning away a null finding.
