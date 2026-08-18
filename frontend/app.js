// ============================================================
// API BASE
// ============================================================

const API_BASE =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
        ? "http://127.0.0.1:8000"
        : "https://secure-vision-attendance-1.onrender.com";


// ============================================================
// ELEMENTS
// ============================================================

const imageInput = document.getElementById("image-input");
const fileName = document.getElementById("file-name");
const verifyBtn = document.getElementById("verify-btn");
const resultBox = document.getElementById("result");
const attendanceBox = document.getElementById("attendance");
const refreshBtn = document.getElementById("refresh-btn");
const apiStatus = document.getElementById("api-status");


// ============================================================
// REGISTRATION
// ============================================================

const registerName = document.getElementById("register-name");
const registerImage = document.getElementById("register-image");
const registerFileName = document.getElementById("register-file-name");
const registerBtn = document.getElementById("register-btn");
const registerResult = document.getElementById("register-result");


// ============================================================
// HEALTH
// ============================================================

async function checkHealth() {
    apiStatus.textContent = "Checking API...";

    try {
        const response = await fetch(`${API_BASE}/health`, { cache: "no-store" });

        if (!response.ok) {
            throw new Error("Backend unavailable");
        }

        const data = await response.json();

        apiStatus.textContent =
            data.status === "ok"
                ? "API Online"
                : "API Issue";

    } catch {
        apiStatus.textContent = "API Offline";
    }
}


// ============================================================
// IMAGE SELECTION
// ============================================================

imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];

    if (file) {
        fileName.textContent = file.name;
        verifyBtn.disabled = false;
    } else {
        fileName.textContent = "PNG, JPG, JPEG, WEBP";
        verifyBtn.disabled = true;
    }
});


// ============================================================
// VERIFY
// ============================================================

verifyBtn.addEventListener("click", async () => {
    const file = imageInput.files[0];

    if (!file) return;

    verifyBtn.disabled = true;
    verifyBtn.textContent = "Verifying...";

    resultBox.className = "result";
    resultBox.innerHTML = `
        <div class="result-title">Processing image...</div>
        <div class="result-detail">Running quality checks and face recognition.</div>
    `;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_BASE}/recognition/verify`, {
            method: "POST",
            body: formData
        });

        const contentType = response.headers.get("content-type") || "";
        const data = contentType.includes("application/json")
            ? await response.json()
            : { detail: await response.text() };

        if (!response.ok) {
            throw new Error(data.detail || "Verification failed");
        }

        if (data.status === "rejected") {
            const issues =
                data.quality?.issues?.join(", ") ||
                data.reason ||
                "Image rejected";

            resultBox.className = "result error";
            resultBox.innerHTML = `
                <div class="result-title">Image Rejected</div>
                <div class="result-detail">${issues}</div>
            `;
            return;
        }

        const recognition = data.recognitions?.[0];

        if (!recognition) {
            resultBox.className = "result error";
            resultBox.innerHTML = `
                <div class="result-title">No Face Recognized</div>
                <div class="result-detail">Try another clear image.</div>
            `;
            return;
        }

        if (!recognition.matched) {
            resultBox.className = "result error";
            resultBox.innerHTML = `
                <div class="result-title">Unknown Person</div>
                <div class="result-detail">No registered identity matched this face.</div>
            `;
            return;
        }

        const attendance = data.attendance?.[0];

        resultBox.className = "result success";
        resultBox.innerHTML = `
            <div class="result-title">${recognition.name} Verified</div>
            <div class="result-detail">
                Match score: ${recognition.match_score}%<br>
                Model: ${recognition.model}<br>
                Liveness: ${recognition.liveness?.status || "unknown"}<br>
                Attendance: ${attendance?.status || "processed"}
            </div>
        `;

        await loadAttendance();

    } catch (error) {
        resultBox.className = "result error";
        resultBox.innerHTML = `
            <div class="result-title">Verification Error</div>
            <div class="result-detail">${error.message}</div>
        `;

    } finally {
        verifyBtn.disabled = false;
        verifyBtn.textContent = "Verify & Mark Attendance";
    }
});


// ============================================================
// REGISTRATION IMAGE
// ============================================================

registerImage.addEventListener("change", () => {
    const file = registerImage.files[0];

    if (file) {
        registerFileName.textContent = file.name;
        updateRegisterButton();
    } else {
        registerFileName.textContent = "PNG, JPG, JPEG, WEBP";
        registerBtn.disabled = true;
    }
});


// ============================================================
// REGISTER BUTTON
// ============================================================

registerName.addEventListener("input", updateRegisterButton);

function updateRegisterButton() {
    const name = registerName.value.trim();
    const file = registerImage.files[0];
    registerBtn.disabled = !(name && file);
}


// ============================================================
// REGISTER FACE
// ============================================================

registerBtn.addEventListener("click", async () => {
    const name = registerName.value.trim();
    const file = registerImage.files[0];

    if (!name || !file) return;

    registerBtn.disabled = true;
    registerBtn.textContent = "Registering...";

    registerResult.className = "result";
    registerResult.innerHTML = `
        <div class="result-title">Registering ${name}...</div>
        <div class="result-detail">Checking image quality and saving the face.</div>
    `;

    try {
        const formData = new FormData();
        formData.append("file", file);

        const registerResponse = await fetch(
            `${API_BASE}/enrollment/register?name=${encodeURIComponent(name)}`,
            { method: "POST", body: formData }
        );

        const registerData = await registerResponse.json();

        if (!registerResponse.ok) {
            throw new Error(registerData.detail || "Registration failed.");
        }

        registerResult.innerHTML = `
            <div class="result-title">Face Saved</div>
            <div class="result-detail">Building the face recognition index...</div>
        `;

        const buildResponse = await fetch(
            `${API_BASE}/enrollment/build-index`,
            { method: "POST" }
        );

        const buildData = await buildResponse.json();

        if (!buildResponse.ok) {
            throw new Error(buildData.detail || "Could not start embedding build.");
        }

        await waitForIndex();

        registerResult.className = "result success";
        registerResult.innerHTML = `
            <div class="result-title">${registerData.name} Registered Successfully</div>
            <div class="result-detail">
                Face image saved successfully.<br>
                Embedding index rebuilt successfully.
            </div>
        `;

        registerName.value = "";
        registerImage.value = "";
        registerFileName.textContent = "PNG, JPG, JPEG, WEBP";
        registerBtn.disabled = true;

    } catch (error) {
        registerResult.className = "result error";
        registerResult.innerHTML = `
            <div class="result-title">Registration Failed</div>
            <div class="result-detail">${error.message}</div>
        `;

    } finally {
        registerBtn.textContent = "Register Face";
        updateRegisterButton();
    }
});


// ============================================================
// WAIT FOR INDEX
// ============================================================

async function waitForIndex() {
    for (let attempt = 0; attempt < 60; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 2000));

        const response = await fetch(
            `${API_BASE}/enrollment/build-index/status`,
            { cache: "no-store" }
        );

        if (!response.ok) {
            throw new Error("Could not check embedding build status.");
        }

        const data = await response.json();

        if (data.status === "ready") return;

        if (data.status === "failed") {
            throw new Error(data.error || "Embedding index build failed.");
        }
    }

    throw new Error("Embedding index build timed out.");
}


// ============================================================
// TODAY'S ATTENDANCE
// ============================================================

async function loadAttendance() {
    attendanceBox.innerHTML = `<div class="empty">Loading attendance...</div>`;

    try {
        const response = await fetch(
            `${API_BASE}/attendance/today`,
            { cache: "no-store" }
        );

        if (!response.ok) {
            throw new Error("Unable to load attendance");
        }

        const data = await response.json();
        const records = data.records || [];

        if (records.length === 0) {
            attendanceBox.innerHTML = `
                <div class="empty">No attendance recorded today.</div>
            `;
            return;
        }

        const rows = records.map(record => {
            const status = record.status || "Present";
            const displayStatus =
                status === "already_marked_today"
                    ? "Already Marked"
                    : "Present";
            const method = record.method || "Face Recognition";

            return `
                <tr>
                    <td>${record.name}</td>
                    <td>${record.time}</td>
                    <td>${displayStatus}</td>
                    <td>${method}</td>
                </tr>
            `;
        }).join("");

        attendanceBox.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Time</th>
                        <th>Status</th>
                        <th>Method</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;

    } catch {
        attendanceBox.innerHTML = `
            <div class="empty">Could not load attendance.</div>
        `;
    }
}


// ============================================================
// REFRESH
// ============================================================

refreshBtn.addEventListener("click", loadAttendance);


// ============================================================
// INITIAL LOAD
// ============================================================

checkHealth();
loadAttendance();
