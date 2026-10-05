# EduSurvey Design

## 1. Architecture
EduSurvey uses a lightweight layered web architecture. The architecture separates the user interface, request handling, business logic, and data persistence so that each part of the system can be developed and tested independently.

The system consists of four main components:

1. **Web Browser / User Interface**
   - Provides the interface for Students, Lecturers, and Administrators.
   - Sends HTTP requests when users sign in, view evaluations, submit responses, manage evaluations, or review feedback.
   - Displays HTML pages and system responses returned by the backend.

2. **Flask Web Layer**
   - Handles HTTP routes and incoming requests.
   - Validates request data and forwards operations to the application service layer.
   - Returns rendered HTML pages or API responses to the browser.

3. **Application Service Layer**
   - Contains EduSurvey business logic.
   - Handles evaluation access, evaluation creation, submission rules, deadlines, and feedback retrieval.
   - Coordinates operations between the web layer and the database.

4. **SQLite Database**
   - Provides persistent storage for EduSurvey.
   - Stores users, courses, course enrolments, evaluations, questions, responses, and answers.
   - Is accessed through SQL queries from the application service layer.

### Component Communication

- **Browser → Flask Web Layer:** HTTP requests and form/API data.
- **Flask Web Layer → Application Service Layer:** function calls and validated application data.
- **Application Service Layer → SQLite Database:** SQL queries and database operations.
- **SQLite Database → Application Service Layer:** query results and persisted data.
- **Flask Web Layer → Browser:** rendered HTML pages or API responses.

This architecture supports the Milestone 2 walking skeleton by providing a complete path from the browser to the backend, through the application logic, to a real SQLite database, and back to the browser.

![EduSurvey Architecture](images/architecture.png)
## 2. Data Model
EduSurvey uses a relational data model to manage users, courses, course assignments, evaluations, questions, student responses, and individual answers.

The database consists of eight main tables:

- USERS – stores Student, Lecturer, and Administrator accounts.
- COURSES – stores course information.
- COURSE_ENROLLMENTS – associates Students with the courses in which they are enrolled.
- COURSE_LECTURERS – associates Lecturers with their assigned courses.
- EVALUATIONS – stores course evaluations created by authorized users.
- QUESTIONS – stores questions belonging to an evaluation.
- RESPONSES – records a Student's submission for an evaluation.
- RESPONSE_ANSWERS – stores individual answers to evaluation questions.

### 2.1 Entity Relationships

- One USER can have many COURSE_ENROLLMENTS.
- One COURSE can have many COURSE_ENROLLMENTS.
- One USER acting as a Lecturer can have many COURSE_LECTURERS assignments.
- One COURSE can have many Lecturer assignments.
- One COURSE can contain many EVALUATIONS.
- One USER can create many EVALUATIONS.
- One EVALUATION can contain many QUESTIONS.
- One Student USER can submit many RESPONSES.
- One EVALUATION can receive many RESPONSES.
- One RESPONSE can contain many RESPONSE_ANSWERS.
- One QUESTION can be referenced by many RESPONSE_ANSWERS.

### 2.2 Business Rules and Constraints

The following database constraints support the EduSurvey requirements and business rules:

- USERS.email must be unique.
- COURSES.course_code must be unique.
- (student_id, course_id) in COURSE_ENROLLMENTS must be unique to prevent duplicate course enrolments.
- (lecturer_id, course_id) in COURSE_LECTURERS must be unique to prevent duplicate Lecturer assignments.
- (evaluation_id, student_id) in RESPONSES must be unique so that a Student can submit only one response for each evaluation.
- (response_id, question_id) in RESPONSE_ANSWERS must be unique so that a response contains only one answer for each question.
- USERS.role is restricted to student, lecturer, or administrator.
- EVALUATIONS.status is restricted to valid states such as draft, open, and closed.
- QUESTIONS.question_type is restricted to supported types such as rating and text.
- RESPONSE_ANSWERS.rating_value, when provided, must be between 1 and 5.
- A Lecturer may create and manage evaluations only for courses to which they are assigned through COURSE_LECTURERS.
- A Student may access evaluations only for courses in which they are enrolled through COURSE_ENROLLMENTS.

### 2.3 ER Diagram

![EduSurvey ER Diagram](images/erd.png)
## 3. API Design
EduSurvey provides REST-style API endpoints for authentication, course evaluations, student submissions, and lecturer feedback. The API supports the core P0 user stories defined in the requirements.

| Method | Endpoint | Actor | Purpose | Input | Success | Errors |
|---|---|---|---|---|---|---|
| POST | `/api/auth/login` | All users | Sign in to EduSurvey | `email`, `password` | `200 OK` with authenticated user/session | `400 Bad Request`, `401 Unauthorized` |
| POST | `/api/auth/logout` | Authenticated user | Sign out and invalidate the current session | Current session | `200 OK` | `401 Unauthorized` |
| GET | `/api/evaluations` | Student | View evaluations assigned to the student | Current user/session | `200 OK` with evaluation list | `401 Unauthorized`, `403 Forbidden` |
| GET | `/api/evaluations/{id}` | Student | View an evaluation and its questions | Evaluation ID | `200 OK` with evaluation details | `403 Forbidden`, `404 Not Found` |
| POST | `/api/evaluations/{id}/responses` | Student | Submit a completed course evaluation | Answers to evaluation questions | `201 Created` | `400 Bad Request`, `409 Conflict`, `422 Unprocessable Entity` |
| POST | `/api/evaluations` | Lecturer / Administrator | Create a course evaluation | Course, title, deadline, questions | `201 Created` | `400 Bad Request`, `403 Forbidden` |
| GET | `/api/lecturer/courses/{courseId}/feedback` | Lecturer | View feedback for an assigned course | Course ID | `200 OK` with feedback data | `403 Forbidden`, `404 Not Found` |
| GET | `/api/evaluations/{id}/statistics` | Lecturer | View evaluation feedback statistics | Evaluation ID | `200 OK` with statistics | `403 Forbidden`, `404 Not Found` |

### API Rules

- Authentication is required for all endpoints except `/api/auth/login`.
- Students may only access evaluations assigned to courses in which they are enrolled.
- A student may submit an evaluation only once. A duplicate submission returns `409 Conflict`.
- An evaluation cannot be submitted after its deadline.
- Lecturers may create evaluations only for courses assigned to them.
- Lecturers may access feedback and statistics only for their assigned courses.
- Administrators may create and manage evaluations at the system level.
- Invalid or missing request data returns an appropriate `400` or `422` response.
- Requests for resources that do not exist return `404 Not Found`.
- Unauthorized role or course access returns `403 Forbidden`.

### Response-Time Requirement

Under normal operating conditions, key user interactions including sign in, evaluation submission, and feedback/statistics retrieval should return a system response within **3 seconds**, consistent with the Milestone 1 requirements.
## 4. Walking Skeleton

## 5. Design Decisions

## 6. What Changed Since M1
