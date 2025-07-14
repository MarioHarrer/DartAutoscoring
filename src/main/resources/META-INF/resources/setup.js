document.addEventListener('DOMContentLoaded', function() {
    const configureButton = document.getElementById('configureButton');
    const modeConfigOptions = document.getElementById('modeConfigOptions');
    const modeSelect = document.getElementById('modeSelect');
    const mode501Config = document.getElementById('mode501Config');
    const clockConfig = document.getElementById('clockConfig');

    if(configureButton && modeConfigOptions)
        configureButton.addEventListener('click', function() {
            modeConfigOptions.style.display = 'block';
            updateModeConfig();
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