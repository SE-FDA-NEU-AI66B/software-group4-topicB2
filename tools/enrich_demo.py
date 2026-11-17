"""Add synthetic demo records transactionally; never update existing records.

Run against a reviewed demo database. Password comes from an environment variable.
Reserved namespace: *@demo.edusurvey.invalid and DEMO-* course codes.
"""
import argparse
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.database import connect, insert_id, is_postgres

COURSES = ['Software Engineering', 'Artificial Intelligence', 'Database Systems',
           'Web Development', 'Data Structures', 'Machine Learning', 'Statistics',
           'Linear Algebra', 'Computer Networks', 'Operating Systems', 'Cybersecurity',
           'Cloud Computing', 'Data Visualization', 'Natural Language Processing',
           'Computer Vision', 'Business Analytics', 'Microeconomics', 'Macroeconomics',
           'Digital Marketing', 'Project Management', 'Research Methods',
           'Human Computer Interaction', 'Distributed Systems', 'Ethics in AI']
QUESTIONS = [('The course concepts were clearly explained.', 'rating'),
             ('The learning materials supported my understanding.', 'rating'),
             ('The assessment criteria were clear.', 'rating'),
             ('The workload was appropriate.', 'rating'),
             ('What should we improve?', 'text')]


def enrich(database, credential, now=None):
    if len(credential) < 12:
        raise ValueError('Use a demo credential of at least 12 characters.')
    instant = now or datetime.now(UTC)
    hashed = generate_password_hash(credential)
    counts = {'users': 0, 'courses': 0, 'evaluations': 0, 'responses': 0}
    with connect(database) as db:
        if is_postgres(database):
            db.execute("SELECT pg_advisory_xact_lock(hashtextextended('edusurvey/demo-enrichment', 0))")
        else:
            db.execute('BEGIN IMMEDIATE')

        def account(email, name, role):
            existing = db.execute('SELECT id, role FROM users WHERE email=?', (email,)).fetchone()
            if existing:
                if existing['role'] != role:
                    raise ValueError('Reserved demo account has an unexpected role.')
                return existing['id']
            counts['users'] += 1
            return insert_id(db, 'INSERT INTO users(email,password_hash,full_name,role) VALUES (?,?,?,?)', (email, hashed, name, role))

        lecturers = [account(f'lecturer{i}@demo.edusurvey.invalid', f'Demo Lecturer {i}', 'lecturer') for i in range(1, 7)]
        students = [account(f'student{i}@demo.edusurvey.invalid', f'Demo Student {i:02}', 'student') for i in range(1, 31)]
        account('admin@demo.edusurvey.invalid', 'Demo Administrator', 'administrator')
        for index, name in enumerate(COURSES):
            code = f'DEMO-{index+1:03}'
            # Existing course namespace is never modified or enriched again.
            if db.execute('SELECT id FROM courses WHERE course_code=?', (code,)).fetchone():
                continue
            course_id = insert_id(db, 'INSERT INTO courses(course_code,course_name) VALUES (?,?)', (code, name))
            counts['courses'] += 1
            lecturer = lecturers[index % len(lecturers)]
            db.execute('INSERT INTO course_lecturers(lecturer_id,course_id) VALUES (?,?)', (lecturer, course_id))
            enrolled = [s for i, s in enumerate(students) if i == 0 or (i + index) % 3 != 0]
            for student in enrolled:
                db.execute('INSERT INTO course_enrollments(student_id,course_id) VALUES (?,?)', (student, course_id))
            status = 'closed' if index % 8 == 7 else 'open'
            deadline = instant + (timedelta(days=-1) if status == 'closed' else timedelta(days=3 + index))
            evaluation = insert_id(db, 'INSERT INTO evaluations(course_id,created_by,title,deadline,status) VALUES (?,?,?,?,?)', (course_id, lecturer, f'{name} · Semester feedback', deadline.isoformat(), status))
            counts['evaluations'] += 1
            questions = [(insert_id(db, 'INSERT INTO questions(evaluation_id,question_text,question_type,is_required,question_order) VALUES (?,?,?,?,?)', (evaluation, text, kind, 1, order)), kind) for order, (text, kind) in enumerate(QUESTIONS, 1)]
            for offset, student in enumerate(enrolled[1:12]):
                response = insert_id(db, "INSERT INTO responses(evaluation_id,student_id,submitted_at,status) VALUES (?,?,?,'submitted')", (evaluation, student, (instant - timedelta(days=2)).isoformat()))
                counts['responses'] += 1
                for question, kind in questions:
                    comment = ['Course content needs more practical examples.', 'Teaching delivery was clear and helpful.', 'The workload needs better pacing.', 'Assessment criteria could be clearer.'][offset % 4]
                    db.execute('INSERT INTO response_answers(response_id,question_id,rating_value,text_value) VALUES (?,?,?,?)', (response, question, 3 + offset % 3 if kind == 'rating' else None, comment if kind == 'text' else None))
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default=os.environ.get('EDUSURVEY_DEMO_DATABASE'), help='Demo SQLite path; set EDUSURVEY_DEMO_DATABASE for PostgreSQL to keep URLs out of shell arguments.')
    args = parser.parse_args()
    if not args.database:
        parser.error('Set EDUSURVEY_DEMO_DATABASE or --database.')
    if os.environ.get('EDUSURVEY_ENV') == 'production':
        parser.error('Use an isolated demo database, not the production runtime.')
    secret = os.environ.get('EDUSURVEY_DEMO_PASSWORD', '')
    if not secret:
        parser.error('Set EDUSURVEY_DEMO_PASSWORD before seeding.')
    print(enrich(args.database, secret))
