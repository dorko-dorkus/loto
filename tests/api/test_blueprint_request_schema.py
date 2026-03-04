from apps.api.schemas import BlueprintRequest


def test_blueprint_request_normalizes_optional_fields() -> None:
    payload = BlueprintRequest(
        workorder_id="WO-1",
        work_type=" Intrusive-Mech ",
        hazard_class=[" Pressure ", "CHEMICAL"],
        exposure_mode=" RELEASE-POSSIBLE ",
    )

    assert payload.work_type == "intrusive_mech"
    assert payload.hazard_class == ["pressure", "chemical"]
    assert payload.exposure_mode == "release_possible"


def test_blueprint_request_accepts_string_hazard_class_and_none_defaults() -> None:
    payload = BlueprintRequest(
        workorder_id="WO-2",
        work_type=None,
        hazard_class=" Steam-Pressure ",
        exposure_mode=None,
    )

    assert payload.work_type is None
    assert payload.hazard_class == "steam_pressure"
    assert payload.exposure_mode is None


def test_blueprint_request_defaults_optional_fields_when_omitted() -> None:
    payload = BlueprintRequest(
        workorder_id="WO-3",
        work_type=None,
        hazard_class=None,
        exposure_mode=None,
    )

    assert payload.work_type is None
    assert payload.hazard_class is None
    assert payload.exposure_mode is None
