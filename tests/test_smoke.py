import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.app import app


def test_home_route():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_evaluations_route():
    client = app.test_client()
    response = client.get("/evaluations")

    assert response.status_code == 200
    assert b"EduSurvey" in response.data