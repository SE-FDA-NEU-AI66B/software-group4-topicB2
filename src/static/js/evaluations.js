
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const API_URL = "/api/evaluations";

    const elements = {
        container: document.getElementById("evaluationContainer"),
        loading: document.getElementById("loadingState"),
        error: document.getElementById("errorState"),
        errorMessage: document.getElementById("errorMessage"),
        empty: document.getElementById("emptyState"),
        noResults: document.getElementById("noResultsState"),

        total: document.getElementById("totalCount"),
        active: document.getElementById("activeCount"),
        dueSoon: document.getElementById("dueSoonCount"),
        completed: document.getElementById("completedCount"),
        resultCount: document.getElementById("resultCount"),

        search: document.getElementById("searchInput"),
        filter: document.getElementById("statusFilter"),

        refresh: document.getElementById("refreshButton"),
        retry: document.getElementById("retryButton"),
        clearFilters: document.getElementById("clearFiltersButton"),

        sidebar: document.getElementById("sidebar"),
        menuButton: document.getElementById("mobileMenuButton"),
        overlay: document.getElementById("mobileOverlay")
    };

    let evaluations = [];
    let isLoading = false;

    // ---------------------------------
    // STATE MANAGEMENT
    // ---------------------------------

    function hideAllStates() {
        elements.loading.classList.add("hidden");
        elements.error.classList.add("hidden");
        elements.empty.classList.add("hidden");
        elements.noResults.classList.add("hidden");
    }

    function showLoading() {
        hideAllStates();
        elements.loading.classList.remove("hidden");
        elements.resultCount.textContent = "Loading...";
        elements.container.innerHTML = "";
    }

    function showError(message) {
        hideAllStates();

        elements.errorMessage.textContent = message;
        elements.error.classList.remove("hidden");

        elements.resultCount.textContent = "Unavailable";
        elements.container.innerHTML = "";
    }

    function showEmpty() {
        hideAllStates();
        elements.empty.classList.remove("hidden");
        elements.resultCount.textContent = "0 evaluations";
        elements.container.innerHTML = "";
    }

    function showNoResults() {
        hideAllStates();
        elements.noResults.classList.remove("hidden");
        elements.resultCount.textContent = "0 results";
        elements.container.innerHTML = "";
    }

    // ---------------------------------
    // API
    // ---------------------------------

    async function loadEvaluations() {
        if (isLoading) return;

        isLoading = true;
        showLoading();

        if (elements.refresh) {
            elements.refresh.disabled = true;
        }

        try {
            const response = await fetch(API_URL, {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            });

            const data = await response.json();

            if (!response.ok) {
                const message =
                    data?.error?.message ||
                    "Unable to retrieve your evaluations.";

                if (response.status === 401) {
                    throw new Error(
                        "Your session has expired. Please sign in again."
                    );
                }

                if (response.status === 403) {
                    throw new Error(
                        "You do not have permission to view these evaluations."
                    );
                }

                throw new Error(message);
            }

            if (
                !data ||
                !Array.isArray(data.evaluations)
            ) {
                throw new Error(
                    "The server returned an invalid response."
                );
            }

            evaluations = data.evaluations;

            updateStatistics();

            hideAllStates();

            if (evaluations.length === 0) {
                showEmpty();
            } else {
                renderEvaluations();
            }

        } catch (error) {
            console.error("EduSurvey API error:", error);

            showError(
                error.message ||
                "Something went wrong. Please try again."
            );

        } finally {
            isLoading = false;

            if (elements.refresh) {
                elements.refresh.disabled = false;
            }
        }
    }

    // ---------------------------------
    // STATISTICS
    // ---------------------------------

    function updateStatistics() {
        const counts = {
            Active: 0,
            "Due soon": 0,
            Completed: 0,
            Closed: 0
        };

        evaluations.forEach((item) => {
            if (Object.prototype.hasOwnProperty.call(
                counts,
                item.survey_status
            )) {
                counts[item.survey_status]++;
            }
        });

        elements.total.textContent = evaluations.length;
        elements.active.textContent = counts.Active;
        elements.dueSoon.textContent = counts["Due soon"];
        elements.completed.textContent = counts.Completed;
    }

    // ---------------------------------
    // FORMATTING
    // ---------------------------------

    function formatDeadline(value) {
        if (!value) {
            return "Not specified";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return new Intl.DateTimeFormat("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            hour12: true
        }).format(date);
    }

    function getStatusClass(status) {
        const classes = {
            "Active": "status-active",
            "Due soon": "status-due-soon",
            "Completed": "status-completed",
            "Closed": "status-closed"
        };

        return classes[status] || "status-closed";
    }

    function escapeHTML(value) {
        return String(value ?? "").replace(
            /[&<>"']/g,
            (character) => {
                const entities = {
                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    '"': "&quot;",
                    "'": "&#039;"
                };

                return entities[character];
            }
        );
    }

    // ---------------------------------
    // FILTERING
    // ---------------------------------

    function getFilteredEvaluations() {
        const keyword = elements.search.value
            .trim()
            .toLowerCase();

        const selectedStatus = elements.filter.value;

        return evaluations.filter((item) => {
            const title = String(item.survey_title || "");
            const course = String(item.course_name || "");
            const lecturer = String(item.lecturer_name || "");

            const matchesKeyword = [
                title,
                course,
                lecturer
            ].some((value) =>
                value.toLowerCase().includes(keyword)
            );

            const matchesStatus =
                selectedStatus === "All" ||
                item.survey_status === selectedStatus;

            return matchesKeyword && matchesStatus;
        });
    }

    // ---------------------------------
    // RENDER EVALUATION CARDS
    // ---------------------------------


function createEvaluationCard(item) {
    const status = item.survey_status || "Closed";

    const title = escapeHTML(
        item.survey_title || "Untitled evaluation"
    );

    const course = escapeHTML(
        item.course_name || "Not assigned"
    );

    const lecturer = escapeHTML(
        item.lecturer_name || "Not assigned"
    );

    const deadline = escapeHTML(
        formatDeadline(item.submission_deadline)
    );

    const evaluationId = Number(item.id);

    const canStart =
        Number.isSafeInteger(evaluationId) &&
        evaluationId > 0 &&
        ["Active", "Due soon"].includes(status);

    const card = document.createElement("article");
    card.className = "evaluation-card";

    card.innerHTML = `
        <div class="card-top">
            <h3 class="card-title">${title}</h3>

            <span class="card-status ${getStatusClass(status)}">
                ${escapeHTML(status)}
            </span>
        </div>

        <div class="card-details">

            <div class="detail-item">
                <span class="detail-label">Course name</span>
                <span class="detail-value">${course}</span>
            </div>

            <div class="detail-item">
                <span class="detail-label">Lecturer</span>
                <span class="detail-value">${lecturer}</span>
            </div>

            <div class="detail-item">
                <span class="detail-label">Submission deadline</span>
                <span class="detail-value">${deadline}</span>
            </div>

        </div>

        <div class="card-actions">
            ${
                canStart
                    ? `
                        <a
                            class="button primary start-evaluation-button"
                            href="/evaluations/${evaluationId}/complete"
                            aria-label="Start evaluation: ${title}"
                        >
                            Start Evaluation
                            <span aria-hidden="true">→</span>
                        </a>
                    `
                    : status === "Completed"
                        ? `
                            <span class="evaluation-completed-label">
                                ✓ Evaluation completed
                            </span>
                        `
                        : `
                            <span class="evaluation-unavailable-label">
                                Evaluation unavailable
                            </span>
                        `
            }
        </div>
    `;

    return card;
}


    function renderEvaluations() {
        hideAllStates();

        const filtered = getFilteredEvaluations();

        elements.resultCount.textContent =
            `${filtered.length} of ${evaluations.length} evaluations`;

        elements.container.innerHTML = "";

        if (filtered.length === 0) {
            showNoResults();
            return;
        }

        const list = document.createElement("div");
        list.className = "evaluation-list";

        filtered.forEach((item) => {
            list.appendChild(createEvaluationCard(item));
        });

        elements.container.appendChild(list);
    }

    // ---------------------------------
    // SEARCH AND FILTER EVENTS
    // ---------------------------------

    elements.search.addEventListener("input", () => {
        if (evaluations.length > 0) {
            renderEvaluations();
        }
    });

    elements.filter.addEventListener("change", () => {
        if (evaluations.length > 0) {
            renderEvaluations();
        }
    });

    elements.clearFilters.addEventListener("click", () => {
        elements.search.value = "";
        elements.filter.value = "All";

        renderEvaluations();
    });

    // ---------------------------------
    // REFRESH AND RETRY
    // ---------------------------------

    elements.refresh.addEventListener("click", loadEvaluations);
    elements.retry.addEventListener("click", loadEvaluations);

    // ---------------------------------
    // MOBILE SIDEBAR
    // ---------------------------------

    function openSidebar() {
        elements.sidebar.classList.add("open");
        elements.overlay.classList.add("show");

        elements.menuButton.setAttribute(
            "aria-expanded",
            "true"
        );
    }

    function closeSidebar() {
        elements.sidebar.classList.remove("open");
        elements.overlay.classList.remove("show");

        elements.menuButton.setAttribute(
            "aria-expanded",
            "false"
        );
    }

    elements.menuButton.addEventListener("click", () => {
        if (elements.sidebar.classList.contains("open")) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    elements.overlay.addEventListener("click", closeSidebar);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeSidebar();
        }

        if (
            (event.metaKey || event.ctrlKey) &&
            event.key.toLowerCase() === "k"
        ) {
            event.preventDefault();
            elements.search.focus();
        }
    });

    // Close mobile sidebar when navigating.
    elements.sidebar.querySelectorAll(".nav-link").forEach((link) => {
        link.addEventListener("click", closeSidebar);
    });

    // ---------------------------------
    // INITIALIZE
    // ---------------------------------

    loadEvaluations();
});
