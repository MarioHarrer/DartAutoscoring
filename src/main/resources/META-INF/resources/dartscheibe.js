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

        // Farbe je nach Ringtyp
        let fill;
        if (ringName === "double" || ringName === "triple") {
            fill = (i % 2 === 0) ? "#c00" : "#0c0"; // Rot / Grün
        } else if (ringName === "single_outer" || ringName === "single_inner") {
            fill = (i % 2 === 0) ? "#000" : "#d4af7f"; // Schwarz / Beige (Goldbraun)
        }

        path.setAttribute("fill", fill);
        path.setAttribute("stroke", "#fff");
        path.setAttribute("data-score", ringName + "-" + sectorNumbers[i]);
        path.addEventListener("click", () => {
            const raw = path.getAttribute("data-score");
            const [zone, num] = raw.split("-");
            let score = parseInt(num);
            let zoneLabel = "Single";
            if (zone === "double") {
                score *= 2;
                zoneLabel = "Double";
            } else if (zone === "triple") {
                score *= 3;
                zoneLabel = "Triple";
            }

            Swal.fire({
                title: `${zoneLabel} ${num}`,
                text: `${score} points`,
                icon: 'success',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            });

            sendThrow(score);
        });
        svg.appendChild(path);
    }
}

// Rings (außen nach innen)
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
bull1.addEventListener("click", () => {
    Swal.fire({
        title: "Outer Bull",
        text: "25 points",
        icon: 'success',
        toast: true,
        position: 'top-end',
        timer: 2000,
        showConfirmButton: false
    });
    sendThrow(25);
});
svg.appendChild(bull1);

// Inner Bull (50 Punkte)
const bull2 = document.createElementNS("http://www.w3.org/2000/svg", "circle");
bull2.setAttribute("cx", "0");
bull2.setAttribute("cy", "0");
bull2.setAttribute("r", "10");
bull2.setAttribute("fill", "red");
bull2.setAttribute("data-score", "bull-50");
bull2.addEventListener("click", () => {
    Swal.fire({
        title: "Bullseye!",
        text: "50 points",
        icon: 'success',
        toast: true,
        position: 'top-end',
        timer: 2000,
        showConfirmButton: false
    });
    sendThrow(50);
});
svg.appendChild(bull2);

// Zahlenbeschriftung
for (let i = 0; i < 20; i++) {
    const angle = sectorAngles[i] + 9;
    const [x, y] = polarToCartesian(210, angle);
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", x);
    label.setAttribute("y", y);
    label.textContent = sectorNumbers[i];
    svg.appendChild(label);
}

async function sendThrow(score) {
    try{
        const response = await fetch("/dartboard/throw", {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `throw=${score}`
        });
        if(response.ok) {
            setTimeout(() =>
            window.location.reload(), 2000)
        }else{
            Swal.fire({
                title: "Error",
                text: "Something went wrong",
                icon: 'error',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            })
        }
    }catch (error){
        console.error("Fehler bei, saenden des Wurfes");
    }

}
