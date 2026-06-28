async function shortenURL() {
    const url = document.getElementById("urlInput").value;

    const response = await fetch("http://127.0.0.1:8000/shorten", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            original_url: url
        })
    });

    const data = await response.json();

    document.getElementById("result").innerHTML =
        `Short URL: <a href="${data.short_url}" target="_blank">${data.short_url}</a>`;
}