function toggleCamera(cid) {

    let btn = document.getElementById('btn-cam-' + cid);

    // Gesperrte Buttons (kein Kamerawurf / manueller Eingriff) reagieren nicht

    if (btn && btn.disabled) {

        return;

    }

    fetch('/api/camera/toggle/' + cid, {
        method: 'POST'

    })

        .then(response => response.json())

        .then(data => {

            console.log("Kamera " + cid + " Status geändert");

            // Optisches Feedback: Button-Farbe direkt vom Python-Status übernehmen

            updateCameraButtons();

        })

        .catch(error => console.error('Fehler beim Umschalten der Kamera:', error));

}

// Setzt einen Button auf einen der drei Zustände:

// 'active'  = Kamera wird gewertet (grün)

// 'ignored' = Kamera per Klick ignoriert (grau, aber wieder einschaltbar)

// 'locked'  = kein Kamerawurf vorhanden oder manuell korrigiert (grau, gesperrt)

function setCameraButtonState(btn, state) {

    if (state === 'active') {

        btn.classList.remove('btn-inactive');

        btn.classList.add('btn-active');

        btn.disabled = false;

        btn.style.cursor = 'pointer';

    } else if (state === 'ignored') {

        btn.classList.remove('btn-active');

        btn.classList.add('btn-inactive');

        btn.disabled = false;

        btn.style.cursor = 'pointer';

    } else {

        btn.classList.remove('btn-active');

        btn.classList.add('btn-inactive');

        btn.disabled = true;

        btn.style.cursor = 'not-allowed';

    }

}

// Holt den aktuellen Kamera-Zustand aus Python und färbt die Buttons entsprechend.

// Dadurch sind nach jedem neuen Wurf automatisch wieder alle Kameras grün.

function updateCameraButtons() {

    fetch('/api/camera/states')

        .then(response => response.json())

        .then(data => {

            for (let cid = 0; cid < 3; cid++) {

                let btn = document.getElementById('btn-cam-' + cid);

                if (!btn) continue;

                const key = String(cid);

                if (!data.has_throw || !(key in data.cams)) {

                    setCameraButtonState(btn, 'locked');

                } else if (data.cams[key]) {

                    setCameraButtonState(btn, 'active');

                } else {

                    setCameraButtonState(btn, 'ignored');

                }

            }

        })

        .catch(error => console.error('Fehler beim Laden des Kamera-Status:', error));

}

// Regelmäßig abfragen, damit Wurf auswerten, Hintergrund speichern und

// manuelle Korrekturen im Browser sofort im Dashboard sichtbar sind

updateCameraButtons();

setInterval(updateCameraButtons, 500);

// --- NEU: MODUS MANUELL / AUTOMATISCH ---

// Schaltet in Python zwischen Manuell und Automatisch um

function setMode(mode) {

    fetch('/api/mode/' + mode, {

        method: 'POST'

    })

        .then(response => response.json())

        .then(data => {

            console.log("Modus gewechselt:", data.mode);

            updateModeDisplay();

        })

        .catch(error => console.error('Fehler beim Umschalten des Modus:', error));

}

// Holt Modus und Status aus Python und aktualisiert Umschalter, Statusanzeige

// und die Buttons "Hintergrund speichern" / "Wurf auswerten" (im Automatik-Modus gesperrt)

function updateModeDisplay() {

    fetch('/api/mode')

        .then(response => response.json())

        .then(data => {

            const isAuto = data.mode === 'auto';

            const btnManual = document.getElementById('btn-mode-manual');

            const btnAuto = document.getElementById('btn-mode-auto');

            if (btnManual && btnAuto) {

                btnManual.className = isAuto ? 'mode-unselected' : 'mode-selected';

                btnAuto.className = isAuto ? 'mode-selected' : 'mode-unselected';

            }

            const btnBackground = document.getElementById('btn-background');

            const btnThrow = document.getElementById('btn-throw');

            [btnBackground, btnThrow].forEach(btn => {

                if (!btn) return;

                btn.disabled = isAuto;

                btn.title = isAuto ? 'Im Automatik-Modus nicht nötig' : '';

            });

            const statusEl = document.getElementById('auto-status');

            if (statusEl) {

                statusEl.textContent = data.status;

            }

        })

        .catch(error => console.error('Fehler beim Laden des Modus:', error));

}

updateModeDisplay();

setInterval(updateModeDisplay, 500);
