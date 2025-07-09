document.addEventListener("DOMContentLoaded", () => {
    const modeBoxes = document.querySelectorAll('.mode-box');
    const startLink = document.getElementById('startLink');

    let selectedMode = null;

    modeBoxes.forEach(box => {
        box.addEventListener('click', () => {
            modeBoxes.forEach(b => b.classList.remove('active'));
            box.classList.add('active');
            selectedMode = box.textContent.trim();
        });
    });

    startLink.addEventListener('click', (e) => {
        if (!selectedMode){
            e.preventDefault();
            alert("Bitte wähle zuerst einen Spielmodus aus")
            return;
        }
    });
});
