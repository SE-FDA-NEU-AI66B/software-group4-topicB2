
"use strict";

const form = document.getElementById("login-form");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const loginButton = document.getElementById("login-button");
const togglePassword = document.getElementById("toggle-password");
const formError = document.getElementById("form-error");

// Redirect after successful authentication.
// Final routes must be confirmed with the backend developer.
const roleRoutes = {
    student: "/evaluations",
    lecturer: "/lecturer",
    administrator: "/admin"
};

function setFieldError(field, message) {
    const errorElement = document.getElementById(
        field.id + "-error"
    );

    errorElement.textContent = message;

    field.setAttribute(
        "aria-invalid",
        message ? "true" : "false"
    );
}

function showFormError(message) {
    formError.textContent = message;
    formError.hidden = !message;
}

function validateForm() {
    let valid = true;
    const email = emailInput.value.trim();

    setFieldError(emailInput, "");
    setFieldError(passwordInput, "");
    showFormError("");

    if (!email) {
        setFieldError(
            emailInput,
            "Please enter your email address."
        );
        valid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        setFieldError(
            emailInput,
            "Please enter a valid email address."
        );
        valid = false;
    }

    if (!passwordInput.value) {
        setFieldError(
            passwordInput,
            "Please enter your password."
        );
        valid = false;
    }

    return valid;
}

// Show and hide password.
togglePassword.addEventListener("click", function () {
    const isHidden = passwordInput.type === "password";

    passwordInput.type = isHidden ? "text" : "password";
    togglePassword.textContent = isHidden ? "Hide" : "Show";

    togglePassword.setAttribute(
        "aria-label",
        isHidden ? "Hide password" : "Show password"
    );

    togglePassword.setAttribute(
        "aria-pressed",
        String(isHidden)
    );
});

// Submit credentials to the backend.
form.addEventListener("submit", async function (event) {
    event.preventDefault();

    if (!validateForm()) {
        return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "Signing in...";

    try {
        // Expected API contract for backend issue #16.
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({
                email: emailInput.value.trim(),
                password: passwordInput.value
            })
        });

        let data = {};

        try {
            data = await response.json();
        } catch (_) {
            // Handle non-JSON responses safely.
        }

        if (!response.ok) {
            if (response.status === 401) {
                showFormError("Invalid email or password.");
            } else if (response.status === 404) {
                showFormError(
                    "The login service is currently unavailable. Please try again later."
                );
            } else {
                showFormError(
                    data.error?.message ||
                    "Unable to sign in. Please try again."
                );
            }
            return;
        }

        // Role must come from the authenticated backend response.
        const role = data.user?.role || data.role;
        const destination = roleRoutes[role];

        if (!destination) {
            showFormError(
                "Your account role could not be verified. Contact your administrator."
            );
            return;
        }

        window.location.assign(destination);

    } catch (error) {
        showFormError(
            "Unable to connect to the server. Check your connection and try again."
        );
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = "Sign in";
    }
});
