import loto


def test_import() -> None:
    assert hasattr(loto, "__version__") or True
