"use strict";
(() => {
    const $ = selector => document.querySelector(selector);
    const role = document.body.dataset.role;
    function node(tag, text, parent) {
        const element = document.createElement(tag);
        element.textContent = text;
        parent.append(element);
        return element;
    }
    async function read(url) {
        const response = await fetch(url, {credentials: 'same-origin', headers: {Accept: 'application/json'}});
        if (response.status === 401) { location.assign('/login'); throw Error('Please sign in again.'); }
        const data = await response.json();
        if (!response.ok) throw Error(data.error?.message || 'Unable to load your account. Please try again.');
        return data;
    }
    async function load() {
        $('#account-retry').hidden = true;
        $('#account-details').hidden = true;
        $('#account-status').textContent = 'Loading your account…';
        $('#account-status').dataset.error = 'false';
        try {
            const [workspace, assigned] = await Promise.all([
                read('/api/workspace'),
                role === 'student' ? read('/api/evaluations') : Promise.resolve(null)
            ]);
            const {user, courses, evaluations} = workspace;
            $('#profile-title').textContent = user.full_name;
            $('#profile-email').textContent = user.email;
            $('#profile-initials').textContent = user.full_name.trim().split(/\s+/).slice(0, 2).map(word => Array.from(word)[0]).join('').toUpperCase();
            const metrics = $('#account-metrics');
            metrics.replaceChildren();
            const metric = (value, label) => { const item = node('div', '', metrics); node('strong', value, item); node('span', label, item); };
            if (role === 'student') {
                const items = assigned.evaluations;
                const completed = items.filter(item => item.survey_status === 'Completed').length;
                const available = items.filter(item => ['Active', 'Due soon'].includes(item.survey_status)).length;
                const closed = items.filter(item => item.survey_status === 'Closed').length;
                metric(items.length, 'Assigned evaluations'); metric(completed, 'Completed'); metric(available, 'Available to complete');
                $('#account-progress').max = Math.max(items.length, 1);
                $('#account-progress').value = completed;
                $('#progress-description').textContent = items.length ? `${completed} of ${items.length} evaluations completed. ${available} available to complete.${closed ? ` ${closed} closed without a submission.` : ''}` : 'No evaluations assigned yet. Check back when your course evaluations open.';
            } else {
                metric(courses.length, role === 'administrator' ? 'University courses' : 'Assigned courses');
                metric(evaluations.length, 'Evaluations');
                metric(evaluations.reduce((total, item) => total + item.response_count, 0), 'Submitted responses');
            }
            $('#account-course-count').textContent = `${courses.length} courses`;
            const list = $('#account-courses'); list.replaceChildren();
            courses.forEach(course => { const item = node('li', '', list); node('small', course.course_code, item); node('strong', course.course_name, item); });
            if (!courses.length) node('li', 'No courses available yet. Contact your administrator if a course is missing.', list);
            $('#account-details').hidden = false;
            $('#account-status').textContent = 'Your account is up to date.';
        } catch (error) {
            $('#account-status').textContent = error instanceof SyntaxError ? 'The service returned an unreadable response. Please try again.' : error.message;
            $('#account-status').dataset.error = 'true';
            $('#account-retry').hidden = false;
        }
    }
    $('#account-retry').addEventListener('click', load);
    load();
})();
