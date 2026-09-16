"""
Task Manager API - starter application.

You do NOT need to modify this file to complete the assessment
(though you may, if you think it helps). Your job is to containerize
it, wire it up to PostgreSQL, and orchestrate it with docker-compose.

It reads its database connection settings from environment variables:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import os
import time

import psycopg2
from fastapi import FastAPI, HTTPException
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

app = FastAPI(title="Task Manager API")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "taskdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )


class Task(BaseModel):
    title: str
    done: bool = False


@app.on_event("startup")
def startup() -> None:
    """Create the tasks table on boot, retrying briefly in case the
    database container isn't ready yet."""
    last_error = None
    for _ in range(10):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN DEFAULT FALSE
                )
                """
            )
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2)
    raise RuntimeError(f"Could not connect to database on startup: {last_error}")


@app.get("/")
def root():
    return {"message": "Task Manager API is running"}


@app.get("/health")
def health():
    try:
        conn = get_connection()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")


@app.get("/tasks")
def list_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
        (task.title, task.done),
    )
    new_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_task
