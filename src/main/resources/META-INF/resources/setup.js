document.addEventListener('DOMContentLoaded', function() {
    const configureButton = document.getElementById('configureButton');
    const modeConfigOptions = document.getElementById('modeConfigOptions');
    const modeSelect = document.getElementById('modeSelect');
    const mode501Config = document.getElementById('mode501Config');
    const clockConfig = document.getElementById('clockConfig');
    const playerSelect = document.querySelector('select[name="players"]');
    const deleteAllPlayers = document.getElementById('deleteAllPlayers');
    const deletePlayer = document.getElementById('deletePlayer');
    const hinzufuegen = document.getElementById('hinzufuegen');
    const chooesemode = document.getElementById('modeSelect');
    const nameInput = document.getElementById('nameInput');

    configureButton.disabled = true;
    playerSelect.addEventListener('change', function() {
        const selected = Array.from(this.selectedOptions).length;

        if(selected > 0 && selected <= 4){
            configureButton.disabled = false;
        }
        else{
            configureButton.disabled = true;

            Swal.fire({
                title:"Ungültige auswahl",
                text: "Maximal 4 Spieler sind erlaubt",
                icon: 'error',
                toast: true,
                position: 'top-end',
                timer: 2000,
                showConfirmButton: false
            })
        }
    })
    if(configureButton && modeConfigOptions)
        configureButton.addEventListener('click', function() {
            modeConfigOptions.style.display = 'block';
            updateModeConfig();
            const selectedArray = Array.from(playerSelect.selectedOptions);
            selectedArray.forEach(option => {
                const hide = document.createElement('input');
                hide.type = 'hidden';
                hide.name = 'players';
                hide.value = option.value;
                playerSelect.form.appendChild(hide)
            })
            const modeHiddenInput = document.createElement('input');
            modeHiddenInput.type = 'hidden';
            modeHiddenInput.name = 'modeType';
            modeHiddenInput.value = modeSelect.value;
            playerSelect.form.appendChild(modeHiddenInput);

            playerSelect.disabled = true;
            configureButton.disabled = true;
            deleteAllPlayers.disabled = true;
            deletePlayer.disabled = true;
            hinzufuegen.disabled = true;
            chooesemode.disabled = true;
            nameInput.disabled = true;
        });

    function updateModeConfig() {
        const selectedMode = modeSelect.value;
        if (selectedMode === 'MODE_501') {
            mode501Config.style.display = 'block';
            clockConfig.style.display = 'none';
        } else {
            mode501Config.style.display = 'none';
            clockConfig.style.display = 'block';
        }
    }
});


document.addEventListener('DOMContentLoaded', function() {

    document.getElementById('deleteAllPlayers').addEventListener('click', async () => {
        const select = document.querySelector('select[name="players"]');
        const options = select.options;

        if(options.length === 0){
            Swal.fire({
                title: "Fehler",
                text: "Es wurden noch keine Spieler hinzugefügt",
                icon: 'warning',
            });
            return;
        }

        const result = await Swal.fire({
            title: "Spieler löschen",
            text: "Möchten Sie wirklich alle Spieler löschen",
            icon: "warning",
            showCancelButton: true,
            cancelButtonText: "Abbrechen",
            cancelButtonColor: "grey",
            showConfirmButton: true,
            confirmButtonText: "Ja",
            confirmButtonColor: "red"
        })

        if (result.isConfirmed) {
            await fetch('/dartboard/players', {
                method: 'DELETE'
            });
            location.reload();
        }
    })


    document.getElementById('deletePlayer').addEventListener('click', async () => {
        const select = document.querySelector('select[name="players"]');
        const selectOptions = Array.from(select.selectedOptions);

        if(selectOptions.length === 0){
            Swal.fire({
                title: "Fehler",
                text: "Wählen Sie mindestens einen Spieler aus",
                icon: 'warning',
            });
            return;
        }
        const result = await Swal.fire({
            title: "Wollen Sie wirklich Spieler löschen?",
            text: `${selectOptions.length} Spieler löschen`,
            icon: "warning",
            showCancelButton: true,
            cancelButtonText: "Abbrechen",
            cancelButtonColor: "grey",
            showConfirmButton: true,
            confirmButtonText: "Ja",
            confirmButtonColor: "red"
        });

        if(result.isConfirmed){
            for(const option of selectOptions){
                const playerId = option.value;
                await fetch(`/dartboard/player/${playerId}`, {
                    method: 'DELETE'
                });
                option.remove();
            }
        }
    });
})


