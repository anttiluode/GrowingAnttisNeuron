from __future__ import annotations

from experiments.run_v3 import run


def test_v3_receipt_records_same_start_same_rule_and_local_only_growth() -> None:
    receipt = run()

    assert receipt["version"] == "v3"
    assert receipt["correlations"] == [0.0, 0.2, 0.4, 0.6]
    assert receipt["input_variance"] == 1.0
    assert receipt["controls"]["same_initial_scale"] is True
    assert receipt["controls"]["same_input_variance"] is True
    assert receipt["controls"]["fixed_lineage_edges"] is True
    assert receipt["controls"]["growth_signal"] == "local_voltage_rms_only"
    assert receipt["controls"]["oracle_fields_used"] == []


def test_v3_receipt_differentiates_morphology_while_regulating_one_setpoint() -> None:
    receipt = run()
    trajectories = receipt["trajectories"]

    assert len(trajectories) == 4
    assert all(item["converged"] for item in trajectories)
    scales = [item["final_scale"] for item in trajectories]
    assert all(left < right for left, right in zip(scales[:-1], scales[1:], strict=True))
    tolerance = receipt["growth_config"]["relative_tolerance"]
    target = receipt["target_rms"]
    assert max(abs(item["final_rms"] / target - 1.0) for item in trajectories) <= tolerance
    assert trajectories[0]["operator_distance_from_baseline"] == 0.0
    assert all(item["operator_distance_from_baseline"] > 0.0 for item in trajectories[1:])


def test_v3_robustness_scans_all_dendritic_ports() -> None:
    receipt = run()
    robustness = receipt["robustness"]

    assert robustness["temporal_ordering_passed"] == 7
    assert robustness["temporal_ordering_total"] == 7
    assert robustness["scale_monotonic_passed"] == 28
    assert robustness["scale_monotonic_total"] == 28


def test_v3_receipt_is_exactly_deterministic() -> None:
    assert run() == run()
