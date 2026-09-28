#!/bin/sh
set -eu
export LC_ALL=C

script=$(mktemp)
trap 'rm -f "$script"' EXIT HUP INT TERM
cat > "$script" <<'SQL'
-- Keep one session so concurrent runners serialize across every migration.
SELECT pg_advisory_lock(1935892845);
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    filename TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

found=false
for file in /migrations/*.sql; do
    [ -f "$file" ] || continue
    found=true
    filename=${file##*/}
    case "$filename" in
        *[!a-zA-Z0-9_.-]*) echo "Unsupported migration filename: $filename" >&2; exit 1 ;;
    esac
    cat >> "$script" <<SQL
SELECT EXISTS (SELECT 1 FROM public.schema_migrations WHERE filename = '$filename') AS applied \gset
\if :applied
\echo Skipping $filename
\else
\echo Applying $filename
\i $file
INSERT INTO public.schema_migrations (filename) VALUES ('$filename');
\endif
SQL
done
[ "$found" = true ] || { echo 'No SQL migrations found in /migrations' >&2; exit 1; }
# Each file owns its BEGIN/COMMIT. Stop immediately on any SQL or include error.
psql -X -v ON_ERROR_STOP=1 -f "$script"
