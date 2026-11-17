(() => {
    document.querySelectorAll('time[data-local-date]').forEach(element => {
        const date = new Date(element.dateTime);
        if (!Number.isNaN(date.getTime())) element.textContent = new Intl.DateTimeFormat(undefined, {dateStyle: 'medium', timeStyle: 'short'}).format(date);
    });
    const toggle = document.querySelector('.app-menu');
    const navigation = document.querySelector('.university-nav');
    if (!toggle || !navigation) return;
    const close = () => { navigation.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); };
    toggle.addEventListener('click', () => {
        const open = toggle.getAttribute('aria-expanded') !== 'true';
        navigation.classList.toggle('is-open', open); toggle.setAttribute('aria-expanded', String(open));
        if (open) navigation.querySelector('a').focus();
    });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && navigation.classList.contains('is-open')) { close(); toggle.focus(); } });
    document.addEventListener('click', event => { if (!navigation.contains(event.target) && !toggle.contains(event.target)) close(); });
    navigation.addEventListener('click', event => { if (event.target.closest('a')) close(); });
    matchMedia('(min-width: 801px)').addEventListener('change', close);
})();
