function toggleCamera(cid) {
    fetch('/api/camera/toggle/' + cid, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            console.log("Kamera " + cid + " Status geändert");

            // Optisches Feedback: Button-Farbe umschalten
            let btn = document.getElementById('btn-cam-' + cid);
            if (btn.classList.contains('btn-active')) {
                btn.classList.remove('btn-active');
                btn.classList.add('btn-inactive');
            } else {
                btn.classList.remove('btn-inactive');
                btn.classList.add('btn-active');
            }
        })
        .catch(error => console.error('Fehler beim Umschalten der Kamera:', error));
}