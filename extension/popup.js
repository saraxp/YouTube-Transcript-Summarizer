// Elements
const btn = document.getElementById("summarise");
const copyButton = document.getElementById("copy-button");
const themeToggle = document.getElementById("theme-toggle");
const themeIcon = document.getElementById("theme-icon");
const popupContainer = document.getElementById("popup-container");
const toast = document.getElementById("toast");

// Summarize Button Event
btn.addEventListener("click", function() {
    btn.disabled = true;
    btn.innerHTML = "Summarizing..."

    // Retrieve URL of active tab
    chrome.tabs.query({ currentWindow: true, active: true }, function(tabs) {
        const url = tabs[0].url;

        function fetchSummary() {
            fetch('http://localhost:5500/summary?url=' + encodeURIComponent(url))
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    // Display summary
                    const summary = data.summary;
                    summaryBox.innerText = summary;

                    // Hide error box in case it was displayed
                    errorBox.style.display = "none";

                    // Re-enable button and reset text
                    btn.disabled = false;
                    btn.innerHTML = "Summarize";
                })
                .catch(error => {
                    // Log and display the error
                    console.error('Error:', error);
                    errorBox.innerText = "Error: Unable to summarize video.";
                    errorBox.style.display = "block";

                    // Re-enable button and reset text
                    btn.disabled = false;
                    btn.innerHTML = "Summarize";
                });
        }

        // Initial fetch attempt
        fetchSummary();
    });
});

// Theme Toggle Button Event
themeToggle.addEventListener("click", () => {
    popupContainer.classList.toggle("dark-theme");
    popupContainer.classList.toggle("light-theme");

    // Change icon based on theme
    if (popupContainer.classList.contains("dark-theme")) {
        themeIcon.innerText = "sunny"; // Sun icon for light theme
    } else {
        themeIcon.innerText = "dark_mode"; // Moon icon for dark theme
    }
});

// Function to Show Toast
function showToast() {
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 1500); // Hide after 1.5 seconds
}
