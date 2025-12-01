// popup.js - ARK Enterprise Client Logic

// Helpers
async function getConfig() {
    return new Promise(resolve => {
        chrome.storage.sync.get(["apiUrl", "apiKey"], (items) => {
            resolve({ apiUrl: items.apiUrl || "http://localhost:8000", apiKey: items.apiKey || "" });
        });
    });
}

function setTab(tab) {
    document.getElementById("single-view").classList.add("hidden");
    document.getElementById("batch-view").classList.add("hidden");
    document.getElementById("history-view").classList.add("hidden");

    document.getElementById(tab + "-view").classList.remove("hidden");

    ["tab-single", "tab-batch", "tab-history"].forEach(id => document.getElementById(id).classList.remove("active"));
    document.getElementById("tab-" + tab).classList.add("active");
}

document.getElementById("tab-single").onclick = () => setTab("single");
document.getElementById("tab-batch").onclick = () => setTab("batch");
document.getElementById("tab-history").onclick = () => { setTab("history"); loadHistory(); };

// UI Helpers
function showResult(html) {
    const el = document.getElementById("single-result");
    el.innerHTML = html;
    el.classList.remove("hidden");
}

// Single Analysis
document.getElementById("btn-analyze").onclick = async () => {
    const btn = document.getElementById("btn-analyze");
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    btn.disabled = true;

    const text = document.getElementById("email-text").value.trim();
    if (!text) {
        alert("Please enter text to analyze");
        btn.innerHTML = originalText;
        btn.disabled = false;
        return;
    }

    const cfg = await getConfig();
    try {
        const r = await fetch(cfg.apiUrl + "/api/v1/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${cfg.apiKey}` },
            body: JSON.stringify({ text, route: document.getElementById("quick-route").value })
        });
        const j = await r.json();

        if (!j.ok) {
            throw new Error(j.error || "Unknown backend error");
        }

        // Render Result
        const urgencyColor = j.urgency === 'high' || j.urgency === 'critical' ? 'badge-red' : (j.urgency === 'medium' ? 'badge-blue' : 'badge-green');

        showResult(`
            <div class="result-header">
                <span class="badge ${urgencyColor}">${(j.intent || 'Unknown').replace('_', ' ')}</span>
                <span class="text-xs text-muted">${Math.round((j.confidence || 0) * 100)}% Match</span>
            </div>
            <div class="text-sm" style="margin-bottom:16px; line-height:1.5">${j.rationale || 'Analysis complete.'}</div>
            <button id="btn-create-ticket" class="btn btn-secondary">
                <i class="fa-solid fa-ticket"></i> Create Support Ticket
            </button>
        `);

        // Attach ticket handler
        document.getElementById("btn-create-ticket").onclick = () => createTicket(j);

        saveHistory({ type: "analysis", item: j, ts: Date.now() });
    } catch (e) {
        showResult(`<div class="text-sm" style="color:#F87171">Error: ${e.message}</div>`);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
};

async function createTicket(obj) {
    const cfg = await getConfig();
    const payload = { title: `${obj.intent}`, body: obj.rationale || '', tags: [obj.intent] };
    try {
        const r = await fetch(cfg.apiUrl + "/api/v1/tickets", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${cfg.apiKey}` },
            body: JSON.stringify(payload)
        });
        const j = await r.json();
        alert(`Ticket #${j.ticket_id} created!`);
    } catch (e) {
        alert("Failed to create ticket: " + e.message);
    }
}

// Gmail Extraction
document.getElementById("btn-extract").onclick = async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => {
                const el = document.querySelector("div[role='main'] .ii.gt");
                return el ? el.innerText : "";
            }
        }, (res) => {
            const text = res && res[0] && res[0].result ? res[0].result : "";
            if (text) document.getElementById("email-text").value = text;
            else alert("No email content found. Open an email in Gmail.");
        });
    } catch (e) {
        alert("Extraction failed: " + e.message);
    }
};

// Batch Scan
document.getElementById("btn-scan").onclick = async () => {
    const cfg = await getConfig();
    document.getElementById("batch-progress-container").classList.remove("hidden");

    try {
        const r = await fetch(cfg.apiUrl + "/api/v1/batch", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${cfg.apiKey}` },
            body: JSON.stringify({ take: 200 })
        });
        const j = await r.json();
        if (j.job_id) pollJob(j.job_id);
        else throw new Error("No job ID returned");
    } catch (e) {
        alert("Batch start failed: " + e.message);
    }
};

// CSV Upload Handling
document.getElementById("csv-file").onchange = function () {
    if (this.files.length > 0) {
        document.getElementById("btn-upload").classList.remove("hidden");
        document.getElementById("btn-upload").textContent = `Process ${this.files[0].name}`;
    }
};

document.getElementById("btn-upload").onclick = async () => {
    const f = document.getElementById("csv-file").files[0];
    if (!f) return;

    const text = await f.text();
    const rows = text.split("\n").map(r => r.trim()).filter(Boolean);
    const cfg = await getConfig();

    document.getElementById("batch-progress-container").classList.remove("hidden");

    try {
        const r = await fetch(cfg.apiUrl + "/api/v1/batch", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${cfg.apiKey}` },
            body: JSON.stringify({ emails: rows })
        });
        const j = await r.json();
        if (j.job_id) pollJob(j.job_id);
    } catch (e) {
        alert("Upload failed: " + e.message);
    }
};

async function pollJob(jobId) {
    const cfg = await getConfig();
    const bar = document.getElementById("progress-bar");
    const txt = document.getElementById("progress-text");
    const status = document.getElementById("batch-status");

    const poll = async () => {
        try {
            const r = await fetch(cfg.apiUrl + "/api/v1/jobs/" + jobId, { headers: { "Authorization": `Bearer ${cfg.apiKey}` } });
            const j = await r.json();
            const p = j.progress || 0;

            bar.style.width = p + "%";
            txt.textContent = p + "%";
            status.textContent = `Processed ${j.processed || 0} / ${j.total || '?'}`;

            if (j.status === "completed") {
                status.textContent = "✅ Complete";
                status.style.color = "#4ADE80";
                saveHistory({ type: "batch_completed", summary: j.summary || {}, ts: Date.now() });
            } else if (j.status === "failed") {
                status.textContent = "❌ Failed";
                status.style.color = "#F87171";
            } else {
                setTimeout(poll, 1000);
            }
        } catch (e) {
            setTimeout(poll, 3000);
        }
    };
    poll();
}

// History
function saveHistory(item) {
    chrome.storage.local.get(["history"], (res) => {
        const h = res.history || [];
        h.unshift(item);
        chrome.storage.local.set({ history: h.slice(0, 50) });
    });
}

function loadHistory() {
    chrome.storage.local.get(["history"], (res) => {
        const list = document.getElementById("history-list");
        list.innerHTML = "";
        (res.history || []).forEach(h => {
            const date = new Date(h.ts).toLocaleTimeString();
            let content = "";

            if (h.type === "analysis") {
                content = `<div><span class="badge badge-blue">${h.item.intent}</span></div>`;
            } else if (h.type === "batch_completed") {
                content = `<div><span class="badge badge-green">Batch Complete</span></div>`;
            }

            list.innerHTML += `
                <div style="padding:12px; border-bottom:1px solid #333">
                    <div class="stat-row">
                        <span style="font-weight:600; font-size:12px">${h.type.toUpperCase().replace('_', ' ')}</span>
                        <span class="text-muted text-xs">${date}</span>
                    </div>
                    ${content}
                </div>
            `;
        });
    });
}

// Init
setTab("single");
