// ============================================================
// SECURE VISION - VIDEO ATTENDANCE
// ============================================================
// Local frontend:
//     http://localhost:5500
//     -> http://127.0.0.1:8000
//
// Deployed frontend:
//     Render frontend
//     -> Render API
//
// The API is selected automatically.
// ============================================================


const VIDEO_API_BASE =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
        ? "http://127.0.0.1:8000"
        : "https://secure-vision-attendance.onrender.com";


// ============================================================
// ELEMENTS
// ============================================================

const videoInput = document.getElementById("video-input");
const videoFileName = document.getElementById("video-file-name");
const videoBtn = document.getElementById("video-btn");
const videoResult = document.getElementById("video-result");


// ============================================================
// CHECK ELEMENTS
// ============================================================

if (!videoInput || !videoFileName || !videoBtn || !videoResult) {

    console.error(
        "Video Attendance: required HTML elements were not found."
    );

} else {


    // ========================================================
    // INITIAL STATE
    // ========================================================

    videoBtn.disabled = true;


    // ========================================================
    // VIDEO FILE SELECTED
    // ========================================================

    videoInput.addEventListener("change", () => {

        const file = videoInput.files[0];

        if (!file) {

            videoFileName.textContent =
                "MP4, MOV, AVI, MKV, WEBM";

            videoBtn.disabled = true;

            return;
        }


        // ----------------------------------------------------
        // Maximum upload size = 50 MB
        // ----------------------------------------------------

        const MAX_SIZE =
            50 * 1024 * 1024;


        if (file.size > MAX_SIZE) {

            videoFileName.textContent =
                "Video is larger than 50 MB";

            videoBtn.disabled = true;

            videoResult.className =
                "result error";

            videoResult.innerHTML = `
                <div class="result-title">
                    Video Too Large
                </div>

                <div class="result-detail">
                    Please upload a video smaller than 50 MB.
                </div>
            `;

            videoInput.value = "";

            return;
        }


        // ----------------------------------------------------
        // Validate video type
        // ----------------------------------------------------

        const allowedTypes = [
            "video/mp4",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-matroska",
            "video/webm"
        ];


        if (
            file.type &&
            !allowedTypes.includes(file.type)
        ) {

            videoFileName.textContent =
                "Unsupported video format";

            videoBtn.disabled = true;

            videoResult.className =
                "result error";

            videoResult.innerHTML = `
                <div class="result-title">
                    Unsupported Video
                </div>

                <div class="result-detail">
                    Please upload MP4, MOV, AVI, MKV or WEBM.
                </div>
            `;

            videoInput.value = "";

            return;
        }


        // ----------------------------------------------------
        // Valid video
        // ----------------------------------------------------

        videoFileName.textContent =
            file.name;

        videoBtn.disabled = false;

        videoResult.className =
            "result";

        videoResult.innerHTML = "";

    });


    // ========================================================
    // UPLOAD VIDEO + MARK ATTENDANCE
    // ========================================================

    videoBtn.addEventListener("click", async () => {

        const file =
            videoInput.files[0];


        if (!file) {
            return;
        }


        // ----------------------------------------------------
        // Disable button while processing
        // ----------------------------------------------------

        videoBtn.disabled = true;

        videoBtn.textContent =
            "Processing Video...";


        videoResult.className =
            "result";


        videoResult.innerHTML = `
            <div class="result-title">
                Scanning Video...
            </div>

            <div class="result-detail">
                Detecting registered faces and recording attendance.
                Please wait.
            </div>
        `;


        // ----------------------------------------------------
        // Create multipart/form-data
        // ----------------------------------------------------

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );


        // ----------------------------------------------------
        // API endpoint
        // ----------------------------------------------------

        const endpoint =
            `${VIDEO_API_BASE}/recognition/video`;


        console.log(
            "Video API endpoint:",
            endpoint
        );


        try {

            // =================================================
            // SEND VIDEO TO FASTAPI
            // =================================================

            const response =
                await fetch(
                    endpoint,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            // =================================================
            // READ SERVER RESPONSE
            // =================================================

            const contentType =
                response.headers.get(
                    "content-type"
                ) || "";


            let data;


            if (
                contentType.includes(
                    "application/json"
                )
            ) {

                data =
                    await response.json();

            } else {

                const text =
                    await response.text();

                throw new Error(
                    `Server returned HTTP ${response.status}: ${text}`
                );
            }


            // =================================================
            // SERVER ERROR
            // =================================================

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    data.message ||
                    `HTTP ${response.status}`
                );
            }


            // =================================================
            // SUCCESS DATA
            // =================================================

            const recognized =
                Array.isArray(data.recognized)
                    ? data.recognized
                    : [];


            const attendance =
                Array.isArray(data.attendance)
                    ? data.attendance
                    : [];


            const videoInfo =
                data.video || {};


            // =================================================
            // VIDEO STATISTICS
            // =================================================

            const filename =
                videoInfo.filename ||
                file.name;


            const duration =
                videoInfo.duration_seconds ??
                0;


            const sampledFrames =
                videoInfo.sampled_frames ??
                0;


            const facesDetected =
                videoInfo.faces_detected ??
                0;


            const unknownFaces =
                data.unknown_faces ??
                0;


            // =================================================
            // RECOGNIZED PEOPLE
            // =================================================

            let peopleHTML = "";


            if (recognized.length > 0) {

                peopleHTML =
                    recognized
                        .map(person => {

                            const name =
                                person.name ||
                                "Unknown";


                            const score =
                                person.match_score ??
                                "-";


                            const distance =
                                person.distance ??
                                "-";


                            const threshold =
                                person.threshold ??
                                "-";


                            const status =
                                person.attendance?.status ||
                                "processed";


                            return `
                                <div class="video-person">
                                    <strong>
                                        ✓ ${name}
                                    </strong>

                                    <br>

                                    Match score:
                                    ${score}%

                                    <br>

                                    Distance:
                                    ${distance}

                                    <br>

                                    Threshold:
                                    ${threshold}

                                    <br>

                                    Attendance:
                                    ${status}
                                </div>
                            `;

                        })
                        .join("");

            } else {

                peopleHTML = `
                    <div>
                        No registered people were recognized.
                    </div>
                `;
            }


            // =================================================
            // ATTENDANCE INFORMATION
            // =================================================

            let attendanceHTML = "";


            if (attendance.length > 0) {

                attendanceHTML =
                    attendance
                        .map(record => {

                            return `
                                <div>
                                    ✓ ${record.name}
                                    — ${record.date}
                                    — ${record.time}
                                    — ${record.status}
                                </div>
                            `;

                        })
                        .join("");

            } else {

                attendanceHTML = `
                    <div>
                        No new attendance records.
                    </div>
                `;
            }


            // =================================================
            // DISPLAY SUCCESS
            // =================================================

            videoResult.className =
                recognized.length > 0
                    ? "result success"
                    : "result";


            videoResult.innerHTML = `

                <div class="result-title">
                    Video Processed Successfully
                </div>

                <div class="result-detail">

                    <strong>
                        Recognized People
                    </strong>

                    <br><br>

                    ${peopleHTML}

                    <br>

                    <strong>
                        Attendance
                    </strong>

                    <br><br>

                    ${attendanceHTML}

                    <br>

                    <strong>
                        Video Details
                    </strong>

                    <br><br>

                    Filename:
                    ${filename}

                    <br>

                    Duration:
                    ${duration} seconds

                    <br>

                    Frames sampled:
                    ${sampledFrames}

                    <br>

                    Faces detected:
                    ${facesDetected}

                    <br>

                    Unknown faces:
                    ${unknownFaces}

                </div>
            `;


            // =================================================
            // REFRESH TODAY'S ATTENDANCE
            // =================================================

            const refreshBtn =
                document.getElementById(
                    "refresh-btn"
                );


            if (refreshBtn) {

                refreshBtn.click();

            }


        } catch (error) {

            // =================================================
            // ERROR
            // =================================================

            console.error(
                "Video processing failed:",
                error
            );


            videoResult.className =
                "result error";


            videoResult.innerHTML = `

                <div class="result-title">
                    Video Processing Failed
                </div>

                <div class="result-detail">
                    ${error.message}
                </div>

            `;

        } finally {

            // =================================================
            // RESTORE BUTTON
            // =================================================

            videoBtn.disabled = false;

            videoBtn.textContent =
                "Upload Video & Mark Attendance";

        }

    });

}