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

# Unique per run so re-running the script never collides with employees
# created by a previous run (avoids false "failures" that are actually
# just 409 duplicate-email rejections from stale data).
RUN_ID = uuid.uuid4().hex[:6]


def create_one(i):
    payload = {
        "name": f"User{i}",
        "email": f"user{i}-{RUN_ID}@co.com",
        "department": "Eng",
        "role": "Dev",
    }
    r = requests.post(URL, json=payload, headers={"X-API-Key": API_KEY})
    return r.status_code, r.json()


if __name__ == "__main__":
    start = time.time()
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(create_one, range(20)))
    elapsed = time.time() - start

    created = [r for r in results if r[0] == 201]
    failed = [r for r in results if r[0] != 201]
    ids = [body.get("employee_id") for _, body in created]

    print(f"Run id: {RUN_ID}")
    print(f"Requests sent: {len(results)}")
    print(f"Created (201): {len(created)}")
    print(f"Failed (non-201): {len(failed)}")
    for status, body in failed:
        print(f"  -> {status}: {body}")
    print(f"Unique ids: {len(set(ids))}")
    print(f"Elapsed: {elapsed:.3f}s")

    if len(created) < 20:
        print(f"DATA LOST: only {len(created)}/20 requests were accepted (server-side error).")
    if len(ids) != len(set(ids)):
        print("DUPLICATE IDS DETECTED -- unsafe!")
    else:
        print("No duplicate ids in responses.")
