"""#206: isolated database readiness, safe correlation and metric boundaries."""

import json
import logging
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta

import pytest

from src import app as app_module
from src import runtime
from tools.summarize_requests import summarize


@pytest.mark.parametrize("failure", ["missing-table", "orphan", "locked"])
def test_health_rejects_unusable_database(api_client, monkeypatch, tmp_path, caplog, failure):
    path = tmp_path / "PRIVATE_CONNECTION_STRING.db"
    with closing(sqlite3.connect(app_module.DATABASE)) as original, closing(sqlite3.connect(path)) as copy:
        original.backup(copy)
    monkeypatch.setattr(app_module, "DATABASE", path)
    with closing(sqlite3.connect(path)) as db:
        if failure == "missing-table":
            db.execute("DROP TABLE questions")
            db.commit()
        elif failure == "orphan":
            db.execute("PRAGMA foreign_keys=OFF")
            db.execute("INSERT INTO response_answers (response_id,question_id,rating_value) VALUES (999,1,4)")
            db.commit()
        else:
            db.execute("BEGIN EXCLUSIVE")  # Only a disposable copy is locked.
        with caplog.at_level(logging.INFO, logger=app_module.app.logger.name):
            response = api_client.get("/health?token=PRIVATE_TOKEN", headers={"Authorization": "Bearer PRIVATE_AUTH"})
        assert response.status_code == 503
        assert response.get_json() == {"status": "unavailable", "database": "unavailable"}
        assert response.headers["Cache-Control"] == "no-store"
        assert "PRIVATE_" not in response.text + caplog.text
        events = [json.loads(record.message) for record in caplog.records if record.message.startswith("{")]
        failure_event = next(event for event in events if event["event"] == "database_unavailable")
        completed = next(event for event in events if event["event"] == "request_completed")
        assert failure_event["request_id"] == completed["request_id"] == response.headers["X-Request-ID"]
        db.rollback()
    # Point back to intact seed DB; the original was never modified.
    monkeypatch.setattr(app_module, "DATABASE", api_client.application.config["TEST_DATABASE"])
    assert api_client.get("/health").status_code == 200


def test_sanitized_correlated_error_and_duration(api_client, monkeypatch, caplog):
    def fail():
        raise RuntimeError("PRIVATE_EXCEPTION_PASSWORD")

    monkeypatch.setitem(app_module.app.view_functions, "home", fail)
    ticks = iter([10.0, 10.125, 20.0, 20.010])
    monkeypatch.setattr(runtime, "perf_counter", lambda: next(ticks))
    api_client.set_cookie("session", "PRIVATE_COOKIE")
    with caplog.at_level(logging.INFO, logger=app_module.app.logger.name):
        response = api_client.post("/?token=PRIVATE_QUERY", json={"answer": "PRIVATE_ANSWER", "password": "PRIVATE_PASSWORD"},
                                   headers={"Authorization": "Bearer PRIVATE_AUTH", "X-Request-ID": "PRIVATE_CLIENT_ID"})
        # POST / is 405 and never invokes home; trigger the real unexpected error via GET.
        response = api_client.get("/?token=PRIVATE_QUERY", headers={"X-Request-ID": "PRIVATE_CLIENT_ID"})
    assert response.status_code == 500
    assert "PRIVATE_" not in response.text + caplog.text
    events = [json.loads(record.message) for record in caplog.records if record.message.startswith("{")]
    failures = [event for event in events if event["event"] == "request_failed"]
    completed = [event for event in events if event["event"] == "request_completed"]
    assert len(completed) == 2 and len(failures) == 1
    assert completed[0]["duration_ms"] == 125.0
    assert completed[1]["duration_ms"] == 10.0
    assert failures[0]["request_id"] == completed[1]["request_id"] == response.headers["X-Request-ID"]
    assert completed[0]["request_id"] != completed[1]["request_id"]
    assert failures[0]["error_type"] == "RuntimeError"
    assert datetime.fromisoformat(completed[0]["timestamp"]).tzinfo is not None


NOW = datetime(2026, 11, 15, 12, tzinfo=UTC)


@pytest.mark.parametrize("route,accept,event_name", [
    ("/api/courses/1/feedback", "application/json", "database_unavailable"),
    ("/lecturer/feedback/1", "text/html", "feedback_database_unavailable"),
])
def test_database_error_logs_are_correlated(api_client, monkeypatch, caplog, route, accept, event_name):
    def unavailable():
        raise sqlite3.OperationalError("PRIVATE_CONNECTION_PASSWORD")

    with api_client.session_transaction() as session:
        session["user_id"], session["role"] = 2, "lecturer"
    monkeypatch.setattr(app_module, "get_db_connection", unavailable)
    with caplog.at_level(logging.INFO, logger=app_module.app.logger.name):
        response = api_client.get(route, headers={"Accept": accept})
    assert response.status_code == 503
    assert "PRIVATE_" not in response.text + caplog.text
    records = [json.loads(record.message) for record in caplog.records if record.message.startswith("{")]
    error = next(record for record in records if record["event"] == event_name)
    completed = next(record for record in records if record["event"] == "request_completed")
    assert error["request_id"] == completed["request_id"] == response.headers["X-Request-ID"]


def test_unrecognized_method_is_not_logged_as_user_input(api_client, caplog):
    with caplog.at_level(logging.INFO, logger=app_module.app.logger.name):
        response = api_client.open("/", method="PRIVATE_METHOD")
    assert response.status_code == 405
    assert "PRIVATE_" not in caplog.text
    record = next(json.loads(item.message) for item in caplog.records if item.message.startswith("{"))
    assert record["method"] == "OTHER"


def event(index, status=200, duration=10, offset=0, endpoint="home"):
    return json.dumps({"event": "request_completed", "timestamp": (NOW + timedelta(seconds=offset)).isoformat(),
                       "request_id": f"{index:032x}", "status": status, "duration_ms": duration, "endpoint": endpoint})


@pytest.mark.parametrize("count,errors,duration,breach", [
    (19, 1, 1001, False), (20, 0, 1000, False), (20, 1, 1000, True), (20, 1, 1001, True),
])
def test_metric_threshold_boundaries(count, errors, duration, breach):
    result = summarize([event(i, 503 if i < errors else 200, duration) for i in range(count)], NOW)
    assert result["requests"] == count
    assert result["error_rate_percent"] == errors / count * 100
    assert result["p95_server_ms"] == duration
    assert result["error_rate_breach"] is breach
    assert result["latency_breach"] is (count >= 20 and duration > 1000)
    assert result["low_sample"] is (count < 20)


def test_metric_window_filtering_and_nearest_rank():
    lines = [event(i, duration=i) for i in range(1, 21)]
    lines += [event(21, 503, offset=-300), event(22, 503, offset=1),  # excluded edges
              event(23, 503, endpoint="health"), event(24, endpoint="static"),
              event(25, 404, offset=-299, endpoint="unmatched"), lines[0]]
    result = summarize(lines, NOW)
    assert result["requests"] == 21 and result["server_errors"] == 0
    assert result["p95_server_ms"] == 19  # ceil(.95 * 21) = 20th item, with extra 10ms.
    assert result["health_failures"] == 1 and result["health_breach"] is True
    assert result["duplicate_events"] == 1


def test_metrics_ignore_bad_samples_without_echoing_input():
    bad = json.loads(event(1))
    bad["duration_ms"] = float("nan")
    result = summarize(["PRIVATE_PASSWORD", json.dumps(bad), "prefix " + event(2, offset=-301)], NOW)
    assert result["requests"] == 0 and result["invalid_events"] == 1
    assert result["p95_server_ms"] is None and result["error_rate_percent"] is None
    assert "PRIVATE_" not in json.dumps(result)
