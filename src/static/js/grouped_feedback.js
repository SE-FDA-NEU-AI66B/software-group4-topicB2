"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("topic-analysis");
    if (!root) return;
    const loading = document.getElementById("topic-loading");
    const error = document.getElementById("topic-error");
    const message = document.getElementById("topic-error-message");
    const empty = document.getElementById("topic-empty");
    const groups = document.getElementById("topic-groups");
    const total = document.getElementById("topic-total");
    const retry = document.getElementById("topic-retry");
    const supported = ["Course Content", "Teaching Delivery", "Workload", "Assessment", "Other"];
    let pending = false;

    function make(tag, className, text) {
        const element = document.createElement(tag);
        element.className = className;
        if (text !== undefined) element.textContent = text;
        return element;
    }

    function render(topics) {
        const populated = topics.filter(topic => topic.count > 0)
            .sort((a, b) => b.count - a.count || supported.indexOf(a.topic) - supported.indexOf(b.topic));
        const count = populated.reduce((sum, topic) => sum + topic.count, 0);
        total.textContent = `${count} ${count === 1 ? "comment" : "comments"} · ${populated.length} ${populated.length === 1 ? "topic" : "topics"}`;
        empty.hidden = count !== 0;
        for (const topic of populated) {
            const card = make("details", "topic-card");
            card.dataset.topic = topic.topic;
            const summary = make("summary", "topic-summary");
            const label = make("span", "topic-title", topic.topic);
            const badge = make("span", "topic-count", `${topic.count} ${topic.count === 1 ? "comment" : "comments"}`);
            const share = Math.round(topic.count / count * 100);
            const proportion = make("span", "topic-share", `${share}% of comments · View comments`);
            const track = make("span", "topic-track");
            track.setAttribute("aria-hidden", "true");
            const bar = make("span", "topic-bar");
            bar.style.width = `${share}%`;
            track.append(bar);
            summary.append(label, badge, track, proportion);
            const comments = make("ul", "topic-comments");
            comments.setAttribute("aria-label", `${topic.topic} comments`);
            card.append(summary, comments);
            // Mount comment text only while expanded, keeping long evaluations manageable.
            card.addEventListener("toggle", () => {
                comments.replaceChildren();
                if (card.open) {
                    for (const text of topic.comments) comments.append(make("li", "topic-comment", text));
                }
            });
            groups.append(card);
        }
    }

    async function load() {
        if (pending) return;
        pending = true;
        root.setAttribute("aria-busy", "true");
        retry.disabled = true;
        loading.hidden = false;
        error.hidden = true;
        empty.hidden = true;
        total.textContent = "";
        groups.replaceChildren();
        try {
            const response = await fetch(`/api/evaluations/${encodeURIComponent(root.dataset.evaluationId)}/feedback/topics`, {
                credentials: "same-origin", cache: "no-store", headers: {Accept: "application/json"}
            });
            if (response.status === 401) {
                window.location.replace("/login");
                return;
            }
            const data = await response.json();
            if (!response.ok) {
                throw new Error(`${data?.error?.message || "The analysis service could not load this feedback."} ${data?.error?.action || "Try again or return to your assigned evaluations."}`);
            }
            if (!Array.isArray(data.topics) || data.topics.length !== supported.length ||
                new Set(data.topics.map(topic => topic?.topic)).size !== supported.length ||
                !data.topics.every(topic => supported.includes(topic?.topic) && Number.isInteger(topic.count) && topic.count >= 0 &&
                    Array.isArray(topic.comments) && topic.count === topic.comments.length && topic.comments.every(text => typeof text === "string" && text.trim()))) {
                throw new Error("The service returned incomplete topic data. Try again; contact your administrator if it continues.");
            }
            render(data.topics);
        } catch (failure) {
            message.textContent = failure instanceof TypeError || failure instanceof SyntaxError
                ? "Unable to retrieve grouped feedback. The connection or service response failed. Check your connection and try again."
                : failure.message;
            error.hidden = false;
        } finally {
            pending = false;
            retry.disabled = false;
            loading.hidden = true;
            root.setAttribute("aria-busy", "false");
        }
    }
    retry.addEventListener("click", load);
    load();
});
