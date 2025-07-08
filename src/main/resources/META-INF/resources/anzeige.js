document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const mode = params.get("mode");

    if (mode) {
        const display = document.getElementById("gamemodeDisplay");
        display.textContent = "gamemode: " + mode;
    }
});