# v3 — signal-grown passive operators

## Question

Can equal-power inputs that differ only in temporal correlation make one local voltage homeostat grow initially identical fixed-lineage dendrites into different passive operators, without phenotype labels, eigenmode targets, reward, or evolution?

## Setup

v3 keeps one developed receiver morphology and freezes its dendritic branch ancestry. Geometry may scale, but the compiler is not allowed to rebuild a different minimum-spanning tree as points move.

All four signal conditions have stationary input variance `1.0`; only AR(1) correlation differs:

```text
rho = 0.0, 0.2, 0.4, 0.6
```

The local growth signal is the stationary RMS voltage at one dendritic compartment. The common setpoint is the `rho = 0` RMS at scale `1.0`:

```text
target RMS = 197.54134567771703
```

The update is multiplicative and local:

```text
relative_error = local_rms / target_rms - 1
growth_scale   = growth_scale * exp(growth_rate * relative_error)
```

The rule sees no sender identity, phenotype label, eigenspectrum, operator target, soma reward, or task loss. Generalized decay spectra and operator distance are measured only after growth.

## Result

Starting from the same scale `1.0`, the four temporal statistics converge to different morphologies:

| AR(1) correlation rho | final dendrite scale |
|---:|---:|
| 0.0 | 1.0000000000 |
| 0.2 | 1.2921115159 |
| 0.4 | 1.6690879387 |
| 0.6 | 2.2373804986 |

Higher positive temporal correlation raises local voltage RMS at the same starting morphology. Because increased dendritic scale lowers that local RMS in this passive substrate, the same homeostat grows farther until the shared setpoint is recovered.

The ordering is not a single-port accident. Across all seven dendritic compartments, local RMS at the starting morphology increased strictly with `rho` in **7/7** cases. Across the scale grid

```text
0.70, 0.85, 1.00, 1.20, 1.50, 1.80, 2.20, 2.60
```

local RMS decreased strictly with scale for every tested compartment and correlation: **28/28** compartment×correlation checks.

Because segment lengths and membrane area are recompiled after growth, the final capacitance, leak, axial conductance and capacitance-whitened passive operator change with morphology. The `rho = 0` trajectory remains exactly at the baseline operator; every positively correlated trajectory ends at nonzero operator distance from baseline.

## What v3 establishes

The causal chain now exists without an oracle phenotype codebook:

```text
temporal signal statistics
          ↓
local dendritic voltage statistic
          ↓
one local homeostatic rule
          ↓
different morphology
          ↓
different passive operator
```

The wall sentence is:

> **Equal-power streams that differ only in temporal correlation can drive the same local voltage homeostat to grow identical starting dendrites into different passive operators; in this canonical receiver the ordering holds at all seven dendritic ports.**

## What it does not establish

This is still a deliberately narrow mechanism test. The morphology has one scalar scale parameter rather than independently growing branches. The input is stationary AR(1), the cable is passive and linear, and the setpoint is calibrated from the `rho = 0` baseline. There is no spiking, AIS, task loss, semantic computation, reward, or evidence that the resulting operators are computationally better.

In particular, v3 does **not** yet prove that a dendrite discovers an optimal memory timescale, that morphology performs useful mode purification, or that the mechanism improves an AI task. It establishes the missing causal bridge: local temporal statistics can manufacture operator diversity from a common starting substrate without a phenotype label.

The deterministic implementation is `experiments/run_v3.py`; CI checks Python 3.11/3.12, the local-homeostasis invariants, the all-port robustness counts, and the v3 scientific smoke run.
