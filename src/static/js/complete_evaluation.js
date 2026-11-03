
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const $ = (selector) => document.querySelector(selector);

    const evaluationId = document.body.dataset.evaluationId;

    const state = {
        evaluation: null,
        questions: [],
        answers: {},
        submitting: false
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

        const canReview = total > 0 && !state.submitting;

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
                 aria-label="Rating for question ${index + 1}">

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

            $(`#count-${question.id}`).textContent =
                `${textarea.value.length}/2000`;

            clearQuestionError(question.id);

            updateProgress();
        });

        return card;
    }

    function renderQuestions() {
        elements.questionsList.innerHTML = "";

        state.questions.forEach((question, index) => {
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
        if (state.submitting) {
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

    function showError(message) {
        elements.loading.classList.add("hidden");

        elements.error.classList.remove("hidden");

        elements.errorMessage.textContent = message;
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

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data?.error?.message ||
                    "Unable to load this evaluation."
                );
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

            renderQuestions();

        } catch (error) {
            showError(error.message);
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
        if (state.submitting) {
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

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data?.error?.message ||
                    "Your evaluation could not be submitted."
                );
            }

            /*
             * IMPORTANT:
             * The current backend implementation only validates
             * the payload and does not save the answers.
             * Do not display a false submission-success message.
             */

            const message = data.message || "";

            if (
                message.includes("not implemented yet") ||
                message.includes("not implemented")
            ) {
                elements.submitFeedback.textContent =
                    "Your answers passed validation, but submission is not available yet. The backend saving functionality must be completed first.";

                return;
            }

            elements.submitFeedback.textContent =
                "The server accepted your submission request. Please verify the saved submission before leaving this page.";

        } catch (error) {
            elements.submitFeedback.textContent = error.message;

        } finally {
            state.submitting = false;

            elements.confirmSubmit.disabled = false;

            elements.confirmSubmit.textContent =
                "Submit evaluation";

            updateProgress();
        }
    }

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
