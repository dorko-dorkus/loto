from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv


class ConfigError(Exception):
    """Exception raised when configuration is invalid.

    Attributes
    ----------
    code: str
        Machine readable error code.
    hint: str
        Human readable hint describing how to fix the issue.
    """

    def __init__(self, *, code: str, hint: str) -> None:
        self.code = code
        self.hint = hint
        super().__init__(hint)


@dataclass
class MaximoConfig:
    mode: str
    base_url: Optional[str] = None
    apikey: Optional[str] = None
    os: Dict[str, str] = field(default_factory=dict)


@dataclass
class IntegrationConfig:
    mode: str
    base_url: Optional[str] = None
    apikey: Optional[str] = None


@dataclass
class AppConfig:
    app_env: str
    data_in: str
    data_out: str
    rulepack_file: str
    maximo: MaximoConfig
    wapr: IntegrationConfig
    coupa: IntegrationConfig


CONFIG_ERROR_CODE = "CONFIG/ENV"


def _required(keys: list[str]) -> None:
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise ConfigError(code=CONFIG_ERROR_CODE, hint=f"Missing environment variables: {', '.join(missing)}")


def load_config() -> AppConfig:
    """Load configuration from ``.env.<APP_ENV>`` and environment variables."""

    app_env = os.getenv("APP_ENV", "demo").lower()
    if app_env not in {"demo", "live"}:
        raise ConfigError(code=CONFIG_ERROR_CODE, hint="APP_ENV must be 'demo' or 'live'")

    # load .env file for the selected environment if present
    load_dotenv(Path(f".env.{app_env}"), override=False)

    # basic application settings
    _required(["DATA_IN", "DATA_OUT", "RULEPACK_FILE"])
    data_in = os.getenv("DATA_IN")
    data_out = os.getenv("DATA_OUT")
    rulepack_file = os.getenv("RULEPACK_FILE")

    # maximo settings
    maximo_mode = os.getenv("MAXIMO_MODE", "MOCK").upper()
    maximo_base_url = os.getenv("MAXIMO_BASE_URL")
    maximo_apikey = os.getenv("MAXIMO_APIKEY")
    maximo_os = {
        k.removeprefix("MAXIMO_OS_"): v
        for k, v in os.environ.items()
        if k.startswith("MAXIMO_OS_")
    }
    if maximo_mode == "LIVE":
        missing = []
        if not maximo_base_url:
            missing.append("MAXIMO_BASE_URL")
        if not maximo_apikey:
            missing.append("MAXIMO_APIKEY")
        if not maximo_os:
            missing.append("MAXIMO_OS_*")
        if missing:
            raise ConfigError(
                code=CONFIG_ERROR_CODE,
                hint="Missing Maximo configuration: " + ", ".join(missing),
            )
    maximo = MaximoConfig(
        mode=maximo_mode,
        base_url=maximo_base_url,
        apikey=maximo_apikey,
        os=maximo_os,
    )

    # wapr settings
    wapr_mode = os.getenv("WAPR_MODE", "MOCK").upper()
    wapr_base_url = os.getenv("WAPR_BASE_URL")
    wapr_apikey = os.getenv("WAPR_APIKEY")
    if wapr_mode == "LIVE":
        missing = []
        if not wapr_base_url:
            missing.append("WAPR_BASE_URL")
        if not wapr_apikey:
            missing.append("WAPR_APIKEY")
        if missing:
            raise ConfigError(
                code=CONFIG_ERROR_CODE,
                hint="Missing WAPR configuration: " + ", ".join(missing),
            )
    wapr = IntegrationConfig(mode=wapr_mode, base_url=wapr_base_url, apikey=wapr_apikey)

    # coupa settings
    coupa_mode = os.getenv("COUPA_MODE", "MOCK").upper()
    coupa_base_url = os.getenv("COUPA_BASE_URL")
    coupa_apikey = os.getenv("COUPA_APIKEY")
    if coupa_mode == "LIVE":
        missing = []
        if not coupa_base_url:
            missing.append("COUPA_BASE_URL")
        if not coupa_apikey:
            missing.append("COUPA_APIKEY")
        if missing:
            raise ConfigError(
                code=CONFIG_ERROR_CODE,
                hint="Missing Coupa configuration: " + ", ".join(missing),
            )
    coupa = IntegrationConfig(mode=coupa_mode, base_url=coupa_base_url, apikey=coupa_apikey)

    return AppConfig(
        app_env=app_env,
        data_in=data_in,  # type: ignore[arg-type]
        data_out=data_out,  # type: ignore[arg-type]
        rulepack_file=rulepack_file,  # type: ignore[arg-type]
        maximo=maximo,
        wapr=wapr,
        coupa=coupa,
    )
