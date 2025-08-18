from loto.bundling import Candidate, select_candidates


def test_knapsack_selector_returns_expected_set_and_reasons():
    candidates = [
        Candidate("A", saved_future_derate=10, readiness_cost=4, simops_cost=3),
        Candidate("B", saved_future_derate=5, readiness_cost=2, simops_cost=1),
        Candidate("C", saved_future_derate=8, readiness_cost=6, simops_cost=4),
        Candidate(
            "D", saved_future_derate=7, readiness_cost=3, simops_cost=4, ready=False
        ),
    ]

    selected, reasons = select_candidates(candidates, max_readiness=8, max_simops=5)

    assert {c.name for c in selected} == {"A", "B"}
    assert reasons == {
        "A": "selected (10 MW saved)",
        "B": "selected (5 MW saved)",
        "C": "excluded to respect readiness/SIMOPs constraints",
        "D": "not ready",
    }
