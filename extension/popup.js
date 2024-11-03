const btn = document.getElementById("summarise");

btn.addEventListener("click", function() {
    btn.disabled = true;
    btn.innerHTML = "Summarising...";

    // Retrieve URL of active tab
    chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
        var url = tabs[0].url;

       
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
                    const p = document.getElementById("output");
                    p.innerText = summary;
                    
                    // Re-enable button 
                    btn.disabled = false;
                    btn.innerHTML = "Summarise";
                })
                .catch(error => {
                    // Log the error
                    console.error('Error:', error);

                    // Display error message
                    const p = document.getElementById("output");
                    p.innerText = "Error: Unable to summarize video.";

                    // Re-enable button 
                    btn.disabled = false;
                    btn.innerHTML = "Summarise";
                });
        }

        // Initial fetch attempt
        fetchSummary();
    });
});
