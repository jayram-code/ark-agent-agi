document.getElementById("btnSave").onclick = () => {
    const apiUrl = document.getElementById("apiUrl").value.trim();
    const apiKey = document.getElementById("apiKey").value.trim();
    chrome.storage.sync.set({ apiUrl, apiKey }, () => {
        document.getElementById("status").textContent = "Saved.";
    });
};
document.getElementById("btnTest").onclick = async () => {
    const apiUrl = document.getElementById("apiUrl").value.trim();
    const apiKey = document.getElementById("apiKey").value.trim();
    try {
        const r = await fetch(apiUrl + "/api/v1/ping", { headers: { "Authorization": `Bearer ${apiKey}` } });
        const j = await r.json();
        document.getElementById("status").textContent = "OK: " + j.msg;
    } catch (e) {
        document.getElementById("status").textContent = "Test failed: " + e.message;
    }
};
// load saved
chrome.storage.sync.get(["apiUrl", "apiKey"], (res) => {
    document.getElementById("apiUrl").value = res.apiUrl || "";
    document.getElementById("apiKey").value = res.apiKey || "";
});
