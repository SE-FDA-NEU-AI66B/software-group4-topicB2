(() => {
    const $ = selector => document.querySelector(selector);
    const overview = $('#health-overview');
    const refresh = $('#refresh-health');
    let checking = false;
    let timer = null;
    function component(selector, value) {
        const element = $(selector);
        const state = ['ok', 'unavailable'].includes(value) ? value : 'unknown';
        element.dataset.state = state;
        element.textContent = {ok: 'Operational', unavailable: 'Unavailable', unknown: 'Unknown'}[state];
    }
    function summary(state, heading, message) {
        overview.dataset.state = state;
        $('#overview-heading').textContent = heading;
        $('#health-message').textContent = message;
        $('#overview-icon').textContent = {healthy: '✓', unavailable: '!', unknown: '?', checking: '◷'}[state];
    }
    async function check() {
        if (checking) return;
        checking = true; refresh.disabled = true; refresh.textContent = 'Checking…'; overview.setAttribute('aria-busy', 'true');
        summary('checking', 'Checking system health…', 'Waiting for a fresh response from /health.');
        $('#http-status').textContent = '—'; component('#application-status'); component('#database-status');
        $('#checked-at').textContent = 'Waiting for response…'; $('#request-duration').textContent = '—';
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 8000);
        const start = performance.now();
        let received = false;
        try {
            const response = await fetch('/health', {credentials: 'omit', cache: 'no-store', headers: {Accept: 'application/json'}, signal: controller.signal});
            received = true;
            $('#http-status').textContent = response.status === 200 ? '200 OK' : response.status === 503 ? '503 Service Unavailable' : `${response.status} · Unexpected response`;
            $('#checked-at').textContent = new Intl.DateTimeFormat(undefined, {dateStyle: 'medium', timeStyle: 'medium'}).format(new Date());
            const data = await response.json();
            component('#application-status', data?.status); component('#database-status', data?.database);
            if (response.status === 200 && data?.status === 'ok' && data?.database === 'ok') {
                summary('healthy', 'All systems operational', 'The application and database passed the latest readiness check.');
            } else if (response.status === 503) {
                summary('unavailable', 'Service temporarily unavailable', 'The server returned HTTP 503. Check the component statuses below and retry shortly.');
            } else {
                summary('unknown', 'Readiness could not be confirmed', 'The HTTP response or component data did not match the expected readiness contract.');
            }
        } catch (error) {
            component('#application-status'); component('#database-status');
            if (received) {
                summary('unknown', 'Health data could not be verified', 'An HTTP response was received, but its JSON data could not be read. Refresh to retry.');
            } else {
                $('#http-status').textContent = 'No HTTP response'; $('#checked-at').textContent = 'No response received';
                summary('unknown', 'Unable to reach the health endpoint', error.name === 'AbortError' ? 'The check timed out after 8 seconds. Refresh to retry.' : 'Check your connection and refresh to try again. Component statuses are unknown.');
            }
        } finally {
            clearTimeout(timeout);
            $('#request-duration').textContent = `${Math.round(performance.now() - start)} ms`;
            overview.setAttribute('aria-busy', 'false'); refresh.disabled = false; refresh.textContent = 'Refresh status'; checking = false;
        }
    }
    refresh.addEventListener('click', check);
    $('#auto-refresh').addEventListener('change', event => {
        clearInterval(timer); timer = event.target.checked ? setInterval(() => { if (!document.hidden) check(); }, 30000) : null;
    });
    window.addEventListener('pagehide', () => clearInterval(timer));
    check();
})();
