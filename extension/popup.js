// Elements
const btn = document.getElementById("summarise");
const copyButton = document.getElementById("copy-button");
const themeToggle = document.getElementById("theme-toggle");
const themeIcon = document.getElementById("theme-icon");
const popupContainer = document.getElementById("popup-container");
const popup = document.getElementById("body");
const toast = document.getElementById("toast");


// Summarize Button Event
btn.addEventListener("click", function() {
    btn.disabled = true;
    btn.innerHTML = "Summarizing...";

    chrome.tabs.query({ currentWindow: true, active: true }, function(tabs) {
        const url = tabs[0].url;

        if (!url.includes("youtube.com/watch")) { // Corrected URL
            alert("Please open a YouTube video tab to summarize.");
            btn.disabled = false;
            btn.innerHTML = "Summarize";
            return;
        }

        // Send a message to the background script to start the summarization
        chrome.runtime.sendMessage({ type: "SUMMARIZE_VIDEO", url: url }, function(response) {
            console.log("Message sent to background script:", response);
        });
    });
});

// Listener for messages from the background script (for summary results)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "SUMMARY_RESULT") {
        const summaryBox = document.getElementById("output");
        const errorBox = document.getElementById("error-box");
        const summarizeButton = document.getElementById("summarise");

        if (request.success) {
            summaryBox.style.display = "block";
            summaryBox.innerText = request.summary;
            errorBox.style.display = "none";
            summarizeButton.innerText = "Summarize";
        } else {
            errorBox.style.display = "flex";
            errorBox.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" viewBox="0 0 256 256"><path d="M236.8,188.09,149.35,36.22h0a24.76,24.76,0,0,0-42.7,0L19.2,188.09a23.51,23.51,0,0,0,0,23.72A24.35,24.35,0,0,0,40.55,224h174.9a24.35,24.35,0,0,0,21.33-12.19A23.51,23.51,0,0,0,236.8,188.09ZM222.93,203.8a8.5,8.5,0,0,1-7.48,4.2H40.55a8.5,8.5,0,0,1-7.48-4.2,7.59,7.59,0,0,1,0-7.72L120.52,44.21a8.75,8.75,0,0,1,15,0l87.45,151.87A7.59,7.59,0,0,1,222.93,203.8ZM120,144V104a8,8,0,0,1,16,0v40a8,8,0,0,1-16,0Zm20,36a12,12,0,1,1-12-12A12,12,0,0,1,140,180Z"></path></svg><p>Error: ${request.error || "Unable to retrieve transcript."} Try a different video.</p>`;
            summaryBox.style.display = "none";
            summarizeButton.innerText = "Retry";
        }
        summarizeButton.disabled = false;
    }
});


document.getElementById("copy-button").addEventListener("click", () => {
    const summaryText = document.getElementById("output").innerText;
    if (!summaryText || summaryText === "Summary will appear here.") return;
    navigator.clipboard.writeText(summaryText)
        .then(() => {
            console.log("Text copied to clipboard!");
            toast.classList.add("show");
            setTimeout(() => {
                toast.classList.remove("show");
            }, 1500);
        })
        .catch(err => {
            console.error("Failed to copy text: ", err);
        });
});

themeToggle.addEventListener("click", () => {
    popup.classList.toggle("dark-theme");
    popup.classList.toggle("light-theme");
    themeIcon.innerHTML = popup.classList.contains("dark-theme")
        ? '<svg xmlns="http://www.w3.org/2000/svg" class="sun-icon" width="30" height="30" fill="currentColor" viewBox="0 0 256 256"><path d="M120,40V16a8,8,0,0,1,16,0V40a8,8,0,0,1-16,0Zm72,88a64,64,0,1,1-64-64A64.07,64.07,0,0,1,192,128Zm-16,0a48,48,0,1,0-48,48A48.05,48.05,0,0,0,176,128ZM58.34,69.66A8,8,0,0,0,69.66,58.34l-16-16A8,8,0,0,0,42.34,53.66Zm0,116.68-16,16a8,8,0,0,0,11.32,11.32l16-16a8,8,0,0,0-11.32-11.32ZM192,72a8,8,0,0,0,5.66-2.34l16-16a8,8,0,0,0-11.32-11.32l-16,16A8,8,0,0,0,192,72Zm5.66,114.34a8,8,0,0,0-11.32,11.32l16,16a8,8,0,0,0,11.32-11.32ZM48,128a8,8,0,0,0-8-8H16a8,8,0,0,0,0,16H40A8,8,0,0,0,48,128Zm80,80a8,8,0,0,0-8,8v24a8,8,0,0,0,16,0V216A8,8,0,0,0,128,208Zm112-88H216a8,8,0,0,0,0,16h24a8,8,0,0,0,0-16Z"></path></svg>'
        : '<svg xmlns="http://www.w3.org/2000/svg" class="moon-icon" width="30" height="30" fill="currentColor" viewBox="0 0 256 256"><path d="M240,96a8,8,0,0,1-8,8H216v16a8,8,0,0,1-16,0V104H184a8,8,0,0,1,0-16h16V72a8,8,0,0,1,16,0V88h16A8,8,0,0,1,240,96ZM144,56h8v8a8,8,0,0,0,16,0V56h8a8,8,0,0,0,0-16h-8V32a8,8,0,0,0-16,0v8h-8a8,8,0,0,0,0,16Zm72.77,97a8,8,0,0,1,1.43,8A96,96,0,1,1,95.07,37.8a8,8,0,0,1,10.6,9.06A88.07,88.07,0,0,0,209.14,150.33,8,8,0,0,1,216.77,153Zm-19.39,14.88c-1.79.09-3.59.14-5.38.14A104.11,104.11,0,0,1,88,64c0-1.79,0-3.59.14-5.38A80,80,0,1,0,197.38,167.86Z"></path></svg>';
});