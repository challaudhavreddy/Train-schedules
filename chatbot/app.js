const trainList = document.querySelector("#train-list");
const resultsCount = document.querySelector("#results-count");
const emptyState = document.querySelector("#empty-state");
const fromInput = document.querySelector("#from-input");
const toInput = document.querySelector("#to-input");
const dateInput = document.querySelector("#date-input");
const chatInput = document.querySelector("#chat-input");
const chatMessages = document.querySelector("#chat-messages");
const sendButton = document.querySelector("#send-button");
const chatHistory = [];
let trains = [];
let selectedType = "All";

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function renderTrain(train) {
  return `
    <details class="train-card">
      <summary class="train-main">
        <div class="train-identity">
          <span class="train-name-row"><span class="train-name">${escapeHtml(train.name)}</span><span class="train-badge">${escapeHtml(train.type)}</span></span>
          <span class="train-number">#${escapeHtml(train.number)} · ${escapeHtml(train.days)}</span>
        </div>
        <div class="journey-times">
          <div class="time-block"><span class="time-value">${escapeHtml(train.depart)}</span><span class="station-name">${escapeHtml(train.from)}</span></div>
          <div class="journey-line"><span>›</span></div>
          <div class="time-block"><span class="time-value">${escapeHtml(train.arrive)}</span><span class="station-name">${escapeHtml(train.to)}</span></div>
        </div>
        <div class="duration-block"><span class="duration-value">${escapeHtml(train.duration)}</span><span class="duration-label">duration</span></div>
        <span class="train-status">${escapeHtml(train.status)}</span>
        <svg class="expand-chevron" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="m5 7.5 5 5 5-5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </summary>
      <div class="train-extra">
        <div class="extra-grid">
          <div class="extra-item"><span class="extra-label">Departure</span><span class="extra-value">${escapeHtml(train.from)} · ${escapeHtml(train.depart)}</span></div>
          <div class="extra-item"><span class="extra-label">Arrival</span><span class="extra-value">${escapeHtml(train.to)} · ${escapeHtml(train.arrive)}</span></div>
          <div class="extra-item"><span class="extra-label">Platform</span><span class="extra-value">${escapeHtml(train.platform)}</span></div>
          <div class="extra-item"><span class="extra-label">Sample fare</span><span class="extra-value">${escapeHtml(train.fare)}</span></div>
          <div class="extra-item"><span class="extra-label">Runs</span><span class="extra-value">${escapeHtml(train.days)}</span></div>
        </div>
        <div class="via-list"><strong>En route:</strong> ${train.via.map(escapeHtml).join(" · ")}</div>
      </div>
    </details>`;
}

function updateTrains() {
  const origin = fromInput.value.trim().toLocaleLowerCase();
  const destination = toInput.value.trim().toLocaleLowerCase();
  const travelDate = dateInput.value;
  const weekday = travelDate
    ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][
        new Date(`${travelDate}T00:00:00`).getDay()
      ]
    : null;
  const filtered = trains.filter((train) => {
    const typeMatches = selectedType === "All" || train.type === selectedType;
    const originMatches = !origin || train.from.toLocaleLowerCase().includes(origin);
    const destinationMatches = !destination || train.to.toLocaleLowerCase().includes(destination);
    const dayMatches = !weekday
      || train.days === "Daily"
      || (train.days === "Daily except Sunday" && weekday !== "Sun")
      || train.days.split(", ").includes(weekday);
    return typeMatches && originMatches && destinationMatches && dayMatches;
  });

  resultsCount.textContent = `${filtered.length} ${filtered.length === 1 ? "route" : "routes"}`;
  trainList.innerHTML = filtered.map(renderTrain).join("");
  emptyState.classList.toggle("hidden", filtered.length > 0);
  trainList.classList.toggle("hidden", filtered.length === 0);

  trainList.querySelectorAll(".train-card").forEach((card) => {
    card.addEventListener("toggle", () => {
      card.classList.toggle("expanded", card.open);
    });
  });
}

async function loadTrains() {
  try {
    const response = await fetch("/api/trains");
    if (!response.ok) throw new Error("The timetable could not be loaded.");
    const data = await response.json();
    trains = data.trains;
    updateTrains();
  } catch (error) {
    trainList.innerHTML = `<p class="data-disclaimer">${escapeHtml(error.message)} Refresh the page to try again.</p>`;
    resultsCount.textContent = "Unavailable";
  }
}

async function checkConnection() {
  const status = document.querySelector("#connection-status");
  const indicator = document.querySelector("#online-dot");
  try {
    const response = await fetch("/api/status");
    if (!response.ok) throw new Error("Status check failed");
    const data = await response.json();
    if (data.connected) {
      status.textContent = `${data.model} · ready`;
      indicator.classList.remove("disconnected");
    } else {
      status.textContent = `${data.model} · unavailable`;
      indicator.classList.add("disconnected");
    }
  } catch {
    status.textContent = "Local AI unavailable";
    indicator.classList.add("disconnected");
  }
}

function addMessage(text, role, extraClass = "") {
  const bubble = document.createElement("div");
  bubble.className = `message ${role}${extraClass ? ` ${extraClass}` : ""}`;
  bubble.textContent = text;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return bubble;
}

async function sendMessage(message) {
  const question = message.trim();
  if (!question || sendButton.disabled) return;

  document.querySelector("#suggestions").classList.add("hidden");
  addMessage(question, "user");
  chatHistory.push({ role: "user", content: question });
  chatInput.value = "";
  chatInput.style.height = "auto";
  sendButton.disabled = true;
  const loadingMessage = addMessage("Thinking through the timetable…", "assistant", "typing");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question, history: chatHistory.slice(0, -1) }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Railwise couldn't answer just now.");
    loadingMessage.textContent = data.reply;
    loadingMessage.classList.remove("typing");
    chatHistory.push({ role: "assistant", content: data.reply });
  } catch (error) {
    loadingMessage.textContent = error.message;
    loadingMessage.classList.remove("typing");
    loadingMessage.classList.add("error");
    chatHistory.pop();
  } finally {
    sendButton.disabled = false;
    chatInput.focus();
  }
}

document.querySelector("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  updateTrains();
  document.querySelector("#schedules").scrollIntoView({ behavior: "smooth", block: "start" });
});

document.querySelector("#swap-button").addEventListener("click", () => {
  const departure = fromInput.value;
  fromInput.value = toInput.value;
  toInput.value = departure;
});

document.querySelectorAll(".filter-button").forEach((button) => {
  button.addEventListener("click", () => {
    selectedType = button.dataset.filter;
    document.querySelector(".filter-button.selected").classList.remove("selected");
    button.classList.add("selected");
    updateTrains();
  });
});

document.querySelectorAll(".route-chip").forEach((button) => {
  button.addEventListener("click", () => {
    fromInput.value = button.dataset.from;
    toInput.value = button.dataset.to;
    updateTrains();
    document.querySelector("#schedules").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

document.querySelector("#reset-button").addEventListener("click", () => {
  fromInput.value = "";
  toInput.value = "";
  selectedType = "All";
  document.querySelector(".filter-button.selected").classList.remove("selected");
  document.querySelector('[data-filter="All"]').classList.add("selected");
  updateTrains();
});

document.querySelector("#chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(chatInput.value);
});

chatInput.addEventListener("input", () => {
  chatInput.style.height = "auto";
  chatInput.style.height = `${Math.min(chatInput.scrollHeight, 84)}px`;
});

document.querySelectorAll(".suggestion-chip").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.textContent));
});

loadTrains();
checkConnection();
