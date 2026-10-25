
def test_lecturer_can_view_assigned_evaluation_feedback(api_client):
    with api_client.session_transaction() as session:
        session["user_id"] = 2
        session["role"] = "lecturer"

    response = api_client.get("/lecturer/feedback/1")

    assert response.status_code == 200
    assert b"Test Evaluation" in response.data
    assert b"Completed evaluations" in response.data
    assert b"The course content was very useful." in response.data


def test_feedback_page_requires_login(api_client):
    response = api_client.get("/lecturer/feedback")

    assert response.status_code == 401


def test_student_cannot_access_lecturer_feedback(api_client):
    with api_client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "student"

    response = api_client.get("/lecturer/feedback")

    assert response.status_code == 403


def test_lecturer_cannot_view_unassigned_evaluation(api_client):
    with api_client.session_transaction() as session:
        session["user_id"] = 2
        session["role"] = "lecturer"

    response = api_client.get("/lecturer/feedback/999")

    assert response.status_code == 404
