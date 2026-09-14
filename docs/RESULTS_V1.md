# v1 Result — Developed Inputs on Passive Cables

## Question

When the v0 developed synapses are compiled as input ports onto explicit passive receiver cables, does intact positional guidance change physical-mode visibility or passive purification cost relative to exact receptor-label shuffling?

v1 is deliberately narrower than a full neuron model. The receiver soma and seven existing dendritic sample points are compiled into a deterministic passive tree with capacitance, leak, and axial conductance. Development chooses the synaptic input port. No dendrites grow, no conductances learn, and no AIS or active channels are present.

## The decisive control

For a given seed, `guided` and `shuffled_labels` have **exactly the same receiver cable geometry and passive physics**. Tests require equality of compartment positions, tree edges, capacitances, axial conductances, system matrices, and generalized decay eigenvalues.

Across the canonical 16 seeds, the receptor multiset, ligand multiset, and receiver-cable physics controls are all exact.

This means v1 cannot honestly attribute a guided-vs-shuffled difference to a changed cable spectrum. Any difference must come from **where the developed synapse injects current into that fixed spectrum**.

## Frozen 16-seed receipt

| mean metric | guided | shuffled labels | guided − shuffled |
|---|---:|---:|---:|
| synapse count | 8.000000 | 8.000000 | 0.000000 |
| visible-mode effective count | 4.914812 | 4.921359 | −0.006547 |
| slow target decay | 0.120859 | 0.120859 | ≈0 |
| next decay gap | 0.003016 | 0.003016 | 0.000000 |
| purification time to 95% | 675.857100 | 679.522568 | −3.665468 |
| soma transfer resistance | 0.005213 | 0.003968 | +0.001245 |

The paired medians tell the other half of the story. The median guided-minus-shuffled differences in visible-mode count, purification time, and soma transfer are essentially zero. The mean shifts are driven by four seeds (`0`, `5`, `9`, and `12`) in which guidance places an accepted input at a different relative dendritic port than the shuffle. In those seeds, guidance excites slightly fewer non-uniform modes, reaches 95% slow-subspace purity about **14.6619 normalized time units sooner**, and has about **0.004979** greater soma DC transfer.

The other canonical seeds are permutation-equivalent for these physical diagnostics up to floating-point noise.

## Interpretation

This is a **mixed, sparse input-placement effect**, not a broad spectral advantage.

The passive operator itself is unchanged. The slowest excited non-uniform decay and the next distinct decay gap are the same in guided and shuffled because the receiver morphology and passive parameters are the same. What development can change in this v1 setup is the forcing vector: which cable compartment receives the synaptic current and therefore how strongly that current projects onto the fixed physical eigenspaces.

The result is therefore a concrete version of the distinction we wanted to expose:

```text
same physical basis + different developed input address
                    ↓
        different modal coefficients
                    ↓
 sometimes different visibility / purification / soma transfer
```

But the effect is not yet general. The receiver morphologies are repeated, fixed, and nearly translation-equivalent. Most exact-label permutations therefore land on physically equivalent ports.

## The negative result matters

v1 does **not** show that chemoaffinity guidance generally improves passive purification. The median paired effect is zero. It also does not show that development changes the cable eigenvalues; the experiment was constructed so that it cannot.

That null structure is useful. It says the next experiment should not tune leak, axial conductance, or the purity threshold until a preferred sign appears. The more direct missing degree of freedom is morphology itself: heterogeneous or developmentally grown dendrites would allow development to alter the physical basis rather than merely choose an address within a repeated basis.

## Random-walk arm

`random_walk` forms only 2.75 accepted synapses on average, with one canonical seed forming none. Its physical metrics are consequently defined for 15/16 seeds and vary much more strongly. As in v0, that arm is a secondary failure/control condition rather than the clean causal comparison, because sparse contact and molecular acceptance strongly select which random inputs survive.

## Purification diagnostic

The v1 purification metric is an oracle physical diagnostic, not a biological learning or growth signal. The capacitance-whitened generalized modes are grouped into near-degenerate eigenspaces, the spatially uniform voltage mode is removed, and the target is the slowest excited non-uniform eigenspace. `purification_time_95` is the continuous passive time required for that eigenspace to carry at least 95% of the remaining non-uniform modal energy.

The units are normalized. The purpose is comparative structure, not a claim about a particular neuron's milliseconds.

## Wall sentence

> **With identical passive dendrites, development cannot change the cable spectrum; it can only choose where the input enters that spectrum. In v1 that placement effect is sparse: four of sixteen seeds shift visibility, purification time, and soma transfer, while most seeds remain permutation-equivalent.**

## What v1 has not tested

No dendrites grow. There are no active channels, spiking dynamics, AIS adaptation, Hebbian/Oja learning, activity-dependent refinement, reward, or evolution. The clean next bridge is to let receiver morphology become heterogeneous or developmental and ask whether development can then reshape the physical eigenspaces themselves.

The exact frozen data are in [`../results/v1.json`](../results/v1.json).
