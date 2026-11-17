"""Acceptance coverage for US08/US13 management and additive synthetic data."""
import sqlite3

import pytest

from src import app as app_module


def login(client, role='lecturer'):
    with client.session_transaction() as session:
        session['user_id'] = {'student': 1, 'lecturer': 2, 'administrator': 3}[role]
        session['role'] = role


def payload():
    return {'course_id': 1, 'title': 'New feedback', 'deadline': '2099-01-01T00:00:00Z',
            'questions': [{'question_text': f'Question {i}', 'question_type': 'rating', 'is_required': True} for i in range(5)]}


def test_management_creation_publish_and_student_visibility(api_client):
    login(api_client)
    result = api_client.post('/api/evaluations', json=payload())
    assert result.status_code == 201
    identifier = result.json['evaluation_id']
    assert result.json['questions_created'] == 5
    assert api_client.patch(f'/api/evaluations/{identifier}/status', json={'status': 'open'}).status_code == 200
    login(api_client, 'student')
    questions = api_client.get(f'/api/evaluations/{identifier}/questions')
    assert questions.status_code == 200
    assert len(questions.json['questions']) == 5
    assert api_client.patch(f'/api/evaluations/{identifier}/status', json={'status': 'closed'}).status_code == 403
    assert api_client.get('/admin/users').status_code == 403


def test_management_denies_other_lecturer_without_writes(api_client):
    login(api_client)
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute('DELETE FROM course_lecturers')
    result = api_client.post('/api/evaluations', json=payload())
    assert result.status_code == 403
    assert result.json['error']['message'] == 'You do not have permission to create an evaluation for this course.'
    assert api_client.patch('/api/evaluations/1/status', json={'status': 'closed'}).status_code == 403
    assert api_client.get('/api/workspace').json['courses'] == []
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT COUNT(*) FROM evaluations').fetchone()[0] == 1


@pytest.mark.parametrize('change', [{'deadline': '2000-01-01'}, {'questions': []}, {'questions': [{'question_text': 'x', 'question_type': 'invalid'}]}])
def test_invalid_creation_is_atomic(api_client, change):
    login(api_client, 'administrator')
    data = payload() | change
    assert api_client.post('/api/evaluations', json=data).status_code == 400
    with sqlite3.connect(app_module.DATABASE) as db:
        assert db.execute('SELECT COUNT(*) FROM evaluations').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM questions').fetchone()[0] == 2


def test_admin_creation_and_account_directory(api_client):
    login(api_client, 'administrator')
    assert api_client.post('/api/evaluations', json=payload()).status_code == 201
    directory = api_client.get('/api/workspace').json
    assert len(directory['users']) == 3
    assert all('password_hash' not in user for user in directory['users'])
    assert api_client.get('/admin/evaluations').status_code == 200



def test_revoked_role_cannot_reuse_signed_session(api_client):
    login(api_client, 'administrator')
    with sqlite3.connect(app_module.DATABASE) as db:
        db.execute("UPDATE users SET role='student' WHERE id=3")
    assert api_client.get('/admin/users').status_code == 403
    assert api_client.get('/api/workspace').json['users'] == []


def test_admin_courses_membership_and_role_constraints(api_client):
    login(api_client, 'administrator')
    data = {'course_code': 'NEW101', 'course_name': 'New course'}
    assert api_client.post('/api/admin/courses', json=data).status_code == 201
    assert api_client.post('/api/admin/courses', json=data).status_code == 409
    assert api_client.post('/api/admin/course-memberships', json={'user_id': 2, 'course_id': 2}).status_code == 201
    assert api_client.post('/api/admin/course-memberships', json={'user_id': 2, 'course_id': 2}).status_code == 409
    assert api_client.post('/api/admin/course-memberships', json={'user_id': 3, 'course_id': 2}).status_code == 400
    assert api_client.patch('/api/admin/users/3/role', json={'role': 'student'}).status_code == 409
    assert api_client.patch('/api/admin/users/2/role', json={'role': 'student'}).status_code == 409
    login(api_client, 'lecturer')
    assert api_client.post('/api/admin/courses', json=data).status_code == 403
    assert api_client.post('/api/admin/course-memberships', json={'user_id': 1, 'course_id': 2}).status_code == 403


def test_partial_draft_persistence_and_submission_protection(api_client):
    login(api_client, 'lecturer')
    identifier = api_client.post('/api/evaluations', json=payload()).json['evaluation_id']
    assert api_client.patch(f'/api/evaluations/{identifier}/status', json={'status': 'open'}).status_code == 200
    login(api_client, 'student')
    questions = api_client.get(f'/api/evaluations/{identifier}/questions').json['questions']
    key = str(questions[0]['id'])
    path = f'/api/evaluations/{identifier}/draft'
    assert api_client.put(path, json={'answers': {key: {'rating_value': 4}}}).status_code == 200
    assert api_client.get(path).json['answers'] == {key: 4}
    assert api_client.put(path, json={'answers': {key: {'rating_value': True}}}).status_code == 400
    assert api_client.get(path).json['answers'] == {key: 4}
    assert api_client.put('/api/evaluations/1/draft', json={'answers': {}}).status_code == 409
    answers = {str(q['id']): {'rating_value': 5} for q in questions}
    assert api_client.post('/api/submissions', json={'evaluation_id': identifier, 'answers': answers}).status_code == 201
    assert api_client.put(path, json={'answers': {}}).status_code == 409
    assert api_client.get(path).status_code == 409
