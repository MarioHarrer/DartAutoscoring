document.addEventListener('DOMContentLoaded', function() {
    const configureButton = document.getElementById('configureButton');
    const modeConfigOptions = document.getElementById('modeConfigOptions');
    const modeSelect = document.getElementById('modeSelect');
    const mode501Config = document.getElementById('mode501Config');
    const clockConfig = document.getElementById('clockConfig');
    const playerSelect = document.querySelector('select[name="players"]');

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
            playerSelect.disabled = true;
            configureButton.disabled = true;
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