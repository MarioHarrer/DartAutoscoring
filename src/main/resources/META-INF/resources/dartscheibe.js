
const isGameOver = document.querySelector('.gewinner-Alert') !== null;

const missButton = document.getElementById('missButton');
const resetButton = document.getElementById('resetButton');
const endMatchButton = document.querySelector('.end-match-button');


if (isGameOver) {

    missButton.disabled = true;
    resetButton.disabled = true;

    endMatchButton.style.backgroundColor = '#28a745';
    endMatchButton.style.transform = 'scale(1.05)';
}


const sectorAngles = Array.from({ length: 20 }, (_, i) => i * 18 - 9);
const sectorNumbers = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];
const svg = document.getElementById("dartboard");

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

                Swal.fire({
                    title: `${zoneLabel} ${num}`,
                    text: `${score * multiplier} Punkte`,
                    icon: 'success',
                    toast: true,
                    position: 'top-end',
                    timer: 2000,
                    showConfirmButton: false
                });
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
            })
            sendThrow(0, false, false);
            return;
        }
        Swal.fire({
            title: "Outer Bull",
            text: "25 Punkte",
            icon: 'success',
            toast: true,
            position: 'top-end',
            timer: 2000,
            showConfirmButton: false
        });
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

    const currentScore = parseInt(document.querySelector('li.active').textContent.split('Punktestand: ')[1]);
    const newScore = currentScore - 50;

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
        Swal.fire({
            title: "Bullseye!",
            text: "50 Punkte",
            icon: 'success',
            toast: true,
            position: 'top-end',
            timer: 2000,
            showConfirmButton: false
        });
        sendThrow(50, true, false);
    }catch(error){
        console.error("Validierungsfehler:", error);
    }
});
svg.appendChild(bull2);

//Zahlenbeschriftung
const numberRadius = 205; // Konstanter Abstand vom Mittelpunkt
for (let i = 0; i < 20; i++) {
    const angle = sectorAngles[i] + 9; // Zentrum des Sektors
    const angleRad = (angle - 90) * Math.PI / 180.0;
    const x = numberRadius * Math.cos(angleRad);
    const y = numberRadius * Math.sin(angleRad);

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", x);
    label.setAttribute("y", y);
    label.setAttribute("text-anchor", "middle"); // Zentrierte Ausrichtung
    label.setAttribute("dominant-baseline", "middle"); // Vertikale Zentrierung
    label.setAttribute("font-size", "16"); // Einheitliche Schriftgröße
    label.setAttribute("font-family", "Arial"); // Einheitliche Schriftart
    label.textContent = sectorNumbers[i];

    svg.appendChild(label);
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
    try{
        const baseUrl = window.location.origin.includes('localhost')
        ? 'http://localhost:8080'
        : window.location.origin;

        const response = await fetch(`${baseUrl}/dartboard/reset`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });

        if(response.ok){

            Swal.fire({
                title: "Rücksetzen",
                text: "Letzter Wurf wurde zurückgesetzt",
                icon: 'info',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            })
            setTimeout(() => window.location.reload(), 2000);
        }else{
            Swal.fire({
                title: "Fehler",
                text: "Etwas ist schief gelaufen",
                icon: 'error',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
                }
            )
        }
    }catch(error){
        console.error("Fehler Bei Wurf rückgangig machen: ", error);
    }
})






