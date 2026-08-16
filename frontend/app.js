const API_BASE = "https://secure-vision-attendance.onrender.com";

// ============================================================
// VERIFY ELEMENTS
// ============================================================

const imageInput = document.getElementById("image-input");
const fileName = document.getElementById("file-name");
const verifyBtn = document.getElementById("verify-btn");
const resultBox = document.getElementById("result");

const attendanceBox = document.getElementById("attendance");
const refreshBtn = document.getElementById("refresh-btn");
const apiStatus = document.getElementById("api-status");

// ============================================================
// REGISTRATION ELEMENTS
// ============================================================

const registerName = document.getElementById("register-name");
const registerImage = document.getElementById("register-image");
const registerFileName = document.getElementById("register-file-name");
const registerBtn = document.getElementById("register-btn");
const registerResult = document.getElementById("register-result");

// ============================================================
// BACKEND HEALTH
// ============================================================

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


// ============================================================
// VERIFY IMAGE SELECTION
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
// VERIFY FACE
// ============================================================

verifyBtn.addEventListener("click", async () => {

    const file = imageInput.files[0];

    if (!file) {
        return;
    }

    verifyBtn.disabled = true;
    verifyBtn.textContent = "Verifying...";

    resultBox.className = "result";

    resultBox.innerHTML = `
        <div class="result-title">
            Processing image...
        </div>

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
            throw new Error(
                data.detail || "Verification failed"
            );
        }


        // ----------------------------------------------------
        // IMAGE QUALITY REJECTED
        // ----------------------------------------------------

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


        // ----------------------------------------------------
        // NO FACE
        // ----------------------------------------------------

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


        // ----------------------------------------------------
        // UNKNOWN PERSON
        // ----------------------------------------------------

        if (!recognition.matched) {

            resultBox.className = "result error";

            resultBox.innerHTML = `
                <div class="result-title">
                    Unknown Person
                </div>

                <div class="result-detail">
                    No registered identity matched this face.
                    <br><br>
                    Distance:
                    ${recognition.distance}
                </div>
            `;

            return;
        }


        // ----------------------------------------------------
        // SUCCESSFUL RECOGNITION
        // ----------------------------------------------------

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

        verifyBtn.textContent =
            "Verify & Mark Attendance";
    }
});


// ============================================================
// REGISTRATION IMAGE SELECTION
// ============================================================

registerImage.addEventListener("change", () => {

    const file = registerImage.files[0];

    if (file) {

        registerFileName.textContent = file.name;

        updateRegisterButton();

    } else {

        registerFileName.textContent =
            "PNG, JPG, JPEG, WEBP";

        registerBtn.disabled = true;
    }
});


// ============================================================
// ENABLE REGISTER BUTTON ONLY WHEN BOTH ARE PROVIDED
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

    if (!name || !file) {
        return;
    }

    registerBtn.disabled = true;

    registerBtn.textContent = "Registering...";

    registerResult.className = "result";

    registerResult.innerHTML = `
        <div class="result-title">
            Registering ${name}...
        </div>

        <div class="result-detail">
            Checking image quality and saving the face.
        </div>
    `;

    try {

        // ----------------------------------------------------
        // STEP 1: REGISTER IMAGE
        // ----------------------------------------------------

        const formData = new FormData();

        formData.append("file", file);

        const registerResponse = await fetch(
            `${API_BASE}/enrollment/register?name=${encodeURIComponent(name)}`,
            {
                method: "POST",
                body: formData
            }
        );

        const registerData =
            await registerResponse.json();


        if (!registerResponse.ok) {

            let message = "Registration failed.";

            if (typeof registerData.detail === "string") {
                message = registerData.detail;
            }

            else if (
                registerData.detail &&
                registerData.detail.quality
            ) {

                const issues =
                    registerData.detail.quality.issues || [];

                message =
                    issues.join(", ") ||
                    "Image quality rejected.";
            }

            throw new Error(message);
        }


        // ----------------------------------------------------
        // STEP 2: START EMBEDDING INDEX BUILD
        // ----------------------------------------------------

        registerResult.innerHTML = `
            <div class="result-title">
                Face Saved
            </div>

            <div class="result-detail">
                Building the face recognition index...
            </div>
        `;


        const buildResponse = await fetch(
            `${API_BASE}/enrollment/build-index`,
            {
                method: "POST"
            }
        );


        const buildData =
            await buildResponse.json();


        if (!buildResponse.ok) {

            throw new Error(
                buildData.detail ||
                "Could not start embedding build."
            );
        }


        // ----------------------------------------------------
        // STEP 3: WAIT FOR INDEX
        // ----------------------------------------------------

        await waitForIndex();


        // ----------------------------------------------------
        // SUCCESS
        // ----------------------------------------------------

        registerResult.className =
            "result success";

        registerResult.innerHTML = `
            <div class="result-title">
                ${registerData.name} Registered Successfully
            </div>

            <div class="result-detail">

                Face image saved successfully.

                <br>

                Embedding index rebuilt successfully.

                <br>

                ${registerData.quality
                    ? `Blur score: ${registerData.quality.blur_score}`
                    : ""
                }

                <br><br>

                You can now verify this person's face
                using the Verify Attendance section.

            </div>
        `;


        // Reset form

        registerName.value = "";

        registerImage.value = "";

        registerFileName.textContent =
            "PNG, JPG, JPEG, WEBP";

        registerBtn.disabled = true;


    } catch (error) {

        registerResult.className =
            "result error";

        registerResult.innerHTML = `
            <div class="result-title">
                Registration Failed
            </div>

            <div class="result-detail">
                ${error.message}
            </div>
        `;

    } finally {

        registerBtn.textContent =
            "Register Face";

        updateRegisterButton();
    }
});


// ============================================================
// WAIT FOR EMBEDDING INDEX
// ============================================================

async function waitForIndex() {

    const maxAttempts = 60;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {

        await new Promise(resolve =>
            setTimeout(resolve, 2000)
        );


        const response = await fetch(
            `${API_BASE}/enrollment/build-index/status`
        );


        if (!response.ok) {

            throw new Error(
                "Could not check embedding build status."
            );
        }


        const data = await response.json();


        // -----------------------------------------------
        // INDEX READY
        // -----------------------------------------------

        if (data.status === "ready") {

            return;
        }


        // -----------------------------------------------
        // INDEX FAILED
        // -----------------------------------------------

        if (data.status === "failed") {

            throw new Error(
                data.error ||
                "Embedding index build failed."
            );
        }


        // -----------------------------------------------
        // STILL BUILDING
        // -----------------------------------------------

        registerResult.innerHTML = `
            <div class="result-title">
                Building Recognition Index...
            </div>

            <div class="result-detail">
                Please wait. This can take a little while
                when the AI model is loading.
            </div>
        `;
    }


    throw new Error(
        "Embedding index build timed out."
    );
}


// ============================================================
// LOAD TODAY'S ATTENDANCE
// ============================================================

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
            throw new Error(
                "Unable to load attendance"
            );
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

                <td>
                    ${record.name}
                </td>

                <td>
                    ${record.time}
                </td>

                <td>
                    ${record.match_distance}
                </td>

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


// ============================================================
// REFRESH ATTENDANCE
// ============================================================

refreshBtn.addEventListener(
    "click",
    loadAttendance
);


// ============================================================
// INITIAL PAGE LOAD
// ============================================================

checkHealth();

loadAttendance();