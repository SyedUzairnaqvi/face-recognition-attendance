// ============================================================
// SECURE VISION - VIDEO ATTENDANCE
// ============================================================

const VIDEO_API_BASE =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
        ? "http://127.0.0.1:8000"
        : "https://secure-vision-attendance-1.onrender.com";

const videoInput = document.getElementById("video-input");
const videoFileName = document.getElementById("video-file-name");
const videoBtn = document.getElementById("video-btn");
const videoResult = document.getElementById("video-result");

if (!videoInput || !videoFileName || !videoBtn || !videoResult) {
    console.error("Video Attendance: required HTML elements were not found.");
} else {
    videoBtn.disabled = true;

    videoInput.addEventListener("change", () => {
        const file = videoInput.files[0];

        if (!file) {
            videoFileName.textContent = "MP4, MOV, AVI, MKV, WEBM";
            videoBtn.disabled = true;
            return;
        }

        const MAX_SIZE = 50 * 1024 * 1024;
        const allowedTypes = [
            "video/mp4",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-matroska",
            "video/webm"
        ];

        if (file.size > MAX_SIZE) {
            videoFileName.textContent = "Video is larger than 50 MB";
            videoBtn.disabled = true;
            videoResult.className = "result error";
            videoResult.innerHTML = `
                <div class="result-title">Video Too Large</div>
                <div class="result-detail">Please upload a video smaller than 50 MB.</div>
            `;
            videoInput.value = "";
            return;
        }

        if (file.type && !allowedTypes.includes(file.type)) {
            videoFileName.textContent = "Unsupported video format";
            videoBtn.disabled = true;
            videoResult.className = "result error";
            videoResult.innerHTML = `
                <div class="result-title">Unsupported Video</div>
                <div class="result-detail">Please upload MP4, MOV, AVI, MKV or WEBM.</div>
            `;
            videoInput.value = "";
            return;
        }

        videoFileName.textContent = file.name;
        videoBtn.disabled = false;
        videoResult.className = "result";
        videoResult.innerHTML = "";
    });

    videoBtn.addEventListener("click", async () => {
        const file = videoInput.files[0];
        if (!file) return;

        videoBtn.disabled = true;
        videoBtn.textContent = "Processing Video...";

        videoResult.className = "result";
        videoResult.innerHTML = `
            <div class="result-title">Scanning Video...</div>
            <div class="result-detail">
                Detecting registered faces and recording attendance. Please wait.
            </div>
        `;

        const formData = new FormData();
        formData.append("file", file);

        const endpoint = `${VIDEO_API_BASE}/recognition/video`;
        console.log("Video API endpoint:", endpoint);

        try {
            const response = await fetch(endpoint, {
                method: "POST",
                body: formData
            });

            const contentType = response.headers.get("content-type") || "";
            const data = contentType.includes("application/json")
                ? await response.json()
                : { detail: await response.text() };

            if (!response.ok) {
                throw new Error(data.detail || data.message || `HTTP ${response.status}`);
            }

            const recognized = Array.isArray(data.recognized) ? data.recognized : [];
            const attendance = Array.isArray(data.attendance) ? data.attendance : [];
            const videoInfo = data.video || {};

            const filename = videoInfo.filename || file.name;
            const duration = videoInfo.duration_seconds ?? 0;
            const sampledFrames = videoInfo.sampled_frames ?? 0;
            const facesDetected = videoInfo.faces_detected ?? 0;
            const unknownFaces = data.unknown_faces ?? 0;

            let peopleHTML = "";

            if (recognized.length > 0) {
                peopleHTML = recognized.map(person => {
                    const name = person.name || "Unknown";
                    const score = person.match_score ?? "-";
                    const distance = person.distance ?? "-";
                    const threshold = person.threshold ?? "-";
                    const status = person.attendance?.status || "processed";

                    return `
                        <div class="video-person">
                            <strong>✓ ${name}</strong><br>
                            Match score: ${score}%<br>
                            Distance: ${distance}<br>
                            Threshold: ${threshold}<br>
                            Attendance: ${status}
                        </div>
                    `;
                }).join("");
            } else {
                peopleHTML = `<div>No registered people were recognized.</div>`;
            }

            let attendanceHTML = "";

            if (attendance.length > 0) {
                attendanceHTML = attendance.map(record => `
                    <div>
                        ✓ ${record.name} — ${record.date} — ${record.time} — ${record.status}
                    </div>
                `).join("");
            } else {
                attendanceHTML = `<div>No new attendance records.</div>`;
            }

            videoResult.className = recognized.length > 0 ? "result success" : "result";
            videoResult.innerHTML = `
                <div class="result-title">Video Processed Successfully</div>
                <div class="result-detail">
                    <strong>Recognized People</strong><br><br>
                    ${peopleHTML}
                    <br>
                    <strong>Attendance</strong><br><br>
                    ${attendanceHTML}
                    <br>
                    <strong>Video Details</strong><br><br>
                    Filename: ${filename}<br>
                    Duration: ${duration} seconds<br>
                    Frames sampled: ${sampledFrames}<br>
                    Faces detected: ${facesDetected}<br>
                    Unknown faces: ${unknownFaces}
                </div>
            `;

            const refreshBtn = document.getElementById("refresh-btn");
            if (refreshBtn) refreshBtn.click();

        } catch (error) {
            console.error("Video processing failed:", error);
            videoResult.className = "result error";
            videoResult.innerHTML = `
                <div class="result-title">Video Processing Failed</div>
                <div class="result-detail">${error.message}</div>
            `;
        } finally {
            videoBtn.disabled = false;
            videoBtn.textContent = "Upload Video & Mark Attendance";
        }
    });
}
