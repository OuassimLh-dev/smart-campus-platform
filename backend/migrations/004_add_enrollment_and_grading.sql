-- Apply once after 003_add_departments_and_courses.sql.
BEGIN;
CREATE TABLE academic_terms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    academic_year VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_term_name_year UNIQUE (name, academic_year),
    CONSTRAINT term_dates_ordered CHECK (start_date < end_date)
);
CREATE TABLE course_offerings (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    professor_id INTEGER NOT NULL REFERENCES professor_profiles(id),
    term_id INTEGER NOT NULL REFERENCES academic_terms(id),
    section VARCHAR(50) NOT NULL,
    capacity INTEGER NOT NULL,
    is_open BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_offering_course_term_section UNIQUE (course_id, term_id, section),
    CONSTRAINT offering_capacity_positive CHECK (capacity > 0),
    CONSTRAINT offering_section_not_blank CHECK (length(trim(section)) > 0)
);
CREATE INDEX ix_course_offerings_course_id ON course_offerings(course_id);
CREATE INDEX ix_course_offerings_professor_id ON course_offerings(professor_id);
CREATE INDEX ix_course_offerings_term_id ON course_offerings(term_id);
CREATE TYPE enrollment_status AS ENUM ('enrolled', 'dropped', 'completed');
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES student_profiles(id),
    course_offering_id INTEGER NOT NULL REFERENCES course_offerings(id),
    status enrollment_status NOT NULL DEFAULT 'enrolled',
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_enrollment_student_offering UNIQUE (student_id, course_offering_id)
);
CREATE INDEX ix_enrollments_student_id ON enrollments(student_id);
CREATE INDEX ix_enrollments_course_offering_id ON enrollments(course_offering_id);
CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    enrollment_id INTEGER NOT NULL UNIQUE REFERENCES enrollments(id),
    grade NUMERIC(5,2) NOT NULL,
    feedback TEXT,
    graded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT grade_valid_range CHECK (grade >= 0 AND grade <= 100)
);
COMMIT;
