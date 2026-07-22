import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests
from dotenv import load_dotenv

load_dotenv()

PORT = os.environ.get("PORT", "5000")
URL = f"http://localhost:{PORT}/employees"
API_KEY = os.environ.get("API_KEY", "dev-secret-key")

REQUEST_COUNT = 200
WORKERS = 20

# Unique per run so re-running the script never collides with employees
# created by a previous run.
RUN_ID = uuid.uuid4().hex[:6]


def create_one(i):
    payload = {
        "name": f"LoadUser{i}",
        "email": f"loaduser{i}-{RUN_ID}@co.com",
        "department": "Eng",
        "role": "Dev",
    }
    try:
        r = requests.post(URL, json=payload, headers={"X-API-Key": API_KEY}, timeout=10)
        return r.status_code, r.json()
    except requests.RequestException as exc:
        return None, {"error": str(exc)}


if __name__ == "__main__":
    print(f"Firing {REQUEST_COUNT} requests through {WORKERS} concurrent workers...")
    start = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(create_one, range(REQUEST_COUNT)))
    elapsed = time.time() - start

    created = [r for r in results if r[0] == 201]
    failed = [r for r in results if r[0] != 201]
    ids = [body.get("employee_id") for _, body in created]

    print(f"Run id: {RUN_ID}")
    print(f"Requests sent: {len(results)}")
    print(f"Created (201): {len(created)}")
    print(f"Failed (non-201): {len(failed)}")
    for status, body in failed[:10]:
        print(f"  -> {status}: {body}")
    if len(failed) > 10:
        print(f"  ... and {len(failed) - 10} more failures")
    print(f"Unique ids: {len(set(ids))}")
    print(f"Elapsed: {elapsed:.3f}s ({len(results) / elapsed:.1f} req/s)")

    if len(created) < REQUEST_COUNT:
        print(f"DATA LOST: only {len(created)}/{REQUEST_COUNT} requests were accepted.")
    if len(ids) != len(set(ids)):
        print("DUPLICATE IDS DETECTED -- unsafe!")
    else:
        print("No duplicate ids in responses -- system stable under load.")
