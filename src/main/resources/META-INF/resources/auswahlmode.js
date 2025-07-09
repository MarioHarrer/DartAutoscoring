document.addEventListener("DOMContentLoaded", () => {
    const modeBoxes = document.querySelectorAll('.mode-box');
    const startLink = document.getElementById('startLink');

    let selectedMode = null;

    modeBoxes.forEach(box => {
        box.addEventListener('click', () => {
            modeBoxes.forEach(b => b.classList.remove('active'));
            box.classList.add('active');
            selectedMode = box.textContent.trim();

            sessionStorage.setItem("selectedMode", selectedMode);
        });
    });

    startLink.addEventListener('click', (e) => {
        if (!selectedMode) {
            e.preventDefault();
            alert("Bitte wähle zuerst einen Spielmodus aus");
            return;
        }

        if (selectedMode === "match") {
            window.location.href = "/match";
        } else if (selectedMode === "around-the-clock") {
            window.location.href = "/around-the-clock";
        } else {
            alert("Unbekannter Modus: " + selectedMode);
        }
    });
});
