const btn = document.getElementById("analyzeBtn");
const resultDiv = document.getElementById("result");
const langSelect = document.getElementById("langSelect");

// UI strings come from i18next (/locales, 10 languages) via window.T().
// Static labels are handled by data-i18n attributes; dynamic strings below
// use T(key, englishFallback) so the page works even if i18next/CDN fails.
const T = window.T || ((key, fallback) => (fallback !== undefined ? fallback : key));

// Machine-translation target per UI language (googletrans codes).
const MT_DEST = { zh: "zh-cn" };
function mtDest(lang) { return MT_DEST[lang] || lang || "en"; }
function currentLang() { return (langSelect && langSelect.value) || "en"; }

// Shared helpers live in /js/json-util.js; local copies keep the page
// working if that script failed to load.
const escapeHtml = window.escapeHtml || function (value) {
    return String(value == null ? "" : value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
};

const tryParseJson = window.tryParseJson || function (text) {
    if (!text || typeof text !== "string") return null;
    try {
        return JSON.parse(text.trim());
    } catch (e) {
        const str = text.trim();
        const start = str.indexOf("{");
        if (start === -1) return null;
        let depth = 0;
        let inString = false;
        let escape = false;
        for (let i = start; i < str.length; i++) {
            const ch = str[i];
            if (escape) {
                escape = false;
                continue;
            }
            if (ch === "\\") {
                escape = true;
                continue;
            }
            if (ch === '"') {
                inString = !inString;
                continue;
            }
            if (inString) continue;
            if (ch === "{") {
                depth += 1;
            } else if (ch === "}") {
                depth -= 1;
                if (depth === 0) {
                    const candidate = str.slice(start, i + 1)
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
};

async function translateText(text, lang) {
    if (!text || lang === "en") return text;
    if (typeof text !== "string") return text;

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 40000);
        
        const response = await fetch("/translate", {
            method: "POST",
            body: JSON.stringify({ text, target_lang: mtDest(lang) }),
            headers: {
                "Content-Type": "application/json"
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) {
            console.warn("Translation API error, returning original text");
            return text;
        }

        const data = await response.json();
        return data.translatedText || text;
    } catch (err) {
        console.warn("Translation failed:", err, "returning original text");
        return text;
    }
}

async function translateAnalysisObject(analysis, lang) {
    if (lang === "en" || typeof analysis !== "object" || !analysis) return analysis;

    // Batch: fire ALL string translations concurrently (one Promise.all),
    // instead of awaiting key-by-key which serializes latency (N x RTT).
    const tasks = [];
    const translated = Array.isArray(analysis) ? [...analysis] : { ...analysis };
    for (const [key, value] of Object.entries(analysis)) {
        if (typeof value === "string") {
            tasks.push(
                translateText(value, lang).then(t => { translated[key] = t; })
            );
        } else if (Array.isArray(value)) {
            translated[key] = new Array(value.length);
            value.forEach((item, idx) => {
                if (typeof item === "string") {
                    tasks.push(
                        translateText(item, lang).then(t => { translated[key][idx] = t; })
                    );
                } else {
                    translated[key][idx] = item;
                }
            });
        } else {
            translated[key] = value;
        }
    }
    await Promise.all(tasks);
    return translated;
}

const normalizeArray = window.normalizeArray || function (items) {
    if (Array.isArray(items)) return items.filter(item => item !== null && item !== undefined && String(item).trim() !== "");
    if (typeof items === "string") {
        const trimmed = items.trim();
        if (!trimmed) return [];
        if (/^\[.*\]$/.test(trimmed) || /^\{.*\}$/.test(trimmed)) {
            try {
                const parsed = JSON.parse(trimmed);
                return Array.isArray(parsed) ? parsed : [parsed];
            } catch {
                            }
        }
        if (trimmed.includes("\n")) {
            return trimmed.split(/\r?\n/).map(item => item.trim()).filter(item => item);
        }
        if (trimmed.includes(",")) {
            return trimmed.split(",").map(item => item.trim()).filter(item => item);
        }
        return [trimmed];
    }
    return [];
};

function renderList(title, items) {
    const normalized = normalizeArray(items);
    if (normalized.length === 0) return "";
    return `
        <div class="result-section">
            <h3>${escapeHtml(title)}</h3>
            <ul>${normalized.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
    `;
}

function renderChips(items) {
    const normalized = normalizeArray(items);
    if (normalized.length === 0) return "<p class=\"muted\">—</p>";
    return `
        <div class="chip-list">
            ${normalized.map(i => `<span class="chip">${escapeHtml(i)}</span>`).join("")}
        </div>
    `;
}

async function renderAnalysis(data, lang) {
    let analysis = typeof data.analysis === "object"
        ? data.analysis
        : tryParseJson(data.analysis);

    // Translate analysis content to the selected language (en = source).
    if (lang !== "en") {
        analysis = await translateAnalysisObject(analysis, lang);
    }
    const heading = T("resume.heading", "Resume Analysis");
    const summaryLabel = T("resume.summary", "Summary");
    const strengthsLabel = T("resume.strengths", "Strengths");
    const weaknessesLabel = T("resume.weaknesses", "Weaknesses");
    const missingSkillsLabel = T("resume.missingSkills", "Missing Skills");
    const projectsLabel = T("resume.projects", "Recommended Projects");
    const certificatesLabel = T("resume.certificates", "Recommended Certificates");
    const careersLabel = T("resume.careers", "Career Paths");
    const actionsLabel = T("resume.actions", "Recommended Actions");
    const jobFitLabel = T("resume.jobFit", "Job Fit");
    const noSummary = T("resume.noSummary", "No summary available.");
    const noComment = T("resume.noComment", "No comment");
    const yesNo = v => v ? T("resume.yes", "Yes") : T("resume.no", "No");

        const resumeScore = analysis?.resume_score ?? null;
    const matchPct = data.job_match ?? (resumeScore ?? 0);

        const scoreDisplay = (resumeScore !== null && resumeScore !== undefined && resumeScore !== "")
        ? Number(resumeScore).toFixed(2)
        : (matchPct !== null ? Number(matchPct).toFixed(2) : "--");

    const matchPctNumber = Math.min(100, Math.max(0, Number(matchPct) || 0));

    let out = `
        <div class="result-card">
            <h2>${heading}</h2>
            <div class="match-card">
                <div class="match-percentage">${matchPctNumber.toFixed(1)}%</div>
                <div class="match-bar">
                    <div class="progress-outer">
                        <div class="progress-inner" style="width: ${matchPctNumber}%"></div>
                    </div>
                    <div style="margin-top:10px;color:#475569">${escapeHtml(jobFitLabel)}: ${escapeHtml(analysis?.match_comment ?? noComment)}</div>
                </div>
            </div>
            <div class="result-grid" style="margin-top:16px">
                <div class="stat">
                    <h3>${escapeHtml(T("resume.resumeScore", "Resume Score"))}</h3>
                    <p>${scoreDisplay}</p>
                </div>
                <div class="stat">
                    <h3>${escapeHtml(T("resume.appliedRole", "Applied Role"))}</h3>
                    <p>${escapeHtml(data.job_title ?? '-')}</p>
                </div>
                <div class="stat">
                    <h3>${escapeHtml(T("resume.isNewGrad", "New Graduate"))}</h3>
                    <p>${escapeHtml(yesNo(data.is_new_grad === 'true' || data.is_new_grad === true))}</p>
                </div>
            </div>
        </div>
    `;

    // If the AI reply wasn't structured JSON, show the raw text instead of
    // empty cards so nothing silently disappears.
    const rawFallback = (!analysis && typeof data.analysis === "string" && data.analysis.trim())
        ? data.analysis.trim() : null;
    const note = T("resume.rawNote", " (AI reply was not structured JSON — showing raw text, see backend log)");
    out += `
        <div class="result-section">
            <h3>${escapeHtml(summaryLabel)}</h3>
            <p>${escapeHtml(analysis?.summary ?? rawFallback ?? noSummary)}${rawFallback ? `<br><span class="muted">${escapeHtml(note)}</span>` : ""}</p>
        </div>
    `;

        out += `<div class="sections-grid">`;
    out += `<div class="result-section list-card"><h3>${strengthsLabel}</h3>${renderList('', analysis?.strengths ?? [])}</div>`;
    out += `<div class="result-section list-card"><h3>${weaknessesLabel}</h3>${renderList('', analysis?.weaknesses ?? [])}</div>`;
    out += `<div class="result-section list-card"><h3>${missingSkillsLabel}</h3>${renderChips(analysis?.missing_skills ?? [])}</div>`;
    out += `</div>`;

        out += `<div class="sections-grid" style="margin-top:8px">`;
    out += `<div class="result-section list-card"><h3>${projectsLabel}</h3>${renderList('', analysis?.recommended_projects ?? [])}</div>`;
    out += `<div class="result-section list-card"><h3>${certificatesLabel}</h3>${renderList('', analysis?.recommended_certificates ?? [])}</div>`;
    out += `<div class="result-section list-card"><h3>${careersLabel}</h3>${renderList('', analysis?.career_paths ?? [])}</div>`;
    out += `</div>`;

        out += `<div class="result-section" style="margin-top:8px"><h3>${escapeHtml(actionsLabel)}</h3>${renderList('', analysis?.recommended_actions ?? [])}</div>`;

    out += renderSuggestedJobs(data.suggested_jobs ?? [], lang);

    return out;
}

function renderSuggestedJobs(jobs, lang) {
    const title = T("resume.pickedTitle", "Jobs picked for you");
    const sub = T("resume.pickedSub", "Picked from real postings by matching your resume content");
    const viewRole = T("common.viewRole", "View role");
    const applyLbl = T("common.apply", "Apply");
    if (!Array.isArray(jobs) || jobs.length === 0) {
        return `<div class="result-section" style="margin-top:8px"><h3>${escapeHtml(title)}</h3>` +
            `<p class="muted">${escapeHtml(T("resume.pickedEmpty", "No matches yet — refresh the real postings first"))}</p></div>`;
    }
    const cards = jobs.map(j => {
        const pct = (j.match !== null && j.match !== undefined && j.match !== "") ? Number(j.match).toFixed(1) + "%" : "—";
        const skills = Array.isArray(j.matched_skills) && j.matched_skills.length
            ? `<div class="chip-list" style="margin-top:8px">${j.matched_skills.map(s => `<span class="chip">${escapeHtml(s)}</span>`).join("")}</div>` : "";
        const links = `<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">` +
            `<a href="/pages/job-details.html?id=${encodeURIComponent(j.id)}" class="card-link">${escapeHtml(viewRole)}</a>` +
            (j.url ? `<a href="${escapeHtml(j.url)}" target="_blank" rel="noopener" class="card-link">${escapeHtml(applyLbl)} ↗</a>` : "") + `</div>`;
        return `<div class="result-section list-card">` +
            `<h3>${escapeHtml(j.title || "—")} <span class="chip">${escapeHtml(pct)}</span></h3>` +
            `<p class="muted">${escapeHtml([j.company, j.location].filter(Boolean).join(" · "))}</p>` +
            `<p style="margin-top:8px">${escapeHtml(j.reason || "")}</p>${skills}${links}</div>`;
    }).join("");
    return `<div class="result-section" style="margin-top:8px"><h3>${escapeHtml(title)}</h3>` +
        `<p class="muted">${escapeHtml(sub)}</p></div>` +
        `<div class="sections-grid" style="margin-top:8px">${cards}</div>`;
}

btn.addEventListener("click", analyzeResume);

async function analyzeResume() {
    const file = document.getElementById("resume").files[0];
    const lang = currentLang();
    const jobTitle = document.getElementById("jobTitle").value;
    const jobType = document.getElementById("jobType").value;
    const isNewGrad = document.getElementById("isNewGrad").checked;

    if (!file) {
        alert(T("resume.uploadAlert", "Please upload a resume."));
        return;
    }

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_title", jobTitle);
    formData.append("job_type", jobType);
    formData.append("is_new_grad", isNewGrad ? "true" : "false");
    formData.append("language", lang);

    resultDiv.innerHTML = `<div class="result-card"><p>${escapeHtml(T("resume.analyzing", "Analyzing…"))}</p></div>`;

    try {
        const headers = {};
        try {
            const user = JSON.parse(localStorage.getItem("user") || "{}");
            if (user.token) headers["Authorization"] = `Bearer ${user.token}`;
        } catch (e) { /* anonymous analysis */ }
        const response = await fetch("/analyze", { method: "POST", body: formData, headers });
        const data = await response.json();

        resultDiv.innerHTML = await renderAnalysis(data, lang);
    } catch (err) {
        console.error(err);
        resultDiv.innerHTML = `<div class="result-card"><h2>${escapeHtml(T("resume.errorTitle", "Error"))}</h2><p>${escapeHtml(T("resume.error", "Something went wrong while analyzing your resume."))}</p></div>`;
    }
}
