document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const messageDiv = document.getElementById("message");
  
  // Get login/signup/teacher sections
  const loginSection = document.getElementById("login-section");
  const teacherSection = document.getElementById("teacher-section");
  const signupForm = document.getElementById("signup-form");
  
  // Get token from localStorage
  let authToken = localStorage.getItem("authToken");

  // Function to show message
  function showMessage(text, isSuccess = true) {
    messageDiv.textContent = text;
    messageDiv.className = isSuccess ? "success" : "error";
    messageDiv.classList.remove("hidden");

    // Hide message after 5 seconds
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Function to check authentication status
  async function checkAuth() {
    if (!authToken) {
      loginSection.classList.remove("hidden");
      teacherSection.classList.add("hidden");
      return false;
    }

    try {
      const response = await fetch(`/me?token=${encodeURIComponent(authToken)}`);
      if (response.ok) {
        const user = await response.json();
        loginSection.classList.add("hidden");
        teacherSection.classList.remove("hidden");
        return true;
      } else {
        localStorage.removeItem("authToken");
        authToken = null;
        checkAuth();
        return false;
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      return false;
    }
  }

  // Handle login
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;

      try {
        const response = await fetch(
          `/login?username=${encodeURIComponent(
            username
          )}&password=${encodeURIComponent(password)}`,
          {
            method: "POST",
          }
        );

        const result = await response.json();

        if (response.ok) {
          authToken = result.token;
          localStorage.setItem("authToken", authToken);
          showMessage("Login successful!");
          loginForm.reset();
          checkAuth();
          fetchActivities();
        } else {
          showMessage(result.detail || "Login failed", false);
        }
      } catch (error) {
        showMessage("Login error. Please try again.", false);
        console.error("Login error:", error);
      }
    });
  }

  // Handle logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        if (authToken) {
          await fetch(`/logout?token=${encodeURIComponent(authToken)}`, {
            method: "POST",
          });
        }
      } catch (error) {
        console.error("Logout error:", error);
      }
      localStorage.removeItem("authToken");
      authToken = null;
      loginForm.reset();
      checkAuth();
      fetchActivities();
    });
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons (only if teacher is logged in)
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) => {
                      const deleteBtn = authToken
                        ? `<button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button>`
                        : "";
                      return `<li><span class="participant-email">${email}</span>${deleteBtn}</li>`;
                    }
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown (only if teacher is logged in)
        if (authToken) {
          const option = document.createElement("option");
          option.value = name;
          option.textContent = name;
          activitySelect.appendChild(option);
        }
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    if (!authToken) {
      showMessage("You must be logged in to remove students", false);
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(
          email
        )}&token=${encodeURIComponent(authToken)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message);

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", false);
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", false);
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      if (!authToken) {
        showMessage("You must be logged in to sign up students", false);
        return;
      }

      const email = document.getElementById("email").value;
      const activity = document.getElementById("activity").value;

      try {
        const response = await fetch(
          `/activities/${encodeURIComponent(
            activity
          )}/signup?email=${encodeURIComponent(
            email
          )}&token=${encodeURIComponent(authToken)}`,
          {
            method: "POST",
          }
        );

        const result = await response.json();

        if (response.ok) {
          showMessage(result.message);
          signupForm.reset();

          // Refresh activities list to show updated participants
          fetchActivities();
        } else {
          showMessage(result.detail || "An error occurred", false);
        }
      } catch (error) {
        showMessage("Failed to sign up. Please try again.", false);
        console.error("Error signing up:", error);
      }
    });
  }

  // Initialize app
  checkAuth();
  fetchActivities();
});
