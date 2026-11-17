
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const $ = (selector) => document.querySelector(selector);

    const evaluationId = document.body.dataset.evaluationId;

    const state = {
        evaluation: null,
        questions: [],
        answers: {},
        submitting: false,
        submitted: false
    };

    const elements = {
        title: $("#evaluationTitle"),
        courseMeta: $("#courseMeta"),
        deadline: $("#deadlineText"),

        progressLabel: $("#progressLabel"),
        progressPercent: $("#progressPercent"),
        progressBar: $("#progressBar"),
        sideAnswered: $("#sideAnswered"),
        requiredRemaining: $("#requiredRemaining"),

        loading: $("#loadingState"),
        error: $("#errorState"),
        errorMessage: $("#errorMessage"),

        questionsList: $("#questionsList"),
        validation: $("#validationMessage"),

        reviewButton: $("#reviewButton"),
        reviewButtonMobile: $("#reviewButtonMobile"),

        reviewDialog: $("#reviewDialog"),
        reviewSummary: $("#reviewSummary"),
        closeReview: $("#closeReview"),
        backToEdit: $("#backToEdit"),
        confirmSubmit: $("#confirmSubmit"),
        submitFeedback: $("#submitFeedback")
    };

    const REQUIRED_MESSAGE =
        "Please answer all required questions before submitting.";

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[character]);
    }

    function getAnswer(question) {
        return state.answers[question.id] ?? "";
    }

    function isAnswered(question) {
        return String(getAnswer(question)).trim() !== "";
    }

    function isRequired(question) {
        return Number(question.is_required) === 1;
    }

    function getMissingQuestions() {
        return state.questions.filter(question =>
            isRequired(question) && !isAnswered(question)
        );
    }

    function formatDeadline(value) {
        if (!value) {
            return "Deadline unavailable";
        }

        const date = new Date(
            String(value).replace(" ", "T")
        );

        if (Number.isNaN(date.getTime())) {
            return `Submission deadline: ${value}`;
        }

        return `Submission deadline: ${date.toLocaleString()}`;
    }

    function updateProgress() {
        if (state.submitted) {
            elements.progressLabel.textContent = "Evaluation completed";
            elements.progressPercent.textContent = "100%";
            elements.progressBar.style.width = "100%";
            elements.sideAnswered.textContent = "Saved";
            elements.requiredRemaining.textContent = "0";
            elements.reviewButton.disabled = true;
            elements.reviewButtonMobile.disabled = true;
            return;
        }
        const total = state.questions.length;

        const answered = state.questions.filter(
            isAnswered
        ).length;

        const missing = getMissingQuestions().length;

        const percentage = total
            ? Math.round(answered / total * 100)
            : 0;

        elements.progressLabel.textContent =
            `${answered} of ${total} answered`;

        elements.progressPercent.textContent =
            `${percentage}%`;

        elements.progressBar.style.width =
            `${percentage}%`;

        elements.progressBar.setAttribute(
            "aria-valuenow",
            String(percentage)
        );

        elements.sideAnswered.textContent =
            `${answered} / ${total}`;

        elements.requiredRemaining.textContent =
            String(missing);

        const canReview = total > 0 && !state.submitting && !state.submitted;

        elements.reviewButton.disabled = !canReview;
        elements.reviewButtonMobile.disabled = !canReview;
    }

    function createRatingQuestion(question, index) {
        const card = document.createElement("article");

        card.className = "question-card";
        card.id = `question-${question.id}`;

        const required = isRequired(question);

        const selectedValue = String(getAnswer(question));

        const options = [1, 2, 3, 4, 5].map(number => `
            <div class="rating-option">
                <input
                    type="radio"
                    id="q${question.id}-${number}"
                    name="question-${question.id}"
                    value="${number}"
                    ${selectedValue === String(number) ? "checked" : ""}
                >

                <label for="q${question.id}-${number}">
                    ${number}
                </label>
            </div>
        `).join("");

        card.innerHTML = `
            <div class="question-heading">

                <span class="question-number">
                    ${index + 1}
                </span>

                <div class="question-title">

                    <h3>
                        ${escapeHTML(question.question_text)}
                    </h3>

                    <span class="question-type">
                        Rating question
                    </span>

                    <div>
                        <span class="${required
                            ? "required-badge"
                            : "optional-badge"}">
                            ${required ? "Required *" : "Optional"}
                        </span>
                    </div>

                </div>

            </div>

            <div class="rating-options"
                 role="radiogroup"
                 aria-label="Rating for question ${index + 1}"
                 aria-required="${required}"
                 aria-describedby="error-${question.id}">

                ${options}

            </div>

            <div class="rating-scale">
                <span>1 · Strongly disagree</span>
                <span>5 · Strongly agree</span>
            </div>

            <p class="question-error hidden"
               id="error-${question.id}">
            </p>
        `;

        card.querySelectorAll("input[type=radio]").forEach(input => {
            input.addEventListener("change", () => {
                state.answers[question.id] = Number(input.value);
                draftChanged();

                clearQuestionError(question.id);

                updateProgress();
            });
        });

        return card;
    }

    function createTextQuestion(question, index) {
        const card = document.createElement("article");

        card.className = "question-card";
        card.id = `question-${question.id}`;

        const required = isRequired(question);

        const answer = String(getAnswer(question));

        card.innerHTML = `
            <div class="question-heading">

                <span class="question-number">
                    ${index + 1}
                </span>

                <div class="question-title">

                    <h3>
                        ${escapeHTML(question.question_text)}
                    </h3>

                    <span class="question-type">
                        Written feedback
                    </span>

                    <div>
                        <span class="${required
                            ? "required-badge"
                            : "optional-badge"}">
                            ${required ? "Required *" : "Optional"}
                        </span>
                    </div>

                </div>

            </div>

            <textarea
                class="answer-textarea"
                id="answer-${question.id}"
                maxlength="2000"
                placeholder="Share your feedback..."
                aria-label="${escapeHTML(question.question_text)}"
                aria-required="${required}"
                aria-describedby="error-${question.id}"
            >${escapeHTML(answer)}</textarea>

            <div class="answer-hint">
                <span>Be specific and constructive.</span>

                <span id="count-${question.id}">
                    ${answer.length}/2000
                </span>
            </div>

            <p class="question-error hidden"
               id="error-${question.id}">
            </p>
        `;

        const textarea = card.querySelector("textarea");

        textarea.addEventListener("input", () => {
            state.answers[question.id] = textarea.value;
            draftChanged();

            $(`#count-${question.id}`).textContent =
                `${textarea.value.length}/2000`;

            clearQuestionError(question.id);

            updateProgress();
        });

        return card;
    }

    function renderQuestions() {
        elements.questionsList.innerHTML = "";

        let previousGroup = null;
        const groups = ['Teaching quality', 'Course content', 'Learning materials', 'Assessment', 'Overall satisfaction'];
        state.questions.forEach((question, index) => {
            const prefix = question.question_text.split(':')[0];
            const group = groups.includes(prefix) ? prefix : null;
            if (group && group !== previousGroup) {
                const heading = document.createElement('h3');
                heading.className = 'question-group-heading';
                heading.textContent = group;
                elements.questionsList.appendChild(heading);
            }
            previousGroup = group;
            let card;

            if (question.question_type === "rating") {
                card = createRatingQuestion(question, index);
            } else if (question.question_type === "text") {
                card = createTextQuestion(question, index);
            } else {
                return;
            }

            elements.questionsList.appendChild(card);
        });

        updateProgress();
    }

    function clearQuestionError(questionId) {
        const card = $(`#question-${questionId}`);
        const error = $(`#error-${questionId}`);

        if (card) {
            card.classList.remove("invalid");
            card.querySelectorAll("input, textarea").forEach(control => control.removeAttribute("aria-invalid"));
        }

        if (error) {
            error.classList.add("hidden");
            error.textContent = "";
        }
    }

    function showValidationErrors() {
        const missing = getMissingQuestions();

        if (missing.length === 0) {
            elements.validation.classList.add("hidden");
            return false;
        }

        elements.validation.textContent = REQUIRED_MESSAGE;

        elements.validation.classList.remove("hidden");

        missing.forEach(question => {
            const card = $(`#question-${question.id}`);
            const error = $(`#error-${question.id}`);

            if (card) {
                card.classList.add("invalid");
                card.querySelectorAll("input, textarea").forEach(control => control.setAttribute("aria-invalid", "true"));
            }

            if (error) {
                error.textContent = "This question is required.";
                error.classList.remove("hidden");
            }
        });

        const firstMissing = missing[0];

        $(`#question-${firstMissing.id}`).scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

        $(`#question-${firstMissing.id}`).querySelector("input, textarea")?.focus({preventScroll: true});
        return true;
    }

    function renderReview() {
        elements.reviewSummary.innerHTML = "";

        state.questions.forEach((question, index) => {
            const item = document.createElement("div");

            item.className = "review-item";

            const answer = getAnswer(question);

            const answerText = String(answer).trim()
                ? String(answer)
                : "No answer provided";

            item.innerHTML = `
                <strong>
                    ${index + 1}. ${escapeHTML(question.question_text)}
                    ${isRequired(question) ? "*" : ""}
                </strong>

                <p>${escapeHTML(answerText)}</p>
            `;

            elements.reviewSummary.appendChild(item);
        });
    }

    function openReview() {
        if (state.submitting || state.submitted) {
            return;
        }

        elements.validation.classList.add("hidden");

        if (showValidationErrors()) {
            return;
        }

        renderReview();

        elements.submitFeedback.textContent = "";

        elements.reviewDialog.showModal();
    }

    function completeSubmission(alreadyCompleted = false) {
        state.submitted = true;
        $("#saveDraft").hidden = true;
        $("#draftStatus").hidden = true;
        if (alreadyCompleted) {
            elements.title.textContent = "Completed evaluation";
            elements.courseMeta.textContent = "Your response is already saved.";
            elements.deadline.textContent = "No further submission is needed.";
            document.querySelector("#submissionSuccess h2").textContent = "You have already completed this evaluation.";
        }
        elements.reviewDialog.close();
        elements.loading.classList.add("hidden");
        elements.error.classList.add("hidden");
        elements.questionsList.hidden = true;
        elements.validation.classList.add("hidden");
        const success = document.getElementById("submissionSuccess");
        success.hidden = false;
        success.focus();
        updateProgress();
    }

    function apiError(response, data) {
        if (response.status === 401) {
            window.location.replace("/login");
            return "Your session has expired. Sign in again to continue.";
        }
        const message = data?.error?.code === "DUPLICATE_SUBMISSION"
            ? "You have already completed this evaluation."
            : data?.error?.message || "The request could not be completed.";
        return `${message} ${data?.error?.action || "Return to My Evaluations and refresh the list before trying again."}`;
    }

    function showError(message) {
        elements.loading.classList.add("hidden");

        elements.error.classList.remove("hidden");

        elements.errorMessage.textContent = message;
    }

    function requestErrorMessage(error) {
        return error instanceof TypeError
            ? "Unable to connect to the service. Check your connection and try again."
            : error.message;
    }

    async function readResponse(response) {
        try {
            const data = await response.json();
            if (!data || typeof data !== "object" || Array.isArray(data)) {
                throw new Error("Invalid response object.");
            }
            return data;
        } catch (_) {
            if (response.status === 401) window.location.replace("/login");
            throw new Error("The service returned an unreadable response. Check your connection and try again.");
        }
    }

    async function loadEvaluation() {
        if (!evaluationId || !/^\d+$/.test(evaluationId)) {
            showError("Invalid evaluation ID.");
            return;
        }

        try {
            const response = await fetch(
                `/api/evaluations/${encodeURIComponent(evaluationId)}/questions`,
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json"
                    },
                    cache: "no-store"
                }
            );

            const data = await readResponse(response);

            if (!response.ok) {
                if (data?.error?.code === "DUPLICATE_SUBMISSION") {
                    completeSubmission(true);
                    return;
                }
                throw new Error(apiError(response, data));
            }

            state.evaluation = data.evaluation;

            state.questions = Array.isArray(data.questions)
                ? data.questions.filter(question =>
                    ["rating", "text"].includes(question.question_type)
                )
                : [];

            if (!state.evaluation) {
                throw new Error("Evaluation details are unavailable.");
            }

            elements.title.textContent =
                state.evaluation.title || "Course Evaluation";

            elements.courseMeta.textContent = [
                state.evaluation.course_code,
                state.evaluation.course_name,
                state.evaluation.lecturer_name
            ].filter(Boolean).join(" · ");

            elements.deadline.textContent =
                formatDeadline(state.evaluation.deadline);

            elements.loading.classList.add("hidden");

            if (state.questions.length === 0) {
                throw new Error(
                    "This evaluation does not contain any supported questions yet."
                );
            }

            const draftResponse = await fetch(`/api/evaluations/${evaluationId}/draft`, {credentials: "same-origin"});
            if (draftResponse.ok) {
                const draft = await draftResponse.json();
                state.answers = draft.answers || {};
                if (Object.keys(state.answers).length) {
                    $("#draftStatus").dataset.state = "saved";
                    $("#draftStatus").textContent = "Your saved draft has been restored. Continue where you left off.";
                }
            }
            renderQuestions();

        } catch (error) {
            showError(requestErrorMessage(error));
        }
    }

    function buildSubmissionPayload() {
        const answers = {};

        state.questions.forEach(question => {
            const value = getAnswer(question);

            if (String(value).trim() === "") {
                return;
            }

            answers[question.id] =
                question.question_type === "rating"
                    ? { rating_value: Number(value) }
                    : { text_value: String(value).trim() };
        });

        return {
            evaluation_id: Number(evaluationId),
            answers
        };
    }

    async function submitEvaluation() {
        if (state.submitting || state.submitted) {
            return;
        }

        if (showValidationErrors()) {
            elements.reviewDialog.close();
            return;
        }

        state.submitting = true;

        elements.confirmSubmit.disabled = true;
        elements.confirmSubmit.textContent = "Submitting...";

        elements.submitFeedback.textContent = "";

        updateProgress();

        try {
            const response = await fetch("/api/submissions", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify(buildSubmissionPayload())
            });

            const data = await readResponse(response);

            if (!response.ok) {
                if (data?.error?.code === "DUPLICATE_SUBMISSION") {
                    completeSubmission(true);
                    return;
                }
                throw new Error(apiError(response, data));
            }
            if (response.status !== 201 || data.status !== "submitted") {
                throw new Error("The server did not confirm a saved response. Return to My Evaluations and refresh before retrying.");
            }
            completeSubmission();

        } catch (error) {
            elements.submitFeedback.textContent = `${requestErrorMessage(error)} If the connection failed, refresh My Evaluations to check whether your response was saved before retrying.`;

        } finally {
            state.submitting = false;

            elements.confirmSubmit.disabled = state.submitted;

            elements.confirmSubmit.textContent =
                "Submit evaluation";

            updateProgress();
        }
    }

    function draftChanged() {
        $("#draftStatus").dataset.state = "dirty";
        $("#draftStatus").textContent = "Unsaved changes. Save your draft before leaving this page.";
    }

    $("#saveDraft").addEventListener("click", async () => {
        const button = $("#saveDraft"); button.disabled = true;
        $("#draftStatus").textContent = "Saving your draft…";
        try {
            const response = await fetch(`/api/evaluations/${evaluationId}/draft`, {
                method: "PUT", credentials: "same-origin", headers: {"Content-Type": "application/json"},
                body: JSON.stringify({answers: buildSubmissionPayload().answers})
            });
            const data = await readResponse(response);
            if (!response.ok) throw new Error(apiError(response, data));
            $("#draftStatus").dataset.state = "saved";
            $("#draftStatus").textContent = data.message;
        } catch (error) { $("#draftStatus").dataset.state = "error"; $("#draftStatus").textContent = requestErrorMessage(error); }
        finally { button.disabled = false; }
    });

    // Event listeners

    elements.reviewButton.addEventListener(
        "click",
        openReview
    );

    elements.reviewButtonMobile.addEventListener(
        "click",
        openReview
    );

    elements.closeReview.addEventListener(
        "click",
        () => elements.reviewDialog.close()
    );

    elements.backToEdit.addEventListener(
        "click",
        () => elements.reviewDialog.close()
    );

    elements.confirmSubmit.addEventListener(
        "click",
        submitEvaluation
    );

    // Initialize page

    loadEvaluation();
});
