# Section 1 — Chosen Process and Its Position on the Spectrum

### (a) The Model

Our team will use an **Agile-centered Hybrid Process with Plan-driven Milestone Gates** for the Survey & Results Analysis Platform. Development is organized into **two-week sprints**. At the beginning of each sprint, **Khuất Đình Trung**, Project Coordinator and Requirements Lead, reviews the backlog, prioritizes requirements, and assigns tasks. **Dương Đức Anh**, Backend and Database Developer, implements the database, APIs, server-side functions, authentication, and data processing. **Lê Sỹ Huy**, Frontend and Testing/Integration Developer, implements the user interface, integration, and functional testing. During the sprint, members develop their assigned features and coordinate dependencies. Completed work is submitted through a Pull Request and reviewed by another member before merging. At sprint end, the team demonstrates the increment, records feedback, and updates the backlog. Each cycle produces a tested working increment.

### (b) Position on the Plan-driven ↔ Agile Spectrum

Our process is positioned **toward the Agile side while retaining plan-driven milestone gates**. Agile activities occur every two weeks through planning, development, testing, review, demonstration, feedback, and re-prioritization. Plan-driven decisions include the main project scope, major features, high-level architecture, four course milestones, final demo date, and required deliverables. These constraints remain fixed, while backlog priorities, UI/UX, form behavior, visualization, bug fixes, and feedback improvements can be re-opened each sprint. This structure provides flexibility while maintaining the academic schedule.

# Section 2 — The Five Diagnostic Questions

### 1. Are your requirements stable or volatile?

Our requirements are **volatile** because needs can change through testing and feedback. The platform includes a dynamic form builder, response collection, statistical analysis, real-time visualization, and role-based functions. For example, question types, validation rules, or result displays may change after testing. Two-week sprints allow these changes to be incorporated into later cycles.

### 2. Does the project carry safety or legal impact?

Our project has **no significant safety or legal impact** because it is an academic survey and data analysis platform and does not control safety-critical systems. Therefore, strict safety-level documentation and change control are unnecessary. Because the system handles accounts and survey responses, the team will implement authentication, authorization, access control, and data protection.

### 3. Is your team large and distributed, or small and co-located?

Our team is **small and co-located, with three members: Khuất Đình Trung, Dương Đức Anh, and Lê Sỹ Huy**. This reduces communication cost and allows members to discuss requirements, coordinate dependencies, review code, and solve problems quickly. This structure supports short Agile cycles without large-team communication overhead.

### 4. Can your customer engage continuously, or only at fixed checkpoints?

The instructor acts as an **active customer and can provide direct weekly feedback**. The team may also collect user feedback during testing. Feedback can be used to refine requirements and re-prioritize the backlog in later sprints. This supports Agile iteration.

### 5. What do organizational and course constraints allow?

The course requires **four fixed milestones and a final demo date**, creating plan-driven structural boundaries. The team must meet these. Within these boundaries, two-week sprints are used to develop, test, review, and improve working increments. The repository will be accessible to the instructor before submission.

# Section 3 — Critical Thinking: Risks of the Opposite Choice

If our team used a **fully plan-driven process**, the biggest risk would be **late discovery of requirement and usability problems**. For example, the team might freeze the survey builder or result visualization early and discover later that users find it difficult to use. Since frontend, backend, database, and testing work may depend on the original design, late changes would cause rework and threaten milestones. The first symptom would be many change requests and rework appearing close to a milestone.

# Section 4 — Process Rules Our Team Commits To

1. Every change to `main` must go through a Pull Request reviewed and approved by at least one other team member.
2. Each sprint lasts two weeks; the backlog must be reviewed and re-prioritized at the start of every sprint.
3. Any requirement change after a sprint starts must be recorded in `docs/changelog.md` with its reason.
4. Every completed feature must pass functional and integration testing before merging into `main`.
5. A working software increment must be demonstrated at each of the four fixed course milestones.



