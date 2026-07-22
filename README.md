# Team Directory API

A REST API for a company employee directory, built with Flask. Full CRUD, JSON
persistence, custom exceptions mapped to HTTP status codes, console + file
logging, thread-safe concurrent writes, and API key auth on write endpoints.

## Setup

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```
venv\Scripts\python.exe main.py
```

Then open http://localhost:5000/ for a simple built-in HTML form, or call the
API directly with curl/Postman as shown below.

Optional environment variables (defaults shown), settable in `.env` or the shell:

```
API_KEY=dev-secret-key
PORT=5000
DIRECTORY_DB_PATH=directory.json
LOG_LEVEL=INFO
```

## Endpoints

All write endpoints (`POST`, `PUT`, `DELETE`) require an `X-API-Key` header
matching the `API_KEY` environment variable.

| Method | Path                     | Description                          | Auth |
|--------|--------------------------|---------------------------------------|------|
| POST   | /employees               | Create an employee (201)              | yes  |
| GET    | /employees               | List all employees (`?department=`)   | no   |
| GET    | /employees/search?q=     | Search by partial name match           | no   |
| GET    | /employees/{id}          | Fetch one employee (404 if missing)    | no   |
| PUT    | /employees/{id}          | Update an employee (404 / 409)         | yes  |
| DELETE | /employees/{id}          | Delete an employee (204)               | yes  |

### Examples

```
curl -X POST http://localhost:5000/employees \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d "{\"name\":\"Ann\",\"email\":\"ann@co.com\",\"department\":\"Eng\",\"role\":\"Dev\"}"

curl http://localhost:5000/employees
curl http://localhost:5000/employees?department=Eng
curl http://localhost:5000/employees/search?q=an
curl http://localhost:5000/employees/<employee_id>

curl -X PUT http://localhost:5000/employees/<employee_id> \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d "{\"name\":\"Ann Lee\",\"email\":\"ann@co.com\",\"department\":\"Eng\",\"role\":\"Lead\"}"

curl -X DELETE http://localhost:5000/employees/<employee_id> \
  -H "X-API-Key: dev-secret-key"
```

## Concurrency test

`test_concurrency.py` fires 20 simultaneous `POST /employees` requests
(each run tagged with a random id so re-running never collides with a
previous run's data) and reports how many were created, whether any
`employee_id`s were duplicated, and how long the run took.

```
venv\Scripts\python.exe test_concurrency.py
```

### Results

To make the race condition reliably reproducible (races are timing-dependent
and don't always show up on a fast local machine), `directory.py` has a
commented-out `time.sleep(0.05)` inside `save_to_file` — see the comment
there for how to re-enable it alongside temporarily removing the
`with self._lock:` in `add_employee`.

**Before — lock removed, artificial delay enabled:**

```
Run id: d6d8d5
Requests sent: 20
Created (201): 20
Failed (non-201): 0
Unique ids: 20
Elapsed: 2.116s
No duplicate ids in responses.
```

The API reported all 20 requests as successful, but `directory.json` on disk
was left corrupted — concurrent unlocked writes to the same file interleaved
mid-write:

```
$ python -c "import json; json.load(open('directory.json'))"
json.decoder.JSONDecodeError: Extra data: line 121 column 4 (char 2402)
```

Inspecting the file directly showed a record with duplicated keys from two
different writes merged together (`"department": "Eng", "role": "Dev",
"department": "Eng", "role": "Dev", ...`) and leftover JSON fragments
appended after the closing `]`. The server claimed success on every request;
the data it persisted did not match.

**After — lock restored, same artificial delay still enabled:**

```
Run id: 2effef
Requests sent: 20
Created (201): 20
Failed (non-201): 0
Unique ids: 20
Elapsed: 3.225s
No duplicate ids in responses.
```

`directory.json` was valid JSON with exactly 20 entries. The run took longer
(3.2s vs 2.1s) because the lock now serializes the 20 threads through the
critical section one at a time instead of letting them overlap — that
slowdown is the cost of correctness, and it's exactly what the lock is
supposed to do.

**Normal run — lock on, artificial delay off (the app's real, permanent
state):**

```
Run id: ec2d86
Requests sent: 20
Created (201): 20
Failed (non-201): 0
Unique ids: 20
Elapsed: 2.068s
No duplicate ids in responses.
```

Fast and clean — the lock only adds meaningful overhead when the artificial
delay is deliberately widening the race window for this demo.

## Deployment (Render)

The app is served in production via `gunicorn` (added to `requirements.txt`)
instead of Flask's development server. `render.yaml` defines the service:

- **Runtime**: Python
- **Build command**: `pip install -r requirements.txt`
- **Start command**: `gunicorn main:app`
- **Environment variables**: set `API_KEY` in Render's dashboard (marked
  `sync: false` so it's never committed); `DIRECTORY_DB_PATH` and
  `LOG_LEVEL` are set with sensible defaults; `PORT` is provided
  automatically by Render.

`gunicorn` only runs on Linux/Mac (it depends on the `fcntl` module, which
doesn't exist on Windows) — this doesn't block local development, since
`venv\Scripts\python.exe main.py` keeps working as before. Render's servers
run Linux, so `gunicorn main:app` runs there without issue.

**Known limitation**: Render's free-tier filesystem is ephemeral — anything
written to `directory.json` is lost on a redeploy/restart. Persistence
itself works correctly while the service is running; this is a platform
constraint, not an application bug. Swapping to a real database (see below)
would resolve it.

## What's next

- Swap JSON persistence for SQLite or a hosted database (Stretch 8) while
  keeping `EmployeeDirectory`'s public method signatures unchanged — this
  would also fix the Render free-tier persistence limitation above.
- Add automated tests (`pytest`) covering each endpoint's success and error
  paths instead of relying on manual curl checks.
- Add server-side pagination to `GET /employees` once the directory grows
  large (the current UI paginates client-side over the full list).
