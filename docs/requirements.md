# EduSurvey Requirements Document

## 1. Product Vision

EduSurvey is an online course evaluation platform for students, lecturers, and university administrators that centralizes the collection, management, and analysis of student feedback, replacing time-consuming paper-based surveys and manual data processing with a more efficient and accessible digital system.

The system provides role-based access for Students, Lecturers, and Administrators. Students can complete course evaluations, Lecturers can review and analyze feedback, and Administrators can create and manage evaluations as well as configure system settings and user access.

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

---

### Persona 3 – Administrator

**Name:** Lan – University Administrator

**Role:** A university administrator responsible for managing EduSurvey evaluations, user access, and system configuration.

**Goal:** Lan wants to manage course evaluations, deadlines, user roles, and system settings from one place so that the evaluation process operates correctly.

**Blocked by:** Without centralized administration functions, it is difficult to control which users can access the system and to keep evaluation configuration consistent.

**In her words:** *"I need to manage evaluations, user access, and important system settings from one place."*

**Technical skill:** Comfortable using university management systems, web applications, and administrative dashboards.

---

# 3. Scenarios

## Scenario 1: User signs in and accesses permitted functions

**Persona:** Minh – Third-year AI student

**Goal:** Sign in securely and access the functions available to his role.

**Steps:**

1. Minh opens EduSurvey.
2. He enters his registered email address and password.
3. The system validates his credentials.
4. The system identifies his assigned role as Student.
5. The system grants access to Student functions.
6. Minh can view and complete his available course evaluations.
7. Minh signs out when he finishes using the system.
8. The system ends his authenticated session and prevents access to authenticated pages until he signs in again.

---

## Scenario 2: Student completes a course evaluation before the deadline

**Persona:** Minh – Third-year AI student

**Goal:** Finish a course evaluation efficiently before the deadline while providing meaningful feedback on his learning experience.

**Steps:**

1. Minh receives a reminder informing him that a course evaluation must be completed within the next 24 hours.
2. He checks the evaluations that are still pending and reviews the deadline for each one.
3. He selects the evaluation for one of the courses he is currently taking.
4. He goes through a set of concise questions covering the course content, teaching quality, and overall learning experience.
5. He gives ratings and writes a brief comment describing what he found useful and what could be improved.
6. Before submitting his responses, he realizes that one required question is still unanswered and provides the missing response.
7. He submits the evaluation and receives a confirmation that his feedback has been successfully recorded.
8. The evaluation is then shown as completed, letting Minh know that no further action is required for that evaluation.

---

## Scenario 3: Lecturer reviews and prioritizes student feedback

**Persona:** Anh – University Lecturer

**Goal:** Identify the key issues raised by students and use summarized feedback to determine areas for course improvement.

**Steps:**

1. After the evaluation period ends, Anh signs in to EduSurvey.
2. He reviews the latest feedback collected for one of his courses.
3. He checks an overview of the feedback, including the number of students who submitted evaluations and the overall rating results.
4. He reviews the feedback that has been automatically organized into common topics, such as course content, teaching delivery, workload, and assessment.
5. He compares how frequently each topic is mentioned to determine which issues are raised most often.
6. He finds that workload is among the most frequently mentioned concerns and examines the related student comments in more detail.
7. He reviews the summary statistics to compare student ratings across different aspects of the course.
8. Based on the feedback, he identifies the main issues that require attention and notes the areas he intends to improve in the next teaching period.
9. He signs out after completing the review.

---

## Scenario 4: Administrator manages evaluations and system access

**Persona:** Lan – University Administrator

**Goal:** Manage course evaluations, users, roles, and system settings.

**Steps:**

1. Lan signs in using her administrator account.
2. The system identifies her role as Administrator.
3. Lan accesses the administrator management area.
4. She creates or edits a course evaluation and configures its deadline and questions.
5. She manages user access and verifies that users have the appropriate system roles.
6. She updates relevant system settings when necessary.
7. The system saves the changes and applies them to the relevant functions.
8. Lan signs out after completing the administration tasks.
9. The system ends her authenticated session and prevents further administrator access until she signs in again.

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

---

## US01 - User Login and Authentication

**Acceptance Criteria**

* **Given** a registered user enters a valid email address and password, **When** the user submits the login request, **Then** the system authenticates the account and grants access within **3 seconds**.

* **Given** a user enters an incorrect email address or password, **When** the user attempts to log in, **Then** the system rejects the request and displays the exact message **"Invalid email or password."**

* **Given** a user successfully logs in, **When** the system identifies the account role, **Then** the user is assigned exactly **1 of 3 supported roles: Student, Lecturer, or Administrator**, and can access only the functions permitted for that role.

---

## US02 - View Available Surveys

**Acceptance Criteria**

* **Given** a student has exactly **3 active course evaluations** assigned, **When** the student views the available surveys, **Then** the system displays exactly **3 active surveys**.

* **Given** a survey is available to the student, **When** its information is displayed, **Then** the system shows exactly **5 details**: survey title, course name, lecturer name, deadline, and status.

* **Given** an unfinished survey has less than **24 hours** remaining before its deadline, **When** the student views the survey list, **Then** the system displays the exact status **"Due soon"** for that survey.

* **Given** the student has already submitted an evaluation, **When** the student views the survey list, **Then** that survey displays the exact status **"Completed"** and cannot be submitted again.

---

## US03 - Complete Course Evaluation

**Acceptance Criteria**

* **Given** a student selects an active course evaluation, **When** the evaluation is opened, **Then** the system displays all questions assigned to that evaluation, including all required questions.

* **Given** an evaluation contains exactly **5 required questions** and the student has answered all **5**, **When** the student submits the evaluation, **Then** the system stores exactly **1 completed response** and changes the survey status to **"Completed"**.

* **Given** an evaluation contains **5 required questions** but the student answers only **4**, **When** the student attempts to submit, **Then** the system rejects the submission and displays the exact message **"Please answer all required questions before submitting."**

* **Given** the student has already submitted the evaluation once, **When** the student attempts to submit the same evaluation again, **Then** the system rejects the second submission and displays the exact message **"You have already completed this evaluation."**

---

## US04 - Review Submitted Feedback

**Acceptance Criteria**

* **Given** a course evaluation has received student responses, **When** the lecturer reviews the feedback, **Then** the system displays the submitted ratings and comments for that course.

* **Given** a course has received exactly **20 completed evaluations**, **When** the lecturer views the feedback summary, **Then** the system displays the response count as exactly **20**.

* **Given** a lecturer attempts to review feedback for a course they do not teach, **When** the request is made, **Then** the system denies access and displays the exact message **"You do not have permission to view this course feedback."**

---

## US05 - Group Feedback by Topic

**Acceptance Criteria**

* **Given** a course has received written student feedback, **When** the lecturer reviews the feedback analysis, **Then** the system groups related comments into meaningful topics.

* **Given** the feedback contains comments related to exactly **4 topics: course content, teaching delivery, workload, and assessment**, **When** the analysis is generated, **Then** the system displays exactly **4 topic groups**.

* **Given** a feedback comment cannot be confidently assigned to an existing topic, **When** the system processes the comment, **Then** it places the comment in the exact category **"Other"** instead of discarding it.

---

## US06 - Highlight Common Issues

**Acceptance Criteria**

* **Given** student feedback has been grouped into topics, **When** the lecturer views the feedback analysis, **Then** the system ranks the topics by how frequently they are mentioned.

* **Given** workload is mentioned in **12 comments**, assessment in **8 comments**, and course content in **5 comments**, **When** the system displays the issue summary, **Then** workload appears as the most frequently mentioned issue with a count of **12**.

* **Given** two topics have the same number of mentions, **When** the system ranks the issues, **Then** both topics display the same frequency count rather than incorrectly assigning one a higher count.

---

## US07 - View Feedback Statistics

**Acceptance Criteria**

* **Given** a course evaluation has completed responses, **When** the lecturer views the statistical summary, **Then** the system displays the total number of responses and the average rating for each rating-based question.

* **Given** a rating question receives the values **4, 5, 3, 4, and 4**, **When** the system calculates the average, **Then** it displays the average rating as exactly **4.0 out of 5.0**.

* **Given** a course evaluation has received **0 responses**, **When** the lecturer views the statistical summary, **Then** the system displays the exact message **"No responses available for this evaluation."**

---

## US08 - Create Course Evaluation

**Acceptance Criteria**

* **Given** an administrator provides a course, evaluation title, deadline, and at least one question, **When** the evaluation is created, **Then** the system saves it and makes it available for the assigned course.

* **Given** an administrator creates an evaluation with exactly **5 questions**, **When** the evaluation is saved successfully, **Then** the system stores and displays exactly **5 questions** for that evaluation.

* **Given** an administrator attempts to create an evaluation without a deadline, **When** the creation request is submitted, **Then** the system rejects the request and displays the exact message **"A deadline is required."**

---

## US09 - Manage Evaluation Deadline

**Acceptance Criteria**

* **Given** an administrator sets a valid future deadline for an evaluation, **When** the deadline is saved, **Then** the updated deadline is displayed to students assigned to that evaluation.

* **Given** an evaluation deadline is set to **23:59 on 30 September 2026**, **When** the current time passes **23:59 on 30 September 2026**, **Then** the evaluation status changes to **"Closed"** and students can no longer submit responses.

* **Given** an administrator attempts to set a deadline earlier than the current date and time, **When** the update is submitted, **Then** the system rejects the change and displays the exact message **"Deadline must be in the future."**

---

## US10 - Send Deadline Reminder

**Acceptance Criteria**

* **Given** a student has an unfinished evaluation with an upcoming deadline, **When** the deadline is approaching, **Then** the system sends a reminder to the student.

* **Given** an unfinished evaluation has exactly **24 hours** remaining before its deadline, **When** the reminder condition is reached, **Then** the system sends exactly **1 reminder** containing the course name and deadline.

* **Given** a student has already completed an evaluation, **When** the reminder process runs, **Then** the system does not send a reminder for that completed evaluation.

---

## US11 - User Sign Out

**Acceptance Criteria**

* **Given** an authenticated user is currently signed in, **When** the user selects the sign-out function, **Then** the system ends the current authenticated session and redirects the user to the login page within **3 seconds**.

* **Given** a user has successfully signed out, **When** the user attempts to access an authenticated page using the previous session, **Then** the system denies access and redirects the user to the login page.

* **Given** a user has signed out successfully, **When** the user attempts to access Student, Lecturer, or Administrator functions without signing in again, **Then** the system does not grant access to those functions.

---

## US12 - Administrator System Management

**Acceptance Criteria**

* **Given** an authenticated user has the Administrator role, **When** the user opens the administrator management area, **Then** the system grants access to administrator management functions.

* **Given** an authenticated user has the Student or Lecturer role, **When** the user attempts to access the administrator management area, **Then** the system denies access and displays the exact message **"You do not have permission to access this area."**

* **Given** an administrator updates a user's assigned role, **When** the change is saved successfully, **Then** the system stores the new role and applies the corresponding access permissions.

* **Given** an administrator updates a valid system setting, **When** the setting is saved successfully, **Then** the system stores the updated setting and applies it to the relevant system functions.

---

# 5. Business Rules

### BR1 – One Submission per Evaluation

**Rule:** A student may submit each course evaluation only once. Once the evaluation has been successfully submitted, the system must not allow the same student to submit the same evaluation again. Any subsequent submission attempt must be rejected, and the original submission must remain unchanged.

**Worked Example:** If Minh submits the evaluation for course AI301 at **14:30 on 20 September 2026**, a second submission attempt for the same evaluation at **14:35** is rejected, and the original submission remains unchanged.

---

### BR2 – Evaluation Deadline Enforcement

**Rule:** Students may submit an evaluation only before its configured deadline. The system must automatically close the evaluation once the deadline has passed, and no new responses may be accepted after the evaluation is closed.

**Worked Example:** If the AI301 evaluation deadline is **23:59 on 30 September 2026**, a submission at **23:58** is accepted, while a submission at **00:01 on 1 October 2026** is rejected because the evaluation is closed.

---

### BR3 – Required Questions Must Be Completed

**Rule:** A student must answer all questions marked as required before an evaluation can be submitted. The system must prevent submission when one or more required questions remain unanswered.

**Worked Example:** If an evaluation contains **5 required questions** and Minh answers only **4**, the submission is rejected. After he answers all **5 questions**, the evaluation can be submitted successfully.

---

### BR4 – Role-Based Access Control

**Rule:** Each authenticated account must have exactly one system role, and users may access only the functions permitted for that role. The system must restrict access to functions that are not available to the user's assigned role.

**Worked Example:** EduSurvey supports **3 roles: Student, Lecturer, and Administrator**. A Student may complete evaluations but cannot create them; a Lecturer may review feedback for their courses but cannot create administrator-managed evaluations; an Administrator may create and manage evaluations and system settings.

---

### BR5 – Rating Scale

**Rule:** All rating-based evaluation questions must use a fixed scale from **1 to 5**, where 1 is the lowest rating and 5 is the highest rating. The system must not accept rating values outside this defined range.

**Worked Example:** If five students give a question the ratings **4, 5, 3, 4, and 4**, the valid average displayed by the system is **4.0 out of 5.0**. A rating of **6** is invalid and must not be accepted.

---

### BR6 – Deadline Reminder Rule

**Rule:** The system sends one deadline reminder for an unfinished evaluation exactly **24 hours before the deadline**. The reminder must be sent only when the evaluation is still unfinished, and no reminder is sent if the evaluation has already been completed.

**Worked Example:** If an evaluation closes at **18:00 on 25 September 2026**, a student who has not completed it receives exactly **1 reminder at 18:00 on 24 September 2026**. A student who submitted the evaluation at **15:00 on 24 September 2026** receives no reminder.

---

### BR7 – Authentication and Session Security

**Rule:** Users must be authenticated before accessing protected Student, Lecturer, or Administrator functions. After a user signs out, the authenticated session must be terminated and protected functions must no longer be accessible until the user signs in again.

**Worked Example:** If Minh signs out at **15:00**, attempting to reopen `/surveys` using the previous authenticated session must be rejected and the system must require Minh to sign in again.

---

### BR8 – Administrator Access

**Rule:** Only users with the Administrator role may access administrator management functions. Students and Lecturers must not be allowed to access system management functions.

**Worked Example:** If a Lecturer attempts to open `/admin/system`, the system denies access. An Administrator can access the page and manage permitted system settings and user roles.

---

# 6. Screens and Flow

| Route | Purpose | Access | Priority |
|---|---|---|---|
| `/` | Landing page and user login | G | P0 |
| `/logout` | Sign out and terminate the current authenticated session | U | P0 |
| `/surveys` | View available course evaluations, deadlines, and completion status | Student | P0 |
| `/surveys/:id` | Complete and submit a selected course evaluation | Student | P0 |
| `/lecturer/feedback` | View courses with collected student feedback | Lecturer | P0 |
| `/lecturer/feedback/:id` | Review grouped feedback, common issues, and summary statistics for a course | Lecturer | P1 |
| `/admin/evaluations` | Create, edit, and manage course evaluations and deadlines | Administrator | P1 |
| `/admin/users` | Manage users and their assigned system roles | Administrator | P1 |
| `/admin/system` | Manage permitted system settings and configuration | Administrator | P1 |

### Access legend

* **G** – Guest
* **Student** – Authenticated user with Student role
* **Lecturer** – Authenticated user with Lecturer role
* **Administrator** – Authenticated user with Administrator role

### System Flow

![EduSurvey System Flow](images/system-flow.png)

The flow begins at the login page. A user enters valid credentials and the system authenticates the account within 3 seconds. The system then identifies the user's assigned role and grants access only to functions permitted for that role.

Students can view and complete evaluations, lecturers can review feedback and statistics for their courses, and administrators can create and manage evaluations, users, roles, and permitted system settings.

When a user signs out, the system terminates the authenticated session and redirects the user to the login page. Protected functions cannot be accessed again until the user signs in successfully.
