chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "REQUEST_DATA") {
        console.log("Message received in YouTube tab");
        sendResponse({ status: "Received" });
    }
});
