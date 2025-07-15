

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

        path.addEventListener("click", () => {
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

            const startMode = document.querySelector('p[startmode]').getAttribute('startmode');
            const endMode = document.querySelector('p[endmode]').getAttribute('endmode');
            const currentScore = parseInt(document.querySelector('li.active').textContent.split('Punktestand: ')[1]);
            const newScore = currentScore - (score * multiplier);

            if(newScore < 0){
                Swal.fire({
                    title: "Ungültiger Wurf",
                    text: "Überworfen",
                    icon: 'error',
                    toast: true,
                    position: 'top-end',
                    timer: 2000,
                    showConfirmButton: false
                })
                sendThrow(0, false, false);
                return;
            }
            if (startMode === 'DOUBLE_IN' && currentScore === 501) {
                if (!isDouble) {
                    Swal.fire({
                        title: "Ungültiger Wurf",
                        text: "Du musst mit Double oder Bull's Eye beginnen",
                        icon: 'error',
                        toast: true,
                        position: 'top-end',
                        timer: 2000,
                        showConfirmButton: false
                    });
                    sendThrow(0, false, false);
                    return;
                }
            } else if (startMode === 'MASTER_IN' && currentScore === 501) {
                if (!isTriple && !isDouble) {
                    Swal.fire({
                        title: "Ungültiger Wurf",
                        text: "Du musst mit Triple, Double oder Bull's Eye beginnen",
                        icon: 'error',
                        toast: true,
                        position: 'top-end',
                        timer: 2000,
                        showConfirmButton: false
                    });
                    sendThrow(0, false, false);
                    return;
                }
            }

            if (endMode === 'DOUBLE_OUT') {
                if (newScore === 0 && !isDouble) {
                    Swal.fire({
                        title: "Ungültiger Wurf",
                        text: "Du musst mit Double oder Bull's Eye ausmachen",
                        icon: 'error',
                        toast: true,
                        position: 'top-end',
                        timer: 2000,
                        showConfirmButton: false
                    });
                    sendThrow(0, false, false);
                    return;
                }
            }
            else if (endMode === 'MASTER_OUT') {
                if (newScore === 0 && !isTriple && !isDouble)
                {
                    Swal.fire({
                        title: "Ungültiger Wurf",
                        text: "Du musst mit Double, Triple oder Bull's Eye ausmachen",
                        icon: 'error',
                        toast: true,
                        position: 'top-end',
                        timer: 2000,
                        showConfirmButton: false
                    });
                    sendThrow(0, false, false);
                    return;
                }
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
        });

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

bull1.addEventListener("click", () => {

    const startMode = document.querySelector('p[startmode]').getAttribute('startmode');
    const endMode = document.querySelector('p[endmode]').getAttribute('endmode');
    const currentScore = parseInt(document.querySelector('li.active').textContent.split('Punktestand: ')[1]);
    const newScore = currentScore - 25;

    if(newScore < 0){
        Swal.fire({
            title: "Ungültiger Wurf",
            text: "Überworfen",
            icon: 'error',
            toast: true,
            position: 'top-end',
            timer: 2000,
            showConfirmButton: false
        })
        sendThrow(0, false, false);
        return;
    }

    if (startMode === 'DOUBLE_IN' && currentScore === 501) {
        Swal.fire({
            title: "Ungültiger Wurf",
            text: "Du musst mit Double oder Bull's Eye beginnen",
            icon: 'error',
            toast: true,
            position: 'top-end',
            timer: 2000,
            showConfirmButton: false
        });
        sendThrow(0, false, false);
        return;
    }
    else if( startMode === 'MASTER_IN' && currentScore === 501){
        Swal.fire({
            title: "Ungültiger Wurf",
            text: "Du musst mit Triple oder Bull's Eye beginnen",
            icon: 'error',
            toast: true,
            position: 'top-end',
            timer: 2000,
            showConfirmButton: false
        })
        sendThrow(0, false, false);
        return;
    }
    if(endMode === 'DOUBLE_OUT'){
        if(newScore === 0){
            Swal.fire({
                title: "Ungültiger Wurf",
                text: "Du musst mit Double oder Bull's Eye ausmachen",
                icon: 'error',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            })
            sendThrow(0, false, false);
            return;
        }
    }else if(endMode === 'MASTER_OUT'){
        if(newScore === 0){
            Swal.fire({
                title: "Ungültiger Wurf",
                text: "Du musst mit Double, Triple oder Bull's Eye ausmachen",
                icon: 'error',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            })
            sendThrow(0, false, false);
            return;
        }
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

    const currentScore = parseInt(document.querySelector('li.active').textContent.split('Punktestand: ')[1]);
    const newScore = currentScore - 50;

    if(newScore < 0){
        Swal.fire({
            title: "Ungültiger Wurf",
            text: "Überworfen",
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
