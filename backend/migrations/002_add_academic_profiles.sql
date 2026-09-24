-- Apply once after 001_add_user_password.sql to an existing PostgreSQL database.
BEGIN;
CREATE TABLE student_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    student_number VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    program VARCHAR(150) NOT NULL,
    year_level INTEGER NOT NULL,
    enrollment_year INTEGER NOT NULL,
    expected_graduation_year INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT student_year_level_positive CHECK (year_level >= 1),
    CONSTRAINT student_enrollment_year_range CHECK (enrollment_year BETWEEN 1900 AND 2200),
    CONSTRAINT student_graduation_year_range CHECK (expected_graduation_year BETWEEN enrollment_year AND 2200)
);
CREATE TABLE professor_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    employee_number VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    academic_title VARCHAR(100) NOT NULL,
    office_location VARCHAR(150) NOT NULL,
    research_interests TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMIT;
