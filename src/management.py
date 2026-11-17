"""Role-scoped workspace. Uses the existing schema and transaction boundary."""
from datetime import UTC, datetime

from flask import jsonify, render_template, request, session

if __package__:
    from .account_store import access, active_admins
    from .database import insert_id, reserve_submission
else:
    from account_store import access, active_admins
    from database import insert_id, reserve_submission


def register_management(app, get_db, login_required, api_error):
    @app.get('/api/workspace')
    @login_required()
    def workspace_data():
        role, user_id = session['role'], session['user_id']
        with get_db() as db:
            user = dict(db.execute('SELECT full_name, email, role FROM users WHERE id=?', (user_id,)).fetchone())
            restriction, params = '', ()
            if role == 'lecturer':
                restriction, params = ' WHERE c.id IN (SELECT course_id FROM course_lecturers WHERE lecturer_id=?)', (user_id,)
            elif role == 'student':
                restriction, params = ' WHERE c.id IN (SELECT course_id FROM course_enrollments WHERE student_id=?)', (user_id,)
            courses = [dict(r) for r in db.execute('SELECT c.id, c.course_code, c.course_name FROM courses c' + restriction + ' ORDER BY c.course_code', params).fetchall()]
            evaluations = []
            rows = db.execute("""SELECT e.*, c.course_name,
                (SELECT COUNT(*) FROM responses r WHERE r.evaluation_id=e.id AND r.status='submitted') AS response_count,
                (SELECT COUNT(*) FROM course_enrollments ce WHERE ce.course_id=e.course_id) AS enrollment_count
                FROM evaluations e JOIN courses c ON c.id=e.course_id""" + restriction + ' ORDER BY e.id DESC', params).fetchall()
            for row in rows:
                item = dict(row)
                if role == 'student' and item['status'] == 'draft':
                    continue
                evaluations.append(item)
            if role != 'student':
                questions = db.execute('SELECT q.evaluation_id,q.question_text,q.question_type,q.is_required FROM questions q JOIN evaluations e ON e.id=q.evaluation_id JOIN courses c ON c.id=e.course_id' + restriction + ' ORDER BY q.question_order', params).fetchall()
                grouped = {}
                for question in questions:
                    grouped.setdefault(question['evaluation_id'], []).append(dict(question))
                for evaluation in evaluations:
                    evaluation['questions'] = grouped.get(evaluation['id'], [])
            users = []
            if role == 'administrator':
                users = [dict(r) for r in db.execute('SELECT id, email, full_name, role FROM users ORDER BY full_name').fetchall()]
        return jsonify(user=user, courses=courses, evaluations=evaluations, users=users)

    @app.get('/dashboard')
    @login_required()
    def dashboard():
        return render_template('workspace.html', role=session['role'])

    @app.get('/lecturer/evaluations')
    @login_required(roles=['lecturer'])
    def lecturer_management():
        return render_template('workspace.html', role=session['role'])

    @app.get('/admin/evaluations')
    @app.get('/admin/users')
    @login_required(roles=['administrator'])
    def administrator_management():
        return render_template('workspace.html', role=session['role'])

    @app.route('/api/evaluations/<int:evaluation_id>/draft', methods=['GET', 'PUT'])
    @login_required(roles=['student'])
    def evaluation_draft(evaluation_id):
        with get_db() as db:
            if request.method == 'PUT':
                reserve_submission(db, evaluation_id, session['user_id'])
            evaluation = db.execute("SELECT e.* FROM evaluations e JOIN course_enrollments ce ON ce.course_id=e.course_id WHERE e.id=? AND ce.student_id=?", (evaluation_id, session['user_id'])).fetchone()
            if evaluation is None:
                return api_error(404, 'NOT_FOUND', 'Evaluation not found.', 'Select an assigned evaluation.')
            response = db.execute('SELECT id,status FROM responses WHERE evaluation_id=? AND student_id=?', (evaluation_id, session['user_id'])).fetchone()
            if response and response['status'] == 'submitted':
                return api_error(409, 'DUPLICATE_SUBMISSION', 'You have already completed this evaluation.', 'View your completion status.')
            if request.method == 'GET':
                answers = {} if response is None else {str(r['question_id']): r['rating_value'] if r['rating_value'] is not None else r['text_value'] for r in db.execute('SELECT question_id,rating_value,text_value FROM response_answers WHERE response_id=?', (response['id'],)).fetchall()}
                return jsonify(answers=answers)
            deadline = datetime.fromisoformat(str(evaluation['deadline']))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=UTC)
            if evaluation['status'] != 'open' or deadline <= datetime.now(UTC):
                return api_error(400, 'EVALUATION_CLOSED', 'This evaluation is not open for submissions.', 'Select an open evaluation.')
            data = request.get_json(silent=True)
            if not isinstance(data, dict) or not isinstance(data.get('answers'), dict):
                return api_error(400, 'INVALID_ANSWERS', 'Answers must be an object.', 'Review the answers.')
            questions = {str(q['id']): q for q in db.execute('SELECT id,question_type FROM questions WHERE evaluation_id=?', (evaluation_id,)).fetchall()}
            validated = []
            for key, value in data['answers'].items():
                question = questions.get(key)
                if question is None or not isinstance(value, dict):
                    return api_error(400, 'INVALID_QUESTION', 'Invalid question.', 'Reload the evaluation.')
                rating, text = value.get('rating_value'), value.get('text_value')
                if question['question_type'] == 'rating':
                    valid = type(rating) is int and 1 <= rating <= 5 and text is None
                else:
                    valid = isinstance(text, str) and 0 < len(text.strip()) <= 2000 and rating is None
                if not valid:
                    return api_error(400, 'INVALID_ANSWER', 'Use ratings 1–5 or text up to 2000 characters.', 'Review your answers.')
                validated.append((int(key), rating, text.strip() if text else None))
            response_id = response['id'] if response else insert_id(db, "INSERT INTO responses(evaluation_id,student_id,status) VALUES (?,?,'draft')", (evaluation_id, session['user_id']))
            db.execute('DELETE FROM response_answers WHERE response_id=?', (response_id,))
            for question_id, rating, text in validated:
                db.execute('INSERT INTO response_answers(response_id,question_id,rating_value,text_value) VALUES (?,?,?,?)', (response_id, question_id, rating, text))
        return jsonify(message='Draft saved. You can return to finish before the deadline.')

    @app.patch('/api/admin/users/<int:user_id>/role')
    @login_required(roles=['administrator'])
    def change_role(user_id):
        data = request.get_json(silent=True)
        role = data.get('role') if isinstance(data, dict) else None
        if role not in {'student', 'lecturer', 'administrator'}:
            return api_error(400, 'INVALID_ROLE', 'Choose a supported role.', 'Review the role.')
        with get_db() as db:
            if getattr(db, 'dialect', '') == 'postgresql':
                db.execute("SELECT pg_advisory_xact_lock(hashtextextended('edusurvey/admin-roles', 0))")
            else:
                db.execute('BEGIN IMMEDIATE')
            actor = db.execute('SELECT role FROM users WHERE id=?', (session['user_id'],)).fetchone()
            if actor is None or actor['role'] != 'administrator' or access(db, session['user_id'])['state'] != 'active':
                return api_error(403, 'FORBIDDEN', 'Administrator access is required.', 'Sign in again.')
            user = db.execute('SELECT role FROM users WHERE id=?', (user_id,)).fetchone()
            if user is None:
                return api_error(404, 'NOT_FOUND', 'Account not found.', 'Refresh the directory.')
            if user['role'] != role:
                if user['role'] == 'administrator' and access(db, user_id)['state'] == 'active' and active_admins(db) <= 1:
                    return api_error(409, 'LAST_ADMIN', 'Keep at least one administrator.', 'Assign another administrator first.')
                enrollment = db.execute('SELECT 1 FROM course_enrollments WHERE student_id=?', (user_id,)).fetchone()
                assignment = db.execute('SELECT 1 FROM course_lecturers WHERE lecturer_id=?', (user_id,)).fetchone()
                if enrollment or assignment:
                    return api_error(409, 'ROLE_IN_USE', 'This account has course relationships.', 'Review enrollments and assignments before changing roles.')
                db.execute('UPDATE users SET role=? WHERE id=?', (role, user_id))
        return jsonify(user_id=user_id, role=role)

    @app.post('/api/admin/courses')
    @login_required(roles=['administrator'])
    def add_course():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or any(not isinstance(data.get(k), str) or not data[k].strip() or len(data[k]) > 200 for k in ('course_code', 'course_name')):
            return api_error(400, 'INVALID_COURSE', 'Course code and name are required (max 200 characters).', 'Review the fields.')
        with get_db() as db:
            result = db.execute('INSERT INTO courses(course_code,course_name) VALUES (?,?) ON CONFLICT (course_code) DO NOTHING', (data['course_code'].strip(), data['course_name'].strip()))
            if result.rowcount == 0:
                return api_error(409, 'DUPLICATE_COURSE', 'Course code already exists.', 'Use the existing course.')
        return jsonify(message='Course created.'), 201

    @app.post('/api/admin/course-memberships')
    @login_required(roles=['administrator'])
    def add_membership():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or any(type(data.get(k)) is not int or data[k] < 1 for k in ('user_id', 'course_id')):
            return api_error(400, 'INVALID_MEMBERSHIP', 'Select an account and a course.', 'Review your selection.')
        with get_db() as db:
            suffix = ' FOR UPDATE' if getattr(db, 'dialect', '') == 'postgresql' else ''
            if not suffix:
                db.execute('BEGIN IMMEDIATE')
            user = db.execute('SELECT role FROM users WHERE id=?' + suffix, (data['user_id'],)).fetchone()
            course = db.execute('SELECT id FROM courses WHERE id=?', (data['course_id'],)).fetchone()
            if user is None or course is None or user['role'] not in {'student', 'lecturer'} or access(db, data['user_id'])['state'] == 'disabled':
                return api_error(400, 'INVALID_MEMBERSHIP', 'Select a student or lecturer and an existing course.', 'Review your selection.')
            table, column = ('course_enrollments', 'student_id') if user['role'] == 'student' else ('course_lecturers', 'lecturer_id')
            # Table/column are fixed constants; only values are user controlled.
            result = db.execute(f'INSERT INTO {table}({column},course_id) VALUES (?,?) ON CONFLICT ({column},course_id) DO NOTHING', (data['user_id'], data['course_id']))
            if result.rowcount == 0:
                return api_error(409, 'DUPLICATE_MEMBERSHIP', 'This course relationship already exists.', 'No changes needed.')
        return jsonify(message='Course relationship saved.'), 201

    @app.patch('/api/evaluations/<int:evaluation_id>/status')
    @login_required(roles=['lecturer', 'administrator'])
    def evaluation_status(evaluation_id):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or data.get('status') not in {'open', 'closed'}:
            return api_error(400, 'INVALID_STATUS', 'Choose open or closed.', 'Review the evaluation status.')
        with get_db() as db:
            # Exclusive lifecycle lock pairs with the submission shared lock.
            if getattr(db, 'dialect', '') == 'postgresql':
                db.execute('SELECT pg_advisory_xact_lock(hashtextextended(?, 0))', (f'edusurvey/evaluation/{evaluation_id}',))
            else:
                db.execute('BEGIN IMMEDIATE')
            suffix = ' FOR UPDATE' if getattr(db, 'dialect', '') == 'postgresql' else ''
            evaluation = db.execute('SELECT * FROM evaluations WHERE id=?' + suffix, (evaluation_id,)).fetchone()
            if evaluation is None:
                return api_error(404, 'NOT_FOUND', 'Evaluation not found.', 'Refresh the list.')
            if session['role'] == 'lecturer' and db.execute('SELECT 1 FROM course_lecturers WHERE lecturer_id=? AND course_id=?', (session['user_id'], evaluation['course_id'])).fetchone() is None:
                return api_error(403, 'FORBIDDEN', 'You do not have permission to manage this course.', 'Select an assigned course.')
            if data['status'] == 'open':
                deadline = datetime.fromisoformat(str(evaluation['deadline']))
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=UTC)
                if deadline <= datetime.now(UTC):
                    return api_error(400, 'INVALID_DEADLINE', 'Deadline must be in the future.', 'Update the deadline first.')
                if not db.execute('SELECT 1 FROM questions WHERE evaluation_id=?', (evaluation_id,)).fetchone():
                    return api_error(400, 'MISSING_QUESTIONS', 'At least one question is required.', 'Add questions before opening.')
            db.execute('UPDATE evaluations SET status=? WHERE id=?', (data['status'], evaluation_id))
        return jsonify(evaluation_id=evaluation_id, status=data['status'])
