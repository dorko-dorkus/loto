from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import structlog
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger()


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


class Settings(BaseSettings):
    app_env: str = Field(default="demo", alias="APP_ENV")
    data_in: str = Field(alias="DATA_IN")
    data_out: str = Field(alias="DATA_OUT")
    rulepack_file: str = Field(alias="RULEPACK_FILE")

    maximo_mode: str = Field(default="MOCK", alias="MAXIMO_MODE")
    maximo_base_url: str | None = Field(default=None, alias="MAXIMO_BASE_URL")
    maximo_apikey: str | None = Field(default=None, alias="MAXIMO_APIKEY")
    maximo_os: Dict[str, str] = Field(default_factory=dict)

    wapr_mode: str = Field(default="MOCK", alias="WAPR_MODE")
    wapr_base_url: str | None = Field(default=None, alias="WAPR_BASE_URL")
    wapr_apikey: str | None = Field(default=None, alias="WAPR_APIKEY")

    coupa_mode: str = Field(default="MOCK", alias="COUPA_MODE")
    coupa_base_url: str | None = Field(default=None, alias="COUPA_BASE_URL")
    coupa_apikey: str | None = Field(default=None, alias="COUPA_APIKEY")

    model_config = SettingsConfigDict(
        env_file=Path(f".env.{os.getenv('APP_ENV', 'demo').lower()}"),
        extra="ignore",
    )

    @field_validator("maximo_os", mode="before")
    @classmethod
    def _gather_maximo_os(cls, v: Dict[str, str] | None) -> Dict[str, str]:
        if v:
            return v
        return {
            k.removeprefix("MAXIMO_OS_"): value
            for k, value in os.environ.items()
            if k.startswith("MAXIMO_OS_")
        }


CONFIG_ERROR_CODE = "CONFIG/ENV"


def validate_env_vars(example: Path | None = None) -> None:
    """Validate presence of environment variables listed in ``.env.example``.

    Parameters
    ----------
    example:
        Optional path to the ``.env.example`` file. Defaults to the project
        root's ``.env.example``.

    Raises
    ------
    ConfigError
        If any expected variable is missing. The function logs a table of
        expected keys with ``Y``/``N`` indicating presence before raising.
    """

    example = example or Path(__file__).resolve().parent.parent / ".env.example"
    keys: list[str] = []
    for line in example.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.append(line.split("=", 1)[0])

    rows: list[tuple[str, str]] = []
    missing: list[str] = []
    for key in keys:
        present = os.getenv(key) is not None
        rows.append((key, "Y" if present else "N"))
        if not present:
            missing.append(key)

    if missing:
        col = max(len("Key"), *(len(k) for k, _ in rows))
        logger.info(f"{'Key'.ljust(col)} Present")
        for key, flag in rows:
            logger.info(f"{key.ljust(col)} {flag}")
        raise ConfigError(
            code=CONFIG_ERROR_CODE,
            hint="Missing environment variables: " + ", ".join(missing),
        )


def _required(keys: list[str]) -> None:
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise ConfigError(
            code=CONFIG_ERROR_CODE,
            hint=f"Missing environment variables: {', '.join(missing)}",
        )


def load_config() -> AppConfig:
    """Load configuration from ``.env.<APP_ENV>`` and environment variables."""

    app_env = os.getenv("APP_ENV", "demo").lower()
    if app_env not in {"demo", "live"}:
        raise ConfigError(
            code=CONFIG_ERROR_CODE, hint="APP_ENV must be 'demo' or 'live'"
        )

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
    coupa = IntegrationConfig(
        mode=coupa_mode, base_url=coupa_base_url, apikey=coupa_apikey
    )

    return AppConfig(
        app_env=app_env,
        data_in=data_in,  # type: ignore[arg-type]
        data_out=data_out,  # type: ignore[arg-type]
        rulepack_file=rulepack_file,  # type: ignore[arg-type]
        maximo=maximo,
        wapr=wapr,
        coupa=coupa,
    )
