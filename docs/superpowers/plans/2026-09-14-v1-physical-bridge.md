# GrowingAnttisNeuron v1 Physical Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile each developed receiver into an explicit passive cable and measure how developmentally chosen synaptic input placement changes physical-mode visibility and passive purification cost.

**Architecture:** Keep v0 development unchanged. Add a self-contained `physical.py` that converts fixed receiver soma+dendrite geometry into deterministic passive trees with non-uniform capacitance, leak, and axial conductance; developed synapses become input ports. Analyze the capacitance-whitened generalized modes and aggregate synapse-level diagnostics in a deterministic v1 receipt.

**Tech Stack:** Python 3.11+, NumPy only, pytest, GitHub Actions, static GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-09-14-v1-physical-bridge-design.md`

## Global Constraints

- No dependency on the AnttisNeuron package; v1 remains self-contained.
- No free dendritic growth, conductance learning, Oja learning, AIS homeostasis, activity-dependent refinement, evolutionary search, reward, spikes, or active channels.
- Receiver cable matrices are arm-independent; guided vs shuffled may differ only through developed input placement.
- Use the generalized/whitened eigenproblem, not a naive eigendecomposition of `G` when capacitance is non-uniform.
- Treat near-degenerate eigenvalues as eigenspaces for purity metrics.
- No preferred scientific sign is required by CI.
- Python receipts are authoritative; JavaScript must not reimplement the physical solver.

---

### Task 1: Passive cable compiler and mathematical invariants

**Files:**
- Create: `growing_anttis_neuron/physical.py`
- Create: `tests/test_physical.py`

**Interfaces:**
- Consumes: `DevelopmentResult`, `DendritePoint`, and `Synapse` from `growing_anttis_neuron.development`.
- Produces:
  - `PassiveCableConfig` dataclass.
  - `ReceiverCable` dataclass with `receiver`, `positions`, `edges`, `capacitance`, `conductance`, `system_matrix`, `step_matrix`, and `soma_index`.
  - `compile_receiver_cable(result: DevelopmentResult, receiver: int, config: PassiveCableConfig | None = None) -> ReceiverCable`.
  - `whitened_modes(cable: ReceiverCable) -> tuple[np.ndarray, np.ndarray]`, returning ascending decay eigenvalues and orthonormal whitened eigenvectors.

- [ ] **Step 1: Write failing cable-structure tests**

Add tests that develop seed 0 guided and assert, for every receiver:

```python
cable = compile_receiver_cable(result, receiver)
assert cable.positions.shape == (8, 2)
assert cable.edges.shape == (7, 2)
assert len({tuple(sorted(edge)) for edge in cable.edges.tolist()}) == 7
assert np.all(cable.capacitance > 0.0)
assert np.all(np.linalg.eigvalsh(cable.system_matrix) > 0.0)
assert np.max(np.abs(np.linalg.eigvals(cable.step_matrix))) < 1.0
```

Also assert the graph is connected by a small test helper that floods from node 0.

- [ ] **Step 2: Run the focused test and confirm RED**

Run: `pytest tests/test_physical.py -q`

Expected: collection/import failure because `growing_anttis_neuron.physical` does not exist.

- [ ] **Step 3: Implement deterministic geometry and passive matrices**

Implement `PassiveCableConfig` with fixed normalized defaults:

```python
@dataclass(frozen=True)
class PassiveCableConfig:
    diameter: float = 0.018
    soma_area: float = 0.020
    capacitance_density: float = 1.0
    leak_density: float = 0.12
    axial_scale: float = 0.0025
    min_segment_length: float = 1e-3
    dt: float = 0.05
    degeneracy_rtol: float = 1e-8
    excitation_tol: float = 1e-12
    purity_target: float = 0.95
```

Validate every field as finite and positive, with `0 < purity_target < 1`.

For one receiver, positions are `[receiver soma, receiver dendrite points in their existing tuple order]`. Build a deterministic Euclidean MST by Kruskal: enumerate all `i < j`, sort by `(distance, i, j)`, and union until `n-1` edges are selected.

Root the tree at soma node 0 only to assign each non-soma compartment an area. For child `j` with parent segment length `ell`:

```python
area[j] = np.pi * diameter * max(ell, min_segment_length)
C[j, j] = capacitance_density * area[j]
G_leak[j, j] = leak_density * area[j]
g_axial = axial_scale * diameter**2 / max(ell, min_segment_length)
```

Use `soma_area` for node 0. Accumulate axial conductance into a symmetric weighted Laplacian. Define `G = G_leak + L_axial` and implicit-Euler

```python
A = np.linalg.solve(C + dt * G, C)
```

Store the diagonal capacitance as a vector and `G` as `system_matrix`.

- [ ] **Step 4: Implement generalized modes**

Use

```python
inv_sqrt_c = np.diag(1.0 / np.sqrt(cable.capacitance))
H = inv_sqrt_c @ cable.system_matrix @ inv_sqrt_c
values, vectors = np.linalg.eigh(H)
```

Validate symmetry and return ascending values/vectors.

- [ ] **Step 5: Run focused tests and commit**

Run: `pytest tests/test_physical.py -q`

Expected: PASS.

Commit message: `feat: compile developed dendrites into passive cables`

---

### Task 2: Developed synapse placement and basis-invariant mode diagnostics

**Files:**
- Modify: `growing_anttis_neuron/physical.py`
- Modify: `tests/test_physical.py`

**Interfaces:**
- Produces:
  - `SynapsePhysicalMetrics` frozen dataclass.
  - `synapse_compartment(result: DevelopmentResult, synapse: Synapse, cable: ReceiverCable) -> int`.
  - `synapse_physical_metrics(result: DevelopmentResult, synapse: Synapse, config: PassiveCableConfig | None = None) -> SynapsePhysicalMetrics`.
  - `purification_time(decays: np.ndarray, energies: np.ndarray, *, purity_target: float, degeneracy_rtol: float, excitation_tol: float) -> float | None`.

- [ ] **Step 1: Write failing placement/control tests**

Add tests that:

```python
guided = develop(seed=3, arm="guided")
shuffled = develop(seed=3, arm="shuffled_labels")
for receiver in range(len(guided.receivers)):
    cg = compile_receiver_cable(guided, receiver)
    cs = compile_receiver_cable(shuffled, receiver)
    np.testing.assert_array_equal(cg.positions, cs.positions)
    np.testing.assert_array_equal(cg.edges, cs.edges)
    np.testing.assert_allclose(cg.capacitance, cs.capacitance, rtol=0, atol=0)
    np.testing.assert_allclose(cg.system_matrix, cs.system_matrix, rtol=0, atol=0)
```

For every guided synapse, assert `synapse_compartment(...)` returns a dendrite node `>= 1` belonging to the same receiver and is the nearest cable dendrite coordinate to `(synapse.x, synapse.y)`.

- [ ] **Step 2: Write failing purity tests**

Use synthetic decays/energies independent of a cable:

```python
decays = np.array([0.2, 0.2, 0.5, 0.9])
energies = np.array([1.0, 3.0, 4.0, 2.0])
t = purification_time(decays, energies, purity_target=0.95,
                      degeneracy_rtol=1e-8, excitation_tol=1e-12)
assert t is not None and t > 0.0
```

At `t`, compute the grouped slow-subspace purity and assert `>= 0.95`; at `max(t-1e-6, 0)` assert it is not greater than the value at `t`.

Add an explicit rotation-invariance test: rotate the two equal-decay target amplitudes with a 2×2 orthogonal matrix, square them back to energies, and assert identical purification time within `1e-10`.

- [ ] **Step 3: Run focused tests and confirm RED**

Run: `pytest tests/test_physical.py -q`

Expected: missing placement/purity APIs.

- [ ] **Step 4: Implement deterministic compartment assignment**

Restrict candidate nodes to cable dendrite nodes `1:` and minimize squared distance to the synapse contact coordinate. Break ties by node index via `np.argmin` on the stable node order.

- [ ] **Step 5: Implement eigenspace grouping and purification**

Filter energies `> excitation_tol`. Sort by decay. Group adjacent decays when

```python
abs(a - b) <= degeneracy_rtol * max(1.0, abs(a), abs(b))
```

Sum energies inside each group. The target group is the slowest excited group. Purity is

```python
num = E0 * np.exp(-2 * lambda0 * t)
den = sum(Eg * np.exp(-2 * lambdag * t) for groups)
```

Return `0.0` if initial purity already meets target, `None` if no non-uniform excited energy exists, otherwise double an upper bracket from `1.0` until the target is reached (limit 256 doublings), then bisection for 100 iterations.

- [ ] **Step 6: Implement synapse physical metrics**

For the synapse’s receiver cable:

1. compute whitened modes,
2. identify the uniform voltage mode by maximal absolute overlap with `sqrt(C) * ones`,
3. remove that mode,
4. form whitened point forcing `f = e_j * synapse.weight / sqrt(C[j])`,
5. modal amplitudes are `vectors.T @ f`, energies are squared amplitudes,
6. compute entropy effective count over positive non-uniform energy,
7. compute target decay, next distinct excited decay gap, and `purification_time_95`,
8. compute soma transfer resistance from `np.linalg.solve(G, e_j)[0] * synapse.weight`.

Return explicit `None` for target/gap/purification when no non-uniform mode is excited.

- [ ] **Step 7: Run focused tests and commit**

Run: `pytest tests/test_physical.py -q`

Expected: PASS.

Commit message: `feat: measure developed input visibility in cable modes`

---

### Task 3: Deterministic v1 ensemble receipt

**Files:**
- Create: `experiments/run_v1.py`
- Create: `tests/test_v1_receipt.py`

**Interfaces:**
- Consumes `develop(...)` and `synapse_physical_metrics(...)`.
- Produces `run(seeds: Iterable[int], development_config: DevelopmentConfig | None = None, cable_config: PassiveCableConfig | None = None) -> dict`.

- [ ] **Step 1: Write failing receipt tests**

Assert a small two-seed run has:

```python
receipt["version"] == "v1"
receipt["seeds"] == [0, 1]
set(receipt["aggregate"]) == {
    "guided", "shuffled_labels", "random_walk", "paired_guided_minus_shuffled"
}
```

Require arm summaries for:

- `synapse_count`,
- `visible_mode_effective_count`,
- `slow_target_decay`,
- `next_decay_gap`,
- `purification_time_95`,
- `soma_transfer_resistance`.

For optional metrics, summary dictionaries must include `defined_count` plus mean/median/min/max over defined values only.

Assert two identical calls return exactly equal dicts.

- [ ] **Step 2: Run tests and confirm RED**

Run: `pytest tests/test_v1_receipt.py -q`

Expected: `experiments.run_v1` missing.

- [ ] **Step 3: Implement ensemble runner**

For each seed and arm, call `develop`, compute metrics for every synapse, and store compact per-seed summaries rather than full trajectories. Preserve the v0 control flags for exact receptor/ligand multisets.

For the primary paired comparison, compute per-seed arm means first, then `guided - shuffled` for each physical metric only when both sides are defined. Never impute missing values.

The CLI uses integer seeds `0..N-1` and defaults to `--seeds 16 --out results/v1.json`.

- [ ] **Step 4: Run receipt tests and full existing suite**

Run:

```bash
pytest tests/test_v1_receipt.py -q
pytest -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add v1 physical bridge ensemble`

---

### Task 4: Produce and freeze the canonical 16-seed result

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create after authoritative run: `results/v1.json`
- Modify: `tests/test_v1_receipt.py`

**Interfaces:**
- CI temporarily emits an artifact from the same `experiments/run_v1.py` used by tests.

- [ ] **Step 1: Add the frozen-receipt test before the file exists**

Add:

```python
def test_frozen_v1_receipt_matches_canonical_run() -> None:
    frozen = json.loads(Path("results/v1.json").read_text(encoding="utf-8"))
    assert frozen == run(seeds=range(16))
```

Run `pytest tests/test_v1_receipt.py -q` and confirm RED with missing `results/v1.json`.

- [ ] **Step 2: Add a temporary authoritative artifact step**

On Python 3.11 only, before tests, run:

```yaml
- name: Generate canonical v1 receipt
  if: matrix.python-version == '3.11'
  run: python experiments/run_v1.py --seeds 16 --out /tmp/v1.json
- name: Upload canonical v1 receipt
  if: matrix.python-version == '3.11'
  uses: actions/upload-artifact@v4
  with:
    name: v1-receipt
    path: /tmp/v1.json
```

Push and wait for the artifact-producing job.

- [ ] **Step 3: Inspect the artifact before freezing**

Check the aggregate for finite values, defined counts, exact arm-independent cable invariants, and no impossible preferred-sign assertion. If the result is null or permutation-equivalent, retain it.

- [ ] **Step 4: Commit the exact artifact as `results/v1.json`**

Do not hand-edit scientific numbers.

- [ ] **Step 5: Remove the artifact-generation CI steps and run the frozen regression**

CI should return to unit/invariant tests + JavaScript syntax + a small scientific smoke run. Add `python experiments/run_v1.py --seeds 4 --out /tmp/v1-smoke.json` as a smoke command.

- [ ] **Step 6: Commit**

Commit message: `results: freeze v1 developed-cable receipt`

---

### Task 5: Interpret the result and update the public surface

**Files:**
- Create: `docs/RESULTS_V1.md`
- Modify: `README.md`
- Modify: `index.html`
- Modify: `tests/test_site.py`

**Interfaces:**
- Documentation consumes only frozen `results/v1.json` values.
- Pages shows a static v1 summary; `site.js` remains the developmental visualization and does not solve cable dynamics.

- [ ] **Step 1: Write a failing site assertion**

Require `index.html` to contain `v1 physical bridge`, `Python receipt`, and `purification`.

Run: `pytest tests/test_site.py -q`

Expected: FAIL because the v1 panel is absent.

- [ ] **Step 2: Write `docs/RESULTS_V1.md` from the frozen receipt**

Include:

- the predeclared question,
- the arm-invariant cable-spectrum control,
- the exact aggregate table,
- paired guided-minus-shuffled physical deltas,
- whether the result is positive, null, or mixed,
- why a null result is evidence for needing morphology heterogeneity/development rather than permission to tune v1,
- the limitation that purification is an oracle physical diagnostic, not a biological growth signal.

- [ ] **Step 3: Update README**

Add a concise v1 section and the command:

```bash
python experiments/run_v1.py --seeds 16 --out /tmp/v1-full.json
```

Do not revise the v0 numbers.

- [ ] **Step 4: Add a static Pages v1 panel**

Use the exact frozen headline values. State that the Python receipt is authoritative. Do not add a second JavaScript physical model.

- [ ] **Step 5: Run all tests**

Run: `pytest -q`

Expected: PASS.

- [ ] **Step 6: Commit**

Commit message: `docs: publish v1 physical bridge result`

---

### Task 6: Final verification and integration

**Files:**
- No new scientific code unless verification exposes a defect.

**Interfaces:**
- Branch must be cleanly ahead of `main` and CI-green on Python 3.11 and 3.12.

- [ ] **Step 1: Run fresh full verification**

Require both Python jobs to pass:

- editable install,
- full pytest suite,
- Pages JavaScript syntax,
- v0 smoke run,
- v1 smoke run.

- [ ] **Step 2: Review the branch diff against the spec**

Check specifically that:

- v0 development behavior was not silently changed,
- guided/shuffled cable matrices are identical,
- no preferred result sign is encoded in tests,
- documentation does not call an input-map difference a cable-spectrum difference,
- null findings remain visible.

- [ ] **Step 3: Create a pull request to `main`**

PR body must report the actual v1 result and controls, including nulls.

- [ ] **Step 4: Merge only after the PR head and post-merge `main` are green**

After merge, verify the `main` SHA and the fresh `main` workflow run before calling v1 complete.
