/**
 * AI Resume Screener — Frontend Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // DOM Elements
    const form = document.getElementById("analyzerForm");
    const jdTextarea = document.getElementById("jobDescription");
    const jdCharCount = document.getElementById("jdCharCount");
    const uploadZone = document.getElementById("uploadZone");
    const fileInput = document.getElementById("resumeFiles");
    const fileList = document.getElementById("fileList");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const clearBtn = document.getElementById("clearBtn");
    const loadingOverlay = document.getElementById("loadingOverlay");
    const resultsSection = document.getElementById("results");
    const resultsSummary = document.getElementById("resultsSummary");
    const jdSkillsTags = document.getElementById("jdSkillsTags");
    const resultsList = document.getElementById("resultsList");

    // Track selected files (DataTransfer to manage file list)
    let selectedFiles = [];

    // ── Character count ──
    jdTextarea.addEventListener("input", () => {
        const count = jdTextarea.value.length;
        jdCharCount.textContent = `${count.toLocaleString()} characters`;
    });

    // ── Drag and Drop ──
    const preventDefaults = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    ["dragenter", "dragover", "dragleave", "drop"].forEach((event) => {
        uploadZone.addEventListener(event, preventDefaults);
    });

    ["dragenter", "dragover"].forEach((event) => {
        uploadZone.addEventListener(event, () => uploadZone.classList.add("dragover"));
    });

    ["dragleave", "drop"].forEach((event) => {
        uploadZone.addEventListener(event, () => uploadZone.classList.remove("dragover"));
    });

    uploadZone.addEventListener("drop", (e) => {
        const files = Array.from(e.dataTransfer.files);
        addFiles(files);
    });

    fileInput.addEventListener("change", () => {
        const files = Array.from(fileInput.files);
        addFiles(files);
    });

    function addFiles(files) {
        const allowedExtensions = ["pdf", "docx", "doc", "txt"];
        files.forEach((file) => {
            const ext = file.name.split(".").pop().toLowerCase();
            if (allowedExtensions.includes(ext)) {
                // Avoid duplicates
                if (!selectedFiles.some((f) => f.name === file.name && f.size === file.size)) {
                    selectedFiles.push(file);
                }
            }
        });
        renderFileList();
    }

    function renderFileList() {
        fileList.innerHTML = "";
        selectedFiles.forEach((file, index) => {
            const item = document.createElement("div");
            item.className = "file-item";
            item.style.animationDelay = `${index * 0.05}s`;

            const sizeKB = (file.size / 1024).toFixed(1);
            const ext = file.name.split(".").pop().toUpperCase();

            item.innerHTML = `
                <div class="file-item-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2" stroke-linecap="round"
                         stroke-linejoin="round">
                        <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
                        <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
                    </svg>
                </div>
                <span class="file-item-name" title="${file.name}">${file.name}</span>
                <span class="file-item-size">${ext} · ${sizeKB} KB</span>
                <button type="button" class="file-item-remove" data-index="${index}" title="Remove file">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2" stroke-linecap="round"
                         stroke-linejoin="round">
                        <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                    </svg>
                </button>
            `;
            fileList.appendChild(item);
        });

        // Remove handlers
        fileList.querySelectorAll(".file-item-remove").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                const idx = parseInt(btn.dataset.index, 10);
                selectedFiles.splice(idx, 1);
                renderFileList();
            });
        });
    }

    // ── Clear All ──
    clearBtn.addEventListener("click", () => {
        jdTextarea.value = "";
        jdCharCount.textContent = "0 characters";
        selectedFiles = [];
        fileList.innerHTML = "";
        fileInput.value = "";
        resultsSection.style.display = "none";
    });

    // ── Form Submit ──
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const jobDescription = jdTextarea.value.trim();
        if (!jobDescription) {
            showToast("Please enter a job description.", "error");
            return;
        }

        if (selectedFiles.length === 0) {
            showToast("Please upload at least one resume.", "error");
            return;
        }

        // Build FormData
        const formData = new FormData();
        formData.append("job_description", jobDescription);
        selectedFiles.forEach((file) => {
            formData.append("resumes", file);
        });

        // Show loading
        loadingOverlay.classList.add("active");
        analyzeBtn.classList.add("loading");

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(data.error || "Something went wrong.");
            }

            renderResults(data);
            showToast(`Successfully ranked ${data.total_resumes} resume(s)!`, "success");

        } catch (err) {
            showToast(err.message, "error");
        } finally {
            loadingOverlay.classList.remove("active");
            analyzeBtn.classList.remove("loading");
        }
    });

    // ── Render Results ──
    function renderResults(data) {
        resultsSection.style.display = "block";

        // Summary
        resultsSummary.textContent = `${data.total_resumes} resume(s) analyzed and ranked against the job description`;

        // JD Skills Tags
        jdSkillsTags.innerHTML = "";
        data.jd_skills.forEach((skill) => {
            const tag = document.createElement("span");
            tag.className = "skill-tag skill-tag-jd";
            tag.textContent = skill;
            jdSkillsTags.appendChild(tag);
        });

        if (data.jd_skills.length === 0) {
            jdSkillsTags.innerHTML = '<span style="color:var(--text-muted); font-size:0.85rem;">No specific skills detected in the job description.</span>';
        }

        // Result Cards
        resultsList.innerHTML = "";
        data.results.forEach((result, idx) => {
            const card = createResultCard(result, idx);
            resultsList.appendChild(card);
        });

        // Re-init lucide for new elements
        if (window.lucide) lucide.createIcons();

        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 300);
    }

    function createResultCard(result, idx) {
        const card = document.createElement("div");
        card.className = "result-card";
        card.style.animationDelay = `${idx * 0.1}s`;

        // Rank badge class
        let rankClass = "rank-default";
        if (result.rank === 1) rankClass = "rank-1";
        else if (result.rank === 2) rankClass = "rank-2";
        else if (result.rank === 3) rankClass = "rank-3";

        // Score color
        const scoreColor = getScoreColor(result.overall_score);

        // Circumference for SVG circle (radius 34)
        const circumference = 2 * Math.PI * 34;
        const offset = circumference - (result.overall_score / 100) * circumference;

        card.innerHTML = `
            <div class="result-card-header">
                <div class="result-rank">
                    <div class="rank-badge ${rankClass}">#${result.rank}</div>
                    <div class="candidate-info">
                        <h3>${escapeHTML(result.name)}</h3>
                        <div class="candidate-meta">
                            <span>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                                     stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                     stroke-linejoin="round">
                                    <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
                                    <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
                                </svg>
                                ${escapeHTML(result.filename)}
                            </span>
                            ${result.email ? `<span>✉ ${escapeHTML(result.email)}</span>` : ""}
                            ${result.experience_years !== null ? `<span>📅 ${result.experience_years}+ yrs</span>` : ""}
                            ${result.education.length > 0 ? `<span>🎓 ${result.education.slice(0, 2).join(", ")}</span>` : ""}
                        </div>
                    </div>
                </div>
                <div class="result-scores">
                    <div class="score-circle">
                        <svg viewBox="0 0 76 76">
                            <circle class="score-circle-bg" cx="38" cy="38" r="34"/>
                            <circle class="score-circle-fill" cx="38" cy="38" r="34"
                                    stroke="${scoreColor}"
                                    stroke-dasharray="${circumference}"
                                    stroke-dashoffset="${offset}"/>
                        </svg>
                        <div class="score-circle-text">
                            <span class="score-value" style="color:${scoreColor}">${result.overall_score}%</span>
                            <span class="score-label">Overall</span>
                        </div>
                    </div>
                    <div class="score-mini">
                        <div class="score-mini-value" style="color:${getScoreColor(result.skill_score)}">${result.skill_score}%</div>
                        <div class="score-mini-label">Skill Match</div>
                    </div>
                    <div class="score-mini">
                        <div class="score-mini-value" style="color:${getScoreColor(result.tfidf_score)}">${result.tfidf_score}%</div>
                        <div class="score-mini-label">Content</div>
                    </div>
                </div>
            </div>

            <div class="result-card-body">
                ${result.skills_matched.length > 0 ? `
                <div class="detail-section">
                    <div class="detail-section-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                             stroke="var(--success)" stroke-width="2" stroke-linecap="round"
                             stroke-linejoin="round">
                            <path d="M20 6 9 17l-5-5"/>
                        </svg>
                        Matched Skills (${result.skills_matched.length})
                    </div>
                    <div class="skills-tags">
                        ${result.skills_matched.map((s) => `<span class="skill-tag skill-tag-matched">✓ ${s}</span>`).join("")}
                    </div>
                </div>` : ""}

                ${result.skills_missing.length > 0 ? `
                <div class="detail-section">
                    <div class="detail-section-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                             stroke="var(--danger)" stroke-width="2" stroke-linecap="round"
                             stroke-linejoin="round">
                            <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                        </svg>
                        Missing Skills (${result.skills_missing.length})
                    </div>
                    <div class="skills-tags">
                        ${result.skills_missing.map((s) => `<span class="skill-tag skill-tag-missing">✗ ${s}</span>`).join("")}
                    </div>
                </div>` : ""}

                ${result.skills_extra.length > 0 ? `
                <div class="detail-section">
                    <div class="detail-section-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                             stroke="var(--info)" stroke-width="2" stroke-linecap="round"
                             stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
                        </svg>
                        Additional Skills
                    </div>
                    <div class="skills-tags">
                        ${result.skills_extra.map((s) => `<span class="skill-tag skill-tag-extra">+ ${s}</span>`).join("")}
                    </div>
                </div>` : ""}

                <div class="detail-section">
                    <div class="detail-section-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                             stroke="var(--warning)" stroke-width="2" stroke-linecap="round"
                             stroke-linejoin="round">
                            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                        </svg>
                        Improvement Suggestions
                    </div>
                    <ul class="suggestion-list">
                        ${result.suggestions.map((s) => `<li class="suggestion-item">${formatSuggestion(s)}</li>`).join("")}
                    </ul>
                </div>
            </div>

            <button type="button" class="result-toggle" onclick="toggleCard(this)">
                <span>View Details</span>
                <svg class="toggle-icon" width="16" height="16" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="2" stroke-linecap="round"
                     stroke-linejoin="round">
                    <path d="m6 9 6 6 6-6"/>
                </svg>
            </button>
        `;

        return card;
    }

    // ── Helpers ──
    function getScoreColor(score) {
        if (score >= 70) return "var(--success)";
        if (score >= 40) return "var(--warning)";
        return "var(--danger)";
    }

    function escapeHTML(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function formatSuggestion(text) {
        // Convert **bold** to <strong>
        return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    }

    function showToast(message, type = "error") {
        // Remove existing toasts
        document.querySelectorAll(".toast").forEach((t) => t.remove());

        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round"
                 stroke-linejoin="round">
                ${type === "error"
                    ? '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>'
                    : '<path d="M20 6 9 17l-5-5"/>'
                }
            </svg>
            <span>${escapeHTML(message)}</span>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(30px)";
            toast.style.transition = "0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // ── Smooth scroll for anchor links ──
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute("href"));
            if (target) {
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });
});

// Global toggle function for result cards
function toggleCard(btn) {
    const card = btn.closest(".result-card");
    card.classList.toggle("expanded");
    const label = btn.querySelector("span");
    label.textContent = card.classList.contains("expanded") ? "Hide Details" : "View Details";
}
