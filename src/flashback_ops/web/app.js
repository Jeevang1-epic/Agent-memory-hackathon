const assistForm = document.getElementById("assistForm");
const feedbackForm = document.getElementById("feedbackForm");
const statusBtn = document.getElementById("statusBtn");
const seedBtn = document.getElementById("seedBtn");
const scenarioSelect = document.getElementById("scenarioSelect");
const applyScenarioBtn = document.getElementById("applyScenarioBtn");
const backendValue = document.getElementById("backendValue");
const entriesValue = document.getElementById("entriesValue");
const sessionsValue = document.getElementById("sessionsValue");
const boostValue = document.getElementById("boostValue");
const withoutConfidence = document.getElementById("withoutConfidence");
const withConfidence = document.getElementById("withConfidence");
const withoutSteps = document.getElementById("withoutSteps");
const withSteps = document.getElementById("withSteps");
const takeawayList = document.getElementById("takeawayList");
const memoryTableBody = document.getElementById("memoryTableBody");
let scenarios = [];

async function callApi(path, payload = null, method = "GET") {
  const init = {
    method,
    headers: {
      "Content-Type": "application/json"
    }
  };
  if (payload) {
    init.body = JSON.stringify(payload);
  }
  const response = await fetch(path, init);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "request failed");
  }
  return response.json();
}

function lines(value) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function commaList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function renderList(target, values, asOrdered = false) {
  target.innerHTML = "";
  const tag = asOrdered ? "li" : "li";
  values.forEach((value) => {
    const node = document.createElement(tag);
    node.textContent = value;
    target.appendChild(node);
  });
}

function renderMemoryRows(items) {
  memoryTableBody.innerHTML = "";
  items.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.incident_id || item.memory_id}</td>
      <td>${item.service}</td>
      <td>${item.score.toFixed(3)}</td>
      <td>${item.outcome}</td>
      <td>${item.root_cause}</td>
    `;
    memoryTableBody.appendChild(tr);
  });
}

function setFeedbackContext(payload) {
  feedbackForm.elements.query_id.value = payload.query_id;
  feedbackForm.elements.session_id.value = payload.session_id;
}

async function refreshStatus() {
  const payload = await callApi("/api/status");
  backendValue.textContent = payload.backend;
  entriesValue.textContent = String(payload.memory_entries);
  sessionsValue.textContent = String(payload.sessions);
}

function hydrateForm(payload) {
  assistForm.elements.service.value = payload.service || "";
  assistForm.elements.severity.value = payload.severity || "medium";
  assistForm.elements.objective.value = payload.objective || "";
  assistForm.elements.symptoms.value = (payload.symptoms || []).join("\n");
  assistForm.elements.logs.value = payload.logs || "";
  assistForm.elements.tags.value = (payload.tags || []).join(", ");
}

async function loadScenarios() {
  scenarios = await callApi("/api/demo/scenarios");
  scenarioSelect.innerHTML = "";
  scenarios.forEach((scenario) => {
    const option = document.createElement("option");
    option.value = scenario.id;
    option.textContent = scenario.name;
    scenarioSelect.appendChild(option);
  });
}

assistForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    service: assistForm.elements.service.value.trim(),
    severity: assistForm.elements.severity.value.trim(),
    objective: assistForm.elements.objective.value.trim(),
    symptoms: lines(assistForm.elements.symptoms.value),
    logs: assistForm.elements.logs.value.trim(),
    tags: commaList(assistForm.elements.tags.value),
    top_k: 4
  };
  try {
    const response = await callApi("/api/assist", payload, "POST");
    boostValue.textContent = response.memory_boost.toFixed(2);
    withoutConfidence.textContent = `Confidence ${response.without_memory.confidence.toFixed(2)}`;
    withConfidence.textContent = `Confidence ${response.with_memory.confidence.toFixed(2)}`;
    renderList(withoutSteps, response.without_memory.steps, true);
    renderList(withSteps, response.with_memory.steps, true);
    renderList(takeawayList, response.tactical_takeaways, false);
    renderMemoryRows(response.recalled_memories);
    setFeedbackContext(response);
    await refreshStatus();
  } catch (error) {
    alert(error.message);
  }
});

feedbackForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const queryId = feedbackForm.elements.query_id.value.trim();
  const sessionId = feedbackForm.elements.session_id.value.trim();
  if (!queryId || !sessionId) {
    alert("Run an assist call first.");
    return;
  }
  const payload = {
    query_id: queryId,
    session_id: sessionId,
    outcome: feedbackForm.elements.outcome.value,
    useful_steps: lines(feedbackForm.elements.useful_steps.value),
    notes: feedbackForm.elements.notes.value.trim()
  };
  try {
    await callApi("/api/feedback", payload, "POST");
    feedbackForm.elements.useful_steps.value = "";
    feedbackForm.elements.notes.value = "";
    await refreshStatus();
  } catch (error) {
    alert(error.message);
  }
});

statusBtn.addEventListener("click", async () => {
  try {
    await refreshStatus();
  } catch (error) {
    alert(error.message);
  }
});

seedBtn.addEventListener("click", async () => {
  try {
    await callApi("/api/seed", {}, "POST");
    await refreshStatus();
  } catch (error) {
    alert(error.message);
  }
});

applyScenarioBtn.addEventListener("click", () => {
  const selected = scenarios.find((item) => item.id === scenarioSelect.value);
  if (selected) {
    hydrateForm(selected.payload);
  }
});

async function bootstrap() {
  try {
    await loadScenarios();
    if (scenarios.length > 0) {
      hydrateForm(scenarios[0].payload);
    }
    await refreshStatus();
  } catch (error) {
    alert(error.message);
  }
}

bootstrap();
