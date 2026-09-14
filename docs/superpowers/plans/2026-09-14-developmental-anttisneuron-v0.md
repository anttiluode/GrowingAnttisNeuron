# Developmental AnttisNeuron v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic 2-D developmental testbed where fixed dendrites are contacted by branching axons guided by chemoaffinity-style fields, then freeze the grown connectivity and measure its operator properties against exact label-shuffle and random-walk controls.

**Architecture:** A pure-NumPy Python reference implementation owns the scientific model and metrics. A small experiment CLI writes deterministic JSON receipts for matched arms and seed ensembles. A dependency-free GitHub Pages companion reimplements only the visual growth rules for exploration and labels itself explanatory rather than evidentiary.

**Tech Stack:** Python 3.11+, NumPy, pytest, static HTML/CSS/JavaScript, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-14-developmental-anttisneuron-design.md`

## Global Constraints

- Fixed dendritic target arbors; only axons grow in v0.
- No lifetime learning, Hebbian refinement, GA, evolution, soma reward, or activity-dependent pruning.
- `guided`, `shuffled_labels`, and `random_walk` use matched developmental conditions; guided vs shuffled preserves exact receptor/ligand multisets.
- Scientific deltas are recorded but never required positive by CI.
- Frozen operator spectral radius must be strictly below one.
- Browser visualization is explanatory; Python receipts are authoritative.

---

### Task 1: Developmental geometry and deterministic axon growth

**Files:**
- Create: `pyproject.toml`
- Create: `growing_anttis_neuron/__init__.py`
- Create: `growing_anttis_neuron/development.py`
- Create: `tests/test_development.py`

**Interfaces:**
- Produces: `DevelopmentConfig`, `Neuron`, `DendritePoint`, `AxonBranch`, `Synapse`, `DevelopmentResult`, `make_world(seed, config)`, `develop(seed, arm, config)`.
- Consumes: NumPy only.

- [ ] **Step 1: Write failing deterministic-development tests**

Test that `develop(seed=7, arm="guided")` is deterministic, all points remain in `[0,1]^2`, synapse pairs are unique, and the generated world contains the configured sender/receiver counts.

- [ ] **Step 2: Run `pytest tests/test_development.py -q` and confirm import/implementation failure**

- [ ] **Step 3: Implement minimal world, fixed dendrites, branching growth cones, cue matching, capture and synapse formation**

Use candidate headings `[-60,-30,0,30,60]` degrees relative to current heading; candidate score is `chemo_weight * affinity_improvement + persistence_weight * cos(turn) - crowding_weight * crowding + noise_weight * N(0,1)`. Clip only by rejecting candidate endpoints outside the unit square. Branch decisions use the per-seed RNG and respect `max_branches_per_sender`.

- [ ] **Step 4: Re-run Task-1 tests to green**

- [ ] **Step 5: Commit the task**

### Task 2: Exact controls and frozen-operator diagnostics

**Files:**
- Create: `growing_anttis_neuron/operator.py`
- Create: `tests/test_operator.py`
- Modify: `growing_anttis_neuron/development.py`

**Interfaces:**
- Consumes: `DevelopmentResult`.
- Produces: `connectivity_matrix(result)`, `operator_metrics(result, config)`, `receipt_for_seed(seed, config)`.

- [ ] **Step 1: Write failing control/operator tests**

Tests must prove guided and shuffled arms have identical sorted receptor vectors and ligand vectors, shuffled changes at least one sender assignment for the canonical seed, `W` has the expected shape, metrics are finite, and `spectral_radius < 1.0`.

- [ ] **Step 2: Run focused tests and confirm failure**

- [ ] **Step 3: Implement exact receptor reassignment for `shuffled_labels`, chemo term removal for `random_walk`, bipartite symmetric operator embedding, topographic error, wiring length, singular values, entropy effective rank, spectral radius, and slow-mode separation**

The symmetric embedding is `[[0, W], [W.T, 0]]`. Scale by its spectral radius before applying `A=(1-leak)I+coupling*S_scaled` so stability is explicit and deterministic.

- [ ] **Step 4: Re-run focused tests to green**

- [ ] **Step 5: Commit the task**

### Task 3: Ensemble experiment and frozen receipt

**Files:**
- Create: `experiments/run_v0.py`
- Create: `results/v0.json`
- Create: `tests/test_v0_receipt.py`

**Interfaces:**
- Consumes: `receipt_for_seed`.
- Produces: CLI `python experiments/run_v0.py --seeds 16 --out results/v0.json` and deterministic aggregate JSON.

- [ ] **Step 1: Write failing receipt/aggregate tests**

Require arm summaries for all three controls, exact seed count, finite aggregates, deterministic JSON structure, and receipt equality for the canonical seed list.

- [ ] **Step 2: Run focused tests and confirm missing experiment/receipt failure**

- [ ] **Step 3: Implement ensemble aggregation**

Report mean/median connection count, topographic error, mean wiring length, effective rank, spectral radius, slow-mode separation, and paired guided-minus-shuffled deltas. Include an interpretation string saying positive scientific deltas are not CI requirements.

- [ ] **Step 4: Generate `results/v0.json` from seeds `0..15` and freeze it**

- [ ] **Step 5: Re-run receipt tests to green and commit**

### Task 4: GitHub Pages developmental microscope

**Files:**
- Create: `index.html`
- Create: `site.js`
- Create: `site.css`

**Interfaces:**
- Standalone browser UI with no build step.
- Arm selector values exactly `guided`, `shuffled_labels`, `random_walk`.

- [ ] **Step 1: Build the static page shell and explanatory copy**

Show the developmental sheet, somata, fixed dendritic targets, growing axon branches, synapses, and a compact operator-metric panel. State prominently that Python receipts are authoritative.

- [ ] **Step 2: Implement deterministic seeded browser growth**

Use a tiny local PRNG, the same cue/compatibility equations and the same candidate-turn set as Python. Include reset-with-seed, pause/resume, single-step, and arm selector controls.

- [ ] **Step 3: Add end-state metrics and visual legend**

Display connection count, topographic error, mean path length, and a small connectivity matrix heatmap. Do not claim spectral metrics from the browser unless computed directly.

- [ ] **Step 4: Add a smoke test by ensuring page assets are plain static files referenced with relative paths**

- [ ] **Step 5: Commit the task**

### Task 5: CI, documentation, and verification

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`
- Create: `docs/RESULTS_V0.md`

**Interfaces:**
- CI matrix: Python 3.11 and 3.12.

- [ ] **Step 1: Add CI running editable install, `pytest -q`, and `python experiments/run_v0.py --seeds 4 --out /tmp/v0-smoke.json`**

- [ ] **Step 2: Expand README with mechanism, controls, run commands, Pages link, and interpretation rules**

- [ ] **Step 3: Write `docs/RESULTS_V0.md` from the frozen receipt without overstating the result**

- [ ] **Step 4: Verify all tests and scientific smoke runs pass on both Python versions**

- [ ] **Step 5: Compare implementation against the design spec; record any deferred items explicitly rather than silently implementing them**

- [ ] **Step 6: Commit and prepare the branch for integration**
