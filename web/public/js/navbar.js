/**
 * navbar.js — inject shared navbar into every page
 * Usage (add to any page, replace any existing navbar HTML):
 *
 *   <div id="navbar-placeholder"></div>
 *   <script src="/js/navbar.js"></script>
 */

(function () {
  const NAVBAR_PATH = '/components/navbar.html';

  /* ── 1. Find placeholder ── */
  const placeholder = document.getElementById('navbar-placeholder');
  if (!placeholder) {
    console.warn('[navbar.js] No #navbar-placeholder found.');
    return;
  }

  /* ── 2. Fetch & inject ── */
  fetch(NAVBAR_PATH)
    .then(r => {
      if (!r.ok) throw new Error(`navbar fetch failed: ${r.status}`);
      return r.text();
    })
    .then(html => {
      // Parse into temp container
      const tmp = document.createElement('div');
      tmp.innerHTML = html;

      // Insert every child node before the placeholder.
      // <script> tags must be re-created so the browser executes them.
      // <style> tags can be cloned directly.
      Array.from(tmp.childNodes).forEach(node => {
        if (node.nodeName === 'SCRIPT') {
          const s = document.createElement('script');
          if (node.src) s.src = node.src;
          else s.textContent = node.textContent;
          placeholder.before(s);
        } else {
          placeholder.before(node.cloneNode(true));
        }
      });

      // Remove now-empty placeholder
      placeholder.remove();

      // Run our own init after injection
      init();
    })
    .catch(err => console.error('[navbar.js]', err));

  /* ── 3. Init — runs after navbar is in the DOM ── */
  function init() {
    markActivePage();
    bindUserMenu();
    loadUserInfo();
  }

  /* ── 3a. Highlight the current page link ── */
  function markActivePage() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-menu a').forEach(a => {
      a.removeAttribute('aria-current');
      const href = a.getAttribute('href');
      if (!href) return;
      const isHome   = href === '/' && (path === '/' || path === '/index.html');
      const isActive = href !== '/' && path.includes(href);
      if (isHome || isActive) a.setAttribute('aria-current', 'page');
    });
  }

  /* ── 3b. User menu open / close / keyboard ── */
  function bindUserMenu() {
    const userBtn  = document.getElementById('userBtn');
    const userMenu = document.getElementById('userMenu');
    if (!userBtn || !userMenu) return;

    // navbar.html already has its own inline script that binds these,
    // but we guard with a flag so we never double-bind.
    if (userBtn.dataset.navBound) return;
    userBtn.dataset.navBound = '1';

    userBtn.addEventListener('click', e => {
      e.stopPropagation();
      const open = !userMenu.classList.contains('hidden');
      userMenu.classList.toggle('hidden', open);
      userBtn.setAttribute('aria-expanded', String(!open));
    });

    document.addEventListener('click', () => {
      userMenu.classList.add('hidden');
      userBtn.setAttribute('aria-expanded', 'false');
    });

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        userMenu.classList.add('hidden');
        userBtn.setAttribute('aria-expanded', 'false');
        userBtn.focus();
      }
    });

    document.getElementById('logoutBtn')?.addEventListener('click', () => {
      localStorage.removeItem('user');
      window.location.href = '/pages/login.html';
    });
  }

  /* ── 3c. Populate user name & initial from localStorage ── */
  function loadUserInfo() {
    try {
      const u = JSON.parse(localStorage.getItem('user') || '{"name":"Guest"}');
      const nameEl    = document.getElementById('userName');
      const initialEl = document.getElementById('userInitial');
      const userBtn   = document.getElementById('userBtn');
      if (nameEl)    nameEl.textContent    = u.name  || 'Guest';
      if (initialEl) initialEl.textContent = (u.initials || u.name || 'G').charAt(0).toUpperCase();
      if (userBtn && u.color) userBtn.style.background = u.color;
    } catch(e) {}
  }

})();