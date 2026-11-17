/* Role-scoped workspace; all writes use the existing authorization APIs. */
const $ = selector => document.querySelector(selector);
let workspace;
let studentEvaluations = [];
const dateLabel = value => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? 'Deadline unavailable' : new Intl.DateTimeFormat(undefined, {dateStyle: 'medium', timeStyle: 'short'}).format(date);
};
function node(tag, text, parent, className) {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    parent?.append(element);
    return element;
}
function notice(element, message, error = false) {
    element.textContent = message;
    element.dataset.error = String(error);
}
async function api(url, options = {}) {
    const response = await fetch(url, {credentials: 'same-origin', ...options});
    if (response.status === 401) { location.assign('/login'); throw Error('Please sign in again.'); }
    let data;
    try { data = await response.json(); }
    catch { throw Error('The service returned an unreadable response. Please try again.'); }
    if (!response.ok) throw Error(data.error?.message || 'Unable to save. Please try again.');
    return data;
}
const write = (url, method, data) => api(url, {method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
function badge(parent, status) {
    const label = node('span', status, parent, 'status-badge'); label.dataset.status = status;
}
function metric(value, label) {
    const card = node('article', '', $('#metrics'), 'metric');
    node('strong', value, card); node('span', label, card);
}
function renderCourses() {
    const list = $('#courses'); list.replaceChildren();
    const query = $('#search').value.trim().toLowerCase();
    const matches = workspace.courses.filter(course => `${course.course_code} ${course.course_name}`.toLowerCase().includes(query));
    $('#course-count').textContent = `${matches.length} of ${workspace.courses.length} courses`;
    matches.forEach(course => {
        const card = node('article', '', list, 'card'); node('small', course.course_code, card); node('h3', course.course_name, card);
        const count = workspace.evaluations.filter(e => e.course_id === course.id).length;
        node('p', `${count} evaluations`, card);
    });
    if (!matches.length) node('p', query ? 'No matching courses. Try another keyword.' : 'No courses assigned yet. Contact your administrator.', list, 'card');
}
function populateSelect(select, records, label) {
    const previous = select.value;
    select.replaceChildren();
    records.forEach(record => { const option = node('option', label(record), select); option.value = record.id; });
    if (records.some(record => String(record.id) === previous)) select.value = previous;
}
function renderEvaluations() {
    const student = Boolean($('#student-evaluations'));
    const list = student ? $('#student-evaluations') : $('#evaluation-list'); list.replaceChildren();
    const filter = $('#evaluation-filter').value;
    const evaluations = student ? studentEvaluations : workspace.evaluations;
    const matches = evaluations.filter(e => filter === 'all' || (student ? e.survey_status : e.status) === filter);
    matches.forEach(evaluation => {
        const card = node('article', '', list, 'card');
        badge(card, student ? evaluation.survey_status : evaluation.status);
        node('h3', student ? evaluation.course_name : evaluation.title, card);
        node('p', student ? evaluation.survey_title : evaluation.course_name, card);
        node('p', `Deadline: ${dateLabel(student ? evaluation.submission_deadline : evaluation.deadline)}`, card);
        if (student) {
            if (['Active', 'Due soon'].includes(evaluation.survey_status)) {
                const link = node('a', 'Continue evaluation →', card); link.href = `/evaluations/${evaluation.id}/complete`;
            }
        } else {
            const details = node('details', '', card); node('summary', `${evaluation.questions.length} questions · Preview`, details);
            const questions = node('ol', '', details);
            evaluation.questions.forEach(question => node('li', `${question.question_text} · ${question.question_type}${question.is_required ? ' · Required' : ' · Optional'}`, questions));
            node('p', `${evaluation.response_count} / ${evaluation.enrollment_count} responses`, card);
            const bar = node('progress', '', card); bar.max = Math.max(evaluation.enrollment_count, 1); bar.value = evaluation.response_count; bar.setAttribute('aria-label', 'Response progress');
            if (workspace.user.role === 'lecturer') { const link = node('a', 'View feedback & statistics →', card); link.href = `/lecturer/feedback/${evaluation.id}`; }
            const button = node('button', evaluation.status === 'open' ? 'Close evaluation' : 'Open evaluation', card, 'secondary');
            button.onclick = async () => {
                button.disabled = true;
                try { await write(`/api/evaluations/${evaluation.id}/status`, 'PATCH', {status: evaluation.status === 'open' ? 'closed' : 'open'}); await load(); }
                catch (error) { notice($('#status'), error.message, true); button.disabled = false; }
            };
        }
    });
    if (!matches.length) node('p', evaluations.length ? 'No evaluations match this status. Choose another filter.' : 'No evaluations yet. Your course evaluations will appear here.', list, 'card');
}
function renderUsers() {
    const list = $('#user-list'); list.replaceChildren();
    const query = $('#account-search').value.trim().toLowerCase();
    const matches = workspace.users.filter(user => `${user.full_name} ${user.email} ${user.role}`.toLowerCase().includes(query));
    matches.forEach(user => {
        const row = node('tr', '', list); node('td', user.full_name, row); node('td', user.email, row);
        const cell = node('td', '', row); const select = node('select', '', cell); select.setAttribute('aria-label', `Role for ${user.full_name}`);
        ['student', 'lecturer', 'administrator'].forEach(role => { const option = node('option', role, select); option.value = role; }); select.value = user.role;
        const save = node('button', 'Save role', cell, 'secondary');
        save.setAttribute('aria-label', `Save role for ${user.full_name}`);
        save.onclick = async () => {
            save.disabled = true;
            try { await write(`/api/admin/users/${user.id}/role`, 'PATCH', {role: select.value}); await load(); notice($('#status'), `Role saved for ${user.full_name}.`); }
            catch (error) { notice($('#status'), error.message, true); save.disabled = false; }
        };
    });
    if (!matches.length) { const cell = node('td', 'No matching accounts.', node('tr', '', list)); cell.colSpan = 3; }
}
function collectQuestions() {
    return [...document.querySelectorAll('.question')].map(row => ({
        question_text: row.querySelector('input[type=text]').value.trim(),
        question_type: row.querySelector('select').value,
        is_required: row.querySelector('input[type=checkbox]').checked
    }));
}
let questionSequence = 0;
function addQuestion() {
    questionSequence += 1;
    const row = node('div', '', $('#questions'), 'question');
    const textLabel = node('label', 'Question text', row); const input = node('input', '', textLabel); input.type = 'text'; input.required = true; input.maxLength = 1000;
    const typeLabel = node('label', 'Answer type', row); const select = node('select', '', typeLabel); select.setAttribute('aria-label', 'Answer type');
    for (const [value, text] of [['rating', 'Rating 1–5'], ['text', 'Written feedback']]) { const option = node('option', text, select); option.value = value; }
    const requiredLabel = node('label', '', row, 'required-control'); const required = node('input', '', requiredLabel); required.type = 'checkbox'; required.checked = true; requiredLabel.append('Required');
    const remove = node('button', 'Remove', row, 'secondary'); remove.type = 'button';
    remove.setAttribute('aria-label', `Remove question ${questionSequence}`);
    remove.onclick = () => { row.remove(); $('#add').focus(); };
}
function preview() {
    const questions = collectQuestions();
    if (!questions.length || questions.some(q => !q.question_text)) { notice($('#form-status'), 'Add question text before previewing.', true); return; }
    const list = $('#preview-questions'); list.replaceChildren();
    questions.forEach((question, index) => {
        const section = node('fieldset', '', list, 'preview-question');
        node('legend', `${index + 1}. ${question.question_text}${question.is_required ? ' (Required)' : ' (Optional)'}`, section);
        if (question.question_type === 'rating') {
            const options = node('div', '', section, 'preview-rating');
            for (let value = 1; value <= 5; value++) { const label = node('label', '', options); const input = node('input', '', label); input.type = 'radio'; input.name = `preview-${index}`; input.value = value; label.append(String(value)); }
            node('p', '1 · Strongly disagree — 5 · Strongly agree', section, 'field-hint');
        } else { const textarea = node('textarea', '', section); textarea.setAttribute('aria-label', question.question_text); textarea.maxLength = 2000; }
    });
    $('#survey-preview').showModal();
}
async function load() {
    $('#retry').hidden = true; notice($('#status'), 'Loading your workspace…'); $('#metrics').setAttribute('aria-busy', 'true');
    try {
        workspace = await api('/api/workspace');
        $('#welcome').textContent = `Welcome, ${workspace.user.full_name}`;
        $('#metrics').replaceChildren(); metric(workspace.courses.length, workspace.user.role === 'administrator' ? 'University courses' : 'Assigned courses');
        renderCourses();
        if ($('#student-evaluations')) {
            studentEvaluations = (await api('/api/evaluations')).evaluations;
            const completed = studentEvaluations.filter(e => e.survey_status === 'Completed').length;
            metric(studentEvaluations.filter(e => ['Active', 'Due soon'].includes(e.survey_status)).length, 'Awaiting your feedback');
            metric(studentEvaluations.filter(e => e.survey_status === 'Due soon').length, 'Due within 24 hours'); metric(completed, 'Completed evaluations');
            const summary = $('#completion-summary'); summary.hidden = false; summary.replaceChildren();
            node('p', `${completed} of ${studentEvaluations.length} evaluations completed`, summary);
            const bar = node('progress', '', summary); bar.max = Math.max(studentEvaluations.length, 1); bar.value = completed; bar.setAttribute('aria-label', 'Evaluation completion');
        } else {
            metric(workspace.evaluations.filter(e => e.status === 'open').length, 'Open evaluations');
            metric(workspace.evaluations.reduce((sum, e) => sum + e.response_count, 0), 'Submitted responses');
            metric(workspace.user.role === 'administrator' ? workspace.users.length : workspace.evaluations.filter(e => e.status === 'draft').length, workspace.user.role === 'administrator' ? 'Registered accounts' : 'Draft evaluations');
            populateSelect($('#create select[name=course_id]'), workspace.courses, c => `${c.course_code} · ${c.course_name}`);
            $('#create button[type=submit]').disabled = !workspace.courses.length;
        }
        renderEvaluations();
        if ($('#user-list')) {
            renderUsers();
            populateSelect($('#membership-form select[name=user_id]'), workspace.users.filter(u => u.role !== 'administrator'), u => `${u.full_name} · ${u.role}`);
            populateSelect($('#membership-form select[name=course_id]'), workspace.courses, c => `${c.course_code} · ${c.course_name}`);
        }
        notice($('#status'), 'Workspace updated.');
    } catch (error) { notice($('#status'), error.message, true); $('#retry').hidden = false; }
    finally { $('#metrics').setAttribute('aria-busy', 'false'); }
}
$('#search').addEventListener('input', () => workspace && renderCourses());
$('#evaluation-filter').addEventListener('change', () => workspace && renderEvaluations());
$('#account-search')?.addEventListener('input', () => workspace && renderUsers());
$('#retry').onclick = load;
if ($('#create')) {
    addQuestion(); $('#add').onclick = addQuestion; $('#preview').onclick = preview;
    $('#close-preview').onclick = () => $('#survey-preview').close();
    $('#create').onsubmit = async event => {
        event.preventDefault(); const form = event.currentTarget; const submit = form.querySelector('[type=submit]'); submit.disabled = true;
        notice($('#form-status'), 'Saving evaluation draft…');
        try {
            const deadline = new Date(form.elements.deadline.value);
            if (Number.isNaN(deadline.getTime()) || deadline <= new Date()) throw Error('Deadline must be in the future.');
            const questions = collectQuestions();
            if (!questions.length) throw Error('At least one question is required.');
            await write('/api/evaluations', 'POST', {course_id: Number(form.elements.course_id.value), title: form.elements.title.value, deadline: deadline.toISOString(), questions});
            notice($('#form-status'), 'Draft saved. Review its questions below, then open it when ready.'); await load();
        } catch (error) { notice($('#form-status'), error.message, true); }
        finally { submit.disabled = false; }
    };
}
for (const [selector, endpoint] of [['#course-form', '/api/admin/courses'], ['#membership-form', '/api/admin/course-memberships']]) {
    const form = $(selector);
    if (form) form.onsubmit = async event => {
        event.preventDefault(); const button = form.querySelector('button'); button.disabled = true;
        const data = Object.fromEntries(new FormData(form));
        if (data.user_id) { data.user_id = Number(data.user_id); data.course_id = Number(data.course_id); }
        try { const result = await write(endpoint, 'POST', data); notice(form.querySelector('[role=status]'), result.message); await load(); }
        catch (error) { notice(form.querySelector('[role=status]'), error.message, true); }
        finally { button.disabled = false; }
    };
}
load();
