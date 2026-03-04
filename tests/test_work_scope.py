from loto.work_scope import infer_exposure_mode


def test_infer_exposure_mode_release_possible_terms() -> None:
    inferred = infer_exposure_mode("Repair packing leak near valve gland")
    assert inferred.exposure_mode == "release_possible"
    assert inferred.escalate_to_intrusive_mech is False
    assert "packing leak" in inferred.matched_terms


def test_infer_exposure_mode_thermal_only_terms() -> None:
    inferred = infer_exposure_mode("Replace insulation support")
    assert inferred.exposure_mode == "thermal_only"
    assert inferred.escalate_to_intrusive_mech is False


def test_infer_exposure_mode_boundary_open_escalates() -> None:
    inferred = infer_exposure_mode("Line break required for spool removal")
    assert inferred.exposure_mode == "release_possible"
    assert inferred.escalate_to_intrusive_mech is True
    assert "line break" in inferred.matched_terms


def test_infer_exposure_mode_uses_permit_hints() -> None:
    inferred = infer_exposure_mode(
        "Routine maintenance", permit={"scope_hint": "actuator swap"}
    )
    assert inferred.exposure_mode == "release_possible"
    assert inferred.escalate_to_intrusive_mech is False
