/**
 * json-util.js — shared helpers (single source of truth).
 * Loaded before ResumeReview.js. Falls back gracefully if missing.
 */
(function (global) {
  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function tryParseJson(text) {
    if (!text || typeof text !== "string") return null;
    try {
      return JSON.parse(text.trim());
    } catch (e) {
      var str = text.trim();
      var start = str.indexOf("{");
      if (start === -1) return null;
      var depth = 0;
      var inString = false;
      var escape = false;
      for (var i = start; i < str.length; i++) {
        var ch = str[i];
        if (escape) { escape = false; continue; }
        if (ch === "\\") { escape = true; continue; }
        if (ch === '"') { inString = !inString; continue; }
        if (inString) continue;
        if (ch === "{") {
          depth += 1;
        } else if (ch === "}") {
          depth -= 1;
          if (depth === 0) {
            var candidate = str.slice(start, i + 1)
              .replace(/,\s*}/g, "}")
              .replace(/,\s*]/g, "]");
            try {
              return JSON.parse(candidate);
            } catch (e2) {
              return null;
            }
          }
        }
      }
      return null;
    }
  }

  function normalizeArray(items) {
    if (Array.isArray(items)) {
      return items
        .filter(function (item) { return item !== null && item !== undefined && String(item).trim() !== ""; })
        .map(function (item) { return String(item); });
    }
    if (typeof items === "string") {
      var trimmed = items.trim();
      if (!trimmed) return [];
      if (/^\[.*\]$/.test(trimmed) || /^\{.*\}$/.test(trimmed)) {
        try {
          var parsed = JSON.parse(trimmed);
          return Array.isArray(parsed) ? parsed.map(String) : [String(parsed)];
        } catch (e) { /* fall through to split */ }
      }
      if (trimmed.indexOf("\n") !== -1) {
        return trimmed.split(/\r?\n/).map(function (s) { return s.trim(); }).filter(Boolean);
      }
      if (trimmed.indexOf(",") !== -1) {
        return trimmed.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
      }
      return [trimmed];
    }
    return [];
  }

  global.ResumeUtils = global.ResumeUtils || {};
  global.ResumeUtils.escapeHtml = escapeHtml;
  global.ResumeUtils.tryParseJson = tryParseJson;
  global.ResumeUtils.normalizeArray = normalizeArray;
  // Backwards-compat globals (ResumeReview.js uses these if present)
  global.escapeHtml = global.escapeHtml || escapeHtml;
  global.tryParseJson = global.tryParseJson || tryParseJson;
  global.normalizeArray = global.normalizeArray || normalizeArray;
})(typeof window !== "undefined" ? window : globalThis);
