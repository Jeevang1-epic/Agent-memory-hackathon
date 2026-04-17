const assistForm = document.getElementById("assistForm");
const feedbackForm = document.getElementById("feedbackForm");
const subscriptionForm = document.getElementById("subscriptionForm");
const seedBtn = document.getElementById("seedBtn");
const freshBtn = document.getElementById("freshBtn");
const runPlanBtn = document.getElementById("runPlanBtn");
const saveFeedbackBtn = document.getElementById("saveFeedbackBtn");
const requestAccessBtn = document.getElementById("requestAccessBtn");
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
const copyWithoutBtn = document.getElementById("copyWithoutBtn");
const copyWithBtn = document.getElementById("copyWithBtn");
const toast = document.getElementById("toast");
const FORM_STATE_KEY = "flashback_ops_form_state_v1";
let scenarios = [];

async function callApi(path, payload = null, method = "GET") {
  const init = { method, headers: {} };
  if (payload) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(payload);
  }
  const response = await fetch(path, init);
  if (!response.ok) {
    let message = "Request failed";
    try {
      const parsed = await response.json();
      message = parsed.detail || parsed.message || message;
    } catch {
      const raw = await response.text();
      message = raw || message;
    }
    throw new Error(message);
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

function listText(values) {
  return values.map((value, index) => `${index + 1}. ${value}`).join("\n");
}

function setFeedbackContext(payload) {
  feedbackForm.elements.query_id.value = payload.query_id;
  feedbackForm.elements.session_id.value = payload.session_id;
}

function clearFeedbackContext() {
  feedbackForm.elements.query_id.value = "";
  feedbackForm.elements.session_id.value = "";
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timeoutId);
  showToast.timeoutId = window.setTimeout(() => {
    toast.classList.remove("show");
  }, 2200);
}

async function withButtonBusy(button, busyText, task) {
  const previous = button.textContent;
  button.disabled = true;
  button.textContent = busyText;
  try {
    return await task();
  } finally {
    button.disabled = false;
    button.textContent = previous;
  }
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

function saveFormState() {
  const state = {
    service: assistForm.elements.service.value,
    severity: assistForm.elements.severity.value,
    objective: assistForm.elements.objective.value,
    symptoms: assistForm.elements.symptoms.value,
    logs: assistForm.elements.logs.value,
    tags: assistForm.elements.tags.value,
    scenario: scenarioSelect.value
  };
  localStorage.setItem(FORM_STATE_KEY, JSON.stringify(state));
}

function restoreFormState() {
  const raw = localStorage.getItem(FORM_STATE_KEY);
  if (!raw) {
    return false;
  }
  try {
    const state = JSON.parse(raw);
    assistForm.elements.service.value = state.service || assistForm.elements.service.value;
    assistForm.elements.severity.value = state.severity || assistForm.elements.severity.value;
    assistForm.elements.objective.value = state.objective || assistForm.elements.objective.value;
    assistForm.elements.symptoms.value = state.symptoms || assistForm.elements.symptoms.value;
    assistForm.elements.logs.value = state.logs || assistForm.elements.logs.value;
    assistForm.elements.tags.value = state.tags || assistForm.elements.tags.value;
    if (state.scenario && scenarios.some((item) => item.id === state.scenario)) {
      scenarioSelect.value = state.scenario;
    }
    return true;
  } catch {
    return false;
  }
}

function resetOutputs() {
  boostValue.textContent = "0.00";
  withoutConfidence.textContent = "Confidence 0.00";
  withConfidence.textContent = "Confidence 0.00";
  withoutSteps.innerHTML = "";
  withSteps.innerHTML = "";
  takeawayList.innerHTML = "";
  memoryTableBody.innerHTML = "";
  feedbackForm.elements.useful_steps.value = "";
  feedbackForm.elements.notes.value = "";
  clearFeedbackContext();
}

function freshWorkspace(clearSaved = false) {
  const selected = scenarios.find((item) => item.id === scenarioSelect.value) || scenarios[0];
  if (selected) {
    hydrateForm(selected.payload);
  }
  resetOutputs();
  if (clearSaved) {
    localStorage.removeItem(FORM_STATE_KEY);
  } else {
    saveFormState();
  }
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
    const response = await withButtonBusy(runPlanBtn, "Running...", async () => callApi("/api/assist", payload, "POST"));
    boostValue.textContent = response.memory_boost.toFixed(2);
    withoutConfidence.textContent = `Confidence ${response.without_memory.confidence.toFixed(2)}`;
    withConfidence.textContent = `Confidence ${response.with_memory.confidence.toFixed(2)}`;
    renderList(withoutSteps, response.without_memory.steps, true);
    renderList(withSteps, response.with_memory.steps, true);
    renderList(takeawayList, response.tactical_takeaways, false);
    renderMemoryRows(response.recalled_memories);
    setFeedbackContext(response);
    saveFormState();
    await refreshStatus();
    showToast("Plan generated");
  } catch (error) {
    showToast(error.message);
  }
});

feedbackForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const queryId = feedbackForm.elements.query_id.value.trim();
  const sessionId = feedbackForm.elements.session_id.value.trim();
  if (!queryId || !sessionId) {
    showToast("Run an assist call first");
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
    await withButtonBusy(saveFeedbackBtn, "Saving...", async () => callApi("/api/feedback", payload, "POST"));
    feedbackForm.elements.useful_steps.value = "";
    feedbackForm.elements.notes.value = "";
    await refreshStatus();
    showToast("Feedback saved to memory");
  } catch (error) {
    showToast(error.message);
  }
});

subscriptionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    email: subscriptionForm.elements.email.value.trim(),
    team_name: subscriptionForm.elements.team_name.value.trim(),
    team_size: Number(subscriptionForm.elements.team_size.value),
    plan: subscriptionForm.elements.plan.value,
    use_case: subscriptionForm.elements.use_case.value.trim()
  };
  try {
    await withButtonBusy(requestAccessBtn, "Submitting...", async () => callApi("/api/subscriptions", payload, "POST"));
    subscriptionForm.reset();
    showToast("Access request queued");
  } catch (error) {
    showToast(error.message);
  }
});

seedBtn.addEventListener("click", async () => {
  try {
    await withButtonBusy(seedBtn, "Loading...", async () => callApi("/api/seed", {}, "POST"));
    await refreshStatus();
    showToast("Memory loaded");
  } catch (error) {
    showToast(error.message);
  }
});

applyScenarioBtn.addEventListener("click", () => {
  const selected = scenarios.find((item) => item.id === scenarioSelect.value);
  if (selected) {
    hydrateForm(selected.payload);
    saveFormState();
    showToast("Scenario applied");
  }
});

freshBtn.addEventListener("click", async () => {
  try {
    freshWorkspace(true);
    await refreshStatus();
    showToast("Workspace refreshed");
  } catch (error) {
    showToast(error.message);
  }
});

assistForm.addEventListener("input", () => {
  saveFormState();
});

assistForm.addEventListener("change", () => {
  saveFormState();
});

assistForm.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    assistForm.requestSubmit();
  }
});

copyWithoutBtn.addEventListener("click", async () => {
  const text = listText(Array.from(withoutSteps.querySelectorAll("li")).map((node) => node.textContent || "").filter(Boolean));
  if (!text) {
    showToast("No baseline steps yet");
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    showToast("Baseline steps copied");
  } catch {
    showToast("Clipboard blocked in this browser");
  }
});

copyWithBtn.addEventListener("click", async () => {
  const text = listText(Array.from(withSteps.querySelectorAll("li")).map((node) => node.textContent || "").filter(Boolean));
  if (!text) {
    showToast("No memory steps yet");
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    showToast("Memory steps copied");
  } catch {
    showToast("Clipboard blocked in this browser");
  }
});

document.addEventListener("mousemove", (event) => {
  const target = event.target;
  if (target instanceof Element && target.closest("input,textarea,select,button,label,a,table,thead,tbody,tr,td")) {
    document.documentElement.style.setProperty("--mx", "0");
    document.documentElement.style.setProperty("--my", "0");
    return;
  }
  const x = (event.clientX / window.innerWidth) * 2 - 1;
  const y = (event.clientY / window.innerHeight) * 2 - 1;
  document.documentElement.style.setProperty("--mx", x.toFixed(3));
  document.documentElement.style.setProperty("--my", y.toFixed(3));
});

async function bootstrap() {
  try {
    await loadScenarios();
    if (!restoreFormState()) {
      freshWorkspace();
    }
    await refreshStatus();
    showToast("Workspace ready");
  } catch (error) {
    showToast(error.message);
  }
}

bootstrap();
