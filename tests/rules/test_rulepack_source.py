import pytest

from loto import models, rule_engine


def test_ruleengine_hash_accepts_models_rulepack():
    assert rule_engine.RulePack is models.RulePack
    engine = rule_engine.RuleEngine()
    pack = models.RulePack()
    with pytest.raises(NotImplementedError):
        engine.hash(pack)
