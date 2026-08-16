const API_BASE = "https://secure-vision-attendance.onrender.com";

const imageInput = document.getElementById("image-input");
const fileName = document.getElementById("file-name");
const verifyBtn = document.getElementById("verify-btn");
const resultBox = document.getElementById("result");
const attendanceBox = document.getElementById("attendance");
const refreshBtn = document.getElementById("refresh-btn");
const apiStatus = document.getElementById("api-status");


// ---------------------------
// Check backend health
// ---------------------------
async function checkHealth() {
    apiStatus.textContent = "Checking API...";

    try {
        const response = await fetch(`${API_BASE}/health`);

        if (!response.ok) {
            throw new Error("Backend unavailable");
        }

        const data = await response.json();

        if (data.status === "ok") {
            apiStatus.textContent = "API Online";
        } else {
            apiStatus.textContent = "API Issue";
        }

    } catch (error) {
        apiStatus.textContent = "API Offline";
    }
}


// ---------------------------
// File selection
// ---------------------------
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


// ---------------------------
// Verify face
// ---------------------------
verifyBtn.addEventListener("click", async () => {

    const file = imageInput.files[0];

    if (!file) {
        return;
    }

    verifyBtn.disabled = true;
    verifyBtn.textContent = "Verifying...";

    resultBox.className = "result";
    resultBox.innerHTML = `
        <div class="result-title">Processing image...</div>
        <div class="result-detail">
            Running quality checks and face recognition.
        </div>
    `;

    const formData = new FormData();
    formData.append("file", file);

    try {

        const response = await fetch(
            `${API_BASE}/recognition/verify`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Verification failed");
        }


        // Image rejected by quality checks
        if (data.status === "rejected") {

            const issues =
                data.quality?.issues?.join(", ") ||
                data.reason ||
                "Image rejected";

            resultBox.className = "result error";

            resultBox.innerHTML = `
                <div class="result-title">
                    Image Rejected
                </div>

                <div class="result-detail">
                    ${issues}
                </div>
            `;

            return;
        }


        const recognition = data.recognitions?.[0];


        // No face / no recognition
        if (!recognition) {

            resultBox.className = "result error";

            resultBox.innerHTML = `
                <div class="result-title">
                    No Face Recognized
                </div>

                <div class="result-detail">
                    Try another clear image.
                </div>
            `;

            return;
        }


        // Unknown person
        if (!recognition.matched) {

            resultBox.className = "result error";

            resultBox.innerHTML = `
                <div class="result-title">
                    Unknown Person
                </div>

                <div class="result-detail">
                    No registered identity matched this face.
                    <br>
                    Distance: ${recognition.distance}
                </div>
            `;

            return;
        }


        // Successful recognition
        const attendance = data.attendance?.[0];

        resultBox.className = "result success";

        resultBox.innerHTML = `
            <div class="result-title">
                ${recognition.name} Verified
            </div>

            <div class="result-detail">

                Match score:
                ${recognition.match_score}%

                <br>

                Model:
                ${recognition.model}

                <br>

                Attendance:
                ${attendance?.status || "processed"}

            </div>
        `;

        await loadAttendance();

    } catch (error) {

        resultBox.className = "result error";

        resultBox.innerHTML = `
            <div class="result-title">
                Verification Error
            </div>

            <div class="result-detail">
                ${error.message}
            </div>
        `;

    } finally {

        verifyBtn.disabled = false;
        verifyBtn.textContent = "Verify & Mark Attendance";
    }
});


// ---------------------------
// Load today's attendance
// ---------------------------
async function loadAttendance() {

    attendanceBox.innerHTML = `
        <div class="empty">
            Loading attendance...
        </div>
    `;

    try {

        const response = await fetch(
            `${API_BASE}/attendance/today`
        );

        if (!response.ok) {
            throw new Error("Unable to load attendance");
        }

        const data = await response.json();
        const records = data.records || [];


        if (records.length === 0) {

            attendanceBox.innerHTML = `
                <div class="empty">
                    No attendance recorded today.
                </div>
            `;

            return;
        }


        const rows = records.map(record => `
            <tr>
                <td>${record.name}</td>
                <td>${record.time}</td>
                <td>${record.match_distance}</td>
            </tr>
        `).join("");


        attendanceBox.innerHTML = `
            <table>

                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Time</th>
                        <th>Distance</th>
                    </tr>
                </thead>

                <tbody>
                    ${rows}
                </tbody>

            </table>
        `;

    } catch (error) {

        attendanceBox.innerHTML = `
            <div class="empty">
                Could not load attendance.
            </div>
        `;
    }
}


// ---------------------------
// Refresh attendance
// ---------------------------
refreshBtn.addEventListener(
    "click",
    loadAttendance
);


// ---------------------------
// Initial page load
// ---------------------------
checkHealth();
loadAttendance();