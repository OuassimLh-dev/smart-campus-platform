# Smart Campus Management Platform

A full-stack campus management system designed to manage students, courses,
faculty, enrollment, grades, and administrative operations.

## Status

🚧 Currently under development.

## Planned Technology Stack

- Python
- FastAPI
- PostgreSQL
- React
- Docker

## Author

Ouassim Lahraoui  
Software Engineering Student
### Professor workflow

Professors can create or edit their academic profile at `/professor/profile`, then
open `/professor/courses` to view offerings assigned to their profile (20 per
page). Each offering links to its roster at
`/professor/courses/:offeringId/students`. The roster combines student identities,
enrollment status, and existing grades. Add a grade from 0–100 (up to two decimal
places) with optional feedback, or explicitly edit an existing grade. Saving an
edit replaces the grade and feedback; recording a grade completes the enrollment.

These pages require an authenticated professor. Other roles are redirected to the
dashboard, and the backend independently enforces offering ownership for rosters
and grades. An unassigned professor receives a permission error without roster or
grade controls. No backend API changes are required.

The frontend uses professor profile endpoints (`GET/PATCH /professors/me`,
`POST /professors/profile`), the filtered offering list
(`GET /course-offerings?professor_id=...&skip=...&limit=20`), offering details,
`GET /course-offerings/{id}/students`, and
`GET /course-offerings/{id}/grades`. Course, term, and professor detail endpoints
supply display labels. Grading uses `POST` and `PATCH /enrollments/{id}/grade`.
All paths use the existing `/api/v1` base and authenticated Axios client.

Verification from the repository root:

```sh
cd backend
.venv/bin/python -m pytest -q
cd ../frontend
npm ci
npm run typecheck
npm run build
```

Run the frontend with `npm run dev` from `frontend/`, alongside the existing
backend. No new environment variables or dependencies are needed.


### Admin workflow

Admin navigation now links to `/admin/users`, `/admin/departments`,
`/admin/courses`, `/admin/terms`, and `/admin/course-offerings`. These routes
reuse the authenticated session and require the admin role; other authenticated
roles return to `/dashboard`. The backend independently authorizes mutations.
Student and professor routes and navigation remain unchanged.

- Users: paginated listing, edit names/email/role/active status, and confirmed
  deactivation. There is no user creation UI. Existing academic profiles may
  prevent incompatible role changes; the backend conflict is shown in the form.
  Deactivating or demoting the signed-in admin ends the local session.
- Departments: create/edit code, name, description, and active status; confirmed
  deactivation retains the record. Only active departments appear in the existing
  backend list.
- Courses: create/edit code, title, description, positive integer credits,
  department, optional professor, and active status; confirmed deactivation.
  Only active courses appear in the existing backend list.
- Terms: create/edit name, academic year, ordered dates, and active status.
  No delete action is provided.
- Offerings: create/edit course, professor, term, section, positive integer
  capacity, and open status. Filter by course, professor, term, or open status.
  No delete action is provided. Backend conflicts such as duplicate sections or
  capacity below occupied seats are displayed without discarding form values.

Lists use 20-record pages. Selectors load all pages of available reference data.
Professor labels use real employee numbers, academic titles, and departments;
no names are invented. Existing references absent from active lists remain
selectable when editing, with their IDs clearly identified.

The shared admin page and form use field definitions matching the backend
schemas, typed records, and a separate Axios service. Required fields, positive
integers, and term date order are validated before saving. Backend validation
and duplicate errors use the existing error helper. Forms disable while saving;
deactivation requires confirmation, including when changing the Active checkbox.

Admin API calls (all under `/api/v1`):

- `GET /users`, `PATCH /users/{id}`, `DELETE /users/{id}`
- `GET/POST /departments`, `PATCH/DELETE /departments/{id}`
- `GET/POST /courses`, `PATCH/DELETE /courses/{id}`
- `GET/POST /terms`, `PATCH /terms/{id}`
- `GET/POST /course-offerings`, `PATCH /course-offerings/{id}`
- `GET /professors` for professor assignment selectors
- Existing `POST /auth/login` and `GET /auth/me` for authentication

Two backend changes support the admin UI: an admin-only paginated professor
profile listing (previously profiles could only be retrieved by known ID), and
DELETE in local CORS methods for existing soft-deletion endpoints. The only
allowed origins remain `http://127.0.0.1:5173` and `http://localhost:5173`.
Tests cover professor-list authentication, role restrictions, pagination,
validation, and DELETE preflights.

Run checks from the repository root:

```sh
cd backend
.venv/bin/python -m pytest -q
cd ../frontend
npm ci
npm run typecheck
npm run build
```

Use `npm run dev` from `frontend/` to run the UI with the existing backend.
No new dependencies or environment variables are required.

Manual acceptance checks: sign in as admin and create/edit a department, course,
term, and offering; verify duplicate errors and offering filters; edit a user and
confirm deactivation; verify student/professor accounts redirect away from admin
URLs and their existing workflows still work. Automated backend tests and the
frontend build passed during implementation. The admin screens were also manually
verified in the browser across users, departments, courses, academic terms, and
course offerings.


### Student grades

Students can open `/grades` from their sidebar or dashboard to view numeric
grades, professor feedback, graded dates, enrollment status, course code/title,
section, and academic term. No feedback and no grades have neutral empty states.
Students without an academic profile receive a link to set one up.

The existing student route guard redirects professors and admins to the dashboard;
anonymous visitors go to login. The backend continues to restrict grades to the
current student. No backend changes or new dependencies are needed.

The student grade service uses `GET /students/me` to check profile availability,
`GET /grades/me` for grades, and `GET /enrollments/me` to link each grade's
`enrollment_id` to an offering. It then loads `GET /course-offerings/{id}`,
`GET /courses/{id}`, and `GET /terms/{id}`. All paths use the `/api/v1` base.
Related lookups are deduplicated within each load. Missing course context does
not hide recorded grades; the page displays a retry action. Primary request
failures use the existing API error handling and session-expiration behavior.

Verification from the repository root:

```sh
cd backend
.venv/bin/python -m pytest -q
cd ../frontend
npm run typecheck
npm run build
```

### Local Docker stack

With Docker Desktop running and a root `.env` containing a random
`JWT_SECRET_KEY` of at least 32 characters:

```sh
docker compose config --quiet
docker compose build
docker compose up -d --wait
docker compose ps
```

Open http://localhost:8080. nginx serves the React build, forwards `/api/` to
FastAPI, and falls back to `index.html` for direct React Router navigation.
The frontend uses the same-origin `/api/v1` base. The backend is also available
at http://127.0.0.1:8000/api/v1/health. Both published ports bind only to loopback.
PostgreSQL is internal to the stack and persists in the `campus_postgres` volume.
This database is separate from any existing host PostgreSQL database.

The stack uses a local-development database password by default; optionally set
`POSTGRES_PASSWORD` before first startup using URL-safe characters. The JWT
secret is required and has no default. Real `.env` files are excluded from image
build contexts. The one-shot `migrate` service automatically applies the existing
`backend/migrations/*.sql` files in filename order using `psql` with
`ON_ERROR_STOP=1`. Files are mounted read-only and retain their own transactions.
Successful filenames are recorded in `public.schema_migrations`; subsequent
runs skip recorded files. A session advisory lock serializes concurrent runners.
Startup order is database healthy → migrations successful → backend healthy →
frontend. A failed migration stops the runner and prevents backend startup.

Existing metadata-created databases are not automatically marked as migrated.
For disposable local data, `docker compose down -v` removes the database volume
so the next startup can build the schema from migrations. Do not use `-v` for
data you need to preserve. A process failure between a migration's own COMMIT
and its tracking insert requires inspecting the database before retrying; the
runner intentionally does not mark unverified migrations as applied.

```sh
docker compose logs backend
docker compose exec db pg_isready -U campus_user -d smart_campus
curl http://127.0.0.1:8000/api/v1/health
curl http://localhost:8080/api/v1/health
curl -I http://localhost:8080/grades
docker compose down
```

`docker compose down` stops the stack without removing database data.
