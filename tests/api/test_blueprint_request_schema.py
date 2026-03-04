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
