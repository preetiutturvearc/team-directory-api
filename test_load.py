import asyncio
import os
import time
import uuid
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("BASE_URL", "https://team-directory.onrender.com")
API_KEY = os.environ.get("API_KEY", "dev-secret-key")

TOTAL_USERS = 200

passed = 0
failed = 0

results = []

start_event = asyncio.Event()


def generate_html_report(total_duration):
    os.makedirs("reports", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/load_test_report_{timestamp}.html"

    success_rate = (passed / TOTAL_USERS) * 100

    response_times = [r["response_time"] for r in results if r["response_time"] is not None]

    avg_time = sum(response_times) / len(response_times) if response_times else 0
    min_time = min(response_times) if response_times else 0
    max_time = max(response_times) if response_times else 0

    rows = ""
    for r in sorted(results, key=lambda x: x["user"]):
        color = "#28a745" if r["status"] == "PASS" else "#dc3545"
        rows += f"""
        <tr>
            <td>{r['user']}</td>
            <td>{r['employee_id']}</td>
            <td style="color:{color};font-weight:bold;">
                {r['status']}
            </td>
            <td>{r['response_time']:.2f} ms</td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>Employee Load Test Report</title>
<style>
body {{
    font-family: Arial;
    background: #f4f6f9;
    margin: 30px;
}}
h1 {{
    text-align: center;
    color: #2c3e50;
}}
.container {{
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 30px;
}}
.card {{
    background: white;
    padding: 20px;
    width: 220px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,.2);
    text-align: center;
}}
.card h2 {{
    margin: 0;
    color: #007bff;
}}
.card p {{
    font-size: 22px;
    font-weight: bold;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
}}
th {{
    background: #007bff;
    color: white;
    padding: 12px;
}}
td {{
    padding: 10px;
    text-align: center;
    border: 1px solid #ddd;
}}
tr:nth-child(even) {{
    background: #f2f2f2;
}}
.footer {{
    margin-top: 30px;
    text-align: center;
    font-size: 14px;
    color: gray;
}}
</style>
</head>
<body>

<h1>Employee Load Test Report</h1>
<p><b>Execution Time:</b> {datetime.now().strftime("%d-%b-%Y %H:%M:%S")}</p>

<div class="container">
    <div class="card">
        <h2>Total Users</h2>
        <p>{TOTAL_USERS}</p>
    </div>
    <div class="card">
        <h2>Created</h2>
        <p>{passed}</p>
    </div>
    <div class="card">
        <h2>Failed</h2>
        <p>{failed}</p>
    </div>
    <div class="card">
        <h2>Success Rate</h2>
        <p>{success_rate:.2f}%</p>
    </div>
    <div class="card">
        <h2>Total Duration</h2>
        <p>{total_duration:.2f} sec</p>
    </div>
    <div class="card">
        <h2>Average Response</h2>
        <p>{avg_time:.2f} ms</p>
    </div>
    <div class="card">
        <h2>Minimum Response</h2>
        <p>{min_time:.2f} ms</p>
    </div>
    <div class="card">
        <h2>Maximum Response</h2>
        <p>{max_time:.2f} ms</p>
    </div>
</div>

<h2>User Results</h2>
<table>
<tr>
    <th>User</th>
    <th>Employee ID</th>
    <th>Status</th>
    <th>Response Time</th>
</tr>
{rows}
</table>

<div class="footer">
    Generated automatically by Python Concurrent Load Test
</div>

</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n======================================")
    print(" Load Test Completed Successfully")
    print("======================================")
    print(f"Total Users : {TOTAL_USERS}")
    print(f"Created     : {passed}")
    print(f"Failed      : {failed}")
    print(f"Duration    : {total_duration:.2f} sec")
    print(f"Report      : {filename}")


async def create_employee(user_id, client):
    global passed, failed

    await start_event.wait()

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "name": f"Employee {user_id}",
        "email": f"{uuid.uuid4().hex}@company.com",
        "department": "QA",
        "role": "Tester",
    }

    start = time.perf_counter()

    try:
        response = await client.post(f"{BASE_URL}/employees", json=payload, headers=headers)
        response_time = (time.perf_counter() - start) * 1000

        if response.status_code == 201:
            employee = response.json()
            passed += 1
            results.append({
                "user": user_id,
                "employee_id": employee["employee_id"],
                "status": "PASS",
                "response_time": response_time,
            })
        else:
            failed += 1
            results.append({
                "user": user_id,
                "employee_id": "-",
                "status": "FAIL",
                "response_time": response_time,
            })

    except Exception:
        response_time = (time.perf_counter() - start) * 1000
        failed += 1
        results.append({
            "user": user_id,
            "employee_id": "-",
            "status": "ERROR",
            "response_time": response_time,
        })


async def main():
    overall_start = time.perf_counter()

    async with httpx.AsyncClient(timeout=30) as client:
        tasks = [asyncio.create_task(create_employee(i, client)) for i in range(1, TOTAL_USERS + 1)]

        print(f"\n{TOTAL_USERS} users are ready.")
        print("Launching all users simultaneously...\n")

        start_event.set()
        await asyncio.gather(*tasks)

    duration = time.perf_counter() - overall_start
    generate_html_report(duration)


if __name__ == "__main__":
    asyncio.run(main())
