from __future__ import annotations

import logging
import os
import sqlite3
import time
import tomllib
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Any, Dict, List
from uuid import uuid4

import jwt
import requests  # type: ignore[import-untyped]
import sentry_sdk
import structlog
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_oidc import get_auth
from fastapi_oidc.types import IDToken
from jwt import PyJWTError
from opentelemetry import trace
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from starlette.datastructures import MutableHeaders

from loto.config import validate_env_vars
from loto.errors import GenerationError
from loto.errors import ImportError as LotoImportError
from loto.errors import LotoError, ValidationError
from loto.impact_config import load_impact_config
from loto.integrations import get_permit_adapter
from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.inventory import (
    CANONICAL_UNITS,
    InventoryRecord,
    InventoryStatus,
    Reservation,
    StockItem,
    check_wo_parts_required,
    load_item_unit_map,
    normalize_units,
)
from loto.loggers import configure_logging, request_id_var, rule_hash_var, seed_var
from loto.materials.jobpack import DEFAULT_LEAD_DAYS, build_jobpack
from loto.models import RulePack
from loto.rule_engine import RuleEngine
from loto.scheduling.des_engine import Task
from loto.scheduling.monte_carlo import simulate
from loto.service import plan_and_evaluate
from loto.service.blueprints import inventory_state

from .audit import add_record
from .demo_data import demo_data
from .hats_endpoints import router as hats_router  # provides hats KPI endpoints
from .pid_endpoints import router as pid_router
from .schemas import (
    BlueprintRequest,
    BlueprintResponse,
    CommitRequest,
    JobInfo,
    JobStatus,
    SchedulePoint,
    ScheduleRequest,
    ScheduleResponse,
    Step,
)
from .workorder_endpoints import router as workorder_router

# mypy: ignore-errors


configure_logging()
validate_env_vars()

_required_env = [
    "MAXIMO_BASE_URL",
    "MAXIMO_APIKEY",
    "OIDC_CLIENT_ID",
    "OIDC_CLIENT_SECRET",
    "OIDC_ISSUER",
]
_missing = [k for k in _required_env if not os.getenv(k)]
if _missing:
    raise RuntimeError("Missing required environment variables: " + ", ".join(_missing))

ENV = os.getenv("APP_ENV", "").lower()
if ENV == "live":
    ENV_BADGE = "PROD"
elif ENV == "test":
    ENV_BADGE = "TEST"
else:
    ENV_BADGE = "DRY-RUN"

_rule_engine = RuleEngine()
_default_rulepack = (
    Path(__file__).resolve().parents[2] / "config" / "hswa_rules_v1.1.yaml"
)
_rulepack_path = Path(os.getenv("RULEPACK_FILE", _default_rulepack))
RULE_PACK = _rule_engine.load(_rulepack_path)
RULE_PACK_HASH = _rule_engine.hash(RULE_PACK)
RULE_PACK_ID = RULE_PACK.metadata.get("id")
RULE_PACK_VERSION = RULE_PACK.metadata.get("version")
try:
    APP_VERSION = pkg_version("loto")
except PackageNotFoundError:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    APP_VERSION = tomllib.loads(pyproject.read_text())["project"]["version"]


def _git_sha() -> str:
    try:
        result = run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (CalledProcessError, FileNotFoundError):
        return "unknown"


GIT_SHA = _git_sha()
logging.info("loaded rulepack %s sha256=%s", _rulepack_path, RULE_PACK_HASH)

_APPROVAL_DB = Path(__file__).resolve().parents[2] / "approvals.db"

app = FastAPI(title="loto API")

# In-memory storage for background job statuses
JOBS: Dict[str, JobStatus] = {}


@app.middleware("http")
async def metrics(request: Request, call_next):
    """Collect basic request metrics."""

    requests_total.inc()
    response = await call_next(request)
    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        rate_limited_total.inc()
    return response


class CORSMiddlewareWithEnv(CORSMiddleware):
    async def __call__(self, scope, receive, send):
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append("X-Env", ENV_BADGE)
            await send(message)

        await super().__call__(scope, receive, send_wrapper)


origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
if "http://localhost:3000" not in origins:
    origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddlewareWithEnv,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pid_router)
app.include_router(hats_router)
app.include_router(workorder_router)

if os.getenv("TRACE_ENABLED", "").lower() == "true":
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    exporter_type = os.getenv("TRACE_EXPORTER", "").lower()
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: "loto-api"}))
    exporter = None
    if exporter_type == "console":
        exporter = ConsoleSpanExporter()
    elif exporter_type == "otlp":
        try:  # pragma: no cover - optional dependency
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
        except ImportError:  # pragma: no cover
            exporter = None
        else:
            exporter = OTLPSpanExporter()
    if exporter:
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

REGISTRY = CollectorRegistry()
plans_generated_total = Counter(
    "plans_generated_total",
    "Total number of plans generated",
    registry=REGISTRY,
)
errors_total = Counter(
    "errors_total", "Total number of plan generation errors", registry=REGISTRY
)
plan_generation_duration_seconds = Histogram(
    "plan_generation_duration_seconds",
    "Plan generation duration in seconds",
    registry=REGISTRY,
)

requests_total = Counter("requests_total", "Total HTTP requests", registry=REGISTRY)
rate_limited_total = Counter(
    "rate_limited_total", "Total HTTP 429 responses", registry=REGISTRY
)
job_duration_seconds = Histogram(
    "job_duration_seconds",
    "Background job duration in seconds",
    registry=REGISTRY,
)


@app.get("/metrics")
def get_metrics() -> Response:
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "").lower() == "true"
JWT_SECRET = os.getenv("JWT_SECRET", "secret")


# OIDC configuration
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "")
OIDC_ISSUER = os.getenv("OIDC_ISSUER", "https://example.com")
OIDC_SERVER = os.getenv("OIDC_SERVER", OIDC_ISSUER)
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", OIDC_CLIENT_ID)
OIDC_CACHE_TTL = int(os.getenv("OIDC_CACHE_TTL", "3600"))
PLANNER_EMAIL_DOMAIN = os.getenv("PLANNER_EMAIL_DOMAIN", "")


class OIDCUser(IDToken):
    email: str | None = None
    roles: List[str] = Field(default_factory=list)


authenticate_user = get_auth(
    client_id=OIDC_CLIENT_ID,
    audience=OIDC_AUDIENCE,
    base_authorization_server_uri=OIDC_SERVER,
    issuer=OIDC_ISSUER,
    signature_cache_ttl=OIDC_CACHE_TTL,
    token_type=OIDCUser,
)


def _assign_roles(user: OIDCUser) -> OIDCUser:
    if not user.roles:
        domain = (user.email or "").split("@")[-1]
        if PLANNER_EMAIL_DOMAIN and domain == PLANNER_EMAIL_DOMAIN:
            user.roles = ["planner"]
        else:
            user.roles = ["viewer"]
    return user


def _auth_header(authorization: str | None = Header(default=None)) -> str:
    if authorization is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return authorization


def get_current_user(auth_header: str = Depends(_auth_header)) -> OIDCUser:
    user = authenticate_user(auth_header)
    return _assign_roles(user)


def current_user_from_header(auth_header: str) -> OIDCUser:
    user = authenticate_user(auth_header)
    return _assign_roles(user)


def _require_role(role: str):
    def checker(user: OIDCUser = Depends(get_current_user)) -> OIDCUser:
        if role not in user.roles:
            raise HTTPException(status_code=403, detail="forbidden")
        return user

    return checker


require_worker = _require_role("worker")
require_supervisor = _require_role("supervisor")
require_hs_rep = _require_role("HS rep")
require_admin = _require_role("admin")
require_planner = _require_role("planner")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str


class ApprovalRequest(BaseModel):
    """Approval payload containing the approver identifier."""

    user_id: str


@app.post("/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest) -> TokenResponse:
    expected = os.getenv("AUTH_TOKEN", "")
    if AUTH_REQUIRED and expected and payload.password != expected:
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = jwt.encode({"sub": payload.username}, JWT_SECRET, algorithm="HS256")
    return TokenResponse(access_token=token)


@app.get("/roles/worker", dependencies=[Depends(require_worker)], tags=["auth"])
def worker_role() -> dict[str, bool]:
    return {"ok": True}


@app.get("/roles/supervisor", dependencies=[Depends(require_supervisor)], tags=["auth"])
def supervisor_role() -> dict[str, bool]:
    return {"ok": True}


@app.get("/roles/hsrep", dependencies=[Depends(require_hs_rep)], tags=["auth"])
def hs_rep_role() -> dict[str, bool]:
    return {"ok": True}


@app.get("/roles/admin", dependencies=[Depends(require_admin)], tags=["auth"])
def admin_role() -> dict[str, bool]:
    return {"ok": True}


@app.middleware("http")
async def auth_guard(request: Request, call_next):
    """Enforce JWT bearer token on non-read-only requests when required."""
    if AUTH_REQUIRED and request.method not in {"GET", "HEAD", "OPTIONS"}:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            resp = Response(status_code=401)
            resp.headers["X-Env"] = ENV_BADGE
            return resp
        token = auth_header.split(" ", 1)[1]
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except PyJWTError:
            resp = Response(status_code=401)
            resp.headers["X-Env"] = ENV_BADGE
            return resp
    return await call_next(request)


@app.middleware("http")
async def log_context(request: Request, call_next):
    req_id = str(uuid4())
    traceparent = request.headers.get("traceparent")
    trace_id = traceparent.split("-")[1] if traceparent else str(uuid4())
    token = request_id_var.set(req_id)
    structlog.contextvars.bind_contextvars(request_id=req_id, trace_id=trace_id)
    try:
        response = await call_next(request)
        return response
    finally:
        request_id_var.reset(token)
        seed_var.set(None)
        rule_hash_var.set(None)
        structlog.contextvars.unbind_contextvars(
            "request_id", "trace_id", "seed", "rule_hash"
        )


@app.middleware("http")
async def audit_log(request: Request, call_next):
    """Record basic request information to the audit log."""
    response = await call_next(request)
    user = "anonymous"
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user = str(payload.get("sub", user))
        except PyJWTError:
            user = "invalid"
    action = f"{request.method} {request.url.path}"
    try:
        add_record(user=user, action=action)
    except Exception:
        logging.exception("failed to record audit log")
    return response


@app.exception_handler(HTTPException)
async def _handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Return errors in a consistent JSON envelope."""
    content = exc.detail if isinstance(exc.detail, dict) else {"error": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(LotoError)
async def _handle_loto_error(request: Request, exc: LotoError) -> None:
    """Convert internal errors into HTTP errors."""
    status_map = {
        ValidationError: status.HTTP_400_BAD_REQUEST,
        LotoImportError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        GenerationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    status_code = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    raise HTTPException(
        status_code=status_code, detail={"code": exc.code, "message": exc.hint}
    )


@app.exception_handler(Exception)
async def _handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler to wrap unexpected exceptions."""
    logging.exception("Unhandled exception: %s", exc)
    sentry_sdk.capture_exception(exc)
    return JSONResponse(status_code=500, content={"error": str(exc)})


RATE_LIMIT_PATHS = {"/pid/overlay", "/schedule"}
RATE_LIMIT_CAPACITY = int(os.getenv("RATE_LIMIT_CAPACITY", "100000"))
RATE_LIMIT_INTERVAL = float(os.getenv("RATE_LIMIT_INTERVAL", "60"))
_global_rate_limit = {"tokens": RATE_LIMIT_CAPACITY, "ts": time.monotonic()}
_route_rate_limits = {
    path: {"tokens": RATE_LIMIT_CAPACITY, "ts": time.monotonic()}
    for path in RATE_LIMIT_PATHS
}


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    now = time.monotonic()

    path = request.url.path
    if path.startswith("/jobs"):
        return await call_next(request)

    bucket = _global_rate_limit
    elapsed = now - bucket["ts"]
    if elapsed > RATE_LIMIT_INTERVAL:
        bucket["tokens"] = RATE_LIMIT_CAPACITY
        bucket["ts"] = now
    if bucket["tokens"] <= 0:
        retry_after = RATE_LIMIT_INTERVAL - elapsed
        response = Response(status_code=429)
        response.headers["Retry-After"] = str(int(retry_after) + 1)
        response.headers["X-Env"] = ENV_BADGE
        return response
    bucket["tokens"] -= 1

    if path in _route_rate_limits:
        bucket = _route_rate_limits[path]
        elapsed = now - bucket["ts"]
        if elapsed > RATE_LIMIT_INTERVAL:
            bucket["tokens"] = RATE_LIMIT_CAPACITY
            bucket["ts"] = now
        if bucket["tokens"] <= 0:
            retry_after = RATE_LIMIT_INTERVAL - elapsed
            response = Response(status_code=429)
            response.headers["Retry-After"] = str(int(retry_after) + 1)
            response.headers["X-Env"] = ENV_BADGE
            return response
        bucket["tokens"] -= 1

    return await call_next(request)


STATE: Dict[str, Any] = {}


@dataclass
class WorkOrder:
    """Minimal work order representation for demo inventory checks."""

    id: str
    reservations: List[Reservation]


class ProposeRequest(BaseModel):
    """Payload for proposing plan and schedule updates."""

    plan: Dict[str, Any] = Field(default_factory=dict, description="Proposed targets")
    schedule: Dict[str, Any] = Field(
        default_factory=dict, description="Proposed assignments"
    )

    class Config:
        extra = "forbid"


class ProposeResponse(BaseModel):
    """Response highlighting differences from current state."""

    diff: Dict[str, Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict, description="Differences vs current targets/assignments"
    )
    idempotency_key: str

    class Config:
        extra = "forbid"


class ValidationReport(BaseModel):
    missing_assets: List[Dict[str, str | None]] = Field(default_factory=list)
    missing_locations: List[Dict[str, str | None]] = Field(default_factory=list)


class InventoryItemPayload(BaseModel):
    description: str
    unit: str
    qty_onhand: int
    reorder_point: int
    site: str | None = None
    bin: str | None = None


class NormalizeRequest(BaseModel):
    items: List[InventoryItemPayload]


@app.get("/healthz", tags=["LOTO"])
async def healthz(request: Request) -> dict[str, Any]:
    """Health check endpoint including rate limit counters."""

    def _ping_service(base_url_env: str, mode_env: str) -> dict[str, str]:
        mode = os.getenv(mode_env, "MOCK").upper()
        if mode == "MOCK":
            return {"status": "mock"}
        url = os.getenv(base_url_env, "")
        if not url:
            return {"status": "unconfigured"}
        try:
            requests.head(url, timeout=5)
        except requests.RequestException as exc:
            return {"status": "error", "detail": exc.__class__.__name__}
        return {"status": "ok"}

    def _db_status() -> dict[str, Any]:
        versions_dir = Path(__file__).with_name("alembic") / "versions"
        head = None
        for path in sorted(versions_dir.glob("*.py")):
            head = path.stem.split("_")[0]
        db_url = os.getenv("DATABASE_URL", "sqlite:////tmp/loto.db")
        revision = None
        try:
            with create_engine(db_url).connect() as conn:
                row = conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).fetchone()
                revision = row[0] if row else None
        except Exception:
            revision = None
        return {"revision": revision, "head": head}

    report = demo_data.validate()
    missing_assets = len(report["missing_assets"])
    missing_locations = len(report["missing_locations"])
    if missing_assets or missing_locations:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "missing_assets": missing_assets,
                "missing_locations": missing_locations,
            },
        )

    role = "anonymous"
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            user = current_user_from_header(auth_header)
            role = user.roles[0] if user.roles else role
        except HTTPException:
            logging.debug("failed to resolve current user from header", exc_info=True)
    return {
        "status": "ok",
        "role": role,
        "rate_limit": {
            "capacity": RATE_LIMIT_CAPACITY,
            "interval": RATE_LIMIT_INTERVAL,
            "counters": {
                "global": _global_rate_limit["tokens"],
                **{path: state["tokens"] for path, state in _route_rate_limits.items()},
            },
        },
        "adapters": {
            "maximo": _ping_service("MAXIMO_BASE_URL", "MAXIMO_MODE"),
            "coupa": _ping_service("COUPA_BASE_URL", "COUPA_MODE"),
            "permit": _ping_service("ELLIPSE_BASE_URL", "ELLIPSE_MODE"),
        },
        "db": _db_status(),
        "integrity": {
            "missing_assets": missing_assets,
            "missing_locations": missing_locations,
        },
    }


@app.post("/admin/validate", tags=["admin"], response_model=ValidationReport)
def admin_validate() -> JSONResponse:
    """Return structured report of referential integrity issues."""
    report = demo_data.validate()
    status = 200
    if report["missing_assets"] or report["missing_locations"]:
        status = 400
    return JSONResponse(status_code=status, content=report)


@app.post("/admin/normalize", tags=["admin"])
def admin_normalize(payload: NormalizeRequest, dry_run: bool = True) -> Dict[str, Any]:
    """Normalise inventory units and report anomalies."""

    mapping = load_item_unit_map()
    records = [InventoryRecord(**item.model_dump()) for item in payload.items]
    normalised = normalize_units(records, mapping)
    diffs = [
        {"description": o.description, "from": o.unit, "to": n.unit}
        for o, n in zip(records, normalised)
        if o.unit != n.unit
    ]
    if dry_run:
        return {"diffs": diffs}
    anomalies = [rec for rec in normalised if rec.unit not in CANONICAL_UNITS]
    return {
        "items": [asdict(rec) for rec in normalised],
        "anomalies": len(anomalies),
    }


@app.get("/version", tags=["LOTO"])
async def version() -> dict[str, str]:
    """Return the application version."""
    return {"version": APP_VERSION, "git_sha": GIT_SHA}


@app.post("/plans/{plan_id}/approve", tags=["LOTO"])
def approve_plan(plan_id: str, payload: ApprovalRequest) -> Dict[str, Any]:
    """Persist approval for a plan and report readiness."""

    conn = sqlite3.connect(_APPROVAL_DB)
    with conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS approvals (plan_id TEXT, user_id TEXT, UNIQUE(plan_id, user_id))"
        )
        conn.execute(
            "INSERT OR IGNORE INTO approvals (plan_id, user_id) VALUES (?, ?)",
            (plan_id, payload.user_id),
        )
        cur = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM approvals WHERE plan_id = ?",
            (plan_id,),
        )
        (count,) = cur.fetchone()
    return {"plan_id": plan_id, "approvals": count, "ready": count >= 2}


class DemoMaximoAdapter:
    """Tiny Maximo adapter serving demo data from the repository."""

    def load_context(self, workorder_id: str) -> Dict[str, Any]:
        """Return file paths and metadata for the given work order."""

        base = Path(__file__).resolve().parents[2] / "demo"
        impact_cfg = load_impact_config(
            base / "unit_map.yaml", base / "redundancy_map.yaml"
        )
        return {
            "line_csv": base / "line_list.csv",
            "valve_csv": base / "valves.csv",
            "drain_csv": base / "drains.csv",
            "source_csv": base / "sources.csv",
            "asset_tag": "A",  # arbitrary asset tag for demo data
            "impact_cfg": impact_cfg,
        }


def _generate_blueprint(payload: BlueprintRequest) -> BlueprintResponse:
    """Plan isolations for a work order and return impact metrics."""

    stores = DemoStoresAdapter()
    bom = demo_data.get_bom(payload.workorder_id)
    work_order = WorkOrder(
        id=payload.workorder_id,
        reservations=[
            Reservation(
                item_id=line["item_id"],
                quantity=line["quantity"],
                critical=line.get("critical", False),
            )
            for line in bom
        ],
    )

    def lookup_stock(item_id: str) -> StockItem | None:
        try:
            status = stores.inventory_status(item_id)
        except KeyError:
            return None
        return StockItem(
            item_id=item_id,
            quantity=status.get("available", 0),
            reorder_point=status.get("reorder_point", 0),
        )

    def check_parts(wo: object) -> InventoryStatus:
        assert isinstance(wo, WorkOrder)
        return check_wo_parts_required(wo, lookup_stock)

    inv_status = check_parts(work_order)
    parts_status: Dict[str, str] = {}
    for res in work_order.reservations:
        stock = lookup_stock(res.item_id)
        available = stock.quantity if stock else 0
        reorder = stock.reorder_point if stock else 0
        if available < res.quantity:
            parts_status[res.item_id] = "short"
        elif res.critical and available <= reorder:
            parts_status[res.item_id] = "low"
        else:
            parts_status[res.item_id] = "ok"

    bp = demo_data.get_blueprint(payload.workorder_id)
    if bp is not None:
        return BlueprintResponse(
            steps=[Step(**s) for s in bp.get("steps", [])],
            unavailable_assets=bp.get("unavailable_assets", []),
            unit_mw_delta=bp.get("unit_mw_delta", {}),
            blocked_by_parts=inv_status.blocked,
            parts_status=parts_status,
        )

    adapter = DemoMaximoAdapter()
    ctx = adapter.load_context(payload.workorder_id)
    impact_cfg = ctx["impact_cfg"]
    permit = get_permit_adapter().fetch_permit(payload.workorder_id)
    cfg: Dict[str, Any] = {"callback_time_min": permit.get("callback_time_min", 0)}

    global STATE
    STATE = dict(inventory_state(work_order, check_parts, STATE))

    with (
        open(ctx["line_csv"]) as line,
        open(ctx["valve_csv"]) as valve,
        open(ctx["drain_csv"]) as drain,
        open(ctx["source_csv"]) as source,
    ):
        start = time.perf_counter()
        try:
            plan, _, impact, prov = plan_and_evaluate(
                line,
                valve,
                drain,
                source,
                asset_tag=str(ctx["asset_tag"]),
                rule_pack=RulePack(),
                stimuli=[],
                asset_units=impact_cfg.asset_units,
                unit_data=impact_cfg.unit_data,
                unit_areas=impact_cfg.unit_areas,
                penalties=impact_cfg.penalties,
                asset_areas=impact_cfg.asset_areas,
                config=cfg,
            )
            plans_generated_total.inc()
        except Exception:
            errors_total.inc()
            raise
        finally:
            plan_generation_duration_seconds.observe(time.perf_counter() - start)
    seed_var.set(prov.seed)
    rule_hash_var.set(prov.rule_hash)
    structlog.contextvars.bind_contextvars(seed=prov.seed, rule_hash=prov.rule_hash)
    logging.info("request complete")

    steps: List[Step] = [
        Step(component_id=a.component_id, method=a.method) for a in plan.actions
    ]

    return BlueprintResponse(
        steps=steps,
        unavailable_assets=sorted(impact.unavailable_assets),
        unit_mw_delta=impact.unit_mw_delta,
        blocked_by_parts=inv_status.blocked,
        parts_status=parts_status,
    )


def _blueprint_worker(job_id: str, payload: BlueprintRequest) -> None:
    """Background task to compute a blueprint and store the result."""

    job = JOBS[job_id]
    job.status = "running"
    start = time.perf_counter()
    try:
        with tracer.start_as_current_span("blueprint"):
            result = _generate_blueprint(payload)
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
    else:
        job.result = result.model_dump()
        job.status = "done"
    finally:
        job_duration_seconds.observe(time.perf_counter() - start)


@app.post("/blueprint", response_model=JobInfo, tags=["LOTO"], status_code=202)
async def post_blueprint(
    payload: BlueprintRequest, background_tasks: BackgroundTasks
) -> JobInfo:
    """Queue blueprint generation in a background task."""

    job_id = str(uuid4())
    JOBS[job_id] = JobStatus(status="queued")
    background_tasks.add_task(_blueprint_worker, job_id, payload)
    return JobInfo(job_id=job_id)


def _diff(
    current: Dict[str, Any], proposed: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Return key-wise difference between two mappings."""

    delta: Dict[str, Dict[str, Any]] = {}
    for key in set(current) | set(proposed):
        cur = current.get(key)
        prop = proposed.get(key)
        if cur != prop:
            delta[key] = {"current": cur, "proposed": prop}
    return delta


@app.post("/propose", response_model=ProposeResponse, tags=["LOTO"])
async def post_propose(payload: ProposeRequest) -> ProposeResponse:
    """Return diffs between proposed plan/schedule and current state."""

    current: Dict[str, Dict[str, Any]] = {
        "targets": {"A": 1},
        "assignments": {"A": "crew-1"},
    }

    diff = {
        "targets": _diff(current["targets"], payload.plan),
        "assignments": _diff(current["assignments"], payload.schedule),
    }

    return ProposeResponse(diff=diff, idempotency_key=str(uuid4()))


def _generate_schedule(
    payload: ScheduleRequest, strict: bool, user: OIDCUser
) -> ScheduleResponse:
    """Return a synthetic schedule for the given work order.

    When ``strict`` is ``True`` and the work order is blocked by missing parts,
    a ``409 Conflict`` response is raised instead of an empty schedule.
    """

    stores = DemoStoresAdapter()
    bom = demo_data.get_bom(payload.workorder)
    work_order = WorkOrder(
        id=payload.workorder,
        reservations=[
            Reservation(
                item_id=line["item_id"],
                quantity=line["quantity"],
                critical=line.get("critical", False),
            )
            for line in bom
        ],
    )

    def lookup_stock(item_id: str) -> StockItem | None:
        try:
            status = stores.inventory_status(item_id)
        except KeyError:
            return None
        return StockItem(
            item_id=item_id,
            quantity=status.get("available", 0),
            reorder_point=status.get("reorder_point", 0),
        )

    inv_status = check_wo_parts_required(work_order, lookup_stock)

    seed_int = 0
    if inv_status.blocked:
        seed_var.set(seed_int)
        rule_hash_var.set(RULE_PACK_HASH)
        structlog.contextvars.bind_contextvars(seed=seed_int, rule_hash=RULE_PACK_HASH)
        logging.info("request complete")
        missing_parts = [
            {"item_id": res.item_id, "quantity": res.quantity}
            for res in inv_status.missing
        ]
        if strict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "blocked_by_parts": True,
                    "missing_parts": missing_parts,
                },
            )
        return ScheduleResponse(
            schedule=[],
            seed=str(seed_int),
            objective=0.0,
            blocked_by_parts=True,
            rulepack_sha256=RULE_PACK_HASH,
            rulepack_id=RULE_PACK_ID,
            rulepack_version=RULE_PACK_VERSION,
        )

    # Minimal demo task graph
    tasks = {
        "prep": Task(duration=1),
        "exec": Task(duration=2, predecessors=["prep"]),
    }

    mc_res = simulate(tasks, {}, runs=20)
    today = date.today()
    schedule: List[SchedulePoint] = []
    for i, pct in enumerate(mc_res.task_percentiles.values()):
        schedule.append(
            SchedulePoint(
                date=(today + timedelta(days=i)).isoformat(),
                p10=pct.get("P10", 0.0),
                p50=pct.get("P50", 0.0),
                p90=pct.get("P90", 0.0),
                price=0.0,
                hats=i + 1,
            )
        )

    seed_var.set(seed_int)
    rule_hash_var.set(RULE_PACK_HASH)
    structlog.contextvars.bind_contextvars(seed=seed_int, rule_hash=RULE_PACK_HASH)
    logging.info("request complete")
    return ScheduleResponse(
        schedule=schedule,
        seed=str(seed_int),
        objective=0.0,
        blocked_by_parts=False,
        rulepack_sha256=RULE_PACK_HASH,
        rulepack_id=RULE_PACK_ID,
        rulepack_version=RULE_PACK_VERSION,
    )


def _schedule_worker(
    job_id: str, payload: ScheduleRequest, strict: bool, user: OIDCUser
) -> None:
    """Background task to compute a schedule."""

    job = JOBS[job_id]
    job.status = "running"
    start = time.perf_counter()
    try:
        with tracer.start_as_current_span("schedule"):
            result = _generate_schedule(payload, strict, user)
    except HTTPException as exc:
        job.status = "failed"
        if isinstance(exc.detail, dict):
            job.result = exc.detail
        else:
            job.error = str(exc.detail)
    except Exception as exc:  # pragma: no cover - unexpected errors
        job.status = "failed"
        job.error = str(exc)
    else:
        job.result = result.model_dump()
        job.status = "done"
    finally:
        job_duration_seconds.observe(time.perf_counter() - start)


@app.post("/schedule", response_model=JobInfo, tags=["LOTO"], status_code=202)
async def post_schedule(
    payload: ScheduleRequest,
    background_tasks: BackgroundTasks,
    strict: bool = False,
    user: OIDCUser = Depends(require_planner),
) -> JobInfo:
    """Enqueue schedule generation in a background task."""

    job_id = str(uuid4())
    JOBS[job_id] = JobStatus(status="queued")
    background_tasks.add_task(_schedule_worker, job_id, payload, strict, user)
    return JobInfo(job_id=job_id)


@app.post("/plans", response_model=JobInfo, tags=["LOTO"], status_code=202)
async def post_plans(
    payload: ScheduleRequest, background_tasks: BackgroundTasks
) -> JobInfo:
    """Temporary alias for :func:`post_schedule` used in tests."""

    return await post_schedule(payload, background_tasks)


@app.get("/jobs/{job_id}", response_model=JobStatus, tags=["LOTO"])
async def get_job_status(job_id: str) -> JobStatus:
    """Return the status and result of a previously submitted job."""

    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/workorders/{workorder_id}/jobpack", tags=["LOTO"])
async def get_jobpack(
    workorder_id: str,
    permit_start: date | None = None,
    lead_days: int = DEFAULT_LEAD_DAYS,
) -> dict[str, object]:
    """Return a mock job pack for the given work order."""
    seed_int = 0
    seed_var.set(seed_int)
    rule_hash_var.set(RULE_PACK_HASH)
    structlog.contextvars.bind_contextvars(seed=seed_int, rule_hash=RULE_PACK_HASH)
    return build_jobpack(
        workorder_id,
        permit_start=permit_start,
        lead_days=lead_days,
        rulepack_sha256=RULE_PACK_HASH,
        rulepack_id=RULE_PACK_ID,
        rulepack_version=RULE_PACK_VERSION,
        seed=str(seed_int),
    )


@app.post("/commit/{workorder_id}", tags=["LOTO"], status_code=204)
async def post_commit(workorder_id: str, payload: CommitRequest) -> Response:
    """Commit changes for *workorder_id* after enforcing safety gates."""

    if not payload.sim_ok:
        raise HTTPException(status_code=400, detail={"code": "SIMULATION_RED"})
    if not all(payload.policies.values()):
        raise HTTPException(status_code=400, detail={"code": "POLICY_CHIPS_MISSING"})
    return Response(status_code=204)
