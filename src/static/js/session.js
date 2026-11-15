"use strict";
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-sign-out]").forEach(button => {
        button.addEventListener("click", async () => {
            const status = button.parentElement.querySelector("[data-sign-out-status]");
            button.disabled = true;
            status.textContent = "Signing out…";
            try {
                const response = await fetch("/api/auth/logout", {method: "POST", credentials: "same-origin", headers: {Accept: "application/json"}});
                if (!response.ok) throw new Error("Sign out failed.");
                window.location.replace("/login");
            } catch (_) {
                status.textContent = "Unable to sign out. Check your connection and try again.";
                button.disabled = false;
            }
        });
    });
    // Revalidate a browser-restored page rather than showing stale private content.
    window.addEventListener("pageshow", async event => {
        if (!event.persisted) return;
        document.body.style.visibility = "hidden";
        try {
            const response = await fetch("/api/auth/me", {credentials: "same-origin", cache: "no-store"});
            if (response.status === 401) window.location.replace("/login");
            else window.location.reload();
        } catch (_) { window.location.replace("/login"); }
    });
});
