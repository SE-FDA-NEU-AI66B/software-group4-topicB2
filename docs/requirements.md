# EduSurvey Requirements Document

## 1. Product Vision

EduSurvey is a course evaluation management platform designed for students, lecturers, and university administrators. The system helps educational institutions collect, manage, and analyze student feedback efficiently, reducing the limitations of traditional paper-based surveys and manual data processing.

---

# 2. Personas

### Persona 1 – Student

**Name:** Minh – Third-year AI student

**Role:** A third-year university student studying Artificial Intelligence who completes course evaluation surveys during the semester.

**Goal:** Minh wants to complete course evaluations quickly and efficiently, with clear reminders before the submission deadline.

**Blocked by:** Minh often forgets survey deadlines and finds long surveys tiring and time-consuming, especially when the questions are repetitive or not focused on the most important aspects of the course.

**In his words:** *"I often forget the deadline, and the surveys are too long. I want reminders and questions that are short and focused."*

**Technical skill:** Comfortable using smartphones, laptops, and web applications. Minh expects the survey system to be simple, responsive, and easy to use on mobile devices.

**Interview note:** Interviewed an anonymous third-year Artificial Intelligence student on **18 September 2026**. The student identified forgotten deadlines and overly long surveys as the main problems, and preferred deadline reminders and shorter, more focused survey questions.


---

### Persona 2 – Lecturer

**Name:** Anh – University Lecturer

**Role:** A university lecturer who reviews student course evaluations to understand teaching effectiveness and identify areas for improvement.

**Goal:** Anh wants to understand student feedback quickly, identify the most common issues, and use clear statistics to decide which aspects of the course should be improved.

**Blocked by:** Student feedback is often too general, making it difficult to determine which problems are the most important. When there are many responses, manually reading and comparing individual comments also makes it difficult to identify recurring themes.

**In his words:** *"The feedback is often too general, so it is difficult to know which issues are actually important. I want the system to group feedback by topic, highlight the most common issues, and show useful statistics."*

**Technical skill:** Comfortable using university systems, web applications, and basic data dashboards. Anh prefers information to be summarized clearly rather than manually reviewing a large number of individual responses.

**Interview note:** Interviewed a university lecturer on **18 September 2026**. The lecturer identified overly general feedback and difficulty prioritizing issues as the main problems. The lecturer preferred a system that automatically groups feedback by topic, highlights frequently mentioned issues, and provides summary statistics.


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
