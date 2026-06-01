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

function tryParseJson(text) {
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
}

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

function translateText(text, lang) {
    if (lang !== "th" || !text) return text;
    if (typeof text !== "string") return text;

    let result = text;

    // Comprehensive Thai translation for common resume terms and phrases
    const translations = {
        "resume": "เรซูเม่",
        "relevant": "ที่เกี่ยวข้อง",
        "job position": "ตำแหน่งงาน",
        "strong background": "พื้นฐานที่แข็งแกร่ง",
        "lacks": "ขาด",
        "experience": "ประสบการณ์",
        "projects": "โครงการ",
        "certificates": "ใบรับรอง",
        "graduate": "บัณฑิต",
        "recent graduate": "บัณฑิตจบใหม่",
        "skills": "ทักษะ",
        "programming languages": "ภาษาโปรแกรมมิ่ง",
        "operating systems": "ระบบปฏิบัติการ",
        "software": "ซอฟต์แวร์",
        "development": "การพัฒนา",
        "web development": "พัฒนาเว็บ",
        "teaching": "การสอน",
        "user experience design": "การออกแบบประสบการณ์ผู้ใช้",
        "relevant experience": "ประสบการณ์ที่เกี่ยวข้อง",
        "lack of": "ขาดแคลน",
        "directly related": "เกี่ยวข้องโดยตรง",
        "self-motivated": "มีสติเต็มไปด้วย",
        "creative thinker": "ผู้คิดสร้างสรรค์",
        "detail-oriented": "สนใจรายละเอียด",
        "time management": "การจัดการเวลา",
        "develop": "พัฒนา",
        "create": "สร้าง",
        "contribute": "มีส่วนร่วม",
        "open-source": "โอเพนซอร์ส",
        "engineer": "วิศวกร",
        "scientist": "นักวิทยาศาสตร์",
        "developer": "นักพัฒนา",
        "obtain": "ได้มา",
        "gain": "ได้รับ",
        "portfolio": "พอร์ตโฟลิโอ",
        "GitHub": "GitHub",
        "academic": "ด้านวิชาการ",
        "mathematics": "คณิตศาสตร์",
        "physics": "ฟิสิกส์",
        "computer science": "วิทยาศาสตร์คอมพิวเตอร์",
        "candidate": "ผู้สมัคร",
        "position": "ตำแหน่ง",
        "match": "ตรงกับ",
        "The resume": "เรซูเม่",
        "provided": "ที่ให้มา",
        "is relevant": "มีความเกี่ยวข้อง",
        "However": "อย่างไรก็ตาม",
        "lacking": "ขาด",
        "which are": "ซึ่ง",
        "are strong": "แข็งแกร่ง",
        "but they are": "แต่มัน",
        "not directly": "ไม่ตรง",
    };

    // Replace longer phrases first (to avoid partial replacements)
    const sortedKeys = Object.keys(translations).sort((a, b) => b.length - a.length);
    
    for (const key of sortedKeys) {
        const regex = new RegExp(`\\b${key}\\b`, "gi");
        result = result.replace(regex, translations[key]);
    }

    return result;
}

function translateAnalysisObject(analysis, lang) {
    if (lang !== "th" || typeof analysis !== "object" || !analysis) return analysis;

    const translated = {};
    for (const [key, value] of Object.entries(analysis)) {
        if (typeof value === "string") {
            translated[key] = translateText(value, lang);
        } else if (Array.isArray(value)) {
            translated[key] = value.map(item => 
                typeof item === "string" ? translateText(item, lang) : item
            );
        } else {
            translated[key] = value;
        }
    }
    return translated;
}

function normalizeArray(items) {
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
}

function renderList(title, items) {
    const normalized = normalizeArray(items);
    if (normalized.length === 0) return "";
    return `
        <div class="result-section">
            <h3>${title}</h3>
            <ul>${normalized.map(item => `<li>${item}</li>`).join("")}</ul>
        </div>
    `;
}

function renderChips(items) {
    const normalized = normalizeArray(items);
    if (normalized.length === 0) return "<p class=\"muted\">—</p>";
    return `
        <div class="chip-list">
            ${normalized.map(i => `<span class="chip">${i}</span>`).join("")}
        </div>
    `;
}

function renderAnalysis(data, lang) {
    let analysis = typeof data.analysis === "object"
        ? data.analysis
        : tryParseJson(data.analysis);

    // Translate analysis content based on language selection
    if (lang === "th") {
        console.log("Translating analysis to Thai...", analysis);
        analysis = translateAnalysisObject(analysis, lang);
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
                    <div style="margin-top:10px;color:#475569">${jobFitLabel}: ${analysis?.match_comment ?? (lang === 'th' ? 'ไม่มีความคิดเห็น' : 'No comment')}</div>
                </div>
            </div>
            <div class="result-grid" style="margin-top:16px">
                <div class="stat">
                    <h3>${lang === "th" ? "คะแนนเรซูเม่" : "Resume Score"}</h3>
                    <p>${scoreDisplay}</p>
                </div>
                <div class="stat">
                    <h3>${lang === "th" ? "ตำแหน่งที่สมัคร" : "Applied Role"}</h3>
                    <p>${data.job_title ?? '-'}</p>
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
            <h3>${summaryLabel}</h3>
            <p>${analysis?.summary ?? t.noSummary}</p>
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
    out += `<div class="result-section" style="margin-top:8px"><h3>${actionsLabel}</h3>${renderList('', analysis?.recommended_actions ?? [])}</div>`;

    return out;
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
        const response = await fetch("/analyze", { method: "POST", body: formData });
        const data = await response.json();

        console.group("Resume Analysis Debug");
        console.log("Raw response data:", data);
        console.log("analysis field type:", typeof data.analysis, data.analysis);
        const parsedAnalysis = typeof data.analysis === "object" ? data.analysis : tryParseJson(data.analysis);
        console.log("Parsed analysis:", parsedAnalysis);
        console.groupEnd();

        resultDiv.innerHTML = renderAnalysis(data, lang);
    } catch (err) {
        console.error(err);
        resultDiv.innerHTML = `<div class="result-card"><h2>${translations[lang].errorTitle}</h2><p>${translations[lang].error}</p></div>`;
    }
}
