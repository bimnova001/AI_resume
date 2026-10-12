const btn = document.getElementById("analyzeBtn");
const resultDiv = document.getElementById("result");
const langSelect = document.getElementById("langSelect");

const translations = {
    en: {
        title: "AI Resume Analyzer",
        subtitle: "Upload your resume, choose the job type, and receive clear feedback for job fit, strengths, weaknesses, and improvement suggestions.",
        resume: "Resume PDF",
        jobTitle: "Job Title",
        jobTitlePlaceholder: "AI Engineer",
        jobType: "Job Type",
        jobTypePlaceholder: "Select job type (optional)",
        newGrad: "I am a new graduate",
        analyze: "Analyze Resume",
        uploadAlert: "Please upload a resume.",
        error: "Something went wrong while analyzing your resume.",
        noSummary: "No summary available.",
        analyzing: "Analyzing...",
        errorTitle: "Error"
    },
    th: {
        title: "วิเคราะห์เรซูเม่ด้วย AI",
        subtitle: "อัปโหลดเรซูเม่ เลือกประเภทงาน แล้วรับคำแนะนำชัดเจนสำหรับการสมัครงานและจุดปรับปรุง",
        resume: "ไฟล์เรซูเม่ PDF",
        jobTitle: "ชื่อตำแหน่งงาน",
        jobTitlePlaceholder: "AI Engineer",
        jobType: "ประเภทงาน",
        jobTypePlaceholder: "เลือกประเภทงาน (ไม่บังคับ)",
        newGrad: "ฉันเป็นบัณฑิตจบใหม่",
        analyze: "วิเคราะห์เรซูเม่",
        uploadAlert: "กรุณาอัปโหลดเรซูเม่",
        error: "เกิดข้อผิดพลาดขณะวิเคราะห์เรซูเม่ของคุณ",
        noSummary: "ไม่มีสรุปผลให้แสดง",
        analyzing: "กำลังวิเคราะห์...",
        errorTitle: "ข้อผิดพลาด"
    }
};

function translateUI(lang) {
    const t = translations[lang] || translations.en;
    document.querySelector(".hero h1").textContent = t.title;
    document.querySelector(".hero-text").textContent = t.subtitle;
    document.querySelector("label[for='resume']").textContent = t.resume;
    document.querySelector("label[for='jobTitle']").textContent = t.jobTitle;
    document.getElementById("jobTitle").placeholder = t.jobTitlePlaceholder;
    document.querySelector("label[for='jobType']").textContent = t.jobType;
    document.querySelector("#jobType option[value='']").textContent = t.jobTypePlaceholder;
    document.querySelector("label[for='isNewGrad']").textContent = t.newGrad;
    document.getElementById("analyzeBtn").textContent = t.analyze;
}

langSelect.addEventListener("change", () => translateUI(langSelect.value));
translateUI(langSelect.value);

// Shared helpers live in /js/json-util.js (single source of truth).
// Fall back to local copies if the script failed to load.
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

const thaiTranslations = {
    "resume_score": "คะแนนเรซูเม่",
    "match_comment": "ความเหมาะสมกับตำแหน่ง",
    "summary": "สรุป",
    "strengths": "จุดแข็ง",
    "weaknesses": "จุดอ่อน",
    "missing_skills": "ทักษะที่ขาด",
    "recommended_projects": "โครงการที่แนะนำ",
    "recommended_certificates": "ใบรับรองที่แนะนำ",
    "career_paths": "เส้นทางอาชีพ",
    "recommended_actions": "ข้อแนะนำเพิ่มเติม",
};

async function translateText(text, lang) {
    if (lang !== "th" || !text) return text;
    if (typeof text !== "string") return text;

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 40000);
        
        const response = await fetch("/translate", {
            method: "POST",
            body: JSON.stringify({ text }),
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
    if (lang !== "th" || typeof analysis !== "object" || !analysis) return analysis;

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
                // fall through to split
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

    // Translate analysis content based on language selection
    if (lang === "th") {
        console.log("Translating analysis to Thai via LibreTranslate...", analysis);
        analysis = await translateAnalysisObject(analysis, lang);
        console.log("Translated analysis:", analysis);
    }

    const t = translations[lang] || translations.en;
    const heading = lang === "th" ? "ผลการวิเคราะห์" : "Resume Analysis";
    const summaryLabel = lang === "th" ? "สรุป" : "Summary";
    const strengthsLabel = lang === "th" ? "จุดแข็ง" : "Strengths";
    const weaknessesLabel = lang === "th" ? "จุดอ่อน" : "Weaknesses";
    const missingSkillsLabel = lang === "th" ? "ทักษะที่ขาด" : "Missing Skills";
    const projectsLabel = lang === "th" ? "โครงการที่แนะนำ" : "Recommended Projects";
    const certificatesLabel = lang === "th" ? "ใบรับรองที่แนะนำ" : "Recommended Certificates";
    const careersLabel = lang === "th" ? "เส้นทางอาชีพ" : "Career Paths";
    const actionsLabel = lang === "th" ? "ข้อแนะนำเพิ่มเติม" : "Recommended Actions";
    const jobFitLabel = lang === "th" ? "ความเหมาะสม" : "Job Fit";
    const matchLabel = lang === "th" ? "ตรงกับงาน" : "Match %";

    // If analysis couldn't be parsed, still show minimal UI
    const resumeScore = analysis?.resume_score ?? null;
    const matchPct = data.job_match ?? (resumeScore ?? 0);

    // Build main match card with progress bar
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
                    <div style="margin-top:10px;color:#475569">${escapeHtml(jobFitLabel)}: ${escapeHtml(analysis?.match_comment ?? (lang === 'th' ? 'ไม่มีความคิดเห็น' : 'No comment'))}</div>
                </div>
            </div>
            <div class="result-grid" style="margin-top:16px">
                <div class="stat">
                    <h3>${lang === "th" ? "คะแนนเรซูเม่" : "Resume Score"}</h3>
                    <p>${scoreDisplay}</p>
                </div>
                <div class="stat">
                    <h3>${lang === "th" ? "ตำแหน่งที่สมัคร" : "Applied Role"}</h3>
                    <p>${escapeHtml(data.job_title ?? '-')}</p>
                </div>
                <div class="stat">
                    <h3>${lang === "th" ? "เป็นบัณฑิตจบใหม่" : "New Graduate"}</h3>
                    <p>${data.is_new_grad === 'true' || data.is_new_grad === true ? (lang === 'th' ? 'ใช่' : 'Yes') : (lang === 'th' ? 'ไม่' : 'No')}</p>
                </div>
            </div>
        </div>
    `;

    // Summary
    out += `
        <div class="result-section">
            <h3>${escapeHtml(summaryLabel)}</h3>
            <p>${escapeHtml(analysis?.summary ?? t.noSummary)}</p>
        </div>
    `;

    // Lists grid
    out += `<div class="sections-grid">`;
    out += `<div class="result-section list-card"><h3>${strengthsLabel}</h3>${renderList('', analysis?.strengths ?? [])}</div>`;
    out += `<div class="result-section list-card"><h3>${weaknessesLabel}</h3>${renderList('', analysis?.weaknesses ?? [])}</div>`;
    out += `<div class="result-section list-card"><h3>${missingSkillsLabel}</h3>${renderChips(analysis?.missing_skills ?? [])}</div>`;
    out += `</div>`;

    // Recommendations (projects, certificates, careers, actions)
    out += `<div class="sections-grid" style="margin-top:8px">`;
    out += `<div class="result-section list-card"><h3>${projectsLabel}</h3>${renderList('', analysis?.recommended_projects ?? [])}</div>`;
    out += `<div class="result-section list-card"><h3>${certificatesLabel}</h3>${renderList('', analysis?.recommended_certificates ?? [])}</div>`;
    out += `<div class="result-section list-card"><h3>${careersLabel}</h3>${renderList('', analysis?.career_paths ?? [])}</div>`;
    out += `</div>`;

    // Actions
    out += `<div class="result-section" style="margin-top:8px"><h3>${escapeHtml(actionsLabel)}</h3>${renderList('', analysis?.recommended_actions ?? [])}</div>`;

    // AI-picked jobs from the real postings DB (top-3 for this resume)
    out += renderSuggestedJobs(data.suggested_jobs ?? [], lang);

    return out;
}

function renderSuggestedJobs(jobs, lang) {
    const title = lang === "th" ? "งานที่ AI แนะนำสำหรับคุณ" : "Jobs picked for you";
    const sub = lang === "th"
        ? "เลือกจากประกาศงานจริงโดยเทียบเนื้อหาเรซูเม่ของคุณ"
        : "Picked from real postings by matching your resume content";
    if (!Array.isArray(jobs) || jobs.length === 0) {
        return `<div class="result-section" style="margin-top:8px"><h3>${escapeHtml(title)}</h3>` +
            `<p class="muted">${escapeHtml(lang === "th" ? "ยังไม่มีงานที่ตรง — ลองดึงประกาศงานจริงก่อน" : "No matches yet — refresh the real postings first")}</p></div>`;
    }
    const cards = jobs.map(j => {
        const pct = (j.match !== null && j.match !== undefined && j.match !== "") ? Number(j.match).toFixed(1) + "%" : "—";
        const skills = Array.isArray(j.matched_skills) && j.matched_skills.length
            ? `<div class="chip-list" style="margin-top:8px">${j.matched_skills.map(s => `<span class="chip">${escapeHtml(s)}</span>`).join("")}</div>` : "";
        const links = `<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">` +
            `<a href="/pages/job-details.html?id=${encodeURIComponent(j.id)}" class="card-link">View role</a>` +
            (j.url ? `<a href="${escapeHtml(j.url)}" target="_blank" rel="noopener" class="card-link">Apply ↗</a>` : "") + `</div>`;
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
    const lang = langSelect.value || "en";
    const jobTitle = document.getElementById("jobTitle").value;
    const jobType = document.getElementById("jobType").value;
    const isNewGrad = document.getElementById("isNewGrad").checked;

    if (!file) {
        alert(translations[lang].uploadAlert);
        return;
    }

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_title", jobTitle);
    formData.append("job_type", jobType);
    formData.append("is_new_grad", isNewGrad ? "true" : "false");
    formData.append("language", lang);

    console.log("Sending analyze request", {
        job_title: jobTitle,
        job_type: jobType,
        is_new_grad: isNewGrad,
        language: lang,
    });

    resultDiv.innerHTML = `<div class="result-card"><p>${translations[lang].analyzing}</p></div>`;

    try {
        const headers = {};
        try {
            const user = JSON.parse(localStorage.getItem("user") || "{}");
            if (user.token) headers["Authorization"] = `Bearer ${user.token}`;
        } catch (e) { /* anonymous analysis */ }
        const response = await fetch("/analyze", { method: "POST", body: formData, headers });
        const data = await response.json();

        console.group("Resume Analysis Debug");
        console.log("Raw response data:", data);
        console.log("analysis field type:", typeof data.analysis, data.analysis);
        const parsedAnalysis = typeof data.analysis === "object" ? data.analysis : tryParseJson(data.analysis);
        console.log("Parsed analysis:", parsedAnalysis);
        console.groupEnd();

        resultDiv.innerHTML = await renderAnalysis(data, lang);
    } catch (err) {
        console.error(err);
        resultDiv.innerHTML = `<div class="result-card"><h2>${translations[lang].errorTitle}</h2><p>${translations[lang].error}</p></div>`;
    }
}
