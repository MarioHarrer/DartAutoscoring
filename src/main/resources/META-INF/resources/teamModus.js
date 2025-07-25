document.addEventListener('DOMContentLoaded', function() {
    const teamModeCheckbox = document.getElementById('teamModeCheckbox');
    const teamSettings = document.getElementById('teamSettings');
    const playerSelect = document.querySelector('select[name="players"]');
    const teamPlayerSelects = document.querySelectorAll('.team-player');
    const startMatchButton = document.getElementById('startMatchButton');

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

        if (selectedPlayers.length === 4) {
            updateTeamPlayerOptions(selectedPlayers);
        }
    });

    teamPlayerSelects.forEach(select => {
        select.addEventListener('change', function(event) {
            const currentSelect = event.target;
            const selectedValue = currentSelect.value;

            if (selectedValue === "") return;

            const duplicateSelect = Array.from(teamPlayerSelects).find(otherSelect =>
                otherSelect !== currentSelect &&
                otherSelect.value === selectedValue
            );

            if (duplicateSelect) {
                Swal.fire({
                    icon: 'error',
                    title: 'Fehler',
                    text: 'Dieser Spieler wurde bereits einem Team zugeordnet!',
                    confirmButtonText: 'OK'
                }).then(() => {
                    currentSelect.value = "";
                });
                startMatchButton.disabled = true;
            } else {
                const allSelections = Array.from(teamPlayerSelects)
                    .map(select => select.value)
                    .filter(value => value !== "");
                const uniqueSelections = new Set(allSelections);

                startMatchButton.disabled = allSelections.length !== uniqueSelections.size;
            }
        });
    });

    function updateTeamPlayerOptions(selectedPlayers) {
        teamPlayerSelects.forEach(select => {
            select.innerHTML = '<option value="">Spieler wählen</option>';
            selectedPlayers.forEach(player => {
                const option = document.createElement('option');
                option.value = player.value;
                option.textContent = player.textContent;
                select.appendChild(option);
            });
        });
    }
});
