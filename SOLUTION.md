# Junior DevOps Assessment — Solution

## Repository

GitHub repository:

https://github.com/mayssabj/junior-devops-assessment

GitHub Actions:

https://github.com/mayssabj/junior-devops-assessment/actions

The final commit is:

```text
c60ecec feat: harden stack and add database backups
```

The CI workflow was executed successfully on the final commit.

---

## Overview

This project containerizes a Task Manager API, connects it to PostgreSQL,
and orchestrates the services with Docker Compose.

The implementation was done incrementally:

* Day 1: Docker containerization
* Day 2: Docker Compose, PostgreSQL and persistence
* Day 3: CI with GitHub Actions
* Day 4: resilience, backups and security hardening

The application code in `starter-app/main.py` was intentionally left
unchanged, as the assessment instructions state that the starter
application is provided and the DevOps work should focus on
containerization, infrastructure and orchestration.

---

## 1. How to Run Everything from a Clean Checkout

### Prerequisites

The following tools are required:

* Git
* Docker
* Docker Compose v2

### Clone the repository

```bash
git clone https://github.com/mayssabj/junior-devops-assessment.git
cd junior-devops-assessment
```

### Create the environment file

The real `.env` file is intentionally not committed.

Create it from the provided example:

```bash
cp .env.example .env
```

For a local assessment environment, the example values can be used as-is.

### Start the stack

```bash
docker compose up -d --build
```

### Check the services

```bash
docker compose ps
```

PostgreSQL should become `healthy`.

### Test the API

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","database":"connected"}
```

The API is available at:

```text
http://localhost:8000
```

The pgAdmin interface is available locally at:

```text
http://localhost:5050
```

PostgreSQL is intentionally not published to the host. The API connects
to it internally using:

```text
db:5432
```

### Stop the stack

```bash
docker compose down
```

The PostgreSQL data volume is preserved.

To remove the containers and the PostgreSQL volume:

```bash
docker compose down -v
```

---

## 2. Day 1 — Docker Containerization

### Objective

Containerize the provided FastAPI application without modifying its
application logic.

### Implementation

The Dockerfile:

* uses Python 3.12 slim;
* installs dependencies from `requirements.txt`;
* copies the starter application;
* exposes port 8000;
* runs Uvicorn on `0.0.0.0:8000`;
* creates a dedicated non-root `appuser`.

The dependency file is copied before the source code to improve Docker
layer caching.

### Important assumption

The application expects its database configuration through:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

Running the API container alone without PostgreSQL therefore does not
provide a complete working environment. The application itself was not
modified to work around this dependency.

---

## 3. Day 2 — Docker Compose and PostgreSQL

### Objective

Orchestrate the API and PostgreSQL using Docker Compose.

### Services

The Compose stack contains:

| Service   | Purpose                   | Port             |
| --------- | ------------------------- | ---------------- |
| `app`     | FastAPI Task Manager API  | `8000`           |
| `db`      | PostgreSQL 17             | Internal only    |
| `pgadmin` | PostgreSQL administration | `127.0.0.1:5050` |

### PostgreSQL

PostgreSQL uses the official:

```text
postgres:17
```

image.

Database data is persisted using the named volume:

```text
postgres_data
```

The database has a healthcheck using `pg_isready`.

The API and pgAdmin depend on the database healthcheck before starting.

### Persistence validation

The API was used to create tasks and the PostgreSQL data was verified
through pgAdmin.

The stack was also stopped and restarted to confirm that the database
volume preserves the data.

---

## 4. Day 3 — Continuous Integration

### CI implementation

The GitHub Actions workflow is located at:

```text
.github/workflows/ci.yml
```

The workflow:

1. checks out the repository;
2. creates a CI `.env` from `.env.example`;
3. builds the Docker image;
4. starts the Docker Compose stack;
5. waits for the API health endpoint;
6. verifies `/health`;
7. shuts down the stack.

The workflow runs on both:

```yaml
push:
pull_request:
```

### Validation

The initial CI run passed successfully.

The final Day 4 commit also triggered the CI workflow successfully.

This provides a basic automated verification that the Docker image can
be built and that the complete Compose stack can start correctly.

---

## 5. Day 4 — Selected Improvements

For Day 4, I selected:

1. Restart & resource policies
2. Database backups
3. Security pass

I selected these because they address three different operational
concerns:

* resilience;
* recoverability;
* security and least privilege.

The goal was to improve the operational characteristics of the stack
without modifying the application code.

---

## 6. Restart & Resource Policies

### Restart policy

All services use:

```yaml
restart: unless-stopped
```

This allows Docker to automatically restart services after an
unexpected container failure while still allowing an intentional
manual stop.

### Resource limits

The following limits were configured:

| Service    | CPU limit | Memory limit |
| ---------- | --------- | ------------ |
| PostgreSQL | 1 CPU     | 512 MiB      |
| API        | 0.5 CPU   | 256 MiB      |
| pgAdmin    | 0.5 CPU   | 512 MiB      |

The pgAdmin memory limit was increased from 256 MiB to 512 MiB after
observing that its runtime memory usage was close to the original limit.

### Validation

Configuration:

```bash
docker compose config
```

Runtime resources:

```bash
docker stats --no-stream
```

API health:

```bash
curl http://localhost:8000/health
```

Expected result:

```json
{"status":"ok","database":"connected"}
```

---

## 7. Database Backups

### Objective

Provide a repeatable PostgreSQL backup mechanism and verify that a
generated backup can actually be restored.

### Backup script

The backup procedure is implemented in:

```text
scripts/backup.sh
```

The script:

* creates the `backups/` directory if necessary;
* verifies that PostgreSQL is running;
* executes `pg_dump` inside the database container;
* creates timestamped SQL dumps;
* verifies that the backup is not empty;
* keeps the seven most recent backups.

Example:

```text
backups/taskdb_20260917_153950.sql
```

### Credentials

No PostgreSQL password is hardcoded in the backup script.

The script uses:

```bash
$POSTGRES_USER
$POSTGRES_DB
```

from the environment already available inside the PostgreSQL container.

### Retention

The script keeps the seven most recent:

```text
taskdb_*.sql
```

backup files and removes older ones.

### Git protection

Database dumps are excluded from Git:

```gitignore
backups/*
!backups/.gitkeep
```

The actual database contents therefore remain local.

### Restore validation

A temporary database named:

```text
taskdb_restore_test
```

was created.

The generated backup was restored into this database and queried with:

```sql
SELECT * FROM tasks ORDER BY id;
```

The restored database contained the expected task records.

The temporary database was then removed.

This confirms that the backup was not only generated successfully but
was also usable for recovery.

---

## 8. Security Pass

### 8.1 Non-root application

The Dockerfile creates a dedicated application user:

```dockerfile
RUN useradd --create-home --shell /bin/bash appuser
```

and runs the API using:

```dockerfile
USER appuser
```

This avoids running the application process as root.

### 8.2 Least-privilege environment variables

The API receives only the database variables it requires:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

pgAdmin receives only:

```text
PGADMIN_DEFAULT_EMAIL
PGADMIN_DEFAULT_PASSWORD
```

The database service receives only:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

This avoids unnecessarily exposing unrelated environment variables to
containers.

### 8.3 PostgreSQL not exposed to the host

PostgreSQL does not publish port 5432.

It is reachable by the other Compose services through:

```text
db:5432
```

### 8.4 pgAdmin restricted to localhost

pgAdmin is published as:

```yaml
ports:
  - "127.0.0.1:${PGADMIN_PORT}:80"
```

Therefore it is available locally through:

```text
http://localhost:5050
```

without binding the service to all host network interfaces.

### 8.5 Local secrets and database dumps

The real `.env` file is excluded from Git:

```gitignore
.env
```

Database dumps are also excluded:

```gitignore
backups/*
!backups/.gitkeep
```

A sanitized `.env.example` is provided for reproducibility.

---

## 9. Assumptions

The following assumptions were made:

1. Docker and Docker Compose are available on the machine running the
   assessment.
2. The assessment is intended to run locally, so the default credentials
   in `.env.example` are acceptable for the local environment.
3. The provided FastAPI application is considered the application
   boundary and its logic should not be modified.
4. PostgreSQL persistence is required across normal container restarts,
   so a named Docker volume is used.
5. pgAdmin is useful for local database administration but should not be
   publicly exposed.
6. The backup requirement is interpreted as PostgreSQL logical backups
   using `pg_dump`, rather than physical PostgreSQL backups.

---

## 10. Trade-offs and What I Would Do Differently in Production

This solution is designed for a local DevOps assessment rather than a
real production deployment.

### Secrets

For production, I would not store passwords in a local `.env` file.
I would use a proper secret-management mechanism such as Docker secrets,
Kubernetes Secrets integrated with a secret manager, or a cloud secret
management service.

### Backup storage

The current backup script stores dumps locally.

In production, backups should be copied to durable external storage,
preferably object storage with:

* encryption;
* restricted access;
* lifecycle policies;
* retention policies;
* versioning or immutability where appropriate.

### Backup automation

The current script is manually executed.

In production, it would be scheduled and monitored. Backup failures
should generate alerts.

### Restore testing

A production system should periodically perform automated restore tests,
not only create backups.

The restore process should also have defined RPO and RTO targets.

### PostgreSQL high availability

A single PostgreSQL container is appropriate for this assessment but is
not a highly available production database architecture.

For production, I would consider managed PostgreSQL or a properly
designed PostgreSQL HA solution with replication and tested failover.

### Container image security

With more time, I would add:

* image vulnerability scanning;
* dependency scanning;
* pinned image digests;
* SBOM generation;
* container security checks.

### CI/CD

The current CI validates build and application health.

For a production pipeline, I would additionally include:

* automated API tests;
* linting;
* security scanning;
* image scanning;
* image publishing to a registry;
* deployment to a staging environment;
* deployment approval gates.

### Observability

A production deployment would need centralized logs, metrics and
alerts with defined SLOs/SLIs rather than relying only on the Compose
healthcheck.

---

## 11. Approximate Time Spent

The times below are approximate.

| Day   | Main work                                                                    | Approx. time |
| ----- | ---------------------------------------------------------------------------- | ------------ |
| Day 1 | Dockerfile, image build and container validation                             | ~1–2 h       |
| Day 2 | Docker Compose, PostgreSQL, persistence and pgAdmin                          | ~2–3 h       |
| Day 3 | GitHub Actions CI and validation                                             | ~1–2 h       |
| Day 4 | Resource limits, backups, restore test, security hardening and documentation | ~3–4 h       |

The exact time includes troubleshooting, validation and documentation,
not only writing the configuration files.

---

## 12. Final Validation

The final Compose configuration was validated with:

```bash
docker compose config
```

The services were started with:

```bash
docker compose up -d
```

The service status was checked with:

```bash
docker compose ps
```

The API returned:

```json
{"status":"ok","database":"connected"}
```

A PostgreSQL backup was generated with:

```bash
./scripts/backup.sh
```

The backup was restored into a temporary database and the restored
records were verified.

The final commit was pushed to GitHub and the GitHub Actions CI workflow
passed for that commit.

---

## 13. Final Repository Structure

Relevant DevOps files:

```text
.
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── docker-compose.yml
├── SOLUTION.md
├── backups/
│   └── .gitkeep
├── scripts/
│   └── backup.sh
└── starter-app/
    ├── main.py
    └── requirements.txt
```

The real `.env` file and generated SQL database backups are intentionally
not committed.

