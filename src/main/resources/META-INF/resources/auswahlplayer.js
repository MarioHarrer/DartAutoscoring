document.addEventListener("DOMContentLoaded", () => {
    const modeBoxes2 = document.querySelectorAll('.mode-box2');
    const startLink = document.getElementById('startLink');

    let selectedPlayer = null;

    modeBoxes2.forEach(box => {
        box.addEventListener('click', () => {
            modeBoxes2.forEach(b => b.classList.remove('active'));
            box.classList.add('active');
            selectedPlayer = box.textContent.trim();
        });
    })

    startLink.addEventListener('click', (e) => {
        if (!selectedPlayer) {
            e.preventDefault();
            alert("Bitte wähle zuerst die anzahl der Spieler aus")
            return;
        }
    });
});