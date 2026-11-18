/* A transport rejection is different from an HTTP error or invalid JSON. */
(() => {
    const script = document.currentScript;
    class NetworkFailure extends TypeError {
        constructor() { super('Unable to connect to the service. Check your connection and try again.'); this.name = 'NetworkFailure'; }
    }
    let panel;
    let retryAction;
    let currentOptions = {};
    function clear() { if (panel) panel.hidden = true; }
    async function request(...args) {
        try { return await fetch(...args); }
        catch (error) { if (error instanceof TypeError) throw new NetworkFailure(); throw error; }
    }
    function report(error, retry, options = {}) {
        if (!(error instanceof NetworkFailure)) return false;
        if (!panel) {
            panel = document.createElement('section'); panel.className = 'network-state'; panel.setAttribute('role', 'alert'); panel.setAttribute('aria-label', 'Network error');
            // Static, local SVG only. API/error content is never injected as HTML.
            panel.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m3 3 18 18M2 8.5a16 16 0 0 1 3-2M8.5 5.4A16 16 0 0 1 22 8.5M5 12a11 11 0 0 1 3-1.7M12 9.5a11 11 0 0 1 7 2.5M8.5 15.5a5.5 5.5 0 0 1 6.5-.5M12 19h.01" stroke-linecap="round"/></svg><div><strong>No internet connection</strong><p data-network-detail></p></div><button type="button">Try Again</button>';
            panel.querySelector('button').addEventListener('click', async () => {
                const action = retryAction;
                const retryOptions = currentOptions;
                clear();
                try { await action(); }
                catch (failure) {
                    if (!report(failure, action, retryOptions)) {
                        // HTTP/business failures remain in the originating flow.
                        clear();
                    }
                }
            });
        }
        retryAction = retry; currentOptions = options;
        panel.querySelector('[data-network-detail]').textContent = options.write
            ? 'Your input is still here. Check the latest server data before repeating an action; no success was confirmed.'
            : 'Check your connection, then try again. Your unsaved input stays on this page.';
        const host = options.host || document.querySelector('.login-box') || document.querySelector('.content-container') || document.querySelector('main') || document.body;
        host.prepend(panel); panel.hidden = false;
        return true;
    }
    window.EduNetwork = {fetch: request, report, clear, isNetworkError: error => error instanceof NetworkFailure,
        actor: {id: script?.dataset.userId, role: script?.dataset.role}};
})();
