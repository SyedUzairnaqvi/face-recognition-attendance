const VIDEO_API_BASE = "https://secure-vision-attendance.onrender.com";

const videoInput = document.getElementById("video-input");
const videoFileName = document.getElementById("video-file-name");
const videoBtn = document.getElementById("video-btn");
const videoResult = document.getElementById("video-result");

videoInput.addEventListener("change", () => {
    const file = videoInput.files[0];
    if (file) {
        videoFileName.textContent = file.name;
        videoBtn.disabled = false;
    } else {
        videoFileName.textContent = "MP4, MOV, AVI, MKV, WEBM";
        videoBtn.disabled = true;
    }
});

videoBtn.addEventListener("click", async () => {
    const file = videoInput.files[0];
    if (!file) return;

    videoBtn.disabled = true;
    videoBtn.textContent = "Processing Video...";
    videoResult.className = "result";
    videoResult.innerHTML = `
        <div class="result-title">Scanning video...</div>
        <div class="result-detail">Detecting registered faces and recording attendance. This may take a little while.</div>
    `;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${VIDEO_API_BASE}/recognition/video`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Video processing failed");
        }

        const recognized = data.recognized || [];
        const attendance = data.attendance || [];

        const peopleHtml = recognized.length
            ? recognized.map(person => `
                <div>
                    ✓ ${person.name} — ${person.match_score ?? "-"}% — ${person.attendance?.status || "processed"}
                </div>
            `).join("")
            : "No registered people were recognized.";

        videoResult.className = recognized.length ? "result success" : "result";
        videoResult.innerHTML = `
            <div class="result-title">Video Processed</div>
            <div class="result-detail">
                ${peopleHtml}
                <br>
                Frames sampled: ${data.video?.sampled_frames ?? 0}<br>
                Faces detected: ${data.video?.faces_detected ?? 0}<br>
                Unknown faces: ${data.unknown_faces ?? 0}<br>
                Duration: ${data.video?.duration_seconds ?? 0}s
            </div>
        `;

        const refreshBtn = document.getElementById("refresh-btn");
        if (refreshBtn) refreshBtn.click();

    } catch (error) {
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
