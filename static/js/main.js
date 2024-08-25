document.addEventListener('DOMContentLoaded', () => {
    const step1Form = document.getElementById('add-swimmer-form-step-1');
    const step2Form = document.getElementById('add-swimmer-form-step-2');
    const eventList = document.getElementById('event-list');

    step1Form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(step1Form);
        const ageGroup = formData.get('age_group');
        const gender = formData.get('gender');
        if (ageGroup) {
            const response = await fetch(`/events?age_group=${ageGroup}&gender=${gender}`);
            const events = await response.json();
            eventList.innerHTML = '';
            events.forEach(event => {
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = event.id;
                checkbox.name = 'event_id[]';
                checkbox.id = `event_${event.id}`;
                checkbox.style = "width: 10px";

                const label = document.createElement('label');
                label.htmlFor = `event_${event.id}`;
                label.textContent = event.name;

                const div = document.createElement('div');
                div.appendChild(checkbox);
                div.appendChild(label);
                eventList.appendChild(div);
            });

            document.getElementById('step1_name').value = formData.get('name');
            document.getElementById('step1_dob').value = formData.get('dob');
            document.getElementById('step1_age_group').value = parseInt(formData.get('age_group'));
            document.getElementById('step1_gender').value = formData.get('gender');
            step1Form.style.display = 'none';
            step2Form.style.display = 'block';
        }
    });

    step2Form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(step2Form);
        const data = Object.fromEntries(formData);
        data.event_id = formData.getAll('event_id[]'); // Use the correct event IDs
        const response = await fetch('/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (response.ok) {
            window.location.reload();
        } else {
            alert('Failed to add swimmer');
        }
    });
});
