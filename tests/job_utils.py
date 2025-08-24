import time

from fastapi.testclient import TestClient


def wait_for_job(client: TestClient, job_id: str, timeout: float = 5.0):
    """Poll the /jobs/{id} endpoint until the job completes."""
    end = time.time() + timeout
    while time.time() < end:
        res = client.get(f"/jobs/{job_id}")
        data = res.json()
        if data["status"] in {"done", "failed"}:
            return data
        time.sleep(0.01)
    raise TimeoutError(f"job {job_id} did not finish")
