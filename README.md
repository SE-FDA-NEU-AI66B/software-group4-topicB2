# EduSurvey – University Course Evaluation System

EduSurvey is an online survey and evaluation system for universities. The system helps training departments collect student feedback about courses and lecturers, analyze evaluation results, and support improvements in education quality.

## Milestone 3 – P0 User Stories and Entry Points

The following table provides the starting screen, route, and navigation path for each P0 user story.

| User Story | Description | Starting Screen | Route / Entry Point | Status |
|---|---|---|---|---|
| US01 | User Login and Authentication | Login | `/login` | Implemented |
| US02 | View Available Course Evaluations | My Evaluations | `/evaluations` | Implemented |
| US03 | Complete and Submit Course Evaluation | My Evaluations | `/evaluations/<evaluation_id>/complete` | Implemented; verify backend persistence |
| US04 | Review Submitted Student Feedback | Lecturer authentication | `GET /api/courses/<course_id>/feedback` | Backend implemented; frontend pending |
| US11 | User Sign Out | Authenticated session | `POST /api/auth/logout` | Backend implemented; visible UI control pending |

### 1. US01 – User Login and Authentication

**Starting screen:** Login

**Route:** `/login`

**Purpose:** Allow registered university users to authenticate and access the system according to their roles.

**Navigation:**
1. Open EduSurvey.
2. Navigate to the Login screen.
3. Enter university email and password.
4. Click **Sign in**.
5. After successful authentication, access the appropriate user workflow.

### 2. US02 – View Available Course Evaluations

**Starting screen:** My Evaluations

**Route:** `/evaluations`

**API:** `GET /api/evaluations`

**Purpose:** Allow students to view assigned course evaluations, check deadlines, and monitor submission status.

**Navigation:**
1. Log in using a student account.
2. Open **My Evaluations**.
3. Browse available evaluation cards.
4. Use search and status filters to find an evaluation.
5. Select **Start Evaluation** to begin an available evaluation.

Each evaluation displays five key details:
- Survey title
- Course name
- Lecturer name
- Submission deadline
- Survey status

Supported statuses:
- Active
- Due soon
- Completed
- Closed

### 3. US03 – Complete and Submit Course Evaluation

**Starting screen:** My Evaluations

**Route:** `/evaluations/<evaluation_id>/complete`

**APIs:**
- `GET /api/evaluations/<evaluation_id>/questions`
- `POST /api/submissions`

**Purpose:** Allow students to answer evaluation questions and submit their feedback.

**Navigation:**
1. Log in using a student account.
2. Open **My Evaluations**.
3. Select an available evaluation.
4. Click **Start Evaluation**.
5. Answer the rating-based and text-based questions.
6. Complete all required questions.
7. Click **Review Answers**.
8. Review the responses and click **Submit Evaluation**.

The system validates required answers and prevents invalid or duplicate submissions according to the backend business rules.

### 4. US04 – Review Submitted Student Feedback

**Starting point:** Lecturer authentication.

**Backend API:** `GET /api/courses/<course_id>/feedback`

**Parent Story:** #50

**Task:** #51

**Purpose:** Allow lecturers to retrieve submitted student feedback for courses they are assigned to teach.

**Workflow:**
1. Authenticate using a lecturer account.
2. Identify the course assigned to the lecturer.
3. Request the course feedback through the lecturer feedback API.
4. The backend verifies lecturer course ownership.
5. Authorized lecturers receive submitted ratings, written comments, and completed evaluation counts.

**Access restriction:**

Lecturers cannot retrieve feedback for courses they are not assigned to teach. Unauthorized requests return HTTP 403 with the following message:

`You do not have permission to view this course feedback.`

**Implementation note:** The backend API is implemented. A dedicated lecturer-facing frontend screen is not yet available in the documented implementation.

### 5. US11 – User Sign Out

**Starting point:** Authenticated session.

**API:** `POST /api/auth/logout`

**Purpose:** Allow users to terminate their authenticated session securely.

**Expected workflow:**
1. The authenticated user selects Sign out.
2. The frontend sends a POST request to the logout API.
3. The backend clears the current session.
4. The user is redirected to the Login screen.

**Implementation note:** The logout API is available. A visible Sign out control in the frontend is pending implementation.

---

## Project Setup

For complete installation, database initialization, configuration, and execution instructions, refer to:

**[Project Setup Guide – docs/SETUP.md](docs/SETUP.md)**

### Clone the Repository

```bash
git clone https://github.com/SE-FDA-NEU-AI66B/software-group4-topicB2.git

cd software-group4-topicB2
```

### Run the Application

Follow the environment setup and database initialization instructions in [docs/SETUP.md](docs/SETUP.md).

After completing the setup, run:

```bash
python -m flask --app src.app run --debug --port 5004
```

Open the application in your browser:

`http://127.0.0.1:5004`

Use the student or lecturer demo accounts documented in the setup guide.

---

## Team

| Name | GitHub | Role |
|---|---|---|
| Le Sy Huy | lesyhuy2k6-gif | Scrum Master (Sprint 1) |
| Khuat Dinh Trung | khuatnhatminhcfpro-cmyk | Product Owner (PO) |
| Duong Duc Anh | tlduongducanh281-jpg | Scrum Master (Sprint 2) |

## Project Board

[EduSurvey Sprint Board](https://github.com/orgs/SE-FDA-NEU-AI66B/projects/4/views/1)

## Documentation

| Document | Description |
|---|---|
| [Setup Guide](docs/SETUP.md) | Installation and application setup |
| [UI Documentation](docs/ui.md) | M3 screens, routes, wireframes, and UI states |

## Testing

Run the automated test suite:

```bash
python -m pytest -v
```

## Definition of Done

A task is considered Done when:

- The work required by the issue is completed.
- The acceptance criteria of the issue are satisfied.
- The changes are committed and pushed to the repository.
- Required pull request reviews are completed and the pull request is approved.
- All required checks pass.
- The related issue is updated and moved to Done.