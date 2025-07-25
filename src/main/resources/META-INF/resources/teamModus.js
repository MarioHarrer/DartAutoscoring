document.addEventListener('DOMContentLoaded', function() {
    const teamModeCheckbox = document.getElementById('teamModeCheckbox');
    const teamSettings = document.getElementById('teamSettings');
    const playerSelect = document.querySelector('select[name="players"]');
    const teamPlayerSelects = document.querySelectorAll('.team-player');

    teamModeCheckbox.addEventListener('change', function() {
        teamSettings.style.display = this.checked ? 'block' : 'none';


        teamPlayerSelects.forEach(select => {
            select.disabled = !this.checked;
        });
    });

    playerSelect.addEventListener('change', function() {
        const selectedPlayers = Array.from(this.selectedOptions);

        teamModeCheckbox.disabled = selectedPlayers.length !== 4;
        if (selectedPlayers.length !== 4) {
            teamModeCheckbox.checked = false;
            teamSettings.style.display = 'none';
        }

        // Aktualisiere Team-Spieler-Optionen
        if (selectedPlayers.length === 4) {
            updateTeamPlayerOptions(selectedPlayers);
        }
    });

    function updateTeamPlayerOptions(selectedPlayers) {
        teamPlayerSelects.forEach(select => {
            // Lösche bestehende Optionen
            select.innerHTML = '<option value="">Spieler wählen</option>';

            // Füge ausgewählte Spieler als Optionen hinzu
            selectedPlayers.forEach(player => {
                const option = document.createElement('option');
                option.value = player.value;
                option.textContent = player.textContent;
                select.appendChild(option);
            });
        });
    }
});
