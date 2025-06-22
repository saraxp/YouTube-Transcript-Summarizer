// background.js (service worker)

const FLASK_SERVER_URL = "http://localhost:5500"; // Ensure this matches your Flask server's address

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "SUMMARIZE_VIDEO") {
        const url = request.url;
        console.log("Background script received request to summarize URL:", url);

        fetch(`${FLASK_SERVER_URL}/summarize`, { // Ensure this matches your Flask route
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => {
            if (!response.ok) {
                // Log detailed error from server
                return response.text().then(text => {
                    throw new Error(`HTTP Error ${response.status}: ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("Summary data received from Flask:", data);
            // Send success message back to popup
            chrome.runtime.sendMessage({ type: "SUMMARY_RESULT", success: true, summary: data.summary, transcript: data.transcript });
            sendResponse({ status: "success" }); // Acknowledge message receipt
        })
        .catch(error => {
            console.error("Fetch error in background script:", error);
            // Send error message back to popup
            chrome.runtime.sendMessage({ type: "SUMMARY_RESULT", success: false, error: error.message || "Unknown error" });
            sendResponse({ status: "error", message: error.message }); // Acknowledge message receipt
        });

        // Return true to indicate that sendResponse will be called asynchronously
        return true;
    }
});