// ============================================================
// HIGH-VOLUME BATCH RECOGNITION
// ============================================================

const BATCH_API_BASE =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
        ? "http://127.0.0.1:8000"
        : "https://secure-vision-attendance.onrender.com";

const batchInput = document.getElementById("batch-image-input");
const batchButton = document.getElementById("batch-btn");
const batchFileName = document.getElementById("batch-file-name");
const batchResult = document.getElementById("batch-result");
const batchProgress = document.getElementById("batch-progress");
const batchProgressText = document.getElementById("batch-progress-text");

const BATCH_SIZE = 25;
const MAX_FILES = 50000;

function showBatchResult(title, detail, type = "") {
    batchResult.className = `result ${type}`.trim();
    batchResult.innerHTML = `
        <div class="result-title">${title}</div>
        <div class="result-detail">${detail}</div>
    `;
}

function setProgress(done, total) {
    const percent = total ? Math.round((done / total) * 100) : 0;
    batchProgress.value = percent;
    batchProgressText.textContent = `${done.toLocaleString()} / ${total.toLocaleString()} images • ${percent}%`;
}

batchInput.addEventListener("change", () => {
    const files = Array.from(batchInput.files || []);
    if (!files.length) {
        batchFileName.textContent = "Select images or an entire folder";
        batchButton.disabled = true;
        return;
    }

    if (files.length > MAX_FILES) {
        batchFileName.textContent = `Too many files: ${files.length.toLocaleString()} (max ${MAX_FILES.toLocaleString()})`;
        batchButton.disabled = true;
        return;
    }

    const imageFiles = files.filter(file => file.type.startsWith("image/"));
    batchFileName.textContent = `${imageFiles.length.toLocaleString()} image(s) selected`;
    batchButton.disabled = imageFiles.length === 0;
});

async function processChunk(files) {
    const formData = new FormData();
    files.forEach(file => formData.append("files", file, file.name));

    let lastError = null;

    for (let attempt = 1; attempt <= 2; attempt++) {
        try {
            const response = await fetch(`${BATCH_API_BASE}/recognition/batch-verify`, {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || "Batch processing failed");
            }
            return data;
        } catch (error) {
            lastError = error;
            if (attempt === 1) {
                await new Promise(resolve => setTimeout(resolve, 1500));
            }
        }
    }

    throw lastError || new Error("Batch processing failed");
}

batchButton.addEventListener("click", async () => {
    const files = Array.from(batchInput.files || [])
        .filter(file => file.type.startsWith("image/"));

    if (!files.length) return;

    batchButton.disabled = true;
    batchButton.textContent = "Processing...";
    batchProgress.value = 0;
    setProgress(0, files.length);

    showBatchResult(
        "High-volume recognition started",
        "Images are processed in safe chunks. Keep this tab open until completion."
    );

    let processed = 0;
    let matched = 0;
    let unknown = 0;
    let faces = 0;
    let events = 0;
    let failedChunks = 0;
    const started = performance.now();

    try {
        for (let start = 0; start < files.length; start += BATCH_SIZE) {
            const chunk = files.slice(start, start + BATCH_SIZE);
            const data = await processChunk(chunk);

            processed += chunk.length;
            matched += Number(data.matched_faces || 0);
            unknown += Number(data.unknown_faces || 0);
            faces += Number(data.faces_detected || 0);
            events += Number(data.events_saved || 0);

            setProgress(processed, files.length);
            showBatchResult(
                `Processing ${Math.round((processed / files.length) * 100)}%`,
                `${processed.toLocaleString()} images • ${faces.toLocaleString()} faces • ` +
                `${matched.toLocaleString()} matched • ${unknown.toLocaleString()} unknown`
            );
        }

        const elapsed = Math.max((performance.now() - started) / 1000, 0.001);
        const rate = files.length / elapsed;

        showBatchResult(
            "Batch completed",
            `${files.length.toLocaleString()} images processed in ${elapsed.toFixed(1)} seconds.<br>` +
            `${faces.toLocaleString()} faces • ${matched.toLocaleString()} matched • ` +
            `${unknown.toLocaleString()} unknown • ${events.toLocaleString()} events saved.<br>` +
            `Average upload/processing throughput: ${rate.toFixed(1)} images/sec.`,
            "success"
        );
    } catch (error) {
        failedChunks += 1;
        showBatchResult(
            "Batch stopped",
            `${processed.toLocaleString()} of ${files.length.toLocaleString()} images completed. ` +
            `You can retry the remaining set. ${error.message}`,
            "error"
        );
    } finally {
        batchButton.disabled = false;
        batchButton.textContent = "Process Images & Mark Attendance";
    }
});
