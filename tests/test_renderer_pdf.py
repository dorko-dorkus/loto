import io

from PyPDF2 import PdfReader

from loto.models import (
    IsolationAction,
    IsolationPlan,
    SimReport,
    SimResultItem,
    Stimulus,
)
from loto.renderer import Renderer


def test_pdf_contains_plan_id():
    plan = IsolationPlan(
        plan_id="plan-123",
        actions=[IsolationAction(component_id="A", method="lock", duration_s=1.0)],
    )
    stim = Stimulus(name="stim1", magnitude=1.0, duration_s=1.0)
    sim = SimReport(
        results=[SimResultItem(stimulus=stim, success=True, impact=0.1)],
        total_time_s=1.0,
    )

    pdf_bytes = Renderer().pdf(
        plan, sim, rule_hash="abc123", seed=42, timezone="Pacific/Auckland"
    )

    assert pdf_bytes, "pdf() should return non-empty bytes"

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(page.extract_text() for page in reader.pages)
    assert "Work Order ID: plan-123" in text
    assert "Rule Pack Hash: abc123" in text
    assert "Seed: 42" in text
    assert "Timezone: Pacific/Auckland" in text
    assert "Because" in text
