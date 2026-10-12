/**
 * api.js — single place that decides HOW the browser reaches the backend.
 *
 * - Page served from Node (:3000)  -> relative URLs (Express proxies to FastAPI)
 * - Page served from anywhere else  -> absolute http://localhost:8000 (direct,
 *   overridable with ?api=host:port or localStorage 'api_base')
 *
 * Include before any page script: <script src="/js/api.js"></script>
 * Use: Api.get("/jobs?limit=5"), Api.post("/jobs/refresh", {...})
 */
(function (global) {
  var DEFAULT_BACKEND = "http://localhost:8000";

  function detectBase() {
    try {
      var q = new URLSearchParams(location.search).get("api");
      if (q) return "http://" + q.replace(/^https?:\/\//, "");
      var saved = localStorage.getItem("api_base");
      if (saved) return saved;
    } catch (e) { /* ignore */ }
    if (location.protocol === "file:") return DEFAULT_BACKEND;
    if (location.port && String(location.port) !== "3000") return DEFAULT_BACKEND;
    return ""; // same-origin -> Node proxy
  }

  var BASE = detectBase();

  function url(path) { return BASE + path; }

  async function parseError(res) {
    var body = null;
    try { body = await res.json(); }
    catch (e) {
      try { return { message: await res.text().then(function (t) { return t.slice(0, 200); }) }; }
      catch (e2) { return { message: "HTTP " + res.status }; }
    }
    var err = new Error((body && (body.detail || body.error)) || ("HTTP " + res.status));
    if (body && body.code) err.code = body.code;
    return err;
  }

  async function request(path, options) {
    var res = await fetch(url(path), options);
    if (!res.ok) throw await parseError(res);
    try { return await res.json(); }
    catch (e) { return {}; }
  }

  function get(path) { return request(path); }

  function post(path, body, token) {
    var headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = "Bearer " + token;
    return request(path, {
      method: "POST", headers: headers, body: JSON.stringify(body || {}),
    });
  }

  function authToken() {
    try { return (JSON.parse(localStorage.getItem("user") || "{}") || {}).token || ""; }
    catch (e) { return ""; }
  }

  global.Api = {
    BASE: BASE,
    BACKEND: DEFAULT_BACKEND,
    url: url, get: get, post: post, authToken: authToken,
  };
})(typeof window !== "undefined" ? window : globalThis);
