# Starter App

A minimal FastAPI service with three endpoints:

- `GET /` - basic liveness message
- `GET /health` - checks it can reach PostgreSQL
- `GET /tasks` / `POST /tasks` - list/create rows in a `tasks` table

You are not expected to know FastAPI. You will not need to write or
understand application logic to complete this assessment - treat this
as "the app my team handed me to deploy."

If you want to run it directly on your machine (outside Docker) to
poke at it first:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DB_HOST=localhost DB_PORT=5432 DB_NAME=taskdb DB_USER=postgres DB_PASSWORD=postgres
uvicorn main:app --reload --port 8000
```

This requires a PostgreSQL instance already running locally - which
is exactly the kind of dependency you'll be containerizing.
