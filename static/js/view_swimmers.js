document.addEventListener('DOMContentLoaded', () => {
    // Fetch swimmers from backend and populate table
    function fetchSwimmers(searchQuery = '') {
        let url = '/swimmers/';
        if (searchQuery) {
            url += `?name=${encodeURIComponent(searchQuery)}`;
        }

        fetch(url)
            .then(response => response.json())
            .then(swimmers => {
                if (!Array.isArray(swimmers)) {
                    throw new Error("Response is not an array");
                }
                const swimmersBody = document.getElementById('swimmersBody');
                swimmersBody.innerHTML = '';
                swimmers.forEach(swimmer => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><button onclick="deleteSwimmer(${swimmer.id})">Delete</button></td>
                        <td class="editable" data-field="name">${swimmer.name}</td>
                        <td class="editable" data-field="dob">${swimmer.dob ? new Date(swimmer.dob).toLocaleDateString('en-GB') : ''}</td>
                        <td class="editable" data-field="age_group">${swimmer.age_group}</td>
                        <td class="editable" data-field="gender">${swimmer.gender}</td>
                        <td class="editable" data-field="sfi_id">${swimmer.sfi_id || ''}</td>
                        <td>${swimmer.club || ''}</td>
                        <td>${swimmer.events ? swimmer.events.map(ev => ev.event.name).join(', ') : ''}</td>
                        <td><button onclick='showEventPopup(${swimmer.id}, "${swimmer.name}", ${JSON.stringify(swimmer.events)})'>Manage Events</button></td>

                    `;
                    swimmersBody.appendChild(row);
                });
            })
            .catch(error => console.error('Error fetching swimmers:', error));
    }

    // Fetch swimmers on page load
    fetchSwimmers();

    // Handle search form submission
    document.getElementById('searchForm').addEventListener('submit', (event) => {
        event.preventDefault();
        const searchName = document.getElementById('searchName').value;
        fetchSwimmers(searchName);
    });

    // Function to delete swimmer
    window.deleteSwimmer = function(swimmerId) {
        if (confirm('Are you sure you want to delete this swimmer?')) {
            fetch(`/swimmers/${swimmerId}`, {
                method: 'DELETE',
            })
                .then(response => {
                    if (response.ok) {
                        fetchSwimmers(); // Refresh the swimmers list
                    } else {
                        alert('Failed to delete swimmer');
                    }
                })
                .catch(error => console.error('Error deleting swimmer:', error));
        }
    };

    // Function to show popup with events and allow deleting them
    window.showEventPopup = function(swimmerId, swimmerName, events) {
        // Create the popup content
        const popupContent = document.createElement('div');
        console.log("Inside ShowEventPopup");
        popupContent.classList.add('popup-content');
        popupContent.innerHTML = `
            <h3>Manage Events for ${swimmerName}</h3>
            <ul id="eventList">
                ${events.map(event => `<li>${event.event.name} <button onclick="deleteEvent(${swimmerId}, ${event.id})">❌</button></li>`).join('')}
            </ul>
            <button onclick="closePopup()">Close</button>
        `;

        // Create the popup container
        const popup = document.createElement('div');
        popup.classList.add('popup');
        popup.appendChild(popupContent);

        // Append the popup to the body
        document.body.appendChild(popup);
    };

    // Function to close the popup
    window.closePopup = function() {
        const popup = document.querySelector('.popup');
        if (popup) {
            popup.remove();
        }
    };

    // Function to delete an event for a swimmer
    window.deleteEvent = function(swimmerId, eventId) {
        if (confirm('Are you sure you want to delete this event?')) {
            fetch(`/swimmers/${swimmerId}/events/${eventId}`, {
                method: 'DELETE',
            })
                .then(response => {
                    if (response.ok) {
                        alert('Event deleted successfully');
                        closePopup();
                        fetchSwimmers(); // Refresh swimmers after event is deleted
                    } else {
                        alert('Failed to delete event');
                    }
                })
                .catch(error => console.error('Error deleting event:', error));
        }
    };
});
