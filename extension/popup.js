document.addEventListener('DOMContentLoaded', function () {
    const extractBtn = document.getElementById('extractBtn');
    const sendBtn = document.getElementById('sendBtn');
    const input = document.getElementById('input');
    const responseDiv = document.getElementById('response');
    const loader = document.getElementById('loader');

    // API URL - Change this to your Cloud Run URL after deployment
    const API_URL = "http://localhost:8000/api/v1/run";

    extractBtn.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (tab.url.includes("mail.google.com")) {
            chrome.tabs.sendMessage(tab.id, { action: "extract_email" }, (response) => {
                if (response && response.text) {
                    input.value = response.text;
                } else {
                    input.value = "Could not extract email content. Please copy manually.";
                }
            });
        } else {
            input.value = "Not on Gmail. Please copy text manually.";
        }
    });

    sendBtn.addEventListener('click', async () => {
        const text = input.value.trim();
        if (!text) return;

        responseDiv.style.display = 'none';
        loader.style.display = 'block';
        sendBtn.disabled = true;

        try {
            const res = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    customer_id: "EXT_USER",
                    source: "extension"
                })
            });

            const data = await res.json();
            loader.style.display = 'none';
            responseDiv.style.display = 'block';

            if (data.ok) {
                // demo_api returns data directly, not nested in result.payload
                responseDiv.textContent = JSON.stringify(data, null, 2);
            } else {
                responseDiv.textContent = "Error: " + (data.error || "Unknown error");
            }
        } catch (error) {
            loader.style.display = 'none';
            responseDiv.style.display = 'block';
            responseDiv.textContent = "Network Error: " + error.message + "\nMake sure the API server is running.";
        } finally {
            sendBtn.disabled = false;
        }
    });
});
