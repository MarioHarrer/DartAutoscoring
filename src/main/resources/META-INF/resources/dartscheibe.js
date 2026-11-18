const isGameOver = document.querySelector('.gewinner-Alert') !== null;

const missButton = document.getElementById('missButton');
const resetButton = document.getElementById('resetButton');
const endMatchButton = document.querySelector('.end-match-button');


// "Rückgängig" funktioniert jetzt auch über Leg-Grenzen und nach dem Siegwurf –
// gesperrt nur, wenn noch gar kein Wurf existiert
const noThrowsYet = document.getElementById('dartboard').dataset.historyEmpty === 'true';


if (noThrowsYet) {
    resetButton.disabled = true;
}

if (isGameOver) {
    missButton.disabled = true;

    endMatchButton.style.backgroundColor = '#28a745';
    endMatchButton.style.transform = 'scale(1.05)';
}

const sectorAngles = Array.from({ length: 20 }, (_, i) => i * 18 - 9);
const sectorNumbers = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];
const svg = document.getElementById("dartboard");
const isAtcMode = svg.dataset.mode === 'MODE_AROUND_THE_CLOCK';

// Zeigt nach einem gültigen Wurf den Hinweis an.
// Bei Around the Clock kommt die Meldung (Treffer / Daneben) vom Backend.
function showThrowToast(title, text, validation) {
    if (isAtcMode) {
        const hit = validation.title === 'Treffer!';
        Swal.fire({
            title: `${title} – ${validation.title}`,
            text: validation.text,
            icon: hit ? 'success' : 'info',
            toast: true,
            position: 'top-end',
            timer: 2000,
            showConfirmButton: false
        });
        return;
    }
    Swal.fire({
        title: title,
        text: text,
        icon: 'success',
        toast: true,
        position: 'top-end',
        timer: 2000,
        showConfirmButton: false
    });
}

function polarToCartesian(r, angleDeg) {
    const angleRad = (angleDeg - 90) * Math.PI / 180.0;
    return [r * Math.cos(angleRad), r * Math.sin(angleRad)];
}

function createRing(startR, endR, ringName) {
    for (let i = 0; i < 20; i++) {
        const startAngle = sectorAngles[i];
        const endAngle = sectorAngles[i] + 18;

        const [x1, y1] = polarToCartesian(startR, startAngle);
        const [x2, y2] = polarToCartesian(endR, startAngle);
        const [x3, y3] = polarToCartesian(endR, endAngle);
        const [x4, y4] = polarToCartesian(startR, endAngle);

        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        const d = `
        M ${x1} ${y1}
        L ${x2} ${y2}
        A ${endR} ${endR} 0 0 1 ${x3} ${y3}
        L ${x4} ${y4}
        A ${startR} ${startR} 0 0 0 ${x1} ${y1}
        Z`;
        path.setAttribute("d", d);

        let fill;
        if (ringName === "double" || ringName === "triple") {
            fill = (i % 2 === 0) ? "#c00" : "#0c0";
        } else if (ringName === "single_outer" || ringName === "single_inner") {
            fill = (i % 2 === 0) ? "#000" : "#d4af7f";
        }

        path.setAttribute("fill", fill);
        path.setAttribute("stroke", "#fff");
        path.setAttribute("data-score", ringName + "-" + sectorNumbers[i]);

        path.addEventListener("click", async () => {
            // Manueller Klick -> Kameras im Python sperren
            lockCameraButtons();
            fetch('http://localhost:5000/api/action/clear_lines', { method: 'POST' }).catch(e => console.log(e));

            const raw = path.getAttribute("data-score");
            const [zone, num] = raw.split("-");
            const score = parseInt(num);
            let isDouble = false;
            let isTriple = false;
            let multiplier = 1;
            let zoneLabel = "Single";

            if (zone === "double") {
                isDouble = true;
                multiplier = 2;
                zoneLabel = "Double";
            } else if (zone === "triple") {
                isTriple = true;
                multiplier = 3;
                zoneLabel = "Triple";
            }

            try {
                const validation = await validateThrow(score, isDouble, isTriple);

                if (!validation.valid) {
                    Swal.fire({
                        title: validation.title,
                        text: validation.text,
                        icon: 'error',
                        toast: true,
                        position: 'top-end',
                        timer: 2000,
                        showConfirmButton: false
                    });
                    sendThrow(0, false, false);
                    return;
                }

                showThrowToast(`${zoneLabel} ${num}`, `${score * multiplier} Punkte`, validation);
                sendThrow(score, isDouble, isTriple);
            } catch (error) {
                console.error("Validierungsfehler:", error);
            }
        })

        svg.appendChild(path);
    }
}

// Ringe (außen nach innen)
createRing(170, 190, "double");
createRing(100, 120, "triple");
createRing(120, 170, "single_outer");
createRing(20, 100, "single_inner");

// Outer Bull (25 Punkte)
const bull1 = document.createElementNS("http://www.w3.org/2000/svg", "circle");
bull1.setAttribute("cx", "0");
bull1.setAttribute("cy", "0");
bull1.setAttribute("r", "20");
bull1.setAttribute("fill", "green");
bull1.setAttribute("data-score", "bull-25");

bull1.addEventListener("click", async () => {
    lockCameraButtons();
    fetch('http://localhost:5000/api/action/clear_lines', { method: 'POST' }).catch(e => console.log(e));

    try{
        const validation = await validateThrow(25, false, false);

        if(!validation.valid){
            Swal.fire({
                title: validation.title,
                text: validation.text,
                icon: 'error',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            });
            sendThrow(0, false, false);
            return;
        }
        showThrowToast("Outer Bull", "25 Punkte", validation);
        sendThrow(25, false, false);
    }catch(error){
        console.error("Validierungsfehler:", error);
    }
});
svg.appendChild(bull1);

// Inner Bull (50 Punkte)
const bull2 = document.createElementNS("http://www.w3.org/2000/svg", "circle");
bull2.setAttribute("cx", "0");
bull2.setAttribute("cy", "0");
bull2.setAttribute("r", "10");
bull2.setAttribute("fill", "red");
bull2.setAttribute("data-score", "bull-50");
bull2.addEventListener("click", async () => {

    lockCameraButtons();
    fetch('http://localhost:5000/api/action/clear_lines', { method: 'POST' }).catch(e => console.log(e));

    try {
        const validation = await validateThrow(50, true, false);

        if(!validation.valid){
            Swal.fire({
                title: validation.title,
                text: validation.text,
                icon: 'error',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            });
            sendThrow(0, false, false);
            return;
        }
        showThrowToast("Bullseye!", "50 Punkte", validation);
        sendThrow(50, true, false);
    }catch(error){
        console.error("Validierungsfehler:", error);
    }
});
svg.appendChild(bull2);

//Zahlenbeschriftung
const numberRadius = 205;
for (let i = 0; i < 20; i++) {
    const angle = sectorAngles[i] + 9;
    const angleRad = (angle - 90) * Math.PI / 180.0;
    const x = numberRadius * Math.cos(angleRad);
    const y = numberRadius * Math.sin(angleRad);

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", x);
    label.setAttribute("y", y);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("dominant-baseline", "middle");
    label.setAttribute("font-size", "16");
    label.setAttribute("font-family", "Arial");
    label.textContent = sectorNumbers[i];

    svg.appendChild(label);
}

// Hilfsfunktion zum Sperren der Kamera-Buttons nach manuellem Klick
function lockCameraButtons() {
    for (let i = 0; i < 3; i++) {
        let btn = document.getElementById('btn-cam-' + i);
        if (btn) {
            btn.disabled = true;
            btn.classList.remove('btn-active');
            btn.classList.add('btn-inactive');
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        }
    }
}

async function sendThrow(score, isDouble = false, isTriple = false) {
    try {
        const formData = new URLSearchParams();
        formData.append('score', score);
        formData.append('isDouble', isDouble);
        formData.append('isTriple', isTriple);

        const baseUrl = window.location.origin.includes('localhost')
            ? 'http://localhost:8080'
            : window.location.origin;

        const response = await fetch(`${baseUrl}/dartboard/throw`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        if(response.ok) {
            setTimeout(() => window.location.reload(), 2000);
        } else {
            Swal.fire({
                title: "Error",
                text: "Etwas ist schief gelaufen",
                icon: 'error',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            });
        }
    } catch (error) {
        console.error("Fehler beim Senden des Wurfes", error);
    }
}

async function validateThrow(score, isDouble, isTriple) {
    try {
        const formData = new URLSearchParams();
        formData.append('score', score);
        formData.append('isDouble', isDouble);
        formData.append('isTriple', isTriple);

        const baseUrl = window.location.origin.includes('localhost')
            ? 'http://localhost:8080'
            : window.location.origin;

        const response = await fetch(`${baseUrl}/dartboard/validate-throw`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Netzwerkfehler bei der Validierung');
        }

        return await response.json();
    } catch (error) {
        console.error("Validierungsfehler:", error);
        throw error;
    }
}

document.getElementById("missButton").addEventListener("click", async function() {
    lockCameraButtons();
    fetch('http://localhost:5000/api/action/clear_lines', { method: 'POST' }).catch(e => console.log(e));

    try {
        await sendThrow(0, false, false);

        Swal.fire({
            title: "Miss",
            text: "0 Punkte",
            icon: 'success',
            toast: true,
            position: 'top-end',
            timer: 2000,
            showConfirmButton: false
        });
    } catch (error) {
        console.error("Fehler beim Fehlwurf:", error);
        Swal.fire({
            title: "Fehler",
            text: "Etwas ist schief gelaufen",
            icon: 'error',
            toast: true,
            position: 'top-end',
            timer: 2000,
            showConfirmButton: false
        });
    }
});

document.getElementById("resetButton").addEventListener("click", async function() {
    lockCameraButtons();
    fetch('http://localhost:5000/api/action/clear_lines', { method: 'POST' }).catch(e => console.log(e));

    try {
        const baseUrl = window.location.origin.includes('localhost')
            ? 'http://localhost:8080'
            : window.location.origin;

        const response = await fetch(`${baseUrl}/dartboard/reset`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });

        if (response.status === 204) {
            Swal.fire({
                title: "Nicht möglich",
                text: "Der letzte Wurf wurde bereits zurückgesetzt oder es gibt noch keinen Wurf",
                icon: 'warning',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            });
        } else if (response.ok) {
            Swal.fire({
                title: "Rücksetzen",
                text: "Letzter Wurf wurde zurückgesetzt",
                icon: 'info',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            });
            setTimeout(() => window.location.reload(), 2000);
        } else {
            Swal.fire({
                title: "Fehler",
                text: "Etwas ist schief gelaufen",
                icon: 'error',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            });
        }
    } catch (error) {
        console.error("Fehler Bei Wurf rückgängig machen: ", error);
    }
});

document.getElementById('startCameraButton').addEventListener('click', function() {
    fetch('/dartboard/startCamera', {
        method: 'POST',
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Netzwerkantwort war nicht ok');
            }
            Swal.fire({
                title: 'Kameras gestartet!',
                text: 'Das Python-Skript wurde erfolgreich geweckt. Bitte kalibriere nun die Kameras in Python.',
                icon: 'success',
                toast: true,
                position: 'top-end',
                timer: 4000,
                showConfirmButton: false
            });
        })
        .catch(error => {
            Swal.fire({
                title: 'Fehler!',
                text: 'Fehler beim Starten der Kameras. Läuft das Python-Skript im Hintergrund?',
                icon: 'error',
                confirmButtonText: 'OK'
            });
        });
});

const socket = new WebSocket(`ws://${window.location.host}/websocket/dartboard`);

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === "throwRegistered") {
        // Sobald Python einen Wurf erkennt, schalten wir die Buttons sofort klickbar frei!
        for (let i = 0; i < 3; i++) {
            let btn = document.getElementById('btn-cam-' + i);
            if (btn) {
                btn.disabled = false;
                btn.classList.remove('btn-inactive');
                btn.classList.add('btn-active');
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            }
        }

        if (data.showAlert) {
            Swal.fire({
                title: data.alertTitle,
                text: data.alertText,
                icon: data.alertIcon,
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            }).then(() => {
                window.location.reload();
            });

            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            window.location.reload();
        }
    }
};