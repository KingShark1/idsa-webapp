document.addEventListener('DOMContentLoaded', () => {
    let currentEventId = null;
    let draggedRow = null;
    
    // Add event listener for the print button
    const printButton = document.getElementById('printButton');
    printButton.addEventListener('click', () => {
        window.print();
    });

    // Fetch and display events with participants
    function fetchEvents() {
        fetch('/competition_data')
            .then(response => response.json())
            .then(events => {
                const eventsContainer = document.getElementById('eventsContainer');
                eventsContainer.innerHTML = '';
                events.forEach(event => {
                    if (event.participant_count > 0) { // Only include events with participants
                        const ageGroupText = event.age_group === 0 ? 'Senior' : `Group ${event.age_group}`;
                        const genderText = event.gender === 'male' 
                            ? (event.age_group === 0 ? 'Men' : 'Boys')
                            : (event.age_group === 0 ? 'Women' : 'Girls');
                        const eventTitle = `Event No. ${event.id} : ${event.name} ${genderText} ${ageGroupText}`;
    
                        const eventDiv = document.createElement('div');
                        eventDiv.id = `event_${event.id}_container`;
                        eventDiv.className = 'event-container';
    
                        // Add event title and edit button to the container
                        eventDiv.innerHTML = `
                            <h3>${eventTitle}</h3>
                            <button onclick="editEvent(${event.id})" id="editButton_${event.id}" class="edit-button">Edit Event</button>
                            <button onclick="recalculateHeats(${event.id})" id="calculateButton_${event.id}" class="edit-button">Recalculate Heats</button>
                            <div id="event_${event.id}_participants"></div>
                        `;
                        eventsContainer.appendChild(eventDiv);
                        drawEmptyHeats(event.id, event.participant_count, eventTitle);
                        loadEventParticipants(event.id);
                    }
                });
            })
            .catch(error => console.error('Error fetching events:', error));
    }
    async function recalculateHeats(eventId) {
        const url = `/recalculate_heats_lanes/${eventId}`;
    
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
    
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
    
            const data = await response.json();
            console.log(data.message);
        } catch (error) {
            console.error('Error recalculating heats:', error);
        }
    }

    function drawEmptyHeats(eventId, totalParticipants, eventTitle) {
        const eventParticipantsDiv = document.getElementById(`event_${eventId}_participants`);
        eventParticipantsDiv.innerHTML = '';
        eventParticipantsDiv.className = 'event-container'
        const numHeats = Math.ceil(totalParticipants / 8);
    
        for (let i = 0; i < numHeats; i++) {         
            const heatTable = document.createElement('table');
            heatTable.innerHTML = `
                <thead>
                    <tr>
                        <th colspan="7">Heat ${i + 1}</th>
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
                <tbody id="heat_${eventId}_${i + 1}" data-event-id="${eventId}" data-heat-id="${i + 1}">
                    ${createEmptyRows()}
                </tbody>
            `;
            eventParticipantsDiv.appendChild(heatTable);
        }
    }
    // Create empty rows
    function createEmptyRows() {
        let rows = '';
        for (let i = 0; i < 8; i++) {
            rows += `
                <tr data-participant-id="null" draggable="true" ondragstart="dragStart(event)" ondragover="dragOver(event)" ondrop="drop(event)">
                    <td>${i + 1}</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td><input type="text" class="mm" disabled></td>
                    <td><input type="text" class="ss" disabled></td>
                    <td><input type="text" class="ms" disabled></td>
                </tr>
            `;
        }
        return rows;
    }

    function loadEventParticipants(eventId) {
        fetch(`/event_participants?event_id=${eventId}`)
            .then(response => response.json())
            .then(participants => {
                participants.forEach(participant => {
                    const heatBody = document.getElementById(`heat_${eventId}_${participant.heat_id}`);
                    const row = heatBody.querySelectorAll('tr')[participant.lane_id - 1];
                    const timeParts = participant.time ? participant.time.split(':') : ['', '', ''];
                    row.setAttribute('data-participant-id', participant.id);
                    row.cells[1].textContent = participant.swimmer.name;
                    row.cells[2].textContent = participant.swimmer.dob ? new Date(participant.swimmer.dob).toLocaleDateString('en-GB') : '';
                    row.cells[3].textContent = participant.swimmer.club || '';
                    row.cells[4].querySelector('input').value = timeParts[0];
                    row.cells[5].querySelector('input').value = timeParts[1];
                    row.cells[6].querySelector('input').value = timeParts[2];
                });
            })
            .catch(error => console.error('Error loading participants:', error));
    }

    // Drag and drop functionality
    function dragStart(event) {
        draggedRow = event.target.closest('tr');
        event.dataTransfer.effectAllowed = 'move';
    }

    function dragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }

    function drop(event) {
        event.preventDefault();
        const heatBody = event.target.closest('tbody');
        const dropRow = event.target.closest('tr');

        // Ensure the dragged and dropped rows are within the same event
        if (heatBody && dropRow && draggedRow && heatBody.dataset.eventId === draggedRow.closest('tbody').dataset.eventId && dropRow !== draggedRow) {
            // const dropIndex = Array.from(heatBody.children).indexOf(dropRow);
            heatBody.insertBefore(draggedRow, dropRow);

            // Save the updated lane assignments
            updateLaneAssignments(heatBody);
        }
        draggedRow.classList.remove('dragged');
        draggedRow = null;
    }

    function updateLaneAssignments(heatBody) {
        const eventId = heatBody.dataset.eventId;
        const heatId = heatBody.dataset.heatId;
        const rows = Array.from(heatBody.querySelectorAll('tr'));
        rows.forEach((row, index) => {
            const participantId = row.getAttribute('data-participant-id');
            if (participantId !== "null") {
                const laneId = index + 1;
                updateLane(participantId, laneId, heatId);
            }
        });
    }

    function updateLane(swimmerEventId, laneId, heatId) {
        fetch('/update_lane', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ swimmer_event_id: swimmerEventId, lane_id: laneId, heat_id: heatId })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Lane updated:', data);
        })
        .catch(error => console.error('Error updating lane:', error));
    }

    // Edit event
    function editEvent(eventId) {
        currentEventId = eventId;
        const eventParticipantsDiv = document.getElementById(`event_${eventId}_participants`);
        const inputs = eventParticipantsDiv.querySelectorAll('input');
        inputs.forEach(input => {
            input.removeAttribute('disabled');
        });

        const editButton = document.querySelector(`#editButton_${eventId}`);
        editButton.textContent = 'Submit Event';
        editButton.onclick = () => submitEvent(eventId);
        eventParticipantsDiv.scrollIntoView({ behavior: 'smooth' });
    }

    // Submit event
    function submitEvent(eventId) {
        console.log(`Submitting event ${eventId}`);
        const eventParticipantsDiv = document.getElementById(`event_${eventId}_participants`);
        const rows = eventParticipantsDiv.querySelectorAll('tr[data-participant-id]');
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

        console.log("Updates to send:", updates);

        fetch('/update_times', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Times updated:', data);
            const inputs = eventParticipantsDiv.querySelectorAll('input');
            inputs.forEach(input => {
                input.setAttribute('disabled', 'true');
            });
            const editButton = document.querySelector(`#editButton_${eventId}`);
            editButton.textContent = 'Edit Event';
            editButton.onclick = () => editEvent(eventId);
            
            const calculateButton = document.querySelector(`#calculateButton_${eventId}`);
            calculateButton.textContent = 'Recalculate Heats';
            calculateButton.onclick() = () => recalculateHeats(eventId);

        })
        .catch(error => console.error('Error updating times:', error));
    }

    // Fetch events on page load
    fetchEvents();

    // Export functions to the global scope
    window.recalculateHeats = recalculateHeats;
    window.editEvent = editEvent;
    window.submitEvent = submitEvent;
    window.dragStart = dragStart;
    window.dragOver = dragOver;
    window.drop = drop;
});
