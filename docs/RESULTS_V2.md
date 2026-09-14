# v2 — developmental operator codebook

## Question

Can a cheap developmental address stand in for a family of genuinely different passive dendritic operators, and does breaking only the address→operator relation break that compatibility?

v2 is intentionally an **oracle/calibration experiment**. It does not claim that molecular labels encode eigenmodes, that the four phenotypes are biologically privileged, or that the coded arm is functionally optimal.

## Matched design

For each seed, GrowingAnttisNeuron first grows **one guided anatomy**. Both v2 arms reuse that exact same developed organism: same axons, synapses, synaptic weights, contact coordinates, receiver positions and developmental history.

The only changed object is a four-entry receiver phenotype codebook. Phenotype IDs select dendritic length scales

```text
0 → 0.70
1 → 0.90
2 → 1.20
3 → 1.45
```

Scaling is applied to dendritic offsets around a fixed soma. Because cable area, capacitance, leak and axial path length are recomputed, these are genuinely different passive operators, not labels on identical cables.

`coded_operator` repeats the phenotype sequence `0,1,2,3,...` across developmental receiver addresses. `shuffled_operator` permutes the **exact same phenotype multiset** among the same receiver addresses. The sender/receiver anatomy is not regrown.

The target phenotype for a developed synapse is the sender's developmental address modulo four. Thus the coded arm is a calibration reference: its phenotype match is 1 by construction and its normalized target-operator error is 0 by construction.

## Frozen 16-seed result

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

The controls are exact in every seed: one developed anatomy, one synapse set, and one phenotype inventory are shared between arms.

The decisive calibration result is therefore narrow and clean: an address can name a different physical operator family, and exact phenotype shuffling breaks that address→operator correspondence while leaving the developed wiring untouched. Across the 16 seeds, the shuffled arm retains only 28.125% mean phenotype match and incurs 0.099527 mean normalized operator-target error.

## What did *not* happen

The codebook did **not** produce a broad downstream physical advantage. The paired median differences in visible-mode count, next-decay gap, purification time and soma transfer are essentially zero. Purification differences even change sign across seeds, spanning roughly −195 to +195 normalized time units.

That negative result matters. The v2 phenotype map is an imposed developmental codebook, not a discovered functional law. Matching the oracle phenotype target proves that molecular/developmental identity can be coupled to physical operator identity; it does **not** prove that this particular coupling improves computation.

The slow target decay is also essentially invariant across the four scale phenotypes in this normalized passive construction. Other operator details, spectral gaps, modal visibility, purification trajectories and transfer can change, but this specific decay diagnostic does not distinguish the codebook.

## Wall sentence

> **A four-entry developmental address can name four genuinely different passive dendritic operators on the exact same grown network; shuffling only that address→operator relation drops mean phenotype match from 1.0 to 0.281 and creates 0.0995 normalized operator error, but it does not confer a broad purification advantage.**

## What v3 must remove

v3 should remove the oracle phenotype ID entirely.

All receivers should start from the same morphology. Distinct, equal-power temporal input statistics should drive a **local activity homeostat** that changes dendritic scale using only locally observable voltage statistics. If different signal statistics settle into different morphologies/operators, then operator diversity is no longer assigned by a codebook:

```text
signal statistics
      ↓
local dendritic response
      ↓
local growth / shrinkage
      ↓
different physical operators
```

The critical controls are equal input power, identical initial morphology, a same-statistics collapse condition, and a temporal-order-destroyed control. No sender ID, desired phenotype, eigenspectrum target, soma reward, GA or evolution should enter the growth rule.

Canonical receipt: [`../results/v2.json`](../results/v2.json).
