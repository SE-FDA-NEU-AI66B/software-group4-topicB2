const $ = s => document.querySelector(s);
let workspace;
const dateLabel = value => new Intl.DateTimeFormat(undefined, {dateStyle: 'medium', timeStyle: 'short'}).format(new Date(value));
function node(tag, text, parent) { const el = document.createElement(tag); el.textContent = text; parent?.append(el); return el; }
async function api(url, options = {}) {
    const response = await fetch(url, {credentials: 'same-origin', ...options});
    if (response.status === 401) { location.assign('/login'); throw Error('Please sign in again.'); }
    const data = await response.json();
    if (!response.ok) throw Error(data.error?.message || 'Unable to save. Try again.');
    return data;
}
function courses() {
    const list = $('#courses'); list.replaceChildren();
    const query = $('#search').value.toLowerCase();
    const matches = workspace.courses.filter(c => `${c.course_code} ${c.course_name}`.toLowerCase().includes(query));
    matches.forEach(c => { const card = node('article', '', list); card.className = 'card'; node('small', c.course_code, card); node('h3', c.course_name, card); });
    if (!matches.length) node('p', 'No matching courses.', list);
}
function question() {
    const row = node('div', '', $('#questions')); row.className = 'question';
    const label = node('label', 'Question text', row); const input = node('input', '', label); input.required = true; input.maxLength = 1000;
    const typeLabel = node('label', 'Answer type', row); const select = node('select', '', typeLabel);
    for (const [value, text] of [['rating', 'Rating 1–5'], ['text', 'Written feedback']]) { const option = node('option', text, select); option.value = value; }
    const remove = node('button', 'Remove', row); remove.type = 'button'; remove.onclick = () => row.remove();
}
async function load() {
    $('#retry').hidden = true; $('#status').textContent = 'Loading your workspace…';
    try {
        workspace = await api('/api/workspace');
        $('#welcome').textContent = `Welcome, ${workspace.user.full_name}`;
        $('#metrics').replaceChildren();
        for (const [value, label] of [[workspace.courses.length, 'Assigned courses'], [workspace.evaluations.length, 'Visible evaluations']]) {
            const card = node('div', '', $('#metrics')); card.className = 'metric'; node('strong', value, card); node('span', label, card);
        }
        courses();
        if ($('#student-evaluations')) {
            const result = await api('/api/evaluations');
            const list = $('#student-evaluations'); list.replaceChildren();
            result.evaluations.forEach(e => {
                const card = node('article', '', list); card.className = 'card';
                node('small', e.survey_status, card); node('h3', e.course_name, card);
                node('p', e.survey_title, card); node('p', `Deadline: ${dateLabel(e.submission_deadline)}`, card);
                if (['Active', 'Due soon'].includes(e.survey_status)) { const link = node('a', 'Continue evaluation', card); link.href = `/evaluations/${e.id}/complete`; }
            });
            if (!result.count) node('p', 'No evaluations assigned yet.', list);
            const card = node('div', '', $('#metrics')); card.className = 'metric';
            node('strong', result.evaluations.filter(e => e.survey_status === 'Completed').length, card); node('span', 'Completed evaluations', card);
        }
        if ($('#create')) {
            const select = $('#create select[name=course_id]'); select.replaceChildren();
            workspace.courses.forEach(c => { const option = node('option', `${c.course_code} · ${c.course_name}`, select); option.value = c.id; });
            $('#evaluation-list').replaceChildren();
            workspace.evaluations.forEach(e => {
                const card = node('article', '', $('#evaluation-list')); card.className = 'card';
                node('small', `${e.course_name} · ${e.status}`, card); node('h3', e.title, card);
                node('p', `Deadline: ${dateLabel(e.deadline)}`, card);
                const details = node('details', '', card); node('summary', `${e.questions.length} questions`, details);
                const questions = node('ol', '', details); e.questions.forEach(q => node('li', `${q.question_text} · ${q.question_type}${q.is_required ? ' · Required' : ''}`, questions));
                node('p', `${e.response_count} / ${e.enrollment_count} responses`, card);
                const bar = node('progress', '', card); bar.max = Math.max(e.enrollment_count, 1); bar.value = e.response_count; bar.setAttribute('aria-label', 'Response progress');
                const button = node('button', e.status === 'open' ? 'Close evaluation' : 'Open evaluation', card);
                button.onclick = async () => {
                    button.disabled = true;
                    try { await api(`/api/evaluations/${e.id}/status`, {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({status: e.status === 'open' ? 'closed' : 'open'})}); await load(); }
                    catch (error) { $('#status').textContent = error.message; button.disabled = false; }
                };
            });
        }
        if ($('#user-list')) {
            $('#user-list').replaceChildren();
            workspace.users.forEach(u => {
                const row = node('tr', '', $('#user-list')); [u.full_name, u.email].forEach(value => node('td', value, row));
                const cell = node('td', '', row); const select = node('select', '', cell); select.setAttribute('aria-label', `Role for ${u.full_name}`);
                ['student', 'lecturer', 'administrator'].forEach(role => { const option = node('option', role, select); option.value = role; }); select.value = u.role;
                const save = node('button', 'Save role', cell);
                save.onclick = async () => { save.disabled = true; try { await api(`/api/admin/users/${u.id}/role`, {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({role: select.value})}); await load(); } catch (error) { $('#status').textContent = error.message; save.disabled = false; } };
            });
            const accounts = $('#membership-form select[name=user_id]'); accounts.replaceChildren();
            workspace.users.filter(u => u.role !== 'administrator').forEach(u => { const option = node('option', `${u.full_name} · ${u.role}`, accounts); option.value = u.id; });
            const courses = $('#membership-form select[name=course_id]'); courses.replaceChildren();
            workspace.courses.forEach(c => { const option = node('option', `${c.course_code} · ${c.course_name}`, courses); option.value = c.id; });
        }
        $('#status').textContent = 'Workspace updated.';
    } catch (error) { $('#status').textContent = error.message; $('#retry').hidden = false; }
}
$('#search').addEventListener('input', () => workspace && courses());
$('#retry').onclick = load;
if ($('#create')) {
    question(); $('#add').onclick = question;
    $('#create').onsubmit = async event => {
        event.preventDefault(); const form = event.currentTarget; const submit = form.querySelector('[type=submit]'); submit.disabled = true;
        try {
            const deadline = new Date(form.elements.deadline.value);
            if (deadline <= new Date()) throw Error('Deadline must be in the future.');
            const questions = [...document.querySelectorAll('.question')].map(row => ({question_text: row.querySelector('input').value, question_type: row.querySelector('select').value, is_required: true}));
            if (!questions.length) throw Error('At least one question is required.');
            await api('/api/evaluations', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({course_id: Number(form.elements.course_id.value), title: form.elements.title.value, deadline: deadline.toISOString(), questions})});
            $('#form-status').textContent = 'Draft saved. Open it below when ready.'; await load();
        } catch (error) { $('#form-status').textContent = error.message; }
        finally { submit.disabled = false; }
    };
}
load();

for (const [selector, endpoint] of [['#course-form', '/api/admin/courses'], ['#membership-form', '/api/admin/course-memberships']]) {
    const form = $(selector);
    if (form) form.onsubmit = async event => {
        event.preventDefault(); const button = form.querySelector('button'); button.disabled = true;
        const data = Object.fromEntries(new FormData(form));
        if (data.user_id) { data.user_id = Number(data.user_id); data.course_id = Number(data.course_id); }
        try { const result = await api(endpoint, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)}); form.querySelector('[role=status]').textContent = result.message; await load(); }
        catch (error) { form.querySelector('[role=status]').textContent = error.message; }
        finally { button.disabled = false; }
    };
}
