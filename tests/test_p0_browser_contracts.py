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
