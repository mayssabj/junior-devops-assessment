# Junior DevOps Assessment — Solution

## Overview

This project containerizes a Task Manager API, connects it to PostgreSQL,
and orchestrates the services with Docker Compose.

The Day 4 improvements focus on:

1. Restart and resource policies
2. PostgreSQL database backups
3. Security hardening

---

## 1. Restart & Resource Policies

### Objective

Improve service resilience and prevent a single container from consuming
an excessive amount of host resources.

### Restart policy

All services use:

```yaml
restart: unless-stopped
