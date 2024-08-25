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


});
