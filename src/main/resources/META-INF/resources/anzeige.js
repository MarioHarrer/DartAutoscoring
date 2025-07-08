document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const mode = params.get("mode");
    const player = params.get("player");

    if (mode) {
        const display = document.getElementById("gamemodeDisplay");
        display.textContent = "gamemode: " + mode;
    }
    if (player) {
        const display = document.getElementById("playerDisplay");
        display.textContent = "players: " + player;
    }
});