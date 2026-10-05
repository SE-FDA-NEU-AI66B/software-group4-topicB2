# EduSurvey Requirements Document

## 1. Product Vision

EduSurvey is an online course evaluation platform for universities that centralizes the creation, distribution, completion, management, and analysis of course evaluations.

The system provides separate experiences for **Students, Lecturers, and Administrators**:

- **Students** can access their assigned evaluations, complete them before the deadline, and receive reminders for unfinished evaluations.
- **Lecturers** can create evaluations for courses they are assigned to and review feedback and statistics for those courses.
- **Administrators** can create and manage evaluations at the system level, manage users and roles, and configure system settings.

EduSurvey aims to replace fragmented or manual course evaluation processes with a centralized system that makes evaluations easier to complete, manage, and analyze.

The platform follows a role-based access model so that each user can access only the functions permitted for their role.

---

# 2. Personas

## Persona 1 – Student

**Name:** Minh – Third-year AI student

**Role:** A third-year university student who completes course evaluation surveys during the semester.

**Goal:** Minh wants to complete course evaluations quickly and efficiently while receiving clear reminders before deadlines.

**Blocked by:** Minh often forgets evaluation deadlines and finds long surveys tiring and time-consuming.

**In his words:** *"I often forget the deadline, and the surveys are too long. I want reminders and questions that are short and focused."*

**Technical skill:** Comfortable using smartphones, laptops, and web applications. Minh expects the evaluation system to be simple, responsive, and easy to use.

**Interview note:** Interviewed an anonymous third-year Artificial Intelligence student on **18 September 2026**. The student identified forgotten deadlines and overly long surveys as the main problems and preferred deadline reminders and shorter, focused questions.

---

## Persona 2 – Lecturer

**Name:** Anh – University Lecturer

**Role:** A university lecturer who creates evaluations for assigned courses and reviews student feedback to understand teaching effectiveness and identify areas for improvement.

**Goal:** Anh wants to create focused evaluations for his assigned courses, monitor response progress, review student feedback, identify common issues, and use statistics to improve teaching.

**Blocked by:** Student feedback can be difficult to analyze when there are many responses. Manually comparing comments makes it difficult to identify recurring issues and prioritize improvements.

**In his words:** *"I want to create evaluations for my courses and quickly understand the most important issues raised by students."*

**Technical skill:** Comfortable using university systems, web applications, and data dashboards.

**Interview note:** Interviewed a university lecturer on **18 September 2026**. The lecturer identified difficulty prioritizing issues in student feedback as a main problem and preferred grouped feedback, common-issue summaries, and statistics.

---

## Persona 3 – Administrator

**Name:** Lan – University Administrator

**Role:** A university administrator responsible for managing evaluations, users, roles, and system configuration.

**Goal:** Lan wants to manage evaluations, user access, roles, deadlines, and system settings from one centralized administration area.

**Blocked by:** Without centralized administration functions, it is difficult to maintain consistent evaluation configuration and control which users can access different system functions.

**In her words:** *"I need to manage evaluations, user access, and important system settings from one place."*

**Technical skill:** Comfortable using university management systems, web applications, and administrative dashboards.

---

# 3. Scenarios

## Scenario 1: Student signs in and accesses permitted functions

**Persona:** Minh – Third-year AI student

**Goal:** Sign in securely and access the functions available to his role.

**Steps:**

1. Minh opens EduSurvey.
2. He enters his registered email address and password.
3. The system validates his credentials.
4. The system identifies his role as Student.
5. The system grants access to Student functions.
6. Minh views his available course evaluations.
7. Minh can complete evaluations assigned to him.
8. Minh signs out when he finishes using the system.
9. The system ends his authenticated session and prevents access to protected functions until he signs in again.

---

## Scenario 2: Student completes a course evaluation before the deadline

**Persona:** Minh – Third-year AI student

**Goal:** Complete a course evaluation efficiently before its deadline.

**Steps:**

1. Minh receives a reminder for an unfinished evaluation approaching its deadline.
2. He opens his list of available evaluations.
3. He reviews the course name, lecturer, deadline, and evaluation status.
4. He selects an active evaluation.
5. He answers the evaluation questions.
6. The system identifies any required questions that have not been answered.
7. Minh completes the missing required response.
8. He submits the evaluation.
9. The system validates and stores the response.
10. The system confirms successful submission.
11. The evaluation status changes to **Completed**.
12. Minh cannot submit the same evaluation again.

## Scenario 3: Lecturer creates an evaluation for an assigned course

**Persona:** Anh – University Lecturer

**Goal:** Create a structured course evaluation for a course assigned to him.

**Steps:**

1. Anh signs in using his Lecturer account.
2. The system identifies his role as Lecturer.
3. Anh opens the evaluation creation function.
4. He selects a course assigned to him.
5. He enters the evaluation title, deadline, and questions.
6. He submits the evaluation for creation.
7. The system validates the evaluation details.
8. The system verifies that Anh is assigned to the selected course.
9. The system saves the evaluation.
10. The evaluation becomes available for the assigned course according to its configured schedule.
11. Anh can monitor the evaluation after it has been created.
12. Anh signs out when he finishes.

---

## Scenario 4: Lecturer reviews and prioritizes student feedback

**Persona:** Anh – University Lecturer

**Goal:** Understand student feedback and identify the most important issues for course improvement.

**Steps:**

1. After students submit evaluations, Anh signs in to EduSurvey.
2. He opens the results for one of his assigned courses.
3. He reviews the response count and response rate.
4. He views the average ratings for evaluation questions.
5. He reviews feedback grouped into topics such as course content, teaching delivery, workload, and assessment.
6. He reviews the most frequently mentioned issues.
7. He examines relevant student comments.
8. He compares statistics across evaluation questions.
9. He identifies the main areas requiring improvement.
10. Anh signs out after completing the review.

---

## Scenario 5: Administrator manages evaluations and system access

**Persona:** Lan – University Administrator

**Goal:** Manage evaluations, users, roles, and system settings.

**Steps:**

1. Lan signs in using her Administrator account.
2. The system identifies her role as Administrator.
3. Lan opens the administrator management area.
4. She creates or manages a course evaluation.
5. She configures the evaluation deadline and questions.
6. She manages user accounts and assigned roles.
7. She updates relevant system settings when necessary.
8. The system validates and saves the changes.
9. The updated configuration is applied to the relevant system functions.
10. Lan signs out.
11. The system ends her authenticated session and prevents further administrator access until she signs in again.

---

# 4. User Stories

| ID | User Story | Priority | Story Points |
|---|---|---|---|
| US01 | As a registered user, I want to log into EduSurvey securely so that I can access the functions available to my role. | P0 | 3 |
| US02 | As a student, I want to view my available course evaluations and their deadlines so that I know which surveys I still need to complete before they close. | P0 | 3 |
| US03 | As a student, I want to complete and submit a course evaluation so that I can provide feedback about the course and lecturer. | P0 | 5 |
| US04 | As a lecturer, I want to review submitted student feedback for my courses so that I can identify common concerns and improve my teaching. | P0 | 5 |
| US05 | As a lecturer, I want student feedback to be grouped by topic so that I can quickly identify recurring areas of concern. | P1 | 5 |
| US06 | As a lecturer, I want the system to highlight the most frequently mentioned issues in student feedback so that I can focus on the areas that need the most attention. | P1 | 5 |
| US07 | As a lecturer, I want to view summary statistics for student evaluations so that I can understand overall course performance without reading every response individually. | P1 | 5 |
| US08 | As an administrator, I want to create a course evaluation with a title, deadline, and questions so that students can provide structured feedback for a course. | P1 | 5 |
| US09 | As an administrator, I want to set and update evaluation deadlines so that students know when each course evaluation is available and when it closes. | P1 | 3 |
| US10 | As a student, I want to receive a reminder before a course evaluation deadline so that I do not forget to complete the survey on time. | P1 | 3 |
| US11 | As an authenticated user, I want to sign out of EduSurvey so that my account and authorized functions are no longer accessible on the current session. | P0 | 2 |
| US12 | As an administrator, I want to manage users, roles, evaluations, and system settings so that I can control how EduSurvey operates. | P1 | 5 |
| US13 | As a lecturer, I want to create a course evaluation with a title, deadline, and questions for my assigned course so that students can provide structured feedback. | P1 | 5 |

---

## US01 - User Login and Authentication

### Acceptance Criteria

- **Given** a registered user enters a valid email address and password, **When** the user submits the login request, **Then** the system authenticates the account and grants access within **3 seconds** under normal operating conditions.

- **Given** a user enters an incorrect email address or password, **When** the user attempts to log in, **Then** the system rejects the request and displays the exact message **"Invalid email or password."**

- **Given** a user successfully logs in, **When** the system identifies the account role, **Then** the user is assigned exactly **1 of 3 supported roles: Student, Lecturer, or Administrator**, and can access only the functions permitted for that role.

---

## US02 - View Available Course Evaluations

### Acceptance Criteria

- **Given** a student has exactly **3 active course evaluations** assigned, **When** the student views the available evaluations, **Then** the system displays exactly **3 active evaluations**.

- **Given** an evaluation is available to the student, **When** its information is displayed, **Then** the system shows exactly **5 details: evaluation title, course name, lecturer name, deadline, and status**.

- **Given** an unfinished evaluation has less than **24 hours** remaining before its deadline, **When** the student views the evaluation list, **Then** the system displays the exact status **"Due Soon"** for that evaluation.

- **Given** the student has already submitted an evaluation, **When** the student views the evaluation list, **Then** that evaluation displays the exact status **"Completed"** and cannot be submitted again.

---

## US03 - Complete and Submit Course Evaluation

### Acceptance Criteria

- **Given** a student selects an active course evaluation, **When** the evaluation is opened, **Then** the system displays all questions assigned to that evaluation, including all required questions.

- **Given** an evaluation contains exactly **5 required questions** and the student has answered all **5**, **When** the student submits the evaluation, **Then** the system stores exactly **1 completed response**, changes the evaluation status to **"Completed"**, and displays the submission confirmation within **3 seconds** under normal operating conditions.

- **Given** an evaluation contains **5 required questions** but the student answers only **4**, **When** the student attempts to submit, **Then** the system rejects the submission and displays the exact message **"Please answer all required questions before submitting."**

- **Given** the student has already submitted the evaluation once, **When** the student attempts to submit the same evaluation again, **Then** the system rejects the second submission and displays the exact message **"You have already completed this evaluation."**

---

## US04 - Review Submitted Student Feedback

### Acceptance Criteria

- **Given** a course evaluation has received student responses, **When** the lecturer reviews the feedback for an assigned course, **Then** the system displays the submitted ratings and comments for that course.

- **Given** a course has received exactly **20 completed evaluations**, **When** the lecturer views the feedback summary, **Then** the system displays the response count as exactly **20**.

- **Given** a lecturer attempts to review feedback for a course they do not teach, **When** the request is made, **Then** the system denies access and displays the exact message **"You do not have permission to view this course feedback."**

- **Given** feedback results are available for an assigned course, **When** the lecturer opens the feedback results, **Then** the system displays the available feedback and response information within **3 seconds** under normal operating conditions.

---

## US05 - Group Student Feedback by Topic

### Acceptance Criteria

- **Given** a course has received written student feedback, **When** the lecturer reviews the feedback analysis, **Then** the system groups related comments into meaningful topics.

- **Given** the feedback contains comments related to exactly **4 topics: course content, teaching delivery, workload, and assessment**, **When** the analysis is generated, **Then** the system displays exactly **4 topic groups**.

- **Given** a feedback comment cannot be confidently assigned to an existing topic, **When** the system processes the comment, **Then** it places the comment in the exact category **"Other"** instead of discarding it.

---

## US06 - Highlight Common Issues

### Acceptance Criteria

- **Given** student feedback has been grouped into topics, **When** the lecturer views the feedback analysis, **Then** the system ranks the topics by how frequently they are mentioned.

- **Given** workload is mentioned in **12 comments**, assessment in **8 comments**, and course content in **5 comments**, **When** the system displays the issue summary, **Then** workload appears as the most frequently mentioned issue with a count of **12**.

- **Given** two topics have the same number of mentions, **When** the system ranks the issues, **Then** both topics display the same frequency count rather than incorrectly assigning one a higher count.

---

## US07 - View Feedback Statistics

### Acceptance Criteria

- **Given** a course evaluation has completed responses, **When** the lecturer views the statistical summary, **Then** the system displays the total number of responses and the average rating for each rating-based question.

- **Given** a rating question receives the values **4, 5, 3, 4, and 4**, **When** the system calculates the average, **Then** it displays the average rating as exactly **4.0 out of 5.0**.

- **Given** a course evaluation has received **0 responses**, **When** the lecturer views the statistical summary, **Then** the system displays the exact message **"No responses available for this evaluation."**

- **Given** statistics are available for an assigned course, **When** the lecturer opens the statistical summary, **Then** the system displays the available statistics within **3 seconds** under normal operating conditions.

---

## US08 - Create Course Evaluation

### Acceptance Criteria

- **Given** an administrator provides a course, evaluation title, deadline, and at least one question, **When** the evaluation is created, **Then** the system saves it and makes it available for the assigned course.

- **Given** an administrator creates an evaluation with exactly **5 questions**, **When** the evaluation is saved successfully, **Then** the system stores and displays exactly **5 questions** for that evaluation.

- **Given** an administrator attempts to create an evaluation without a deadline, **When** the creation request is submitted, **Then** the system rejects the request and displays the exact message **"A deadline is required."**

---

## US09 - Manage Evaluation Deadline

### Acceptance Criteria

- **Given** an administrator sets a valid future deadline for an evaluation, **When** the deadline is saved, **Then** the updated deadline is displayed to students assigned to that evaluation.

- **Given** an evaluation deadline is set to **23:59 on 30 September 2026**, **When** the current time passes **23:59 on 30 September 2026**, **Then** the evaluation status changes to **"Closed"** and students can no longer submit responses.

- **Given** an administrator attempts to set a deadline earlier than the current date and time, **When** the update is submitted, **Then** the system rejects the change and displays the exact message **"Deadline must be in the future."**

---

## US10 - Send Deadline Reminder

### Acceptance Criteria

- **Given** a student has an unfinished evaluation with an upcoming deadline, **When** the deadline is approaching, **Then** the system sends a reminder to the student.

- **Given** an unfinished evaluation has exactly **24 hours** remaining before its deadline, **When** the reminder condition is reached, **Then** the system sends exactly **1 reminder** containing the course name and deadline.

- **Given** a student has already completed an evaluation, **When** the reminder process runs, **Then** the system does not send a reminder for that completed evaluation.

---

## US11 - User Sign Out

### Acceptance Criteria

- **Given** an authenticated user is currently signed in, **When** the user selects the sign-out function, **Then** the system ends the current authenticated session and redirects the user to the login page within **3 seconds** under normal operating conditions.

- **Given** a user has successfully signed out, **When** the user attempts to access an authenticated page using the previous session, **Then** the system denies access and redirects the user to the login page.

- **Given** a user has signed out successfully, **When** the user attempts to access Student, Lecturer, or Administrator functions without signing in again, **Then** the system does not grant access to those functions.

---

## US12 - Administrator System Management

### Acceptance Criteria

- **Given** an authenticated user has the Administrator role, **When** the user opens the administrator management area, **Then** the system grants access to administrator management functions.

- **Given** an authenticated user has the Student or Lecturer role, **When** the user attempts to access the administrator management area, **Then** the system denies access and displays the exact message **"You do not have permission to access this area."**

- **Given** an administrator updates a user's assigned role, **When** the change is saved successfully, **Then** the system stores the new role and applies the corresponding access permissions.

- **Given** an administrator updates a valid system setting, **When** the setting is saved successfully, **Then** the system stores the updated setting and applies it to the relevant system functions.

---

## US13 - Lecturer Creates Course Evaluation

### Acceptance Criteria

- **Given** a lecturer is assigned to a course, **When** the lecturer provides an evaluation title, deadline, and at least one question for that course, **Then** the system saves the evaluation and associates it with the lecturer's assigned course.

- **Given** a lecturer creates an evaluation with exactly **5 questions**, **When** the evaluation is saved successfully, **Then** the system stores and displays exactly **5 questions** for that evaluation.

- **Given** a lecturer attempts to create an evaluation for a course they are not assigned to, **When** the creation request is submitted, **Then** the system rejects the request and displays the exact message **"You do not have permission to create an evaluation for this course."**

- **Given** a lecturer provides a valid evaluation configuration, **When** the lecturer saves the evaluation, **Then** the system confirms the creation within **3 seconds** under normal operating conditions.
---

# 5. Business Rules

## BR1 – One Submission per Evaluation

**Rule:** A student may submit each course evaluation only once. Once the evaluation has been successfully submitted, the system must not allow the same student to submit the same evaluation again.

**Worked Example:** If Minh submits the evaluation for course AI301 at **14:30 on 20 September 2026**, a second submission attempt at **14:35** is rejected and the original submission remains unchanged.

---

## BR2 – Evaluation Deadline Enforcement

**Rule:** Students may submit an evaluation only before its configured deadline. Once the deadline has passed, the evaluation is closed and no new responses may be accepted.

**Worked Example:** If the AI301 evaluation closes at **23:59 on 30 September 2026**, a submission at **23:58** is accepted, while a submission at **00:01 on 1 October 2026** is rejected.

---

## BR3 – Required Questions Must Be Completed

**Rule:** A student must answer all questions marked as required before an evaluation can be submitted.

**Worked Example:** If an evaluation contains **5 required questions** and Minh answers only **4**, the system rejects the submission. After all **5** required questions are answered, the evaluation can be submitted.

---

## BR4 – Role-Based Access Control

**Rule:** Each authenticated account has exactly one system role: **Student, Lecturer, or Administrator**. Users may access only functions permitted for their assigned role.

**Student:**

- View assigned evaluations.
- Complete and submit evaluations.
- Receive reminders.
- Sign out.

**Lecturer:**

- Create evaluations for assigned courses.
- Review feedback for assigned courses.
- View evaluation statistics.
- Sign out.

**Administrator:**

- Create and manage evaluations.
- Manage users and roles.
- Manage evaluation deadlines.
- Manage system settings.
- Sign out.

---

## BR5 – Assigned Course Restriction

**Rule:** A Lecturer may create and manage course evaluations only for courses to which they are assigned. A Lecturer must not be able to create or access evaluation management functions for unrelated courses.

**Worked Example:** If Anh is assigned to AI301 but not AI302, Anh may create an evaluation for AI301 but an attempt to create an evaluation for AI302 is rejected.

---

## BR6 – Rating Scale

**Rule:** All rating-based evaluation questions use a fixed scale from **1 to 5**, where 1 is the lowest rating and 5 is the highest rating.

**Worked Example:** If five students give ratings of **4, 5, 3, 4, and 4**, the system displays an average of **4.0 out of 5.0**.

---

## BR7 – Deadline Reminder Rule

**Rule:** The system sends one reminder for an unfinished evaluation exactly **24 hours before the deadline**. No reminder is sent if the evaluation has already been completed.

---

## BR8 – Interactive Response Time

**Rule:** Key interactive actions that require an immediate response from the system should be completed within **3 seconds under normal operating conditions**.

This applies to key actions such as:

- Sign in.
- Open an assigned evaluation.
- Submit a completed evaluation.
- Save an evaluation configuration.
- View available feedback or statistics.
- Sign out.

Long-running background operations such as scheduled reminders or large-scale feedback analysis may be processed asynchronously.

---

## BR9 – Evaluation Status

**Rule:** Each evaluation has a status based on its lifecycle.

The main statuses are:

- **Draft** – Evaluation is being prepared.
- **Open** – Students can submit responses.
- **Due Soon** – An unfinished evaluation has less than 24 hours remaining.
- **Closed** – The deadline has passed and new submissions are no longer accepted.
- **Completed** – A student has successfully submitted the evaluation.

---

# 6. Screens and Flow

## 6.1 Screens

| Route | Purpose | Access | Priority |
|---|---|---|---|
| `/` | Landing page and user login | G | P0 |
| `/surveys` | View assigned evaluations, deadlines, response status, and evaluation progress | Student | P0 |
| `/surveys/:id` | Complete and submit a selected evaluation | Student | P0 |
| `/lecturer/evaluations` | Create and manage evaluations for assigned courses | Lecturer | P1 |
| `/lecturer/feedback` | View evaluations and response progress for assigned courses | Lecturer | P0 |
| `/lecturer/feedback/:id` | Review grouped feedback, common issues, response rate, and statistics for a course | Lecturer | P1 |
| `/admin/evaluations` | Create and manage course evaluations and deadlines | Administrator | P1 |
| `/admin/users` | Manage user accounts and assigned roles | Administrator | P1 |
| `/admin/settings` | Manage system-level settings and configuration | Administrator | P1 |

### Access Legend

- **G** – Guest
- **Student** – Authenticated Student
- **Lecturer** – Authenticated Lecturer
- **Administrator** – Authenticated Administrator

---

## 6.2 System Flow

The system starts at the login page. After authentication, EduSurvey identifies the user's role and directs the user to the functions permitted for that role.

```text
                              ┌───────────────┐
                              │     Login     │
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │ Authenticate  │
                              │     User      │
                              └───────┬───────┘
                                      │
                 ┌────────────────────┼────────────────────┐
                 │                    │                    │
                 ▼                    ▼                    ▼
          ┌─────────────┐      ┌─────────────┐      ┌───────────────┐
          │   Student   │      │  Lecturer   │      │ Administrator │
          └──────┬──────┘      └──────┬──────┘      └───────┬───────┘
                 │                    │                     │
                 ▼                    ▼                     ▼
       Available Evaluations     My Courses          Administration
                 │                    │                     │
                 ▼              ┌─────┴─────┐        ┌──────┼──────┐
          Select Evaluation      │           │        │      │      │
                 │               ▼           ▼        ▼      ▼      ▼
                 ▼          Create       Review    Users  Evaluations Settings
          Answer Questions  Evaluation   Feedback
                 │               │           │
                 ▼               │           ▼
          Submit Evaluation      │      Statistics
                 │               │           │
                 ▼               │           ▼
            Validation            │      Common Issues
                 │                │
                 ▼                │
            Confirmation          │
                 │                │
                 ▼                │
           Status = Completed ◄──┘

