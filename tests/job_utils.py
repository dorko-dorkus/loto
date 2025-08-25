import time
from typing import Any, Dict, cast

from fastapi.testclient import TestClient


def wait_for_job(
    client: TestClient, job_id: str, timeout: float = 5.0
) -> Dict[str, Any]:
    """Poll the /jobs/{id} endpoint until the job completes."""
    end = time.time() + timeout
    while time.time() < end:
        res = client.get(f"/jobs/{job_id}")
        if res.status_code == 429:
            retry = int(res.headers.get("Retry-After", "1"))
            time.sleep(retry)
            continue
        data = cast(Dict[str, Any], res.json())
        if data["status"] in {"done", "failed"}:
            return data
        time.sleep(0.01)
    raise TimeoutError(f"job {job_id} did not finish")
