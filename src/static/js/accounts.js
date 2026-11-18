(() => {
    const $ = selector => document.querySelector(selector);
    let directory = {users: [], memberships: []};
    let confirmation = null;
    function node(tag, text, parent) { const element = document.createElement(tag); element.textContent = text; parent?.append(element); return element; }
    async function api(url, method = 'GET', data) {
        const response = await fetch(url, {method, credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, ...(data ? {body: JSON.stringify(data)} : {})});
        if (response.status === 401) { location.assign('/login'); throw Error('Sign in again.'); }
        let result; try { result = await response.json(); } catch { throw Error('The service returned an unreadable response. Try again.'); }
        if (!response.ok) throw Error(result.error?.message || 'Unable to complete this action.');
        return result;
    }
    function handoff(accounts) {
        $('#handoff-links').replaceChildren(); $('#handoff').hidden = false;
        accounts.forEach(account => {
            const label = node('label', `${account.email || 'Requested account'} · expires ${new Date(account.expires_at).toLocaleString()}`, $('#handoff-links'));
            const input = node('input', '', label); input.readOnly = true; input.value = location.origin + account.setup_path;
            input.addEventListener('focus', () => input.select());
        });
    }
    function render() {
        const query = $('#directory-search').value.toLowerCase().trim();
        const users = directory.users.filter(user => `${user.full_name} ${user.email}`.toLowerCase().includes(query) && ($('#role-filter').value === 'all' || user.role === $('#role-filter').value) && ($('#state-filter').value === 'all' || user.state === $('#state-filter').value));
        $('#directory-count').textContent = `${users.length} of ${directory.users.length} accounts`;
        $('#directory-rows').replaceChildren();
        users.forEach(user => {
            const row = node('tr', '', $('#directory-rows')); const name = node('td', user.full_name, row); node('small', user.email, name); node('td', user.role, row); node('td', user.invitation_status, row);
            const actions = node('td', '', row); const feedback = node('span', '', actions); feedback.setAttribute('role', 'status');
            const state = node('button', user.state === 'disabled' ? 'Reactivate' : 'Disable', actions); state.className = 'secondary'; state.setAttribute('aria-label', `${state.textContent} ${user.email}`);
            state.onclick = async () => {
                if (!confirm(`${state.textContent} access for ${user.email}? Existing feedback will be preserved.`)) return;
                state.disabled = true;
                try { await api(`/api/admin/accounts/${user.id}/state`, 'PATCH', {state: user.state === 'disabled' ? 'active' : 'disabled'}); await load(); }
                catch (error) { $('#account-status').textContent = error.message; feedback.textContent = error.message; state.disabled = false; }
            };
            const invite = node('button', user.state === 'invited' ? 'Reissue invitation' : 'Reset password', actions); invite.className = 'secondary'; invite.disabled = user.state === 'disabled'; invite.setAttribute('aria-label', `${invite.textContent} for ${user.email}`);
            invite.onclick = async () => {
                invite.disabled = true;
                try { const result = await api(`/api/admin/accounts/${user.id}/invitation`, 'POST', {}); handoff([{email: user.email, ...result}]); await load(); $('#account-status').textContent = 'New setup link ready for private handoff. Earlier links are invalid. No email has been sent.'; }
                catch (error) { $('#account-status').textContent = error.message; feedback.textContent = error.message; }
                finally { invite.disabled = user.state === 'disabled'; }
            };
        });
        if (!users.length) { const cell = node('td', 'No matching accounts.', node('tr', '', $('#directory-rows'))); cell.colSpan = 4; }
    }
    function targets() {
        const membership = directory.memberships[Number($('#existing-membership').value)]; $('#membership-target').replaceChildren();
        directory.users.filter(user => membership && user.role === membership.role && user.id !== membership.user_id && user.state !== 'disabled').forEach(user => { const option = node('option', `${user.full_name} · ${user.email}`, $('#membership-target')); option.value = user.id; });
        $('#membership-target').disabled = $('#membership-action').value !== 'transfer';
    }
    async function load() {
        $('#account-status').textContent = 'Loading account directory…';
        document.querySelectorAll('#new-account button,#preview-import,#membership-change button').forEach(button => { button.disabled = true; });
        try {
            directory = await api('/api/admin/accounts'); render(); $('#existing-membership').replaceChildren();
            directory.memberships.forEach((membership, index) => {
                const user = directory.users.find(candidate => candidate.id === membership.user_id);
                const option = node('option', `${user?.full_name || membership.user_id} · ${membership.role} · ${membership.course_name}`, $('#existing-membership')); option.value = index;
            }); targets();
            $('#new-account button').disabled = false; $('#preview-import').disabled = false;
            $('#membership-change button').disabled = !directory.memberships.length;
            $('#account-status').textContent = 'Account directory updated.';
        } catch (error) { $('#account-status').textContent = error.message; }
    }
    $('#new-account').onsubmit = async event => {
        event.preventDefault(); const form = event.currentTarget; const button = form.querySelector('button'); button.disabled = true;
        try { const result = await api('/api/admin/accounts', 'POST', Object.fromEntries(new FormData(form))); handoff([result.account]); form.reset(); await load(); form.querySelector('[role=status]').textContent = 'Account created. Setup link ready for private handoff; no email has been sent.'; }
        catch (error) { form.querySelector('[role=status]').textContent = error.message; }
        finally { button.disabled = false; }
    };
    function invalidatePreview() { confirmation = null; $('#confirm-import').disabled = true; $('#csv-preview').replaceChildren(); $('#import-status').textContent = 'Preview this CSV before confirming.'; }
    $('#csv-source').oninput = invalidatePreview;
    $('#csv-file').onchange = async event => {
        invalidatePreview(); const file = event.target.files[0]; if (!file) return;
        if (file.size > 65536) { $('#import-status').textContent = 'Maximum CSV size is 64 KB.'; return; }
        $('#csv-source').value = await file.text();
    };
    $('#preview-import').onclick = async () => {
        invalidatePreview(); $('#preview-import').disabled = true;
        try { const result = await api('/api/admin/accounts/import-preview', 'POST', {csv: $('#csv-source').value});
            result.rows.forEach(row => { const tr = node('tr', '', $('#csv-preview')); [row.line, row.name, row.email, row.role, row.error || 'Valid'].forEach(value => node('td', value, tr)); });
            confirmation = result.confirmation; $('#confirm-import').disabled = !result.valid; $('#import-status').textContent = result.valid ? 'Preview valid. Confirm within 15 minutes to create these accounts.' : 'Fix validation errors and preview again. No accounts were created.';
        } catch (error) { $('#import-status').textContent = error.message; }
        finally { $('#preview-import').disabled = false; }
    };
    $('#confirm-import').onclick = async () => {
        if (!confirmation) return; $('#confirm-import').disabled = true;
        try { const result = await api('/api/admin/accounts/import-confirm', 'POST', {csv: $('#csv-source').value, confirmation}); handoff(result.accounts); confirmation = null; await load(); $('#import-status').textContent = result.message; }
        catch (error) { $('#import-status').textContent = error.message + ' Preview again before retrying.'; confirmation = null; }
    };
    $('#membership-change').onsubmit = async event => {
        event.preventDefault(); const membership = directory.memberships[Number($('#existing-membership').value)]; if (!membership) return;
        const button = event.currentTarget.querySelector('button'); const status = event.currentTarget.querySelector('[role=status]');
        if (!confirm('Apply this course access change? Responses remain with their original authors.')) return;
        button.disabled = true;
        try { const result = await api('/api/admin/memberships', 'POST', {...membership, action: $('#membership-action').value, target_id: Number($('#membership-target').value)}); await load(); status.textContent = result.message; }
        catch (error) { status.textContent = error.message; }
        finally { button.disabled = false; }
    };
    for (const selector of ['#directory-search', '#role-filter', '#state-filter']) $(selector).addEventListener('input', render);
    for (const selector of ['#existing-membership', '#membership-action']) $(selector).onchange = targets;
    $('#reload-accounts').onclick = load;
    $('#clear-handoff').onclick = () => { $('#handoff-links').replaceChildren(); $('#handoff').hidden = true; };
    load();
})();
