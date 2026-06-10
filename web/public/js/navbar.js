/**
 * navbar.js — inject shared navbar into every page
 * Usage:
 *   <div id="navbar-placeholder"></div>
 *   <script src="/js/navbar.js"></script>
 */

(function () {
  const NAVBAR_PATH = '/components/navbar.html';

  const placeholder = document.getElementById('navbar-placeholder');
  if (!placeholder) {
    console.warn('[navbar.js] No #navbar-placeholder found.');
    return;
  }

  fetch(NAVBAR_PATH)
    .then(r => {
      if (!r.ok) throw new Error(`navbar fetch failed: ${r.status}`);
      return r.text();
    })
    .then(html => {
      const tmp = document.createElement('div');
      tmp.innerHTML = html;

      // Insert HTML nodes only — SKIP <script> tags
      // navbar.js owns all event binding via init() below
      // to avoid double-bind and the "closes immediately" bug
      Array.from(tmp.childNodes).forEach(node => {
        if (node.nodeName === 'SCRIPT') return;
        placeholder.before(node.cloneNode(true));
      });

      placeholder.remove();
      init();
      // Apply current language to navbar elements
      if (typeof I18n !== "undefined") I18n.applyLang(I18n.getLang());
    })
    .catch(err => console.error('[navbar.js]', err));

  function init() {
    markActivePage();
    bindUserMenu();
    loadUserInfo();
  }

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

  function bindUserMenu() {
    const userBtn  = document.getElementById('userBtn');
    const userMenu = document.getElementById('userMenu');
    if (!userBtn || !userMenu) return;

    // Toggle dropdown
    userBtn.addEventListener('click', e => {
      e.stopPropagation(); // ← critical: prevents document click from closing immediately
      const isOpen = !userMenu.classList.contains('hidden');
      userMenu.classList.toggle('hidden', isOpen);
      userBtn.setAttribute('aria-expanded', String(!isOpen));
    });

    // Close when clicking anywhere outside
    document.addEventListener('click', e => {
      if (!userBtn.contains(e.target) && !userMenu.contains(e.target)) {
        userMenu.classList.add('hidden');
        userBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on Escape
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        userMenu.classList.add('hidden');
        userBtn.setAttribute('aria-expanded', 'false');
        userBtn.focus();
      }
    });

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', () => {
      localStorage.removeItem('user');
      window.location.href = '/pages/login.html';
    });
  }

  function loadUserInfo() {
    try {
      const u = JSON.parse(localStorage.getItem('user') || '{"name":"Guest"}');
      const nameEl    = document.getElementById('userName');
      const initialEl = document.getElementById('userInitial');
      const btn       = document.getElementById('userBtn');
      if (nameEl)    nameEl.textContent    = u.name || 'Guest';
      if (initialEl) initialEl.textContent = (u.initials || u.name || 'G').charAt(0).toUpperCase();
      if (btn && u.color) btn.style.background = u.color;
    } catch(e) {}
  }

})();