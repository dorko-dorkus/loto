from loto.integrations.hats_adapter import DemoHatsAdapter, HatsAdapter


def test_demo_hats_adapter_get_profile_keys() -> None:
    adapter: HatsAdapter = DemoHatsAdapter()
    profile = adapter.get_profile("DEMO-1")
    assert {"inductions", "competencies", "roster"} <= set(profile)
