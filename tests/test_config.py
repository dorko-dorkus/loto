import os
from pathlib import Path

import pytest

from loto.config import ConfigError, load_config


@pytest.mark.parametrize(
    "app_env, contents, check",
    [
        (
            "demo",
            {
                "APP_ENV": "demo",
                "DATA_IN": "in",
                "DATA_OUT": "out",
                "RULEPACK_FILE": "rules.yml",
                "MAXIMO_MODE": "MOCK",
                "WAPR_MODE": "MOCK",
                "COUPA_MODE": "MOCK",
            },
            lambda cfg: cfg.app_env == "demo",
        ),
        (
            "live",
            {
                "APP_ENV": "live",
                "DATA_IN": "in",
                "DATA_OUT": "out",
                "RULEPACK_FILE": "rules.yml",
                "MAXIMO_MODE": "LIVE",
                "MAXIMO_BASE_URL": "https://maximo.local",
                "MAXIMO_APIKEY": "abc",
                "MAXIMO_OS_WORKORDER": "WO",
                "WAPR_MODE": "LIVE",
                "WAPR_BASE_URL": "https://wapr.local",
                "WAPR_APIKEY": "def",
                "COUPA_MODE": "LIVE",
                "COUPA_BASE_URL": "https://coupa.local",
                "COUPA_APIKEY": "ghi",
            },
            lambda cfg: cfg.maximo.os["WORKORDER"] == "WO",
        ),
    ],
)
def test_load_config_valid(tmp_path, monkeypatch, app_env, contents, check):
    env_file = tmp_path / f".env.{app_env}"
    with env_file.open("w") as f:
        for k, v in contents.items():
            f.write(f"{k}={v}\n")
    monkeypatch.chdir(tmp_path)
    # clear environment
    for k in list(os.environ):
        tracked = {
            "APP_ENV",
            "DATA_IN",
            "DATA_OUT",
            "RULEPACK_FILE",
        }
        if k.startswith("MAXIMO") or k.startswith("WAPR") or k.startswith("COUPA") or k in tracked:
            monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("APP_ENV", app_env)
    cfg = load_config()
    assert check(cfg)


@pytest.mark.parametrize(
    "app_env, contents, missing",
    [
        (
            "demo",
            {
                "APP_ENV": "demo",
                "DATA_IN": "in",
                # DATA_OUT missing
                "RULEPACK_FILE": "rules.yml",
            },
            "DATA_OUT",
        ),
        (
            "live",
            {
                "APP_ENV": "live",
                "DATA_IN": "in",
                "DATA_OUT": "out",
                "RULEPACK_FILE": "rules.yml",
                "MAXIMO_MODE": "LIVE",
                # MAXIMO_BASE_URL missing
                "MAXIMO_APIKEY": "abc",
                "MAXIMO_OS_WORKORDER": "WO",
            },
            "MAXIMO_BASE_URL",
        ),
    ],
)
def test_load_config_invalid(tmp_path, monkeypatch, app_env, contents, missing):
    env_file = tmp_path / f".env.{app_env}"
    with env_file.open("w") as f:
        for k, v in contents.items():
            f.write(f"{k}={v}\n")
    monkeypatch.chdir(tmp_path)
    for k in list(os.environ):
        tracked = {
            "APP_ENV",
            "DATA_IN",
            "DATA_OUT",
            "RULEPACK_FILE",
        }
        if k.startswith("MAXIMO") or k.startswith("WAPR") or k.startswith("COUPA") or k in tracked:
            monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("APP_ENV", app_env)
    with pytest.raises(ConfigError) as exc:
        load_config()
    assert exc.value.code == "CONFIG/ENV"
    assert missing in exc.value.hint
