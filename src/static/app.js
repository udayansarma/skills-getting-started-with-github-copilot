document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities", {
        method: "GET",
        headers: {
          "Cache-Control": "no-cache",
          "Pragma": "no-cache"
        }
      });
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      
      // Only clear and repopulate activity select if it's empty or this is the initial load
      if (activitySelect.options.length <= 1) {
        activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
      }

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Create participants list HTML
        const participantsList = details.participants.length > 0
          ? `<ul class="participants-list">${details.participants.map(participant => `
            <li>
              <span class="participant-email">${participant}</span>
              <button class="delete-btn" onclick="unregisterParticipant('${name}', '${participant}')" title="Remove participant">🗑️</button>
            </li>
          `).join('')}</ul>`
          : '<p class="no-participants">No participants yet</p>';

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <strong>Current Participants:</strong>
            ${participantsList}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown only if it doesn't already exist
        let optionExists = false;
        for (let i = 0; i < activitySelect.options.length; i++) {
          if (activitySelect.options[i].value === name) {
            optionExists = true;
            break;
          }
        }
        
        if (!optionExists) {
          const option = document.createElement("option");
          option.value = name;
          option.textContent = name;
          activitySelect.appendChild(option);
        }
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh the activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Make fetchActivities available globally for the unregister function
  window.fetchActivities = fetchActivities;

  // Initialize app
  fetchActivities();
});

// Function to unregister a participant
async function unregisterParticipant(activityName, email) {
  if (!confirm(`Are you sure you want to unregister ${email} from ${activityName}?`)) {
    return;
  }

  try {
    const response = await fetch(
      `/activities/${encodeURIComponent(activityName)}/unregister?email=${encodeURIComponent(email)}`,
      {
        method: "DELETE",
      }
    );

    const result = await response.json();
    const messageDiv = document.getElementById("message");

    if (response.ok) {
      messageDiv.textContent = result.message;
      messageDiv.className = "success";
      // Refresh the activities list to show updated participants
      window.fetchActivities();
    } else {
      messageDiv.textContent = result.detail || "Failed to unregister";
      messageDiv.className = "error";
    }

    messageDiv.classList.remove("hidden");

    // Hide message after 5 seconds
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  } catch (error) {
    const messageDiv = document.getElementById("message");
    messageDiv.textContent = "Failed to unregister. Please try again.";
    messageDiv.className = "error";
    messageDiv.classList.remove("hidden");
    console.error("Error unregistering:", error);
  }
}
