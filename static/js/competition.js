document.addEventListener("DOMContentLoaded", () => {
  let currentEventId = null;
  let draggedRow = null;
  let currentDay = 1;
  let eventsByDay = {};

  // Print Normal Events Button
  const printNormalEventsButton = document.getElementById(
    "printNormalEventsButton",
  );
  printNormalEventsButton.addEventListener("click", () => {
    const eventsContainer = document.getElementById("eventsContainer");
    const finalsContainer = document.getElementById("finalsContainer");

    // Hide finals container during normal events print
    finalsContainer.style.display = "none";

    // Trigger print
    window.print();

    // Reset the display after printing
    finalsContainer.style.display = "block";
  });

  // Print Final Events Button
  const printFinalEventsButton = document.getElementById(
    "printFinalEventsButton",
  );
  printFinalEventsButton.addEventListener("click", () => {
    const eventsContainer = document.getElementById("eventsContainer");
    const finalsContainer = document.getElementById("finalsContainer");

    // Hide normal events container during finals print
    eventsContainer.style.display = "none";

    // Trigger print
    window.print();

    // Reset the display after printing
    eventsContainer.style.display = "block";
  });

  // Fetch configuration from config.json
  function fetchConfig() {
    return fetch("/static/config.json") // Adjust the path if necessary
      .then((response) => response.json())
      .then((config) => {
        eventsByDay = config.eventsByDay;
        totalDays = config.totalDays;
      })

      .catch((error) => console.error("Error fetching config:", error));
  }

  // Create day selector
  function createDaySelector() {
    const daySelector = document.getElementById("daySelector");
    daySelector.innerHTML = "";

    for (let i = 1; i <= totalDays; i++) {
      const dayButton = document.createElement("button");
      dayButton.textContent = `Day ${i}`;
      dayButton.className = `day-button${i === currentDay ? " active" : ""}`;
      dayButton.onclick = () => {
        currentDay = i;
        updateDaySelector();
        fetchEvents();
      };
      daySelector.appendChild(dayButton);
    }
  }

  function updateDaySelector() {
    const buttons = document.querySelectorAll(".day-button");
    buttons.forEach((button, index) => {
      button.classList.toggle("active", index + 1 === currentDay);
    });
  }

  // Fetch and display events for the current day
  function fetchEvents() {
    const [startId, endId] = eventsByDay[currentDay];
    const eventsContainer = document.getElementById("eventsContainer");
    eventsContainer.innerHTML = "";
    const finalsContainer = document.getElementById("finalsContainer");
    finalsContainer.innerHTML = "";

    fetch("/competition_data")
      .then((response) => response.json())
      .then((events) => {
        const filteredEvents = events.filter(
          (event) => event.id >= startId && event.id <= endId,
        );
        filteredEvents.forEach((event) => {
          if (event.participant_count > 0) {
            // Only include events with participants
            const ageGroupText =
              event.age_group === 0 ? "Senior" : `Group ${event.age_group}`;
            const genderText =
              event.gender === "male"
                ? event.age_group === 0
                  ? "Men"
                  : "Boys"
                : event.age_group === 0
                  ? "Women"
                  : "Girls";
            const eventTitle = `Event No. ${event.id} : ${event.name} ${genderText} ${ageGroupText}`;

            const eventDiv = document.createElement("div");
            eventDiv.id = `event_${event.id}_container`;
            eventDiv.className = "event-container";

            // Add event title and edit button to the container
            eventDiv.innerHTML = `
                            <div class="event-wrapper">
                                <h3>${eventTitle}</h3>
                                <button onclick="editEvent(${event.id})" id="editButton_${event.id}" class="edit-button">Edit Event</button>
                                <button onclick="recalculateHeats(${event.id})" id="calculateButton_${event.id}" class="edit-button">Recalculate Heats</button>
                                <div id="event_${event.id}_participants"></div>
                            </div>
                        `;
            eventsContainer.appendChild(eventDiv);
            drawEmptyHeats(event.id, event.participant_count, eventTitle);
            loadEventParticipants(event.id);

            // Handle finals

            if (event.time_trial === false) {
              window.prepareFinalEvent(event, eventTitle);
            }
          }
        });
      })
      .catch((error) => console.error("Error fetching events:", error));
  }

  async function recalculateHeats(eventId) {
    const url = `/recalculate_heats_lanes/${eventId}`;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      console.log(data.message);
    } catch (error) {
      console.error("Error recalculating heats:", error);
    }
  }

  function drawEmptyHeats(eventId, totalParticipants, eventTitle) {
    const eventParticipantsDiv = document.getElementById(
      `event_${eventId}_participants`,
    );
    eventParticipantsDiv.innerHTML = "";
    eventParticipantsDiv.className = "event-container";
    const isRelay = eventTitle.toLowerCase().includes("relay");
    const numHeats = Math.ceil(totalParticipants / 8);

    for (let i = 0; i < numHeats; i++) {
      const heatTable = document.createElement("table");
      heatTable.innerHTML = `
                <thead>
                    <tr>
                        <th colspan="7">${eventTitle}</th>
                    </tr>
                    <tr>
                        <th colspan="7">Heat ${i + 1}</th>
                    </tr>
                    <tr>
                    <th class="column-lane">Lane</th>
                    <th class="column-name">Name</th>
                    ${isRelay ? "" : '<th class="column-dob">DOB</th>'}
                    <th class="column-club">Club/School</th>
                    <th class="column-mm">mm</th>
                    <th class="column-ss">ss</th>
                    <th class="column-ms">ms</th>
                    </tr>
                </thead>
                <tbody id="heat_${eventId}_${i + 1}" data-event-id="${eventId}" data-heat-id="${i + 1}">
                    ${createEmptyRows(isRelay, eventId, i + 1)}
                </tbody>
            `;
      eventParticipantsDiv.appendChild(heatTable);
    }
  }
  // Create empty rows
  function createEmptyRows(isRelay, eventId, heatId) {
    let rows = "";
    for (let i = 0; i < 8; i++) {
      rows += `
                <tr data-participant-id="null" draggable="true" ondragstart="dragStart(event)" ondragover="dragOver(event)" ondrop="drop(event)">
                    <td>${i + 1}</td>
                    <td><button class="add-swimmer-button" onclick="openSwimmerDropdown(${i + 1}, ${eventId}, ${heatId})">+</button></td>
                    ${isRelay ? "" : "<td></td>"}
                    <td></td>
                    <td><input type="text" class="mm" disabled></td>
                    <td><input type="text" class="ss" disabled></td>
                    <td><input type="text" class="ms" disabled></td>
                </tr>
            `;
    }
    return rows;
  }

  window.createEmptyRows = createEmptyRows;

  function loadEventParticipants(eventId) {
    fetch(`/event_participants?event_id=${eventId}`)
      .then((response) => response.json())
      .then((participants) => {
        participants.forEach((participant) => {
          const heatBody = document.getElementById(
            `heat_${eventId}_${participant.heat_id}`,
          );
          const row = heatBody.querySelectorAll("tr")[participant.lane_id - 1];

          if (Array.isArray(participant.swimmers)) {
            // Relay event: Display multiple swimmer names in a single row
            row.setAttribute(
              "data-participant-id",
              `relay-${participant.heat_id}-${participant.lane_id}`,
            );
            row.cells[1].innerHTML = participant.swimmers
              .map((swimmer) => `<div>${swimmer}</div>`)
              .join(""); // Display each swimmer in a new line
            row.setAttribute("data-relay-id", participant.relay_event_id); // Store relay-event-id as a data attribute
            row.cells[2].textContent = participant.club;

            // Populate the time fields
            const timeParts = participant.time
              ? participant.time.split(":")
              : ["", "", ""];
            row.cells[3].querySelector("input.mm").value = timeParts[0];
            row.cells[4].querySelector("input.ss").value = timeParts[1];
            row.cells[5].querySelector("input.ms").value = timeParts[2];
          } else {
            // Regular event: Display individual swimmer information
            const timeParts = participant.time
              ? participant.time.split(":")
              : ["", "", ""];
            row.setAttribute("data-participant-id", participant.id);
            row.cells[1].textContent = participant.swimmer.name;
            row.cells[2].textContent = participant.swimmer.dob
              ? new Date(participant.swimmer.dob).toLocaleDateString("en-GB")
              : "";
            row.cells[3].textContent = participant.swimmer.club.name || "";

            // Populate the time fields
            row.cells[4].querySelector("input.mm").value = timeParts[0];
            row.cells[5].querySelector("input.ss").value = timeParts[1];
            row.cells[6].querySelector("input.ms").value = timeParts[2];
          }
        });
      })
      .catch((error) => console.error("Error loading participants:", error));
  }

  // Drag and drop functionality
  function dragStart(event) {
    draggedRow = event.target.closest("tr");
    event.dataTransfer.effectAllowed = "move";
  }

  function dragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }

  function drop(event) {
    event.preventDefault();
    const heatBody = event.target.closest("tbody");
    const dropRow = event.target.closest("tr");

    // Ensure the dragged and dropped rows are within the same event
    if (
      heatBody &&
      dropRow &&
      draggedRow &&
      heatBody.dataset.eventId ===
        draggedRow.closest("tbody").dataset.eventId &&
      dropRow !== draggedRow
    ) {
      // const dropIndex = Array.from(heatBody.children).indexOf(dropRow);
      heatBody.insertBefore(draggedRow, dropRow);

      // Save the updated lane assignments
      updateLaneAssignments(heatBody);
    }
    draggedRow.classList.remove("dragged");
    draggedRow = null;
  }

  function updateLaneAssignments(heatBody) {
    const eventId = heatBody.dataset.eventId;
    const heatId = heatBody.dataset.heatId;
    const rows = Array.from(heatBody.querySelectorAll("tr"));
    rows.forEach((row, index) => {
      const participantId = row.getAttribute("data-participant-id");
      if (participantId !== "null") {
        const laneId = index + 1;
        updateLane(participantId, laneId, heatId);
      }
    });
  }

  function updateLane(swimmerEventId, laneId, heatId) {
    fetch("/update_lane", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        swimmer_event_id: swimmerEventId,
        lane_id: laneId,
        heat_id: heatId,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Lane updated:", data);
      })
      .catch((error) => console.error("Error updating lane:", error));
  }

  // Edit event
  function editEvent(eventId) {
    currentEventId = eventId;
    const eventParticipantsDiv = document.getElementById(
      `event_${eventId}_participants`,
    );
    const inputs = eventParticipantsDiv.querySelectorAll("input");
    inputs.forEach((input) => {
      input.removeAttribute("disabled");
    });

    const editButton = document.querySelector(`#editButton_${eventId}`);
    editButton.textContent = "Submit Event";
    editButton.onclick = () => submitEvent(eventId);
    eventParticipantsDiv.scrollIntoView({ behavior: "smooth" });
  }

  function submitEvent(eventId) {
    console.log(`Submitting event ${eventId}`);
    const eventParticipantsDiv = document.getElementById(
      `event_${eventId}_participants`,
    );
    const rows = eventParticipantsDiv.querySelectorAll(
      "tr[data-participant-id]",
    );
    const updates = [];
    const eventName = document.querySelector(
      `#event_${eventId}_container h3`,
    ).textContent;

    rows.forEach((row) => {
      const participantId = row.getAttribute("data-participant-id");
      if (participantId !== "null") {
        const mm = row.querySelector(".mm").value;
        const ss = row.querySelector(".ss").value;
        const ms = row.querySelector(".ms").value;
        const time = `${mm}:${ss}:${ms}`;

        if (eventName.includes("Relay")) {
          const relay_id = row.getAttribute("data-relay-id"); // Assuming club_id is stored as a data attribute
          updates.push({ relay_event_id: relay_id, time: time });
        } else {
          updates.push({ swimmer_event_id: participantId, time: time });
        }
      }
    });

    // const url = eventName.includes("Relay") ? '/relay_submission_event' : '/update_times';
    const url = "/update_times";
    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Times updated:", data);
        const inputs = eventParticipantsDiv.querySelectorAll("input");
        inputs.forEach((input) => {
          input.setAttribute("disabled", "true");
        });
        const editButton = document.querySelector(`#editButton_${eventId}`);
        editButton.textContent = "Edit Event";
        editButton.onclick = () => editEvent(eventId);

        const calculateButton = document.querySelector(
          `#calculateButton_${eventId}`,
        );
        calculateButton.textContent = "Recalculate Heats";
        calculateButton.onclick = () => recalculateHeats(eventId);
      })
      .catch((error) => console.error("Error updating times:", error));
  }

  // Function to open a dropdown with eligible swimmers
  function openSwimmerDropdown(laneIndex, eventId, heatId) {
    // Fetch eligible swimmers based on the event's age group and gender
    fetch(`/eligible_swimmers?event_id=${eventId}`) // Modify this to fetch the correct swimmers based on eventId
      .then((response) => response.json())
      .then((swimmers) => {
        // Create a dropdown element
        const dropdown = document.createElement("select");
        dropdown.className = "swimmer-dropdown";
        swimmers.forEach((swimmer) => {
          const option = document.createElement("option");
          option.value = swimmer.id;
          option.text = `${swimmer.name} (${new Date(swimmer.dob).toLocaleDateString("en-GB")}) - ${swimmer.club.name}`;
          dropdown.appendChild(option);
        });

        // Add an event listener to handle swimmer selection
        dropdown.addEventListener("change", (event) => {
          const swimmerId = event.target.value;
          assignSwimmerToHeat(swimmerId, laneIndex, eventId, heatId); // Function to handle swimmer assignment
        });

        // Insert the dropdown into the appropriate cell
        const row = document.querySelector(
          `#heat_${eventId}_${heatId} tr:nth-child(${laneIndex})`,
        );
        row.cells[1].innerHTML = ""; // Clear the plus button
        row.cells[1].appendChild(dropdown); // Insert the dropdown
      })
      .catch((error) =>
        console.error("Error fetching eligible swimmers:", error),
      );
  }

  function assignSwimmerToHeat(swimmerId, laneIndex, eventId, heatId) {
    // Fetch swimmer details to fill in the row
    fetch(`/swimmers/${swimmerId}`)
      .then((response) => response.json())
      .then((swimmer) => {
        console.log(swimmer.dob);
        const row = document.querySelector(
          `#heat_${eventId}_${heatId} tr:nth-child(${laneIndex})`,
        );
        row.setAttribute("data-participant-id", swimmerId);
        row.cells[1].textContent = swimmer.name;
        row.cells[2].textContent = new Date(swimmer.dob).toLocaleDateString(
          "en-GB",
        );
        row.cells[3].textContent = swimmer.club.name;

        // Send a request to the backend to assign the swimmer to this event and lane
        fetch("/assign_swimmer_to_event", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            swimmer_id: swimmer.id,
            event_id: eventId,
            heat_id: heatId,
            lane_id: laneIndex,
          }),
        })
          .then((response) => {
            if (!response.ok) {
              throw new Error("Failed to assign swimmer to heat");
            }
          })
          .catch((error) =>
            console.error("Error assigning swimmer to heat:", error),
          );
      });
  }

  // Fetch events on page load
  fetchConfig().then(() => {
    createDaySelector();
    fetchEvents();
  });
  // Export functions to the global scope
  window.recalculateHeats = recalculateHeats;
  window.editEvent = editEvent;
  window.submitEvent = submitEvent;
  window.dragStart = dragStart;
  window.dragOver = dragOver;
  window.drop = drop;
  window.openSwimmerDropdown = openSwimmerDropdown;
});
