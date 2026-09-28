# Smart Campus Management Platform

A full-stack academic management platform with role-based workflows for students,
professors, and administrators. Built as a software engineering portfolio project
using FastAPI, PostgreSQL, and React.

## Overview

Smart Campus connects academic administration, enrollment, teaching, and grading
in one application. Administrators define the academic structure, students enroll
in course offerings, and assigned professors manage rosters and grades.

## Key Features

- JWT authentication and API-enforced role-based authorization.
- PostgreSQL relational model and a documented REST API.
- Responsive React interface with role-aware navigation and protected routes.
- Docker Compose environment with nginx, database persistence, and SQL migrations.
- Automated backend tests covering authentication, authorization, and academic workflows.

## Role-Based Workflows

| Role | Capabilities |
| --- | --- |
| Student | Manage academic profile; browse courses and offerings; enroll or drop; view enrollment history, grades, and professor feedback. |
| Professor | Manage professor profile; view assigned offerings and student rosters; create and update numeric grades and feedback. |
| Administrator | Manage users, departments, courses, academic terms, and course offerings. |

Grades are recorded on a 0–100 scale. Recording a grade completes the enrollment.
User, department, and course deactivation retains the underlying records; the
current department and course lists show active records only.

```mermaid
flowchart LR
    A[Admin creates academic structure] --> B[Student enrolls]
    B --> C[Professor views roster]
    C --> D[Professor records grade]
    D --> E[Student views grade and feedback]
```

## Architecture

```mermaid
flowchart LR
    browser[Browser]
    subgraph compose[Docker Compose]
        frontend[frontend: nginx + React build]
        subgraph backend[backend]
            api[FastAPI REST API: JWT authentication and RBAC]
            orm[SQLAlchemy]
        end
        migrate[migrate: one-shot SQL runner]
        db[(db: PostgreSQL)]
        frontend -->|/api/ proxy| api
        api --> orm
        orm --> db
        migrate -->|Ordered SQL migrations| db
    end
    browser --> frontend
```

Routers handle HTTP requests, services implement business operations, Pydantic
schemas validate inputs and responses, and SQLAlchemy manages persistence.
The frontend separates API services, authentication state, route guards, and
pages. nginx serves the production build and supports direct React Router links.

Startup order: **database healthy → migrations successful → backend healthy → frontend**.

## Tech Stack

| Area | Technologies |
| --- | --- |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy 2.x, psycopg |
| Database | PostgreSQL 17, ordered SQL migrations |
| Authentication | JWT, Argon2 password hashing, role-based authorization |
| Frontend | React, TypeScript, Vite, React Router, Axios, CSS |
| Runtime | Docker Compose, nginx |
| Testing | pytest; SQLite in-memory databases for automated backend tests |

## Project Structure

```text
backend/
├── app/                 # API routers, services, models, schemas, configuration
├── migrations/          # Ordered PostgreSQL SQL migrations
├── scripts/             # Docker migration runner
├── tests/               # Backend test suite
├── Dockerfile
└── requirements.txt
frontend/
├── src/                 # Pages, components, services, hooks, routes, types
├── Dockerfile
├── nginx.conf
└── package.json
docs/
└── screenshots/         # Reserved for application screenshots
compose.yaml
.env.example
```

## Getting Started with Docker

Prerequisites: Git, Docker with Compose, and Python 3 to generate a secret.

```sh
git clone https://github.com/OuassimLh-dev/smart-campus-platform.git
cd smart-campus-platform
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Paste the generated value into `JWT_SECRET_KEY` in `.env` (at least 32 characters).
Do not commit this file. Then start the stack:

```sh
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
```

Open [Smart Campus](http://localhost:8080). The backend is available on port 8000.
Both published ports bind to loopback. PostgreSQL is internal to the stack and
uses the persistent `campus_postgres` volume, separate from host PostgreSQL data.

Compose supplies the container database URL. The optional `POSTGRES_PASSWORD`
uses a local-development default; set it before first startup to override it,
using URL-safe characters. No default JWT secret is supplied.

A fresh database contains no accounts or academic data. Student accounts can be
registered through the API documentation; there is no registration UI or seeded
demo login. Professor and administrator access requires an appropriately
provisioned account. The admin user-creation API does not assign a password.

Stop the stack while retaining data:

```sh
docker compose down
```

**Warning: the following command deletes the Docker database volume and its data.**

```sh
docker compose down -v
```

## Local Development

Prerequisites: Python 3.13 (used by the backend Docker image), PostgreSQL with
`psql`, and Node.js 22.12 or newer with npm. Commands below use a POSIX shell.
Stop the Docker stack first if its backend occupies port 8000.

Create a PostgreSQL database and login role, then create the root `.env` from
[.env.example](.env.example) if it does not exist. Set `DATABASE_URL` to your local
connection, generate `JWT_SECRET_KEY` as above, and retain `JWT_ALGORITHM=HS256`.
`ACCESS_TOKEN_EXPIRE_MINUTES` controls access-token lifetime.

For a **fresh local database only**, apply the SQL files in order. Set libpq
connection variables for your database; `psql` prompts for its password:

```sh
export PGHOST=localhost PGPORT=5432 PGUSER=campus_user PGDATABASE=smart_campus
for migration in backend/migrations/*.sql; do
  psql -X -v ON_ERROR_STOP=1 -f "$migration" || break
done
```

This manual bootstrap does not create Docker's migration tracking records. Do not
rerun it against an initialized database; apply only pending files when maintaining
a local database. Docker is the primary path for automatic tracked migrations.

Start the backend from the repository root:

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, from the repository root:

```sh
cd frontend
cp .env.example .env
npm install
npm run dev
```

The frontend example sets `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`.
Open [the Vite frontend](http://localhost:5173). Local CORS permits only
`http://localhost:5173` and `http://127.0.0.1:5173`. In Docker, the frontend uses
same-origin `/api/v1` requests through nginx instead.

## Database Migrations

The one-shot `migrate` service mounts [backend/migrations](backend/migrations)
read-only and applies SQL files in filename order. It uses `psql` with
`ON_ERROR_STOP=1`; each migration retains its own `BEGIN`/`COMMIT` transaction.
Successful filenames are recorded in `public.schema_migrations` and skipped on
future runs. A session advisory lock serializes concurrent migration runners.
A failure prevents initial backend startup.

Do not modify previously applied migrations. Add a new ordered migration for a
schema change. Existing databases created outside this runner are not
automatically marked as migrated. If execution is interrupted between a file's
COMMIT and its tracking insert, inspect the schema and tracking table before
retrying. There is no automatic rollback or migration-baselining tool.

## Testing

From the repository root, with backend dependencies installed:

```sh
cd backend
source .venv/bin/activate
python -m pytest
```

The current backend suite contains **288 tests** and uses isolated SQLite
in-memory databases; it does not require a running PostgreSQL instance.

From the repository root, with frontend dependencies installed:

```sh
cd frontend
npm run typecheck
npm run build
```

The production build includes TypeScript compilation. It is a build check, not
an automated browser test suite. Validate Compose configuration from the root:

```sh
docker compose config --quiet
```

## Continuous Integration

[GitHub Actions CI](.github/workflows/ci.yml) runs on pushes to `main` and pull
requests targeting `main`. Independent jobs run the backend pytest suite,
frontend TypeScript checks and production build, and Docker Compose validation,
image builds, and integration startup. Docker checks verify both health endpoints
and the `/grades` SPA route, then always tear down the stack and its volumes.
CI uses disposable test configuration and read-only repository permissions.
Newer runs for the same ref cancel older in-progress runs.

## API Documentation

With the backend running:

- [Swagger UI](http://localhost:8000/docs)
- [OpenAPI schema](http://localhost:8000/openapi.json)
- Health endpoint: `GET /api/v1/health` → `{"status":"ok"}`

Health is also available [through nginx](http://localhost:8080/api/v1/health).
The health endpoint reports API availability, not a database readiness check.

## Security / Authentication

Passwords are hashed with Argon2; API responses exclude password hashes.
Login returns an expiring JWT access token, and API dependencies enforce the
current user's active status, role, and resource ownership. Frontend route guards
support navigation but do not replace backend authorization.

The portfolio frontend stores its token in `sessionStorage`, which is accessible
to JavaScript. Public registration is limited to students. Secrets are loaded
from environment configuration and excluded from image build contexts. Refresh
tokens, password reset, email verification, and OAuth are outside the current scope.

## Screenshots

### Login

![Smart Campus login](docs/screenshots/login.png)

### Student Grades

![Student grades workflow](docs/screenshots/student-grades.png)

### Professor Roster and Grading

![Professor roster and grading](docs/screenshots/professor-roster.png)

### Admin Course Offering Management

![Admin course offering management](docs/screenshots/admin-management.png)

## Current Scope / Future Improvements

The implemented scope covers role-based academic administration, enrollment,
and grading. It is a portfolio application, not a production deployment.
Potential next steps include frontend integration tests, PostgreSQL integration
tests, stronger migration recovery, account provisioning, and deployment
hardening. Attendance, assignments, messaging, notifications, GPA calculations,
and transcripts are not implemented.

## Author

Ouassim Lahraoui — Software Engineering Student
