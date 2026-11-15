# EduSurvey Setup Guide

This guide explains how to set up and run the EduSurvey walking skeleton on a fresh machine.

## 1. Prerequisites

Required tools:

- Python 3.14.x
- pip
- Git
- SQLite 3
- A modern web browser

### macOS

```bash
brew install python sqlite git
```

### Windows

Install Python 3 and Git. During Python installation, select **Add Python to PATH**.

Python includes the `sqlite3` module required to run EduSurvey. The SQLite command-line tool is only needed for manual database verification.

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv sqlite3 git
```

## 2. Clone the Repository

```bash
git clone https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2.git
cd software-group4-topicB2
```

## 3. Create a Virtual Environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

## 4. Install Dependencies

### macOS / Linux

```bash
python3 -m pip install -r requirements.txt
```

### Windows

```bash
python -m pip install -r requirements.txt
```

## 5. Environment Configuration

The current walking skeleton does not require API keys or external services.

The SQLite database is stored locally at:

```text
data/edusurvey.db
```

The database file is generated locally and ignored by Git.

## 6. Initialize and Seed the Database

### macOS / Linux

```bash
python3 src/init_db.py
```

### Windows

```bash
python src/init_db.py
```

Expected output includes:

```text
EduSurvey database initialized successfully.
Seeded evaluations: 10
```

To verify the seed data:

```bash
sqlite3 data/edusurvey.db "SELECT COUNT(*) FROM evaluations;"
```

Expected result:

```text
10
```

## 7. Run the Application

### macOS / Linux

```bash
python3 src/app.py
```

### Windows

```bash
python src/app.py
```

Open:

```text
http://127.0.0.1:5000/evaluations
```

### Expected Result

The page should display EduSurvey course evaluations retrieved from the SQLite database, including course information, evaluation title, deadline, and status.

This verifies the walking skeleton:

```text
Browser → Flask → SQLite → Jinja Template → Browser
```

## 8. Troubleshooting

### Flask module not found

If you see:

```text
ModuleNotFoundError: No module named 'flask'
```

Activate the virtual environment and run:

```bash
python3 -m pip install -r requirements.txt
```

On Windows, use `python` instead of `python3`.

### Database table not found

If you see:

```text
sqlite3.OperationalError: no such table: evaluations
```

Initialize the database again:

```bash
python3 src/init_db.py
```

On Windows:

```bash
python src/init_db.py
```

Then restart the application.

### Port 5000 already in use

Stop the application currently using port 5000, then run EduSurvey again.

## 9. Fresh-Machine Verification

Complete this section after a team member other than the author has tested the setup from a clean environment.

- **Tested by:** Pending verification
- **Operating system:** Pending verification
- **Test date:** Pending verification
- **Setup duration:** Pending verification
- **Result:** Pending verification

Verification checklist:

- [ ] Dependencies install successfully from `requirements.txt`.
- [ ] Database initialization succeeds on a clean environment.
- [ ] All required tables are created.
- [ ] Seed data and database constraints are verified.
- [ ] The Flask application starts successfully.
- [ ] The `/evaluations` page displays evaluation data from SQLite.

## 10. Automated Testing

EduSurvey uses `pytest` to run the automated test suite.

The actual #190 [clean-clone audit](m4-review-evidence.md) installed development
dependencies in a new Python 3.11.9 Windows environment. The current audited
baseline `686bd9e` has five failing runtime/database audit tests; see exact
results and blockers before treating setup as verified for M4. This automated
run does not fill the independent human fresh-machine checklist in Section 9.

### 10.1 Install Test Dependencies

After activating the virtual environment, install the development and testing dependencies:

```bash
python -m pip install -r requirements-dev.txt

python -m playwright install chromium
```

On Linux, install browser system dependencies with `python -m playwright install --with-deps chromium` (requires system package permissions). CI runs this automatically. Browser tests start their own loopback server and temporary SQLite database; do not run the application or initialize the real database for pytest.

```bash
python -m pytest -v
```

To use an existing Chromium/Chrome installation instead of downloading a browser, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to its executable path. This is optional; CI uses Playwright's managed Chromium.

### 10.2 Disposable student demo

```bash
python tools/run_student_demo.py
```

Open `http://127.0.0.1:5000/`. The sign-in page documents the seeded student, lecturer and administrator accounts. This tool creates a temporary database, opens one evaluation for seven days, and removes that data when stopped with Ctrl+C. Responses persist across navigation/reloads while that process runs. It never writes `data/edusurvey.db`; it is a local development demo, not the public deployment/production database configuration. See [the walkthrough and verification evidence](p0-student-navigation.md).
