// background.js
chrome.runtime.onInstalled.addListener(() => {
    console.log("ARK background installed");
});

chrome.alarms.onAlarm.addListener(alarm => {
    if (alarm.name.startsWith("poll:")) {
        const jobId = alarm.name.split(":")[1];
        // message popup or handle background poll if required
        console.log("poll alarm for job", jobId);
    }
});
