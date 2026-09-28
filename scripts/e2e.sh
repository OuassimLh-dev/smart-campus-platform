#!/bin/sh
# Creates and destroys ONLY its own disposable Compose project and volume.
set -eu
cd "$(dirname "$0")/.."
project="smart-campus-e2e-${GITHUB_RUN_ID:-$(date +%s)}-${GITHUB_RUN_ATTEMPT:-$$}"
export POSTGRES_PASSWORD=e2e_only_fake_password
export JWT_SECRET_KEY=e2e-only-fake-jwt-secret-never-use-in-production-123456
export ACCESS_TOKEN_EXPIRE_MINUTES=30
compose() {
    docker compose --env-file /dev/null -p "$project" -f compose.yaml -f compose.e2e.yaml "$@"
}
cleanup() {
    result=$?
    trap - EXIT
    if [ "$result" -ne 0 ]; then
        compose ps -a || true
        compose logs --no-color --tail 100 || true
    fi
    compose down -v --remove-orphans || exit 1
    exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
echo "Disposable E2E project: $project (requires localhost:8080 to be free)"
compose config --quiet
compose up -d --build --wait --wait-timeout 180
compose exec -T backend python - < scripts/seed_e2e.py
npm --prefix frontend run test:e2e -- "$@"
