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

---

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

