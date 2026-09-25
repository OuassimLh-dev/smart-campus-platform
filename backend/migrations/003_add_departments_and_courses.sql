-- Apply once after 002_add_academic_profiles.sql to an existing PostgreSQL database.
BEGIN;
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT department_code_not_blank CHECK (length(trim(code)) > 0),
    CONSTRAINT department_name_not_blank CHECK (length(trim(name)) > 0)
);
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    credits INTEGER NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id),
    professor_id INTEGER REFERENCES professor_profiles(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT course_credits_positive CHECK (credits > 0),
    CONSTRAINT course_code_not_blank CHECK (length(trim(code)) > 0),
    CONSTRAINT course_title_not_blank CHECK (length(trim(title)) > 0)
);
CREATE INDEX ix_courses_department_id ON courses(department_id);
CREATE INDEX ix_courses_professor_id ON courses(professor_id);
COMMIT;
