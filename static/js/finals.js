document.addEventListener('DOMContentLoaded', () => {
    const laneOrder = [4, 5, 3, 6, 2, 7, 1, 8];
    function prepareFinalEvent(event, eventTitle) {
        const finalsContainer = document.getElementById('finalsContainer');

        const finalDiv = document.createElement('div');
        finalDiv.id = `final_${event.id}_container`;
        finalDiv.className = 'final-container';

        finalDiv.innerHTML = `
            <h3>Final for ${eventTitle}</h3>
            <button onclick="editFinalEvent(${event.id})" id="editButton_final_${event.id}" class="edit-button">Edit Final Times</button>
            <div id="final_${event.id}_participants"></div>
        `;

        finalsContainer.appendChild(finalDiv);

        drawEmptyFinal(event.id); // Draw the empty final heat table
        loadFinalParticipants(event.id); // Load the top 8 participants
    }

    function editFinalEvent(eventId) {
        const finalParticipantsDiv = document.getElementById(`final_${eventId}_participants`);
        const inputs = finalParticipantsDiv.querySelectorAll('input');
        
        // Enable inputs for editing
        inputs.forEach(input => {
            input.removeAttribute('disabled');
        });

        // Change the text of the edit button and disable it after editing
        const editButton = document.querySelector(`#editButton_final_${eventId}`);
        editButton.textContent = 'Submit Final Event';
        editButton.onclick = () => submitFinalEvent(eventId);
        // Enable the submit button once editing is allowed
    }

    function submitFinalEvent(eventId) {
        console.log(`Submitting final event ${eventId}`);
        const finalParticipantsDiv = document.getElementById(`final_${eventId}_participants`);
        const rows = finalParticipantsDiv.querySelectorAll('tr[data-participant-id]');
        const updates = [];
    
        rows.forEach(row => {
            const participantId = row.getAttribute('data-participant-id');
            if (participantId !== "null") {
                const mm = row.querySelector('.mm').value;
                const ss = row.querySelector('.ss').value;
                const ms = row.querySelector('.ms').value;
                const time = `${mm}:${ss}:${ms}`;
                updates.push({ swimmer_event_id: participantId, time: time });
            }
        });
    
        fetch('/update_times', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Final times updated:', data);
    
            // Disable all inputs after submission
            const inputs = finalParticipantsDiv.querySelectorAll('input');
            inputs.forEach(input => {
                input.setAttribute('disabled', 'true');
            });
    
            // Update the submit button to indicate submission
            const editButton = document.querySelector(`#editButton_final_${eventId}`);
            editButton.textContent = 'Edit Final Event';
            editButton.onclick = () => editFinalEvent(eventId);
            
        })
        .catch(error => console.error('Error updating final times:', error));
    }
    
    function createFinalsContainer() {
        // We assume "finalsContainer" already exists
        const finalsContainer = document.getElementById('finalsContainer');
        
        const printFinalsButton = document.createElement('button');
        printFinalsButton.id = 'printFinalsButton';
        printFinalsButton.textContent = 'Print Final Events';
        printFinalsButton.addEventListener('click', () => {
            window.print();
        });
    
        finalsContainer.prepend(printFinalsButton);
    
        return finalsContainer;
    }
    function drawEmptyFinal(eventId) {
        const finalParticipantsDiv = document.getElementById(`final_${eventId}_participants`);
        if (!finalParticipantsDiv) {
            console.error(`Element with id final_${eventId}_participants not found`);
            return;
        }

        finalParticipantsDiv.innerHTML = '';
        finalParticipantsDiv.className = 'event-container';

        const finalTable = document.createElement('table');
        finalTable.innerHTML = `
            <thead>
                <tr>
                    <th colspan="7">Final</th>
                </tr>
                <tr>
                    <th class="column-lane">Lane</th>
                    <th class="column-name">Name</th>
                    <th class="column-dob">DOB</th>
                    <th class="column-club">Club/School</th>
                    <th class="column-mm">mm</th>
                    <th class="column-ss">ss</th>
                    <th class="column-ms">ms</th>
                </tr>
            </thead>
            <tbody id="final_${eventId}_1" data-event-id="${eventId}" data-heat-id="1">
                ${window.createEmptyRows(false)} <!-- Now createEmptyRows is global -->
            </tbody>
        `;
        finalParticipantsDiv.appendChild(finalTable);
    }

    function loadFinalParticipants(eventId) {
        fetch(`/top_8_participants?event_id=${eventId}`)
            .then(response => response.json())
            .then(participants => {
                const finalTableBody = document.getElementById(`final_${eventId}_1`);
                participants.forEach((participant, index) => {
                    const row_entry = laneOrder[index] - 1;
                    const row = finalTableBody.querySelectorAll('tr')[row_entry];
                    row.setAttribute('data-participant-id', participant.id);
                    row.cells[1].textContent = participant.swimmer.name;
                    row.cells[2].textContent = participant.swimmer.dob ? new Date(participant.swimmer.dob).toLocaleDateString('en-GB') : '';
                    row.cells[3].textContent = participant.swimmer.club.name || '';
                    if (participant.time) {
                        const [mm, ss, ms] = participant.time.split(':');
                        row.cells[4].querySelector('input').value = mm;
                        row.cells[5].querySelector('input').value = ss;
                        row.cells[6].querySelector('input').value = ms;
                    }
                });
            })
            .catch(error => console.error('Error loading final participants:', error));
    }

    // Export functions to the global scope if needed
    window.prepareFinalEvent = prepareFinalEvent;
    window.editFinalEvent = editFinalEvent; // Expose editEvent function globally
    window.submitFinalEvent = submitFinalEvent;
});
