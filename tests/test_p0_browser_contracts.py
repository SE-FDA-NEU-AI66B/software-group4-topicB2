"""Real Chromium UI checks with temporary SQLite data and a controlled app clock."""

import os
import sqlite3
from pathlib import Path
from threading import Thread

import pytest
from playwright.sync_api import expect, sync_playwright
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from src import app as app_module


@pytest.fixture
def browser_app(api_client):
    """Reuse the isolated API fixture, never the production/demo database."""
    database = app_module.DATABASE
    with sqlite3.connect(database) as db:
        db.execute("DELETE FROM response_answers")
        db.execute("DELETE FROM responses")
        db.execute("UPDATE users SET password_hash = ?", (generate_password_hash("Password123!"),))
    server = make_server("127.0.0.1", 0, app_module.app, threaded=True)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    with sync_playwright() as playwright:
        options = {"headless": True}
        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        if executable:
            options["executable_path"] = executable
        browser = playwright.chromium.launch(**options)
        try:
            yield browser, f"http://127.0.0.1:{server.server_port}", database
        finally:
            browser.close()
            server.shutdown()
            worker.join(timeout=5)
            server.server_close()


def sign_in(page, url, email="student@test.com"):
    page.goto(url, wait_until="domcontentloaded")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_label("Email", exact=False).fill(email)
    page.locator("#password").fill("Password123!")
    page.get_by_role("button", name="Sign in", exact=True).click()


@pytest.mark.parametrize("viewport", [{"width": 1440, "height": 900}, {"width": 390, "height": 844}], ids=["laptop", "phone"])
def test_logout_navigates_to_login(browser_app, viewport):
    """M5-UI01/02; P0C-07: click-only completion, persistence and keyboard logout."""
    browser, url, database = browser_app
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    sign_in(page, url)
    expect(page).to_have_url(f"{url}/evaluations")
    assert page.request.get(url + "/evaluations").headers["cache-control"] == "no-store"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("link", name="Start evaluation").click()
    # The navigation can finish before the questions fetch; validate a loaded form.
    expect(page.locator('input[type="radio"][value="5"]')).to_have_count(1)
    review = page.locator("#reviewButtonMobile" if viewport["width"] < 600 else "#reviewButton")
    expect(review).to_be_enabled()
    review.click()
    expect(page.locator("#validationMessage")).to_be_visible()
    rating = page.locator('input[type="radio"][value="5"]')
    rating.focus()
    page.keyboard.press("Space")
    expect(rating).to_be_checked()
    page.locator("textarea").fill("Useful course content.")
    review.click()
    page.get_by_role("button", name="Submit evaluation", exact=True).click()
    expect(page.locator("#submissionSuccess")).to_be_visible()
    expect(review).to_be_disabled()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if evidence_dir := os.environ.get("P0_SCREENSHOT_DIR"):
        Path(evidence_dir).mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(Path(evidence_dir) / f"saved-{viewport['width']}.png"), full_page=True)
    page.reload(wait_until="domcontentloaded")
    expect(page.locator("#submissionSuccess")).to_be_visible()
    page.get_by_role("link", name="Back to My Evaluations").click()
    expect(page.locator("#completedCount")).to_have_text("1")
    expect(page.get_by_role("link", name="Start evaluation")).to_have_count(0)
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM responses WHERE status='submitted'").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM response_answers").fetchone()[0] == 2
    evidence_dir = os.environ.get("P0_SCREENSHOT_DIR")
    if evidence_dir:
        destination = Path(evidence_dir)
        destination.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(destination / f"completed-{viewport['width']}.png"), full_page=True)
    logout = page.get_by_role("button", name="Sign out", exact=True)
    logout.focus()
    expect(logout).to_be_focused()
    page.keyboard.press("Enter")
    expect(page).to_have_url(f"{url}/login")
    assert context.request.get(f"{url}/api/auth/me").status == 401
    assert context.request.get(f"{url}/api/evaluations").status == 401
    assert context.request.get(f"{url}/evaluations").status == 401  # Server redirect remains #215.
    context.close()


def test_login_error_visible_message(browser_app):
    """P0C-03: visible message mapping, separate from API credential partition tests."""
    browser, url, _ = browser_app
    page = browser.new_page()
    page.route("**/api/auth/login", lambda route: route.fulfill(status=401, json={"error": {"code": "INVALID_CREDENTIALS"}}))
    sign_in(page, url)
    expect(page.locator("#form-error")).to_have_text("Invalid email or password. Check your credentials and try again.")
    expect(page.get_by_role("button", name="Sign in", exact=True)).to_be_enabled()
    page.close()


@pytest.mark.parametrize("email,path", [("lecturer@test.com", "/lecturer/feedback"), ("admin@test.com", "/account")])
def test_role_landing_and_logout(browser_app, email, path):
    """M5-UI03: role landing exists, exposes sign-out and denies student APIs."""
    browser, url, _ = browser_app
    page = browser.new_page(viewport={"width": 390, "height": 844})
    sign_in(page, url, email)
    expect(page).to_have_url(url + path)
    assert page.request.get(url + "/api/evaluations").status == 403
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("button", name="Sign out", exact=True).click()
    expect(page).to_have_url(url + "/login")
    assert page.request.get(url + "/api/auth/me").status == 401
    page.close()


def test_submission_deadline_race_and_retryable_logout(browser_app):
    """M5-UI04: server rejects expiry after opening; failed logout remains retryable."""
    browser, url, database = browser_app
    page = browser.new_page()
    sign_in(page, url)
    page.get_by_role("link", name="Start evaluation").click()
    page.locator('label[for="q1-5"]').click()
    with sqlite3.connect(database) as db:
        db.execute("UPDATE evaluations SET deadline = '2026-11-04 12:00:00'")
    page.locator("#reviewButton").click()
    page.get_by_role("button", name="Submit evaluation", exact=True).click()
    expect(page.locator("#submitFeedback")).to_contain_text("deadline has passed")
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 0
    page.get_by_role("button", name="Back to editing").click()
    page.route("**/api/auth/logout", lambda route: route.abort())
    page.get_by_role("button", name="Sign out", exact=True).click()
    expect(page.locator("[data-sign-out-status]")).to_contain_text("Check your connection and try again")
    expect(page.get_by_role("button", name="Sign out", exact=True)).to_be_enabled()
    page.unroute("**/api/auth/logout")
    page.get_by_role("button", name="Sign out", exact=True).click()
    expect(page).to_have_url(url + "/login")
    page.close()


def test_due_soon_label_and_filter(browser_app):
    """P0C-04: UI consumes real strict-boundary API statuses and filters Due soon."""
    browser, url, database = browser_app
    with sqlite3.connect(database) as db:
        db.execute("UPDATE evaluations SET deadline = '2026-11-05 11:59:59'")
        db.execute("INSERT INTO evaluations (course_id, created_by, title, deadline, status) VALUES (1, 2, 'At 24 hours', '2026-11-05 12:00:00', 'open')")
    page = browser.new_page()
    sign_in(page, url)
    expect(page.locator("#dueSoonCount")).to_have_text("1")
    expect(page.locator("#activeCount")).to_have_text("1")
    page.locator("#statusFilter").select_option(label="Due soon")
    expect(page.get_by_role("link", name="Start evaluation")).to_have_count(1)
    expect(page.locator(".status-due-soon")).to_have_text("Due soon")
    expect(page.get_by_text("At 24 hours", exact=True)).to_have_count(0)
    page.close()


@pytest.mark.parametrize("rule", ["closed", "unenrolled"])
def test_open_evaluation_error_explains_next_action(browser_app, rule):
    """M5-UI05: business-rule rejections provide an actionable list link."""
    browser, url, database = browser_app
    page = browser.new_page()
    sign_in(page, url)
    expect(page.get_by_role("link", name="Start evaluation")).to_be_visible()
    with sqlite3.connect(database) as db:
        if rule == "closed":
            db.execute("UPDATE evaluations SET status = 'closed'")
        else:
            db.execute("DELETE FROM course_enrollments")
    page.get_by_role("link", name="Start evaluation").click()
    expect(page.locator("#errorState")).to_be_visible()
    expect(page.locator("#errorMessage")).not_to_be_empty()
    page.locator("#errorState").get_by_role("link", name="Back to evaluations", exact=True).click()
    expect(page).to_have_url(url + "/evaluations")
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 0
    page.close()


def seed_lecturer_feedback(database):
    """Synthetic submitted, draft and foreign-course feedback for US04 UI cases."""
    from contextlib import closing

    with closing(sqlite3.connect(database)) as db, db:
        db.execute("INSERT INTO responses (id, evaluation_id, student_id, submitted_at, status) VALUES (1, 1, 1, '2026-11-04 10:00:00', 'submitted')")
        db.execute("INSERT INTO response_answers (response_id, question_id, rating_value) VALUES (1, 1, 4)")
        db.execute("INSERT INTO response_answers (response_id, question_id, text_value) VALUES (1, 2, ?)", ('Helpful examples. Practical labs made the concepts easier to follow.',))
        db.execute("INSERT INTO users (id, email, password_hash, full_name, role) VALUES (4, 'draft@example.test', 'fixture-hash', 'Draft Student', 'student')")
        db.execute("INSERT INTO responses (id, evaluation_id, student_id, status) VALUES (2, 1, 4, 'draft')")
        db.execute("INSERT INTO response_answers (response_id, question_id, text_value) VALUES (2, 2, 'DRAFT_ONLY_COMMENT')")
        db.execute("INSERT INTO courses (id, course_code, course_name) VALUES (2, 'OTHER202', 'FOREIGN_COURSE')")
        db.execute("INSERT INTO evaluations (id, course_id, created_by, title, deadline, status) VALUES (2, 2, 2, 'UNASSIGNED_PRIVATE', '2099-01-01 00:00:00', 'open')")
        db.execute("INSERT INTO questions (id, evaluation_id, question_text, question_type, is_required, question_order) VALUES (3, 2, 'Foreign question', 'text', 0, 1)")
        db.execute("INSERT INTO responses (id, evaluation_id, student_id, status, submitted_at) VALUES (3, 2, 1, 'submitted', '2026-11-04 10:00:00')")
        db.execute("INSERT INTO response_answers (response_id, question_id, text_value) VALUES (3, 3, 'FOREIGN_ONLY_COMMENT')")


@pytest.mark.parametrize("viewport", [{"width": 1440, "height": 900}, {"width": 390, "height": 844}], ids=["laptop", "phone"])
def test_lecturer_feedback_click_through(browser_app, viewport):
    """M5-L01/L02; US04 #50 + P0C-07: submitted-only detail and keyboard sign-out."""
    browser, url, database = browser_app
    seed_lecturer_feedback(database)
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    sign_in(page, url, "lecturer@test.com")
    expect(page).to_have_url(url + "/lecturer/feedback")
    expect(page.locator(".evaluation")).to_have_count(1)
    expect(page.locator('.evaluation[data-evaluation-id="1"] strong')).to_have_text("1")
    expect(page.get_by_text("UNASSIGNED_PRIVATE", exact=True)).to_have_count(0)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    review = page.get_by_role("link", name="Review feedback: Test Evaluation", exact=True)
    review.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Student ratings", exact=True)).to_be_visible()
    expect(page.locator("[data-completed-count]")).to_have_text("1")
    expect(page.get_by_label("Feedback summary")).to_contain_text("4.0 / 5")
    expect(page.get_by_role("heading", name="Written comments", exact=True)).to_be_visible()
    expect(page.get_by_text("Helpful examples. Practical labs made the concepts easier to follow.", exact=True)).to_be_visible()
    expect(page.get_by_text("DRAFT_ONLY_COMMENT", exact=True)).to_have_count(0)
    expect(page.get_by_text("FOREIGN_ONLY_COMMENT", exact=True)).to_have_count(0)
    assert page.locator("script:not([src])").count() == 0  # Feedback never creates an executable inline script.
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.reload(wait_until="domcontentloaded")
    expect(page.locator("[data-completed-count]")).to_have_text("1")
    if evidence_dir := os.environ.get("P0_SCREENSHOT_DIR"):
        destination = Path(evidence_dir)
        destination.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(destination / f"lecturer-detail-{viewport['width']}.png"), full_page=True)
    # Verify long unbroken and HTML-like feedback remains text and wraps safely.
    from contextlib import closing

    with closing(sqlite3.connect(database)) as db, db:
        db.execute("UPDATE response_answers SET text_value = ? WHERE response_id=1 AND question_id=2", ('Helpful examples. <script>alert("xss")</script> ' + 'LongFeedback' * 30,))
    page.reload(wait_until="domcontentloaded")
    expect(page.get_by_text('Helpful examples. <script>alert("xss")</script>', exact=False)).to_be_visible()
    assert page.locator("script:not([src])").count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("link", name="All evaluations", exact=False).click()
    expect(page.get_by_role("link", name="Review feedback:", exact=False)).to_have_count(1)
    logout = page.get_by_role("button", name="Sign out", exact=True)
    logout.focus()
    page.keyboard.press("Enter")
    expect(page).to_have_url(url + "/login")
    response = context.request.get(url + "/lecturer/feedback/1", headers={"Accept": "text/html"})
    assert response.status == 200
    assert response.url == url + "/login"
    assert "Helpful examples" not in response.text()
    assert context.request.get(url + "/api/courses/1/feedback").status == 401
    context.close()


def test_lecturer_feedback_empty_states(browser_app):
    """M5-L03: distinguish assigned evaluation without submissions from no assignments."""
    from contextlib import closing

    browser, url, database = browser_app
    page = browser.new_page(viewport={"width": 390, "height": 844})
    sign_in(page, url, "lecturer@test.com")
    expect(page).to_have_url(url + "/lecturer/feedback")
    page.get_by_role("link", name="Review feedback:", exact=False).click()
    expect(page.get_by_role("heading", name="No feedback submitted yet")).to_be_visible()
    expect(page.locator("[data-completed-count]")).to_have_text("0")
    expect(page.get_by_text("draft answers are excluded", exact=False)).to_be_visible()
    page.get_by_role("link", name="Refresh feedback", exact=True).click()
    expect(page.get_by_role("heading", name="No feedback submitted yet")).to_be_visible()
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("DELETE FROM course_lecturers")
    page.get_by_role("link", name="All evaluations", exact=False).click()
    expect(page.get_by_role("heading", name="No evaluations available")).to_be_visible()
    expect(page.get_by_text("contact your university administrator", exact=False)).to_be_visible()
    page.get_by_role("link", name="Refresh assigned evaluations").click()
    expect(page.get_by_role("heading", name="No evaluations available")).to_be_visible()
    if evidence_dir := os.environ.get("P0_SCREENSHOT_DIR"):
        destination = Path(evidence_dir)
        destination.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(destination / "lecturer-empty-390.png"), full_page=True)
    page.close()


@pytest.mark.parametrize("path,code", [("/lecturer/feedback/2", 403), ("/lecturer/feedback/999", 404)])
def test_lecturer_feedback_access_error_recovery(browser_app, path, code):
    """M5-L04: ownership/not-found errors never expose foreign feedback and allow recovery."""
    browser, url, database = browser_app
    seed_lecturer_feedback(database)
    page = browser.new_page()
    sign_in(page, url, "lecturer@test.com")
    expect(page).to_have_url(url + "/lecturer/feedback")
    response = page.goto(url + path, wait_until="domcontentloaded")
    assert response.status == code
    expect(page.get_by_role("alert")).to_be_visible()
    if code == 403:
        expect(page.get_by_text("You do not have permission to view this course feedback.", exact=True)).to_be_visible()
    else:
        expect(page.get_by_text("Evaluation not found.", exact=True)).to_be_visible()
    assert "FOREIGN_ONLY_COMMENT" not in page.content()
    assert "UNASSIGNED_PRIVATE" not in page.content()
    page.get_by_role("link", name="Return to assigned evaluations").click()
    expect(page).to_have_url(url + "/lecturer/feedback")
    expect(page.get_by_role("link", name="Review feedback:", exact=False)).to_have_count(1)
    page.close()


@pytest.mark.parametrize("role", ["anonymous", "student", "administrator"])
def test_lecturer_feedback_wrong_role_browser_errors(browser_app, role):
    """M5-L05: browser-only error presentation; preserve API/JSON denial contracts."""
    browser, url, database = browser_app
    seed_lecturer_feedback(database)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    if role != "anonymous":
        sign_in(page, url, "student@test.com" if role == "student" else "admin@test.com")
        expect(page).to_have_url(url + ("/evaluations" if role == "student" else "/account"))
    expected = 401 if role == "anonymous" else 403
    response = page.goto(url + "/lecturer/feedback/1", wait_until="domcontentloaded")
    assert response.status == (200 if role == "anonymous" else 403)
    if role == "anonymous":
        expect(page).to_have_url(url + "/login")
        expect(page.locator("#login-form")).to_be_visible()
    else:
        expect(page.get_by_role("heading", name="Unable to display feedback")).to_be_visible()
    assert "Helpful examples" not in page.content()
    assert "Test Evaluation" not in page.content()
    denial = page.request.get(url + "/api/courses/1/feedback")
    assert denial.status == expected
    assert denial.headers["content-type"].startswith("application/json")
    legacy = page.request.get(url + "/lecturer/feedback/1", headers={"Accept": "application/json"})
    assert legacy.status == expected
    assert legacy.headers["content-type"].startswith("application/json")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if role == "anonymous":
        expect(page).to_have_url(url + "/login")
    else:
        page.get_by_role("link", name="Return to My account", exact=True).click()
        expect(page).to_have_url(url + "/account")
    page.close()


def test_lecturer_feedback_unavailable_retry(browser_app, monkeypatch):
    """M5-L06: an actual SQLite failure gives safe 503 UI and a working retry."""
    browser, url, database = browser_app
    seed_lecturer_feedback(database)
    page = browser.new_page()
    sign_in(page, url, "lecturer@test.com")
    expect(page).to_have_url(url + "/lecturer/feedback")

    def database_failure():
        raise sqlite3.OperationalError("PRIVATE_DATABASE_FAILURE_DETAIL")

    with monkeypatch.context() as patch:
        patch.setattr(app_module, "get_db_connection", database_failure)
        response = page.reload(wait_until="domcontentloaded")
        assert response.status == 503
        expect(page.get_by_text("Feedback is temporarily unavailable.", exact=True)).to_be_visible()
        assert "PRIVATE_DATABASE_FAILURE_DETAIL" not in page.content()
        assert "Helpful examples" not in page.content()
    page.get_by_role("link", name="Try again", exact=True).click()
    expect(page.get_by_role("link", name="Review feedback:", exact=False)).to_have_count(1)
    page.close()


def seed_topic_comments(database, include_other=False):
    """US05 UI fixture: four meaningful topics, repeated content and excluded data."""
    from contextlib import closing

    seed_lecturer_feedback(database)
    comments = [
        "The course content needs more practical examples.",
        "The course content and syllabus are clear.",
        "The lecturer explained concepts clearly.",
        "The workload leaves little time for practice.",
        "The exam grading criteria need clarification.",
    ]
    if include_other:
        comments.append('A quieter room would help. <script>alert("xss")</script> ' + "LongComment" * 30)
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("UPDATE response_answers SET text_value=? WHERE response_id=1 AND question_id=2", (comments[0],))
        for position, text in enumerate(comments[1:], start=5):
            db.execute("INSERT INTO users (id,email,password_hash,full_name,role) VALUES (?,?,'fixture-hash','Synthetic Student','student')", (position, f"topic{position}@example.test"))
            cursor = db.execute("INSERT INTO responses (evaluation_id,student_id,submitted_at,status) VALUES (1,?,'2026-11-04 10:00:00','submitted')", (position,))
            db.execute("INSERT INTO response_answers (response_id,question_id,text_value) VALUES (?,2,?)", (cursor.lastrowid, text))
    return comments


def open_topic_analysis(page, url):
    sign_in(page, url, "lecturer@test.com")
    expect(page).to_have_url(url + "/lecturer/feedback")
    page.get_by_role("link", name="Review feedback: Test Evaluation", exact=True).click()
    page.get_by_role("link", name="Grouped feedback", exact=True).click()
    expect(page.locator("#topic-analysis")).to_have_attribute("aria-busy", "false")


@pytest.mark.parametrize("viewport", [{"width":1440,"height":900}, {"width":390,"height":844}], ids=["laptop", "phone"])
def test_grouped_feedback_four_topics(browser_app, viewport):
    """US05-UI01/02: exactly four nonempty groups, precise counts and keyboard expansion."""
    browser, url, database = browser_app
    comments = seed_topic_comments(database)
    page = browser.new_page(viewport=viewport)
    open_topic_analysis(page, url)
    expect(page.locator(".topic-card")).to_have_count(4)
    expect(page.locator("#topic-total")).to_have_text("5 comments · 4 topics")
    expect(page.locator(".topic-title")).to_have_text(["Course Content", "Teaching Delivery", "Workload", "Assessment"])
    expect(page.locator('[data-topic="Other"]')).to_have_count(0)
    content = page.locator('[data-topic="Course Content"]')
    expect(content.locator(".topic-count")).to_have_text("2 comments")
    expect(content.locator(".topic-share")).to_contain_text("40%")
    content.locator("summary").focus()
    page.keyboard.press("Enter")
    expect(content).to_have_attribute("open", "")
    expect(content.locator("li")).to_have_text(comments[:2])
    page.keyboard.press("Enter")
    expect(content).not_to_have_attribute("open", "")
    expect(content.locator("li")).to_have_count(0)
    for index, title in enumerate(["Teaching Delivery", "Workload", "Assessment"], start=2):
        group = page.locator(f'[data-topic="{title}"]')
        group.locator("summary").click()
        expect(group.locator("li")).to_have_text([comments[index]])
    assert "DRAFT_ONLY_COMMENT" not in page.locator("#topic-analysis").text_content()
    assert "FOREIGN_ONLY_COMMENT" not in page.locator("#topic-analysis").text_content()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if evidence_dir := os.environ.get("P0_SCREENSHOT_DIR"):
        destination = Path(evidence_dir)
        destination.mkdir(parents=True, exist_ok=True)
        content.locator("summary").click()
        page.locator("#topic-analysis").screenshot(path=str(destination / f"topics-{viewport['width']}.png"))
    page.reload(wait_until="domcontentloaded")
    expect(page.locator(".topic-card")).to_have_count(4)
    expect(page.locator("#topic-total")).to_have_text("5 comments · 4 topics")
    page.close()


def test_grouped_feedback_other_is_safe_text(browser_app):
    """US05-UI03: unclassified comments stay in Other; HTML-like/long text is safe."""
    browser, url, database = browser_app
    comments = seed_topic_comments(database, include_other=True)
    page = browser.new_page(viewport={"width":390,"height":844})
    open_topic_analysis(page, url)
    expect(page.locator(".topic-card")).to_have_count(5)
    expect(page.locator("#topic-total")).to_have_text("6 comments · 5 topics")
    other = page.locator('[data-topic="Other"]')
    other.locator("summary").click()
    expect(other.locator("li")).to_have_text([comments[-1]])
    assert page.locator("script:not([src])").count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.close()


def test_grouped_feedback_empty(browser_app):
    """US05-UI04: zero submitted written comments means no fabricated topic groups."""
    browser, url, _ = browser_app
    page = browser.new_page()
    open_topic_analysis(page, url)
    expect(page.locator("#topic-empty")).to_be_visible()
    expect(page.locator(".topic-card")).to_have_count(0)
    expect(page.locator("#topic-total")).to_have_text("0 comments · 0 topics")
    expect(page.get_by_role("heading", name="No feedback submitted yet")).to_be_visible()
    page.close()


@pytest.mark.parametrize("failure", ["network", "invalid-data", "forbidden"])
def test_grouped_feedback_error_and_retry(browser_app, failure):
    """US05-UI05: explain failed analysis and recover using a real API response."""
    browser, url, database = browser_app
    seed_topic_comments(database)
    page = browser.new_page()
    endpoint = "**/api/evaluations/1/feedback/topics"
    def fail(route):
        if failure == "network":
            route.abort()
        elif failure == "invalid-data":
            route.fulfill(status=200, json={"topics":[{"topic":"Other","count":10,"comments":[]}]})
        else:
            # Lose the real course assignment after HTML loads but before analysis fetch.
            from contextlib import closing

            with closing(sqlite3.connect(database)) as db, db:
                db.execute("DELETE FROM course_lecturers WHERE lecturer_id=2 AND course_id=1")
            route.continue_()
    page.route(endpoint, fail)
    open_topic_analysis(page, url)
    expect(page.locator("#topic-error")).to_be_visible()
    expect(page.locator("#topic-error-message")).not_to_be_empty()
    expect(page.locator("#topic-empty")).to_be_hidden()
    expect(page.locator(".topic-card")).to_have_count(0)
    if failure == "forbidden":
        expect(page.locator("#topic-error-message")).to_contain_text("You do not have permission to view this course feedback.")
    page.unroute(endpoint)
    if failure == "forbidden":
        from contextlib import closing

        with closing(sqlite3.connect(database)) as db, db:
            db.execute("INSERT INTO course_lecturers (lecturer_id,course_id) VALUES (2,1)")
    page.get_by_role("button", name="Try again", exact=True).click()
    expect(page.locator(".topic-card")).to_have_count(4)
    expect(page.locator("#topic-error")).to_be_hidden()
    expect(page.locator("#topic-total")).to_have_text("5 comments · 4 topics")
    page.close()


def test_grouped_feedback_expired_session(browser_app):
    """US05-UI06: an API 401 sends the browser to usable login without groups."""
    browser, url, database = browser_app
    seed_topic_comments(database)
    page = browser.new_page()
    page.route("**/api/evaluations/1/feedback/topics", lambda route: route.fulfill(status=401,json={"error":{"code":"UNAUTHORIZED"}}))
    sign_in(page, url, "lecturer@test.com")
    expect(page).to_have_url(url + "/lecturer/feedback")
    page.get_by_role("link", name="Review feedback: Test Evaluation", exact=True).click()
    expect(page).to_have_url(url + "/login")
    expect(page.locator("#login-form")).to_be_visible()
    expect(page.locator(".topic-card")).to_have_count(0)
    page.close()


@pytest.mark.parametrize("viewport", [{"width": 1440, "height": 900}, {"width": 390, "height": 844}], ids=["laptop", "phone"])
def test_saved_feedback_cross_role_after_closure(browser_app, viewport):
    """M5-A04: real US01→02→03→11→04 clicks, persisted feedback after closure."""
    browser, url, database = browser_app
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    sign_in(page, url)
    page.get_by_role("link", name="Start evaluation").click()
    rating = page.locator('input[type="radio"][value="5"]')
    rating.focus()
    page.keyboard.press("Space")
    expect(rating).to_be_checked()
    page.locator("textarea").fill("M5 audit saved feedback.")
    page.locator("#reviewButtonMobile" if viewport["width"] < 600 else "#reviewButton").click()
    page.get_by_role("button", name="Submit evaluation", exact=True).click()
    expect(page.locator("#submissionSuccess")).to_be_visible()
    with sqlite3.connect(database) as db:
        db.execute("UPDATE evaluations SET status='closed', deadline='2020-01-01' WHERE id=1")
    page.reload(wait_until="domcontentloaded")
    expect(page.locator("#submissionSuccess")).to_be_visible()
    expect(page.locator("#errorState")).not_to_be_visible()
    page.get_by_role("button", name="Sign out", exact=True).click()
    expect(page).to_have_url(url + "/login")
    assert context.request.get(url + "/api/evaluations").status == 401
    sign_in(page, url, "lecturer@test.com")
    page.get_by_role("link", name="Review feedback: Test Evaluation", exact=True).click()
    expect(page.locator("[data-completed-count]")).to_have_text("1")
    expect(page.get_by_label("Feedback summary")).to_contain_text("5.0 / 5")
    expect(page.get_by_text("M5 audit saved feedback.", exact=True)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if evidence_dir := os.environ.get("P0_SCREENSHOT_DIR"):
        destination = Path(evidence_dir)
        destination.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(destination / f"audit-cross-role-{viewport['width']}.png"), full_page=True)
    page.get_by_role("button", name="Sign out", exact=True).click()
    expect(page).to_have_url(url + "/login")
    assert context.request.get(url + "/api/courses/1/feedback").status == 401
    context.close()


@pytest.mark.parametrize("step", ["list", "questions", "submit"])
@pytest.mark.parametrize("failure", ["html-503", "malformed-200", "network"])
def test_unreadable_api_response_has_useful_recovery(browser_app, step, failure):
    """EX-UX01: non-JSON backend/proxy failures explain recovery and never fake success."""
    browser, url, database = browser_app
    page = browser.new_page()
    endpoint = {"list": "/api/evaluations", "questions": "/api/evaluations/1/questions", "submit": "/api/submissions"}[step]
    pattern = "**" + endpoint
    def fail_request(route):
        if failure == "network":
            route.abort()
        else:
            route.fulfill(status=503 if failure == "html-503" else 200,
                          content_type="text/html" if failure == "html-503" else "application/json",
                          body="<html>UPSTREAM_PRIVATE_DIAGNOSTIC</html>" if failure == "html-503" else "{broken-json")

    page.route(pattern, fail_request)
    sign_in(page, url)
    if step != "list":
        page.get_by_role("link", name="Start evaluation").click()
    if step == "submit":
        rating = page.locator('input[type="radio"][value="5"]')
        rating.focus()
        page.keyboard.press("Space")
        expect(rating).to_be_checked()
        page.locator("#reviewButton").click()
        page.get_by_role("button", name="Submit evaluation", exact=True).click()
        error = page.locator("#submitFeedback")
        expect(page.locator("#submissionSuccess")).not_to_be_visible()
        with sqlite3.connect(database) as db:
            assert db.execute('SELECT COUNT(*) FROM responses').fetchone()[0] == 0
    else:
        error = page.locator("#errorMessage")
    expect(error).to_contain_text("Unable to connect to the service." if failure == "network" else "The service returned an unreadable response.")
    expect(error).to_contain_text("try again")
    assert "UPSTREAM_PRIVATE" not in error.inner_text()
    page.unroute(pattern)
    if step == "list":
        page.locator("#retryButton").click()
        expect(page.get_by_role("link", name="Start evaluation")).to_be_visible()
    elif step == "questions":
        page.locator("#errorState").get_by_role("link", name="Back to evaluations", exact=True).click()
        page.get_by_role("link", name="Start evaluation").click()
        expect(page.locator('input[type="radio"][value="5"]')).to_have_count(1)
    else:
        page.get_by_role("button", name="Submit evaluation", exact=True).click()
        expect(page.locator("#submissionSuccess")).to_be_visible()
    page.close()


@pytest.mark.parametrize("email", ["student@test.com", "lecturer@test.com", "admin@test.com"])
def test_private_history_and_expired_session_require_login(browser_app, email):
    """EX-S01: real Back navigation/repeated logout/cookie expiry expose no private page."""
    browser, url, _ = browser_app
    context = browser.new_context()
    page = context.new_page()
    sign_in(page, url, email)
    expect(page.get_by_role("button", name="Sign out", exact=True)).to_be_visible()
    page.get_by_role("link", name="My account", exact=True).click()
    page.get_by_role("button", name="Sign out", exact=True).click()
    expect(page).to_have_url(url + "/login")
    page.go_back(wait_until="domcontentloaded")
    # / is also the approved public login page; admin history can return there.
    expect(page.get_by_role("heading", name="Welcome back", exact=True)).to_be_visible()
    assert page.url in (url + "/", url + "/login")
    expect(page.locator("#password")).to_have_value("")
    expect(page.get_by_role("button", name="Sign out", exact=True)).to_have_count(0)
    assert context.request.post(url + "/api/auth/logout").json() == {"authenticated": False}
    assert context.request.get(url + "/api/auth/me").status == 401
    sign_in(page, url, email)
    expect(page.get_by_role("button", name="Sign out", exact=True)).to_be_visible()
    context.clear_cookies()
    page.get_by_role("link", name="My account", exact=True).click()
    expect(page).to_have_url(url + "/login")
    expect(page.get_by_role("button", name="Sign out", exact=True)).to_have_count(0)
    context.close()


def test_login_empty_and_invalid_inputs_are_actionable(browser_app):
    """EX-UX02: visible form validation, focus and retry without sending bad credentials."""
    browser, url, _ = browser_app
    page = browser.new_page()
    sent = []
    page.on("request", lambda request: sent.append(request.url) if request.url.endswith('/api/auth/login') else None)
    page.goto(url)
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page.locator("#email-error")).to_have_text("Please enter your email address.")
    expect(page.locator("#password-error")).to_have_text("Please enter your password.")
    expect(page.locator("#email")).to_be_focused()
    page.locator("#email").fill("invalid-email")
    page.locator("#password").fill("Password123!")
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page.locator("#email-error")).to_have_text("Please enter a valid email address.")
    assert sent == []
    page.locator("#email").fill("student@test.com")
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page).to_have_url(url + "/evaluations")
    page.close()


@pytest.mark.parametrize('viewport', [{'width': 1440, 'height': 900}, {'width': 390, 'height': 844}], ids=['laptop', 'phone'])
def test_workspace_creation_and_draft_roundtrip(browser_app, viewport):
    browser, url, database = browser_app
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    try:
        sign_in(page, url, 'lecturer@test.com')
        expect(page).to_have_url(url + '/lecturer/feedback')
        page.goto(url + '/lecturer/evaluations')
        expect(page.get_by_role('heading', name='Welcome, Test Lecturer')).to_be_visible()
        page.get_by_label('Evaluation title', exact=True).fill('Live course feedback')
        page.get_by_label('Deadline (your local time)', exact=True).fill('2099-12-01T12:00')
        page.get_by_label('Question text', exact=True).fill('Was the course clear?')
        page.get_by_role('button', name='Save draft', exact=True).click()
        expect(page.locator('#form-status')).to_contain_text('Draft saved')
        card = page.locator('#evaluation-list article').filter(has_text='Live course feedback')
        card.get_by_role('button', name='Open evaluation', exact=True).click()
        expect(card).to_contain_text('open')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.get_by_role('button', name='Sign out', exact=True).click()
        expect(page).to_have_url(url + '/login')
        sign_in(page, url)
        expect(page).to_have_url(url + '/evaluations')
        with sqlite3.connect(database) as db:
            identifier = db.execute("SELECT id FROM evaluations WHERE title='Live course feedback'").fetchone()[0]
        page.goto(f'{url}/evaluations/{identifier}/complete')
        rating = page.locator('input[type=radio][value="4"]')
        expect(rating).to_have_count(1)
        rating.focus()
        page.keyboard.press("Space")
        expect(rating).to_be_checked()
        page.get_by_role('button', name='Save draft', exact=True).click()
        expect(page.locator('#draftStatus')).to_contain_text('Draft saved')
        page.reload()
        expect(page.locator('input[type=radio][value="4"]')).to_be_checked()
    finally:
        context.close()
