from loto.scheduling.gates import (
    compose_gates,
    hold_point,
    permit_gate,
    shared_isolation,
)


def test_permit_gate():
    gate = permit_gate()
    state = {"permit": False}
    assert not gate(state)
    state["permit"] = True
    assert gate(state)


def test_hold_point():
    gate = hold_point()
    state = {"hold": True}
    assert not gate(state)
    state["hold"] = False
    assert gate(state)


def test_shared_isolation():
    gate = shared_isolation("iso1")
    state = {"isolations": set()}
    assert not gate(state)
    state["isolations"].add("iso1")
    assert gate(state)


def test_compose_gates_requires_all():
    g1 = permit_gate()
    g2 = hold_point()
    g3 = shared_isolation("valve")
    composed = compose_gates(g1, g2, g3)

    state = {"permit": False, "hold": True, "isolations": set()}

    # Initially none of the gates are satisfied
    assert not composed(state)

    # Permit granted
    state["permit"] = True
    assert not composed(state)

    # Hold point cleared
    state["hold"] = False
    assert not composed(state)

    # Isolation established
    state["isolations"].add("valve")
    assert composed(state)


def test_compose_gates_empty_returns_true():
    composed = compose_gates()
    assert composed({})
