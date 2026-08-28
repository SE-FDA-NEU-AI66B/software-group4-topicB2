# Section 1 — Chosen Process and Its Position on the Spectrum

## (a) The Model

Our team will use a **Hybrid Agile Process with Plan-driven Milestone Gates** for the Survey & Results Analysis Platform. The development process follows a two-week sprint cycle combined with fixed course milestone checkpoints.

Each cycle starts with sprint planning. **Khuất Đình Trung**, Project Coordinator and Requirements Lead, reviews the backlog, prioritizes requirements, and assigns tasks based on the sprint goal. During the implementation phase, **Dương Đức Anh**, Backend and Database Developer, develops database structures, APIs, server-side functions, authentication, and data processing features. **Lê Sỹ Huy**, Frontend and Testing/Integration Developer, develops the user interface, integrates system components, and performs functional testing. Throughout the sprint, team members coordinate dependencies and resolve technical issues.

Completed features are submitted through Pull Requests and reviewed by another team member before being merged into the main branch. At the end of each sprint, the team demonstrates the completed increment, collects available feedback, updates the backlog, and plans improvements for the next cycle. Each cycle produces a tested working increment together with updated source code, test results, and documented changes.

## (b) Position on the Plan-driven ↔ Agile Spectrum

Our process is positioned **toward the Agile side of the spectrum while maintaining plan-driven milestone gates**. Agile practices are applied through two-week sprints, continuous implementation, testing, code review, demonstrations, and backlog re-prioritization.

However, several decisions remain plan-driven throughout the semester. These include the overall project scope, major system features, high-level architecture, four fixed course milestones, final demo date, and required submission deliverables. These elements are frozen to ensure the project follows academic requirements. In contrast, sprint-level decisions such as UI improvements, visualization methods, validation rules, bug fixes, and feature priorities can be reconsidered after each sprint based on testing results and feedback. This hybrid approach provides flexibility while maintaining control over important deadlines.

# Section 2 — The Five Diagnostic Questions

## 1. Are your requirements stable or volatile?

Our requirements are relatively **volatile** because the Survey & Results Analysis Platform contains multiple interactive features that may require adjustment after development and testing. Features such as the survey creation process, question types, validation rules, data analysis functions, and result visualization may change after usability evaluation. Therefore, a sprint-based process allows the team to adapt requirements without disrupting the entire project plan.

## 2. Does the project carry safety or legal impact?

Our project has **limited safety and legal impact** because it is an academic platform and does not control safety-critical systems or financial/legal operations. Therefore, strict safety documentation and formal change control are not required. However, because the system manages user accounts and survey responses, the team will still apply authentication, authorization, and appropriate data protection practices.

## 3. Is your team large and distributed, or small and co-located?

Our team is **small and co-located, consisting of three members: Khuất Đình Trung, Dương Đức Anh, and Lê Sỹ Huy**. This reduces communication overhead because members can discuss requirements, coordinate implementation, review code, and solve technical problems quickly. A lightweight Agile process is suitable because the team does not require complex communication structures.

## 4. Can your customer engage continuously, or only at fixed checkpoints?

The main customer for this course is the instructor, who provides evaluation mainly through fixed milestones and project reviews. The team can also collect feedback from potential users during testing activities. Therefore, requirements cannot be changed continuously based on customer input, but sprint reviews allow the team to incorporate available feedback into future development cycles.

## 5. What do organizational culture and contract constraints allow?

The course structure creates plan-driven boundaries through **four fixed milestones and a final demo date**. The team must complete required deliverables according to this schedule. Within these constraints, the team is allowed to use Agile sprint cycles for development, testing, review, and improvement. The repository will be made accessible to the instructor before submission according to the course requirements.

# Section 3 — Critical Thinking: Risks of the Opposite Choice

Because our process is Agile-oriented, the opposite choice would be a fully plan-driven process. The biggest risk would be **late discovery of requirement and usability problems**. If the team fixed all requirements, interface designs, and technical decisions at the beginning, problems in features such as survey creation, data visualization, or user interaction might only appear near the final stages. Correcting these problems would require significant rework because backend, frontend, and database components may already depend on the original design. The first symptom would be a sudden increase in change requests and unfinished rework close to milestone deadlines.

# Section 4 — Process Rules Our Team Commits To

1. Every change to the `main` branch must be submitted through a Pull Request and reviewed by at least one other team member before merging.

2. Each sprint lasts two weeks, and the backlog must be reviewed and re-prioritized at the beginning of every sprint.

3. Any requirement change after a sprint starts must be recorded in `docs/changelog.md` with the reason and expected impact.

4. Every completed feature must pass functional testing and integration testing before being merged into the `main` branch.

5. A working software increment must be demonstrated and reviewed at each of the four fixed course milestones.

