document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.getElementById('toggleTop3');
    let showingTop3 = false;

    toggleButton.addEventListener('click', () => {
        showingTop3 = !showingTop3;
        toggleButton.textContent = showingTop3 ? 'Show All' : 'Show Top 3';
        toggleTop3Swimmers(showingTop3);
    });

    function toggleTop3Swimmers(showTop3) {
        const eventDivs = document.querySelectorAll('.left > div');
        eventDivs.forEach(eventDiv => {
            const participantRows = eventDiv.querySelectorAll('.participant-row');
            participantRows.forEach((row, index) => {
                if (showTop3 && index >= 3) {
                    row.style.display = 'none';
                } else {
                    row.style.display = '';
                }
            });
        });
    }
});
