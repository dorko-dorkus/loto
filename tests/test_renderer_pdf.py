import hashlib
import io
import re
from datetime import datetime
from unittest.mock import patch

from PyPDF2 import PdfReader

from loto.models import (
    IsolationAction,
    IsolationPlan,
    SimReport,
    SimResultItem,
    Stimulus,
)
from loto.renderer import Renderer


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return datetime(2024, 1, 1, 0, 0, tzinfo=tz)


def test_pdf_contains_stamps_and_is_deterministic():
    plan = IsolationPlan(
        plan_id="plan-123",
        actions=[IsolationAction(component_id="A", method="lock", duration_s=1.0)],
    )
    stim = Stimulus(name="stim1", magnitude=1.0, duration_s=1.0)
    sim = SimReport(
        results=[SimResultItem(stimulus=stim, success=True, impact=0.1)],
        total_time_s=1.0,
    )

    renderer = Renderer()
    with patch("loto.renderer.datetime", _FixedDatetime):
        pdf_bytes1 = renderer.pdf(
            plan, sim, rule_hash="abc123", seed=42, timezone="Pacific/Auckland"
        )
        pdf_bytes2 = renderer.pdf(
            plan, sim, rule_hash="abc123", seed=42, timezone="Pacific/Auckland"
        )

    assert pdf_bytes1 and pdf_bytes2, "pdf() should return non-empty bytes"

    reader1 = PdfReader(io.BytesIO(pdf_bytes1))
    reader2 = PdfReader(io.BytesIO(pdf_bytes2))
    text1 = "".join(page.extract_text() for page in reader1.pages)
    text2 = "".join(page.extract_text() for page in reader2.pages)
    assert text1 == text2
    assert (
        hashlib.sha256(text1.encode()).hexdigest()
        == hashlib.sha256(text2.encode()).hexdigest()
    )

    assert "WO: plan-123" in text1
    assert "Rule Hash: abc123" in text1
    assert "Seed: 42" in text1
    assert re.search(r"Generated: \d{4}-\d{2}-\d{2} \d{2}:\d{2} (NZDT|NZST)", text1)
    assert "DRY-RUN" in text1
    assert "Because" in text1
