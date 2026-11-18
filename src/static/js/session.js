"use strict";
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-sign-out]").forEach(button => {
        button.addEventListener("click", async () => {
            EduNetwork.clear();
            const status = button.parentElement.querySelector("[data-sign-out-status]");
            button.disabled = true;
            status.textContent = "Signing out…";
            try {
                const response = await EduNetwork.fetch("/api/auth/logout", {method: "POST", credentials: "same-origin", headers: {Accept: "application/json"}});
                if (!response.ok) throw new Error("Sign out failed.");
                window.location.replace("/login");
            } catch (error) {
                EduNetwork.report(error, () => button.click(), {write: true});
                status.textContent = "Unable to sign out. Check your connection and try again.";
                button.disabled = false;
            }
        });
    });
    // Revalidate a browser-restored page rather than showing stale private content.
    async function revalidateSession() {
        document.body.style.visibility = "hidden";
        try {
            const response = await EduNetwork.fetch("/api/auth/me", {credentials: "same-origin", cache: "no-store"});
            if (response.status === 401) { window.location.replace("/login"); return; }
            if (!response.ok) throw new Error('Session verification failed.');
            const data = await response.json();
            if (String(data.user?.id) !== EduNetwork.actor.id || data.user?.role !== EduNetwork.actor.role) {
                window.location.reload(); return;
            }
            EduNetwork.clear(); document.body.style.visibility = "";
        } catch (error) {
            if (!EduNetwork.report(error, revalidateSession)) window.location.replace("/login");
        }
    }
    window.addEventListener("pageshow", event => { if (event.persisted) revalidateSession(); });
});
