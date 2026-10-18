/* ==========================================================================
   SecureCloud – Client-Side Application Logic
   Features:
   - Full backward compatibility with FastAPI endpoints (/upload, /files, /download, DELETE)
   - Outcrowd signature "explode" hover cursor tracking
   - Dynamic mouse-tracking card spotlight glow
   - Drag & drop zone with file preview
   - Live backend health monitoring
   - Real-time search filter and 1-click SHA-256 copy
   ========================================================================== */

const API_BASE_URL = "http://127.0.0.1:8000"; // change if server runs elsewhere

// Required DOM references
const fileInput = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");
const progressWrapper = document.getElementById("progress-wrapper");
const progressBar = document.getElementById("upload-progress");
const progressText = document.getElementById("progress-text");
const progressStageText = document.getElementById("progress-stage-text");
const uploadMsg = document.getElementById("upload-msg");
const filesTableBody = document.querySelector("#files-table tbody");
const filesMsg = document.getElementById("files-msg");

// Outcrowd Interactive Enhancements
const dropZone = document.getElementById("drop-zone");
const dropzoneIdleState = document.getElementById("dropzone-idle-state");
const filePreviewCard = document.getElementById("file-preview-card");
const previewFilename = document.getElementById("preview-filename");
const previewDetails = document.getElementById("preview-details");
const clearFileBtn = document.getElementById("clear-file-btn");
const fileSearchInput = document.getElementById("file-search-input");
const refreshFilesBtn = document.getElementById("refresh-files-btn");
const toastContainer = document.getElementById("toast-container");
const backendStatusBadge = document.getElementById("backend-status-badge");
const statusLabel = document.getElementById("status-label");

// Local cache for search filtering
let cachedFilesList = [];

// ==========================================================================
// 1. Outcrowd Explode Button Effect
// ==========================================================================
function initExplodeButtons() {
    document.querySelectorAll(".outcrowd-btn").forEach(button => {
        let explode = button.querySelector(".explode");
        if (!explode) {
            explode = document.createElement("div");
            explode.className = "explode violet";
            button.appendChild(explode);
        }

        button.addEventListener("mousemove", (e) => {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            explode.style.left = `${x}px`;
            explode.style.top = `${y}px`;
            explode.style.transform = "translate(-50%, -50%) scale(25)";
        });

        button.addEventListener("mouseleave", () => {
            explode.style.transform = "translate(-50%, -50%) scale(0)";
        });
    });
}

// ==========================================================================
// 2. Outcrowd Card Spotlight Glow (Mouse Tracking)
// ==========================================================================
function initCardGlow() {
    const cards = document.querySelectorAll(".card-glow");
    document.addEventListener("mousemove", (e) => {
        cards.forEach(card => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty("--mouse-x", `${x}px`);
            card.style.setProperty("--mouse-y", `${y}px`);
        });
    });
}

// ==========================================================================
// 3. Modern Toast System
// ==========================================================================
function showToast(message, type = "success") {
    if (!toastContainer) return;
    const toast = document.createElement("div");
    toast.className = `modern-toast toast-${type}`;
    
    const iconSvg = type === "success" 
        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="toast-icon"><polyline points="20 6 9 17 4 12"/></svg>`
        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="toast-icon"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;

    toast.innerHTML = `${iconSvg}<span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "toastOut 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards";
        setTimeout(() => toast.remove(), 350);
    }, 3500);
}

// ==========================================================================
// 4. File Selection & Drag & Drop Handling
// ==========================================================================
function handleFileSelection(file) {
    if (!file) {
        uploadBtn.disabled = true;
        dropzoneIdleState.classList.remove("hidden");
        filePreviewCard.classList.add("hidden");
        uploadMsg.textContent = "";
        return;
    }

    uploadBtn.disabled = false;
    uploadMsg.textContent = "";
    dropzoneIdleState.classList.add("hidden");
    filePreviewCard.classList.remove("hidden");

    previewFilename.textContent = file.name;
    const estimatedBlocks = Math.ceil(file.size / (1024 * 1024)) || 1;
    previewDetails.textContent = `${formatBytes(file.size)} • Estimated ${estimatedBlocks} block${estimatedBlocks > 1 ? "s" : ""} (AES-256)`;
}

// Standard file input change
fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    handleFileSelection(file);
});

// Dropzone click triggers file picker
if (dropZone) {
    dropZone.addEventListener("click", (e) => {
        if (e.target.closest("#clear-file-btn")) return;
        fileInput.click();
    });

    // Drag & Drop events
    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
        });
    });

    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length) {
            fileInput.files = dt.files;
            handleFileSelection(dt.files[0]);
        }
    });
}

// Clear selected file
if (clearFileBtn) {
    clearFileBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.value = "";
        handleFileSelection(null);
    });
}

// ==========================================================================
// 5. Upload Handler
// ==========================================================================
uploadBtn.addEventListener("click", async () => {
    const file = fileInput.files[0];
    if (!file) return;

    uploadBtn.disabled = true;
    progressWrapper.classList.remove("hidden");
    progressBar.value = 15;
    progressText.textContent = "15%";
    if (progressStageText) progressStageText.textContent = "Partitioning 1 MiB blocks...";

    const form = new FormData();
    form.append("file", file);

    // Simulated progressive stage animation for smooth UX
    const stageTimer1 = setTimeout(() => {
        progressBar.value = 45;
        progressText.textContent = "45%";
        if (progressStageText) progressStageText.textContent = "Sealing chunks with AES-256-GCM...";
    }, 200);

    const stageTimer2 = setTimeout(() => {
        progressBar.value = 75;
        progressText.textContent = "75%";
        if (progressStageText) progressStageText.textContent = "Dispatching to Amazon S3 bucket...";
    }, 450);

    try {
        const resp = await fetch(`${API_BASE_URL}/upload`, {
            method: "POST",
            body: form,
        });

        clearTimeout(stageTimer1);
        clearTimeout(stageTimer2);

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: "Upload failed" }));
            throw new Error(err.detail || "Upload failed");
        }

        const data = await resp.json();
        progressBar.value = 100;
        progressText.textContent = "100%";
        if (progressStageText) progressStageText.textContent = "Cryptographic manifest verified!";

        uploadMsg.style.color = "#10b981";
        uploadMsg.textContent = `Successfully encrypted & uploaded: ${data.filename}`;
        showToast(`Stored ${data.filename} (${formatBytes(data.file_size || file.size)}) securely!`, "success");

        // Reset file selection
        fileInput.value = "";
        handleFileSelection(null);

        // Refresh file list
        await loadFiles();
    } catch (e) {
        clearTimeout(stageTimer1);
        clearTimeout(stageTimer2);
        uploadMsg.style.color = "#f43f5e";
        uploadMsg.textContent = e.message;
        showToast(e.message, "error");
    } finally {
        setTimeout(() => {
            progressWrapper.classList.add("hidden");
            uploadBtn.disabled = !fileInput.files.length;
        }, 1200);
    }
});

// ==========================================================================
// 6. Load & Render Files List
// ==========================================================================
async function loadFiles() {
    filesTableBody.innerHTML = "";
    filesMsg.textContent = "";

    try {
        const resp = await fetch(`${API_BASE_URL}/files`);
        if (!resp.ok) throw new Error("Failed to fetch file list");
        const files = await resp.json();
        cachedFilesList = files;

        renderFilesTable(files);
    } catch (e) {
        filesMsg.style.color = "#f43f5e";
        filesMsg.innerHTML = `
            <div class="empty-vault-state">
                <div class="empty-vault-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                </div>
                <div class="empty-vault-title">Unable to reach cloud storage</div>
                <div class="empty-vault-desc">${e.message}</div>
            </div>
        `;
    }
}

function renderFilesTable(files) {
    filesTableBody.innerHTML = "";

    if (!files.length) {
        filesMsg.innerHTML = `
            <div class="empty-vault-state">
                <div class="empty-vault-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                </div>
                <div class="empty-vault-title">Vault is empty</div>
                <div class="empty-vault-desc">No encrypted artifacts detected in storage. Upload a file above to initiate segmented AES-256 cloud storage.</div>
            </div>
        `;
        return;
    }

    filesMsg.innerHTML = "";

    files.forEach(f => {
        const tr = document.createElement("tr");
        const fileExt = f.filename.split('.').pop().toLowerCase();
        const shortHash = f.sha256 ? f.sha256.slice(0, 10) : "N/A";

        tr.innerHTML = `
            <td>
                <div class="file-cell-name">
                    <div class="file-type-icon">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
                            <polyline points="13 2 13 9 20 9"/>
                        </svg>
                    </div>
                    <span>${escapeHtml(f.filename)}</span>
                </div>
            </td>
            <td><span class="badge-pill">${formatBytes(f.file_size)}</span></td>
            <td><span class="badge-pill badge-blocks">${f.block_count} Block${f.block_count > 1 ? "s" : ""}</span></td>
            <td>${new Date(f.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</td>
            <td>
                <button type="button" class="sha256-chip" title="Click to copy full SHA-256 hash" data-hash="${f.sha256}">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                    <span>${shortHash}…</span>
                </button>
            </td>
            <td>
                <div class="table-actions">
                    <button class="action-btn" data-id="${f.file_id}" data-action="download" title="Reconstruct and download">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="7 10 12 15 17 10"/>
                            <line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                        Download
                    </button>
                    <button class="action-btn delete" data-id="${f.file_id}" data-action="delete" title="Delete blocks, manifest and key">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                        Delete
                    </button>
                </div>
            </td>
        `;
        filesTableBody.appendChild(tr);
    });

    // Attach click handlers for actions
    attachTableHandlers();
}

function attachTableHandlers() {
    // Action buttons (download & delete)
    filesTableBody.querySelectorAll(".action-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            const targetBtn = e.currentTarget;
            const id = targetBtn.dataset.id;
            const act = targetBtn.dataset.action;

            if (act === "download") {
                showToast("Reconstructing file and decrypting AES-256 blocks...", "success");
                window.location = `${API_BASE_URL}/files/${id}/download`;
            } else if (act === "delete") {
                if (!confirm("Are you sure you want to delete this file? All encrypted blocks, S3 manifests, and local keys will be purged.")) {
                    return;
                }
                try {
                    const resp = await fetch(`${API_BASE_URL}/files/${id}`, { method: "DELETE" });
                    if (!resp.ok) throw new Error("Delete failed");
                    showToast("File and cryptographic assets purged.", "success");
                    await loadFiles();
                } catch (err) {
                    showToast(err.message, "error");
                }
            }
        });
    });

    // Copy SHA-256 checksum to clipboard
    filesTableBody.querySelectorAll(".sha256-chip").forEach(chip => {
        chip.addEventListener("click", async (e) => {
            e.stopPropagation();
            const hash = chip.dataset.hash;
            if (!hash) return;
            try {
                await navigator.clipboard.writeText(hash);
                const originalText = chip.innerHTML;
                chip.innerHTML = `<span>Copied!</span>`;
                setTimeout(() => chip.innerHTML = originalText, 1500);
            } catch (err) {
                showToast("SHA-256: " + hash, "success");
            }
        });
    });
}

// ==========================================================================
// 7. Search & Filter
// ==========================================================================
if (fileSearchInput) {
    fileSearchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        if (!query) {
            renderFilesTable(cachedFilesList);
            return;
        }

        const filtered = cachedFilesList.filter(f => 
            f.filename.toLowerCase().includes(query) ||
            (f.sha256 && f.sha256.toLowerCase().includes(query))
        );
        renderFilesTable(filtered);
    });
}

if (refreshFilesBtn) {
    refreshFilesBtn.addEventListener("click", () => {
        loadFiles();
        showToast("Vault registry refreshed.", "success");
    });
}

// ==========================================================================
// 8. Live Health Check
// ==========================================================================
async function checkBackendHealth() {
    if (!backendStatusBadge || !statusLabel) return;
    try {
        const res = await fetch(`${API_BASE_URL}/health`, { method: "GET" });
        if (res.ok) {
            backendStatusBadge.className = "status-pill status-online";
            statusLabel.textContent = "S3 Vault Active";
        } else {
            backendStatusBadge.className = "status-pill status-checking";
            statusLabel.textContent = "API Status: Warning";
        }
    } catch (err) {
        backendStatusBadge.className = "status-pill status-offline";
        statusLabel.textContent = "Vault Server Offline";
    }
}

// ==========================================================================
// Helper Utilities
// ==========================================================================
function formatBytes(b) {
    if (b === 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    let i = 0;
    while (b >= 1024 && i < units.length - 1) {
        b /= 1024;
        i++;
    }
    return `${b.toFixed(1)} ${units[i]}`;
}

function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ==========================================================================
// Initialization
// ==========================================================================
initExplodeButtons();
initCardGlow();
checkBackendHealth();
loadFiles();

// Re-check health every 30s
setInterval(checkBackendHealth, 30000);
