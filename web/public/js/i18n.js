/**
 * i18n.js — powered by i18next + i18next-http-backend + i18next-browser-languagedetector
 *
 * วาง locales ไว้ที่:
 *   /locales/en/translation.json
 *   /locales/th/translation.json
 *
 * ใส่ใน HTML ก่อน navbar.js:
 *   <script src="/js/i18n.js"></script>
 */

// โหลด i18next จาก CDN (หรือจะ bundle เองก็ได้)
(function loadI18next() {
  const scripts = [
    'https://unpkg.com/i18next@23.11.5/dist/umd/i18next.min.js',
    'https://unpkg.com/i18next-http-backend@2.5.2/i18nextHttpBackend.min.js',
    'https://unpkg.com/i18next-browser-languagedetector@7.2.1/dist/umd/i18nextBrowserLanguageDetector.min.js',
  ];

  let loaded = 0;

  scripts.forEach(src => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = () => {
      loaded++;
      if (loaded === scripts.length) initI18next();
    };
    document.head.appendChild(s);
  });
})();

function initI18next() {
  i18next
    .use(i18nextHttpBackend)
    .use(i18nextBrowserLanguageDetector)
    .init({
      // ภาษา fallback ถ้า detect ไม่ได้
      fallbackLng: 'en',

      // ภาษาที่รองรับ
      supportedLngs: ['en', 'th'],

      // ดึง JSON จาก server
      backend: {
        loadPath: '/locales/{{lng}}/translation.json',
      },

      // detect จาก localStorage ก่อน แล้ว browser
      detection: {
        order: ['localStorage', 'navigator'],
        lookupLocalStorage: 'resumeai_lang',
        caches: ['localStorage'],
      },

      interpolation: {
        escapeValue: false,
      },
    })
    .then(() => {
      applyTranslations();
      // dispatch event ให้ navbar.js และ scripts อื่นรู้ว่าพร้อมแล้ว
      document.dispatchEvent(new CustomEvent('i18n:ready'));
    });
}

/* ── Apply data-i18n attributes ── */
function applyTranslations() {
  // textContent
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const val = i18next.t(key);
    if (val && val !== key) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = val;
      } else {
        el.textContent = val;
      }
    }
  });

  // placeholder only
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const val = i18next.t(el.getAttribute('data-i18n-ph'));
    if (val) el.placeholder = val;
  });

  // aria-label
  document.querySelectorAll('[data-i18n-aria]').forEach(el => {
    const val = i18next.t(el.getAttribute('data-i18n-aria'));
    if (val) el.setAttribute('aria-label', val);
  });

  // sync <html lang>
  document.documentElement.lang = i18next.language;

  // sync language dropdowns
  document.querySelectorAll('.lang-select').forEach(sel => {
    sel.value = i18next.language.split('-')[0]; // 'th-TH' → 'th'
  });
}

/* ── Public API (ใช้แทน I18n เดิม) ── */
window.I18n = {
  // แปล key → string
  t: (key) => i18next.t(key),

  // เปลี่ยนภาษา + apply ทันที
  setLang: (lang) => {
    i18next.changeLanguage(lang).then(() => {
      applyTranslations();
      document.dispatchEvent(new CustomEvent('langchange', { detail: { lang } }));
    });
  },

  // ภาษาปัจจุบัน
  getLang: () => i18next.language?.split('-')[0] || 'en',

  // apply manually (ใช้หลัง inject navbar)
  applyLang: applyTranslations,
};