"""Capture role UI evidence using only a fresh temporary synthetic database.

Usage: python tools/capture_role_ui.py --output /path/to/evidence
Requires Playwright and its browser (or PLAYWRIGHT_CHROMIUM_EXECUTABLE).
Never reads production credentials or the runtime database.
"""
import argparse
import json
import os
import secrets
import sys
import tempfile
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def capture(output):
    from playwright.sync_api import expect, sync_playwright
    from werkzeug.serving import make_server

    with tempfile.TemporaryDirectory(prefix='edusurvey-ui-evidence-') as temporary:
        # Runtime gives DATABASE_URL precedence over the SQLite path. Replace
        # inherited database/hosting configuration before importing the app.
        os.environ['DATABASE_URL'] = ''
        os.environ['EDUSURVEY_DATABASE_BACKEND'] = 'sqlite'
        os.environ['RENDER'] = 'false'
        os.environ['EDUSURVEY_SECRET_KEY'] = secrets.token_urlsafe(32)
        os.environ['EDUSURVEY_ENV'] = 'development'
        os.environ['EDUSURVEY_DATABASE'] = str(Path(temporary) / 'evidence.db')
        # Import after isolating runtime configuration.
        from src.init_db import initialize_database
        initialize_database(m5_demo=True)
        from tools.enrich_demo import enrich
        credential = secrets.token_urlsafe(24)
        enrich(os.environ['EDUSURVEY_DATABASE'], credential, rich=True)
        from src.app import app, get_db_connection
        with get_db_connection() as db:
            evaluation = db.execute("SELECT e.id FROM evaluations e JOIN courses c ON c.id=e.course_id WHERE c.course_code='DEMO-RICH-001'").fetchone()['id']
        server = make_server('127.0.0.1', 0, app, threaded=True)
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        url = f'http://127.0.0.1:{server.server_port}'
        output.mkdir(parents=True, exist_ok=True)
        evidence = []
        try:
            with sync_playwright() as playwright:
                options = {'headless': True}
                if executable := os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):
                    options['executable_path'] = executable
                browser = playwright.chromium.launch(**options)
                screens = [
                    ('login', None, '/login'),
                    ('student-dashboard', 'student1', '/dashboard'),
                    ('student-evaluations', 'student1', '/evaluations'),
                    ('student-survey', 'student1', f'/evaluations/{evaluation}/complete'),
                    ('lecturer-dashboard', 'lecturer1', '/dashboard'),
                    ('lecturer-management', 'lecturer1', '/lecturer/evaluations'),
                    ('lecturer-feedback', 'lecturer1', f'/lecturer/feedback/{evaluation}'),
                    ('admin-dashboard', 'admin', '/dashboard'),
                    ('admin-accounts', 'admin', '/admin/users'),
                ]
                for name, account, route in screens:
                    for device, width, height in [('desktop', 1440, 1000), ('tablet', 820, 1180), ('phone', 390, 844)]:
                        context = browser.new_context(viewport={'width': width, 'height': height}, reduced_motion='reduce')
                        if account:
                            result = context.request.post(url + '/api/auth/login', data={'email': account + '@demo.edusurvey.invalid', 'password': credential})
                            assert result.status == 200
                        page = context.new_page()
                        errors = []
                        page.on('pageerror', lambda error, target=errors: target.append(str(error)))
                        response = page.goto(url + route)
                        assert response.status == 200
                        if page.locator('#status').count():
                            expect(page.locator('#status')).to_have_text('Workspace updated.')
                        elif name == 'student-evaluations':
                            expect(page.locator('#totalCount')).to_have_text('6')
                        elif name == 'student-survey':
                            expect(page.locator('.question-card')).to_have_count(10)
                        elif name == 'lecturer-feedback':
                            expect(page.locator('#topic-analysis')).to_have_attribute('aria-busy', 'false')
                        assert not errors, errors
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (name, device)
                        # Semantic label audit includes only controls exposed to users.
                        unnamed = page.locator('input:not([type=hidden]),select,textarea').evaluate_all('''elements => elements.filter(el => el.getClientRects().length && !el.labels?.length && !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby')).map(el => el.outerHTML)''')
                        assert not unnamed, unnamed
                        filename = f'{name}-{device}.png'
                        page.screenshot(path=str(output / filename))
                        if name == 'admin-accounts':
                            page.locator('#users').evaluate("element => element.scrollIntoView({block: 'start'})")
                            page.screenshot(path=str(output / f'admin-directory-{device}.png'))
                        evidence.append({'screen': name, 'device': device, 'viewport': [width, height], 'screenshot': filename, 'http_status': response.status, 'javascript_errors': errors, 'horizontal_overflow': False, 'unlabelled_controls': len(unnamed)})
                        context.close()
                browser.close()
        finally:
            server.shutdown()
            worker.join(timeout=5)
            server.server_close()
        (output / 'manifest.json').write_text(json.dumps(evidence, indent=2) + '\n')
        print(f'Captured {len(evidence)} role/viewport checks into {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    capture(parser.parse_args().output)
