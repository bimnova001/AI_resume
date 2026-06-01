const express = require("express");
const multer = require("multer");
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");

const app = express();

app.use(express.static("public"));

const upload = multer({
    dest: "temp/"
});

app.post(
    "/analyze",
    upload.single("resume"),
    async (req, res) => {

        try {

            const form = new FormData();

            form.append(
                "file",
                fs.createReadStream(req.file.path),
                req.file.originalname
            );

            form.append("job_title", req.body.job_title);
            form.append("job_type", req.body.job_type || "");
            form.append("is_new_grad", req.body.is_new_grad || "false");
            form.append("language", req.body.language || "en");

            console.log("Proxy received language:", req.body.language);

            const response =
                await axios.post(
                    "http://localhost:8000/analyze",
                    form,
                    {
                        headers:
                            form.getHeaders()
                    }
                );

            res.json(response.data);

            // cleanup temp file
            fs.unlink(req.file.path, () => {});

        } catch (err) {

            console.error(err);

            res.status(500).json({
                error: "Analyze failed"
            });

        }

    }
);

app.listen(
    3000,
    () => console.log(
        "http://localhost:3000"
    )
);