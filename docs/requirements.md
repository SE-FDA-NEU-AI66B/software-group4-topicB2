# EduSurvey Requirements Document

## 1. Product Vision

EduSurvey is a course evaluation management platform designed for students, lecturers, and university administrators. The system helps educational institutions collect, manage, and analyze student feedback efficiently, reducing the limitations of traditional paper-based surveys and manual data processing.

---

# 2. Personas

## Persona 1: Student

**Role:**  
University student who participates in course evaluations.

**Goals:**
- Complete course evaluations easily and conveniently.
- Provide feedback about courses and lecturers.
- Track submitted evaluations.

**Blockers:**
- Traditional feedback methods are time-consuming.
- Students may forget evaluation deadlines.
- Students have limited visibility of their previous feedback.

**Quote:**

> "I want a simple way to evaluate my courses without spending too much time."

**Interview Note:**
- Interviewee: A third-year university student.
- Date: September 2026.
- Topic discussed: Difficulties when completing course evaluations.
- Key finding: Students prefer an online system that is easy to access and track.


---

## Persona 2: Lecturer

**Role:**  
Lecturer who creates surveys and reviews student feedback.

**Goals:**
- Create course evaluation surveys.
- Receive feedback from students.
- Understand student opinions to improve teaching quality.

**Blockers:**
- Manual feedback collection requires significant effort.
- Difficult to summarize large amounts of feedback.
- Limited tools for analyzing evaluation results.

**Quote:**

> "I need a convenient way to understand student feedback and improve my courses."

**Interview Note:**
- Interviewee: A university lecturer.
- Date: September 2026.
- Topic discussed: Challenges in collecting and reviewing student evaluations.
- Key finding: Lecturers need centralized feedback management and simple reports.

---

# 3. Scenarios

## Scenario 1: Student completes course evaluation

**Persona:** Student

**Goal:**  
Submit course feedback to share opinions about the learning experience.

**Steps:**

1. The student logs into the EduSurvey system using their account.
2. The student checks the list of assigned course evaluations.
3. The student selects a course evaluation that needs to be completed.
4. The student reviews the evaluation questions provided by the system.
5. The student provides ratings and comments based on their learning experience.
6. The student submits the completed evaluation.
7. The system stores the feedback and confirms successful submission.


---

## Scenario 2: Lecturer reviews student feedback

**Persona:** Lecturer

**Goal:**  
Review student feedback to understand course quality and improve teaching activities.

**Steps:**

1. The lecturer logs into the EduSurvey system.
2. The lecturer accesses feedback related to their courses.
3. The lecturer reviews submitted student evaluations.
4. The lecturer examines evaluation scores and student comments.
5. The lecturer identifies common feedback trends from students.
6. The lecturer uses collected feedback to improve future teaching activities.

---

# 4. User Stories

| ID | User Story | Priority | Story Points |
|---|---|---|---|
| US01 | As a registered user, I want to log into EduSurvey securely so that I can access system functions. | P1 | 3 |
| US02 | As a student, I want to view available surveys so that I know which courses I need to evaluate. | P1 | 3 |
| US03 | As a student, I want to complete course evaluations so that I can provide feedback about courses and lecturers. | P1 | 5 |
| US04 | As a student, I want to review submitted feedback so that I can track my evaluation history. | P2 | 3 |
| US05 | As a lecturer, I want to manage surveys so that I can collect student feedback effectively. | P1 | 5 |
| US06 | As a lecturer, I want to manage survey questions so that I can customize evaluation content. | P2 | 3 |
| US07 | As a lecturer, I want to view evaluation results so that I can understand student opinions. | P1 | 5 |
| US08 | As an administrator, I want to analyze survey statistics so that I can evaluate overall feedback results. | P2 | 3 |
| US09 | As an administrator, I want to manage users and roles so that I can control access permissions. | P2 | 3 |
| US10 | As an administrator, I want to export evaluation reports so that I can save and share survey results. | P2 | 3 |


## US01 - User Login and Authentication

**Acceptance Criteria**

- Given a registered user enters valid email and password, When the user submits the login form, Then the system authenticates the user and redirects them to the homepage within 3 seconds.

- Given a user enters incorrect login information, When the user submits the login form, Then the system rejects the login request and displays an error message.

- Given a user successfully logs in, When the system identifies the account role, Then the system provides access based on one of 3 roles: Student, Lecturer, or Administrator.


## US02 - View Available Surveys

**Acceptance Criteria**

- Given a student is logged into EduSurvey, When the student opens the survey list page, Then the system displays all surveys assigned to that student.

- Given a student views a survey item, When survey information is loaded, Then the system displays exactly 4 fields: survey title, course name, lecturer name, and deadline.

- Given a student has completed a survey, When the student views the survey list, Then the system shows the survey status as "Completed".


## US03 - Complete Course Evaluation

**Acceptance Criteria**

- Given a student selects an available survey, When the student opens the evaluation page, Then the system displays all questions belonging to that survey.

- Given a student answers all required questions, When the student submits the evaluation, Then the system saves 1 completed response successfully and updates the survey status.

- Given a student leaves required questions unanswered, When the student submits the evaluation, Then the system prevents submission and highlights missing answers.


## US04 - Review Submitted Feedback

**Acceptance Criteria**

- Given a student has submitted an evaluation, When the student opens feedback history, Then the system displays previously submitted feedback.

- Given a student views submitted feedback, When the information is loaded, Then the system displays at least 3 details: course name, submission date, and completion status.

- Given a student has not submitted any evaluation, When the student opens feedback history, Then the system displays a message indicating no submitted feedback exists.


## US05 - Manage Surveys

**Acceptance Criteria**

- Given a lecturer is logged into the system, When the lecturer opens the survey management page, Then the system displays all surveys created by that lecturer.

- Given a lecturer creates a new survey, When valid survey information is submitted, Then the system creates 1 new survey successfully.

- Given a lecturer updates an existing survey, When the lecturer saves changes, Then the system updates the survey information successfully.


## US06 - Manage Survey Questions

**Acceptance Criteria**

- Given a lecturer has created a survey, When the lecturer opens the question management page, Then the system displays all questions belonging to that survey.

- Given a lecturer wants to add a new question, When valid question information is submitted, Then the system creates 1 new survey question successfully.

- Given a lecturer edits or deletes an existing question, When the lecturer confirms the action, Then the system updates the question list successfully.


## US07 - View Evaluation Results

**Acceptance Criteria**

- Given evaluation responses exist in the system, When a lecturer opens the result page, Then the system displays evaluation results for the selected survey.

- Given a survey has received responses, When the result page loads, Then the system displays at least 2 statistics: average score and total number of responses.

- Given no responses exist for a survey, When the lecturer views the result page, Then the system displays a message indicating that no data is available.


## US08 - Analyze Survey Statistics

**Acceptance Criteria**

- Given survey response data exists, When the administrator opens the statistics page, Then the system displays calculated survey statistics.

- Given the administrator selects a survey, When statistics are generated, Then the system displays 3 basic metrics: average rating, total responses, and completion rate.

- Given insufficient data exists, When the administrator requests statistics, Then the system displays a message indicating unavailable data.


## US09 - Manage Users and Roles

**Acceptance Criteria**

- Given an administrator is logged into the system, When the administrator opens the user management page, Then the system displays a list of registered users.

- Given an administrator changes a user's role, When the update is saved, Then the system assigns one of 3 supported roles: Student, Lecturer, or Administrator.

- Given the user list is displayed, When the administrator views a user record, Then the system shows at least 3 details: name, email, and role.


## US10 - Export Evaluation Reports

**Acceptance Criteria**

- Given evaluation results exist in the system, When an administrator selects export, Then the system generates 1 report file containing survey results.

- Given an administrator chooses a report format, When the export process is completed, Then the system provides the generated report successfully.

- Given no evaluation data exists, When the administrator requests an export, Then the system displays a message indicating that no data is available.

---

# 5. Business Rules

## BR1: One evaluation submission per student

A student can submit each evaluation only once.

Example:

Student A submits Course Evaluation 001.  
A second submission for Course Evaluation 001 is rejected.


## BR2: Survey deadline management

Every survey must have a defined deadline.

Example:

A survey created on 01/09/2026 has a deadline on 15/09/2026.


## BR3: Required questions must be completed

Students must answer all required questions before submitting.

Example:

A survey contains 5 required questions.  
If the student answers only 4 questions, submission is rejected.


## BR4: Role-based access control

Users can only access functions according to their roles.

Example:

Student accounts cannot create surveys.  
Lecturer accounts cannot manage system users.


## BR5: Survey ownership

Lecturers can only modify surveys created by their own accounts.

Example:

Lecturer A cannot edit or delete surveys created by Lecturer B.


## BR6: Feedback access restriction

Evaluation results are only available to authorized users.

Example:

Only lecturers responsible for the course and administrators can view evaluation results.

---

# 6. Screens and Flow

## Screens

| Route | Purpose | Access | Priority |
|---|---|---|---|
| /login | User authentication | G | P0 |
| /surveys | View available surveys assigned to students | U | P0 |
| /survey/:id | Complete course evaluation | U | P0 |
| /manage-surveys | Lecturer manages surveys and questions | U | P1 |
| /results | View evaluation results and statistics | U | P1 |


## System Flow

```
Login
   ↓
Lecturer creates and manages surveys
   ↓
Students view available surveys
   ↓
Students complete course evaluation
   ↓
Submit feedback
   ↓
Lecturers and administrators view evaluation results
   ↓
Export evaluation reports
```
