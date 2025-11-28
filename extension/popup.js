// popup.js - ARK extension front-end logic

// helpers
async function getConfig() {
    return new Promise(resolve => {
        chrome.storage.sync.get(["apiUrl", "apiKey"], (items) => {
            resolve({ apiUrl: items.apiUrl || "", apiKey: items.apiKey || "" });
        });
    });
}

function setTab(tab) {
    document.getElementById("single-view").style.display = tab === "single" ? "" : "none";
    document.getElementById("batch-view").style.display = tab === "batch" ? "" : "none";
    document.getElementById("history-view").style.display = tab === "history" ? "" : "none";
    ["tab-single", "tab-batch", "tab-history"].forEach(id => document.getElementById(id).classList.remove("active"));
    document.getElementById("tab-" + tab).classList.add("active");
}

document.getElementById("tab-single").onclick = () => setTab("single");
document.getElementById("tab-batch").onclick = () => setTab("batch");
document.getElementById("tab-history").onclick = () => { setTab("history"); loadHistory(); };

async function showSingleResult(obj) {
    const out = document.getElementById("single-result");
    out.innerHTML = `<div class="muted">Intent: <strong>${obj.intent}</strong> (${Math.round((obj.confidence || 0) * 100)}%)</div>
                   <div class="muted small" style="margin-top:8px">Rationale: ${obj.rationale || '—'}</div>
                   <div style="height:8px"></div>
                   <div><button id="btn-create-ticket">Create Ticket</button></div>`;
    document.getElementById("btn-create-ticket").onclick = async () => {
        const cfg = await getConfig();
        const payload = { title: `${obj.intent} - ${obj.entities?.order || ''}`, body: obj.summary || '', tags: [obj.intent] };
        try {
            const r = await fetch(cfg.apiUrl + "/api/v1/tickets", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${cfg.apiKey}` },
                body: JSON.stringify(payload)
            });
            const j = await r.json();
            alert("Ticket created: " + j.ticket_id);
            saveHistory({ type: "ticket_created", item: j, ts: Date.now() });
        } catch (e) {
            alert("Ticket create failed: " + e.message);
        }
    };
}

// save event to history (chrome.storage.local)
function saveHistory(item) {
    chrome.storage.local.get(["history"], (res) => {
        const h = res.history || [];
        h.unshift(item);
        chrome.storage.local.set({ history: h.slice(0, 200) });
    });
}

function loadHistory() {
    chrome.storage.local.get(["history"], (res) => {
        const list = document.getElementById("history-list");
        list.innerHTML = "";
        (res.history || []).forEach(h => {
            const d = new Date(h.ts || Date.now()).toLocaleString();
            list.innerHTML += `<div style="padding:8px;border-bottom:1px solid #0f2b3f"><div class="muted" style="font-size:12px">${d}</div><div>${JSON.stringify(h, null, 2)}</div></div>`;
        });
    });
}

// single analyze
document.getElementById("btn-analyze").onclick = async () => {
    const text = document.getElementById("email-text").value.trim();
    if (!text) return alert("Paste or extract email first.");
    const cfg = await getConfig();
    try {
        const r = await fetch(cfg.apiUrl + "/api/v1/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${cfg.apiKey}` },
            body: JSON.stringify({ text, route: document.getElementById("quick-route").value })
        });
        const j = await r.json();
        showSingleResult(j);
        saveHistory({ type: "analysis", item: j, ts: Date.now() });
    } catch (e) {
        alert("Analyze error: " + e.message);
    }
};

// extract from gmail (content script must be available)
document.getElementById("btn-extract").onclick = async () => {
    // send a message to content script to extract selected email
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => {
                // content script simple extraction
                const el = document.querySelector("div[role='main'] .ii.gt");
                return el ? el.innerText : "";
            }
        }, async (res) => {
            const text = res && res[0] && res[0].result ? res[0].result : "";
            if (text) document.getElementById("email-text").value = text;
            else alert("Could not extract email - open the email in Gmail and try again.");
        });
    } catch (e) {
        alert("Extract error: " + e.message);
    }
};

// BATCH: start scan
document.getElementById("btn-scan").onclick = async () => {
    const cfg = await getConfig();
    if (!cfg.apiUrl) return alert("Set API URL in Options first.");
    // call backend to start job
    try {
        const r = await fetch(cfg.apiUrl + "/api/v1/batch", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${cfg.apiKey}` },
            body: JSON.stringify({ take: 250 }) // ask backend to fetch last 250 emails
        });
        const j = await r.json();
        if (j.job_id) {
            document.getElementById("batch-status").textContent = "Job started: " + j.job_id;
            pollJob(j.job_id);
        } else {
            alert("Batch start failed");
        }
    } catch (e) {
        alert("Batch start error: " + e.message);
    }
};

// CSV upload
document.getElementById("btn-upload").onclick = async () => {
    const f = document.getElementById("csv-file").files[0];
    if (!f) return alert("Choose a CSV file first.");
    const text = await f.text();
    const rows = text.split("\n").map(r => r.trim()).filter(Boolean);
    const cfg = await getConfig();
    const r = await fetch(cfg.apiUrl + "/api/v1/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${cfg.apiKey}` },
        body: JSON.stringify({ emails: rows })
    });
    const j = await r.json();
    if (j.job_id) {
        document.getElementById("batch-status").textContent = "Job started: " + j.job_id;
        pollJob(j.job_id);
    } else alert("Batch upload failed");
};

// poll job status
async function pollJob(jobId) {
    const cfg = await getConfig();
    const progressBar = document.getElementById("progress-bar");
    const status = document.getElementById("batch-status");
    const poll = async () => {
        try {
            const r = await fetch(cfg.apiUrl + "/api/v1/jobs/" + jobId, { headers: { "Authorization": `Bearer ${cfg.apiKey}` } });
            const j = await r.json();
            const p = j.progress || 0;
            progressBar.style.width = Math.max(2, p) + "%";
            status.textContent = `Status: ${j.status || 'unknown'} — ${p}% — processed ${j.processed || 0}/${j.total || '?'}`
            if (j.status === "completed") {
                saveHistory({ type: "batch_completed", summary: j.summary || {}, ts: Date.now() });
                alert("Batch completed. See history tab for details.");
                return;
            } else if (j.status === "failed") {
                alert("Batch failed: " + (j.error || "unknown"));
                return;
            } else {
                setTimeout(poll, 1500);
            }
        } catch (e) {
            console.error("poll error", e);
            setTimeout(poll, 3000);
        }
    };
    poll();
}

// daily brief
document.getElementById("btn-daily").onclick = async () => {
    const cfg = await getConfig();
    try {
        const r = await fetch(cfg.apiUrl + "/api/v1/daily_brief", {
            method: "POST", headers: { "Authorization": `Bearer ${cfg.apiKey}` }
        });
        const j = await r.json();
        saveHistory({ type: "daily_brief", item: j, ts: Date.now() });
        alert("Daily brief generated — open History to view.");
    } catch (e) {
        alert("Daily brief error: " + e.message);
    }
};

// history exports
document.getElementById("btn-export-csv").onclick = () => {
    chrome.storage.local.get(["history"], (res) => {
        const rows = (res.history || []).map(h => `"${h.type}","${new Date(h.ts).toISOString()}","${JSON.stringify(h.item || h.summary || '')}"`);
        const blob = new Blob([rows.join("\n")], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url; a.download = "ark_history.csv"; a.click();
    });
};
document.getElementById("btn-export-json").onclick = () => {
    chrome.storage.local.get(["history"], (res) => {
        const blob = new Blob([JSON.stringify(res.history || [], null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url; a.download = "ark_history.json"; a.click();
    });
};
document.getElementById("btn-clear-history").onclick = () => {
    chrome.storage.local.set({ history: [] }, () => loadHistory());
};

// init
setTab("single");
