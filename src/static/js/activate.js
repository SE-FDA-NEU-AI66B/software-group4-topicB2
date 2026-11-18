(() => {
    const token = new URLSearchParams(location.hash.slice(1)).get('token');
    history.replaceState(null, '', location.pathname);
    const form = document.querySelector('#password-setup');
    const status = document.querySelector('#setup-status');
    const button = form.querySelector('button');
    if (!token || !/^[A-Za-z0-9_-]{40,128}$/.test(token)) {
        status.textContent = 'This setup link is invalid. Contact your administrator.';
        form.hidden = true; return;
    }
    form.onsubmit = async event => {
        event.preventDefault();
        const credential = document.querySelector('#new-password');
        const confirmation = document.querySelector('#confirm-password');
        if (credential.value !== confirmation.value) {
            status.textContent = 'Passwords do not match.'; confirmation.setAttribute('aria-invalid', 'true'); confirmation.focus(); return;
        }
        confirmation.removeAttribute('aria-invalid'); button.disabled = true; status.textContent = 'Setting your password…';
        try {
            const response = await fetch('/api/auth/set-password', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token, password: credential.value})});
            const data = await response.json();
            if (!response.ok) throw Error(data.error?.message || 'Unable to set your password. Try again.');
            form.reset(); form.hidden = true; status.textContent = data.message;
        } catch (error) { status.textContent = error.message; button.disabled = false; }
    };
})();
