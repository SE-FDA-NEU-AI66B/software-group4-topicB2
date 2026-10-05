PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS response_answers;
DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS evaluations;
DROP TABLE IF EXISTS course_lecturers;
DROP TABLE IF EXISTS course_enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL
        CHECK (role IN ('student', 'lecturer', 'administrator')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE,
    course_name TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE course_enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    enrolled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE (student_id, course_id)
);

CREATE TABLE course_lecturers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecturer_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (lecturer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE (lecturer_id, course_id)
);

CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    title TEXT NOT NULL,
    deadline TIMESTAMP NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('draft', 'open', 'closed')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL
        CHECK (question_type IN ('rating', 'text')),
    is_required INTEGER NOT NULL DEFAULT 1
        CHECK (is_required IN (0, 1)),
    question_order INTEGER NOT NULL,

    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE,
    UNIQUE (evaluation_id, question_order)
);

CREATE TABLE responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    submitted_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'submitted')),

    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (evaluation_id, student_id)
);

CREATE TABLE response_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    rating_value INTEGER CHECK (rating_value BETWEEN 1 AND 5),
    text_value TEXT,

    FOREIGN KEY (response_id) REFERENCES responses(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,

    UNIQUE (response_id, question_id),

    CHECK (
        rating_value IS NOT NULL
        OR text_value IS NOT NULL
    )
);