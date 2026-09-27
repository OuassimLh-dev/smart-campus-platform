# Smart Campus frontend

React + TypeScript + Vite, React Router, and Axios. No UI framework.

## Local development

Install Node.js 22.12+ (Node 24 LTS recommended), which includes npm.

```sh
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. Start the configured FastAPI backend separately on
http://127.0.0.1:8000. A working PostgreSQL database, applied migrations, JWT secret,
and an existing account with a password are required for real login.

The default API URL is http://127.0.0.1:8000/api/v1.
To override it without creating a file:

```sh
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run dev
```

See .env.example for the configuration template. Vite variables are public;
never put secrets in VITE_* variables. No real .env is included.

## Validation

```sh
npm run typecheck
npm run build
npm run preview
```

The build is written to dist/. Preview uses port 5173; stop the development
server before running it. The backend only allows the two local Vite origins
http://127.0.0.1:5173 and http://localhost:5173.

## Structure

- api: Axios configuration, Bearer header, and expired-session handling
- services: typed authentication API calls
- hooks: shared auth context and useAuth
- routes: protected routing
- layouts/components: app shell and shared UI
- pages: login and role-aware dashboard
- types/utils: shared types, token storage, and display helpers

## Authentication

Login posts email/password, stores the access token in sessionStorage, fetches
/auth/me, and redirects only after the user is loaded. Reloading revalidates the
token through /auth/me. Logout and authenticated 401 responses clear the session.
User data and passwords are never persisted. When storage is disabled, the token
is kept only in memory.

Session storage is tab-scoped but remains accessible to JavaScript; this is a
portfolio tradeoff, not an HttpOnly-cookie implementation. Backend RBAC remains
the authority. Student profile, course-offering browsing, and enrollment pages are
implemented; professor/admin management and grades remain placeholders.

## Student workflow

Student navigation links to /profile, /courses, and /enrollments. A missing profile
opens onboarding rather than a generic error. Catalog enrollment posts only
course_offering_id. Dropping an enrolled record requires confirmation and updates
its status without removing it from history. The current backend does not allow
re-enrollment after dropping the same offering.

Offering and enrollment responses contain IDs, not nested course/term data.
Related details are resolved through authenticated detail endpoints, deduplicated
within each page. Professor public profiles do not contain names, so the UI shows
academic title and profile ID. Capacity is total capacity, not seats remaining.
Failed related lookups keep the record visible with an explicit fallback.

The catalog loads 20 offerings per page and optionally filters to open offerings.
Local CORS allows GET, POST, and PATCH from the two existing Vite origins only.
