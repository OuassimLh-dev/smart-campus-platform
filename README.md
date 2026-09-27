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
