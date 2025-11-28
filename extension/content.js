// ARK Enterprise - Gmail Content Script
// Handles email extraction for the extension

(function () {
    'use strict';

    // Listen for messages from popup and background script
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === "extract_email") {
            const emailBody = extractEmailBody();
            sendResponse({ text: emailBody });
        }
    });

    function extractEmailBody() {
        // Try to find the open email body in Gmail
        const bodies = document.querySelectorAll('.a3s.aiL');

        if (bodies.length > 0) {
            // Get the last one (usually the most recent open message in a thread)
            const lastBody = bodies[bodies.length - 1];
            return lastBody.innerText;
        }

        // Fallback: Try to get selected text
        const selection = window.getSelection().toString();
        if (selection) return selection;

        return "No email body found. Please select text or open an email.";
    }
})();
