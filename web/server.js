const express = require("express");
const multer = require("multer");
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");
const path = require("path");

const app = express();
// NOTE: 127.0.0.1 (not localhost) — on Windows, Node may fail to connect to
// localhost:port (IPv6 ::1 refused, no Happy Eyeballs fallback) while browsers work.
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";
const PORT = process.env.PORT || 3000;

// Proxy errors keep the machine-readable code (ECONNREFUSED, ETIMEDOUT…)
// so the dashboard can tell "backend down" apart from "backend error".
function proxyError(err, fallback) {
    if (err.response?.data) return err.response.data;
    return { error: fallback, code: err.code || null };
}

app.use('/locales', express.static(path.join(__dirname, 'locales')));
app.use(express.static(path.join(__dirname, "public")));
app.use(express.json());

const MAX_MB = parseInt(process.env.MAX_UPLOAD_MB || "10", 10);
const upload = multer({
    dest: path.join(__dirname, "temp"),
    limits: { fileSize: MAX_MB * 1024 * 1024 },
    fileFilter: (req, file, cb) => {
        const ok = file.originalname.toLowerCase().endsWith(".pdf");
        cb(ok ? null : new Error("Only PDF files are accepted"), ok);
    },
});

function passthroughAuth(req) {
    const h = req.headers.authorization;
    return h ? { Authorization: h } : {};
}

app.post("/analyze", upload.single("resume"), async (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: "Resume PDF file is required" });
    }
    try {
        const form = new FormData();

        form.append(
            "file",
            fs.createReadStream(req.file.path),
            req.file.originalname
        );

        form.append("job_title", req.body.job_title || "");
        form.append("job_type", req.body.job_type || "");
        form.append("is_new_grad", req.body.is_new_grad || "false");
        form.append("language", req.body.language || "en");

        const headers = { ...form.getHeaders(), ...passthroughAuth(req) };
        const response = await axios.post(
            `${BACKEND_URL}/analyze`,
            form,
            { headers, maxBodyLength: Infinity, timeout: 180000 }
        );

        res.status(response.status).json(response.data);
    } catch (err) {
        console.error(err);
        const status = err.response?.status || 500;
        res.status(status).json(proxyError(err, "Analyze failed"));
    } finally {
        if (req.file) fs.unlink(req.file.path, () => {});
    }
});

app.post("/translate", async (req, res) => {
    try {
        const { text, target_lang } = req.body;

        if (!text) {
            return res.json({ translatedText: text });
        }

        const response = await axios.post(
            `${BACKEND_URL}/translate`,
            { text: text, target_lang: target_lang || "th" },
            { timeout: 35000 }
        );

        const translatedText = response.data.translatedText || text;
        res.json({ translatedText });
    } catch (err) {
        console.error("Translation error:", err.message);
        res.json({ translatedText: req.body.text || "" });
    }
});

// ---- admin / service dashboard passthrough (read-only) ----
for (const route of ["/admin/stats", "/admin/logs", "/admin/source-check"]) {
    app.get(route, async (req, res) => {
        try {
            const r = await axios.get(`${BACKEND_URL}${route}`,
                { params: req.query, timeout: 60000 });
            res.json(r.data);
        } catch (err) {
            res.status(err.response?.status || 500).json(proxyError(err, "Admin API failed"));
        }
    });
}

// ---- jobs passthrough (real postings cached in backend DB) ----
app.get("/jobs/status", async (req, res) => {
    try {
        const r = await axios.get(`${BACKEND_URL}/jobs/status`, { timeout: 15000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "Jobs status failed"));
    }
});

app.get("/jobs", async (req, res) => {
    try {
        const r = await axios.get(`${BACKEND_URL}/jobs`, { params: req.query, timeout: 15000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "Jobs failed"));
    }
});

app.get("/jobs/:id", async (req, res) => {
    try {
        const r = await axios.get(`${BACKEND_URL}/jobs/${req.params.id}`, { timeout: 15000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "Job not found"));
    }
});

app.post("/jobs/refresh", async (req, res) => {
    try {
        const r = await axios.post(`${BACKEND_URL}/jobs/refresh`, req.body || {},
            { headers: passthroughAuth(req), timeout: 120000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "Refresh failed"));
    }
});

app.post("/jobs/:id/save", async (req, res) => {
    try {
        const r = await axios.post(`${BACKEND_URL}/jobs/${req.params.id}/save`, {},
            { headers: passthroughAuth(req), timeout: 15000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "Save failed"));
    }
});

app.get("/saved-jobs", async (req, res) => {
    try {
        const r = await axios.get(`${BACKEND_URL}/saved-jobs`,
            { headers: passthroughAuth(req), timeout: 15000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "Saved jobs failed"));
    }
});

// ---- auth / history passthrough ----
for (const route of ["/auth/register", "/auth/login"]) {
    app.post(route, async (req, res) => {
        try {
            const r = await axios.post(`${BACKEND_URL}${route}`, req.body, { timeout: 15000 });
            res.json(r.data);
        } catch (err) {
            res.status(err.response?.status || 500).json(proxyError(err, "Auth failed"));
        }
    });
}

app.post("/auth/logout", async (req, res) => {
    try {
        const r = await axios.post(`${BACKEND_URL}/auth/logout`, {},
            { headers: passthroughAuth(req), timeout: 15000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "Logout failed"));
    }
});

app.get("/me", async (req, res) => {
    try {
        const r = await axios.get(`${BACKEND_URL}/me`,
            { headers: passthroughAuth(req), timeout: 15000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "Auth failed"));
    }
});

app.get("/history", async (req, res) => {
    try {
        const r = await axios.get(`${BACKEND_URL}/history`,
            { headers: passthroughAuth(req), params: req.query, timeout: 15000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "History failed"));
    }
});

app.post("/analyze-market", async (req, res) => {
    try {
        const r = await axios.post(`${BACKEND_URL}/analyze-market`, {}, { timeout: 180000 });
        res.json(r.data);
    } catch (err) {
        res.status(err.response?.status || 500).json(proxyError(err, "Market analysis failed"));
    }
});

// multer / body errors -> JSON (not HTML crash pages)
app.use((err, req, res, next) => {
    if (!err) return next();
    console.error(err);
    if (err.code === "LIMIT_FILE_SIZE") {
        return res.status(413).json({ error: `File too large (limit ${MAX_MB} MB)` });
    }
    if (err.message === "Only PDF files are accepted") {
        return res.status(415).json({ error: err.message });
    }
    if (err.type === "entity.parse.failed" || err.status === 400) {
        return res.status(400).json({ error: "Invalid JSON body" });
    }
    res.status(500).json({ error: "Request failed" });
});

if (require.main === module) {
    app.listen(PORT, () => console.log(`http://localhost:${PORT} -> ${BACKEND_URL}`));
}

module.exports = app;
