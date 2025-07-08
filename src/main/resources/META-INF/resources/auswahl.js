document.addEventListener("DOMContentLoaded", () => {
    const modeBoxes = document.querySelectorAll('.mode-box');
    const modeBoxes2 = document.querySelectorAll('.mode-box2');
    const startLink = document.getElementById('startLink');

    let selectedMode = null;
    let selectplayer = null;

    modeBoxes.forEach(box => {
        box.addEventListener('click', () => {
            modeBoxes.forEach(b => b.classList.remove('active'));
            box.classList.add('active');
            selectedMode = box.textContent.trim();
        });
    });
    modeBoxes2.forEach(box => {
        box.addEventListener('click', () => {
            modeBoxes2.forEach(b => b.classList.remove('active'));
            box.classList.add('active');
            selectplayer = box.textContent.trim();
        });
    })

    startLink.addEventListener('click', (e) => {
        if (!(selectedMode || selectplayer)) {
            e.preventDefault();
            alert("Bitte wähle zuerst einen Spielmodus und die Anzahl der Spieler aus.");
            return;
        }
        if (!selectedMode){
            e.preventDefault();
            alert("Bitte wähle zuerst einen Spielmodus aus")
            return;
        }
        if (!selectplayer){
            e.preventDefault();
            alert("Bitte wähle die Anzhal der Spieler aus")
            return;
        }
        /*const baseUrl = startLink.getAttribute('href');
        const newUrl = `${baseUrl}?mode=${encodeURIComponent(selectedMode)}`;
        const newUrl2 = `${newUrl}&player=${encodeURIComponent(selectplayer)}`;
        startLink.setAttribute('href', newUrl2);*/

    });
});
