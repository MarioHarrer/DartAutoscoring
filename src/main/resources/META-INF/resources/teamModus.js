document.addEventListener('DOMContentLoaded', function () {
    const teamModeCheckbox = document.getElementById('teamModeCheckbox');
    const teamSettings = document.getElementById('teamSettings');
    const playerSelect = document.querySelector('select[name="players"]');
    const teamPlayerSelects = document.querySelectorAll('.team-player');
    const team1Select = document.querySelector('select[name="team1Players"]');
    const team2Select = document.querySelector('select[name="team2Players"]');
    const startMatchButton = document.getElementById('startMatchButton');
    const form = document.querySelector('form[action="/dartboard/match"]');


    teamModeCheckbox.addEventListener('change', function () {
        const isChecked = this.checked;
        teamSettings.style.display = isChecked ? 'block' : 'none';
        teamPlayerSelects.forEach(select => select.disabled = !isChecked);
        team1Select.selectedIndex = -1;
        team2Select.selectedIndex = -1;
    });


    playerSelect.addEventListener('change', function () {
        const selectedPlayers = Array.from(this.selectedOptions);
        const count = selectedPlayers.length;

        teamModeCheckbox.disabled = count !== 4;
        teamSettings.style.display = count === 4 && teamModeCheckbox.checked ? 'block' : 'none';

        if (count !== 4) {
            teamModeCheckbox.checked = false;
        }

        if (count === 4) {
            updateTeamPlayerOptions(selectedPlayers);
        }
    });


    teamPlayerSelects.forEach(select => {
        select.addEventListener('change', function (event) {
            const selectedValue = event.target.value;
            if (selectedValue === "") return;

            const duplicate = Array.from(teamPlayerSelects).find(s =>
                s !== event.target && s.value === selectedValue
            );

            if (duplicate) {
                Swal.fire({
                    icon: 'error',
                    title: 'Fehler',
                    text: 'Dieser Spieler wurde bereits einem Team zugeordnet!',
                }).then(() => {
                    event.target.value = "";
                });
                startMatchButton.disabled = true;
            } else {
                startMatchButton.disabled = false;
            }
        });
    });


    function updateTeamPlayerOptions(players) {
        teamPlayerSelects.forEach(select => {
            select.innerHTML = ''; // Kein "Spieler wählen"
            players.forEach(player => {
                const option = document.createElement('option');
                option.value = player.value;
                option.textContent = player.textContent;
                select.appendChild(option);
            });
        });
    }


    form.addEventListener('submit', function (e) {
        if (teamModeCheckbox.checked) {
            const selectedPlayers = Array.from(playerSelect.selectedOptions);
            if (selectedPlayers.length !== 4) {
                e.preventDefault();
                alert('Für den Team-Modus müssen genau 4 Spieler ausgewählt sein!');
                return;
            }

            const team1 = Array.from(team1Select.selectedOptions);
            const team2 = Array.from(team2Select.selectedOptions);

            if (team1.length !== 2 || team2.length !== 2) {
                e.preventDefault();
                Swal.fire({
                    title: 'Fehler',
                    text: "Wählen Sie zwei Spieler pro Team aus",
                    icon: 'error',
                    toast: true,
                    position: 'top-end',
                    timer: 2000,
                    showConfirmButton: false
                })
                return;
            }

            // Optional: Setze die Spieler-Reihenfolge
            const all = [...team1, ...team2];
            playerSelect.value = all.map(opt => opt.value);
        }
    });


    function updateAvailablePlayers() {
        const selected1 = Array.from(team1Select.selectedOptions).map(opt => opt.value);
        const selected2 = Array.from(team2Select.selectedOptions).map(opt => opt.value);

        document.querySelectorAll('.team-player option').forEach(option => {
            const isSelected = selected1.includes(option.value) || selected2.includes(option.value);
            const parent = option.parentElement;
            option.disabled = isSelected && !Array.from(parent.selectedOptions).includes(option);
        });
    }

    team1Select.addEventListener('change', function () {
        if (this.selectedOptions.length > 2) {
            Array.from(this.selectedOptions).slice(2).forEach(opt => opt.selected = false);
        }
        updateAvailablePlayers();
    });

    team2Select.addEventListener('change', function () {
        if (this.selectedOptions.length > 2) {
            Array.from(this.selectedOptions).slice(2).forEach(opt => opt.selected = false);
        }
        updateAvailablePlayers();
    });
});