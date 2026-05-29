const API_BASE_URL = window.API_BASE_URL || "http://localhost:8000";

const messages = document.querySelector("#messages");
const form = document.querySelector("#askForm");
const input = document.querySelector("#questionInput");
const sendButton = document.querySelector("#sendButton");
const clearButton = document.querySelector("#clearButton");
const healthStatus = document.querySelector("#healthStatus");
const intentBadge = document.querySelector("#intentBadge");
const domainValue = document.querySelector("#domainValue");
const intentValue = document.querySelector("#intentValue");
const confidenceValue = document.querySelector("#confidenceValue");
const parserValue = document.querySelector("#parserValue");
const answerSourceValue = document.querySelector("#answerSourceValue");
const authStateValue = document.querySelector("#authStateValue");
const sourcesValue = document.querySelector("#sourcesValue");
const dataPreview = document.querySelector("#dataPreview");
const sessionMeta = document.querySelector("#sessionMeta");
const authRole = document.querySelector("#authRole");
const patientIdInput = document.querySelector("#patientIdInput");
const doctorIdInput = document.querySelector("#doctorIdInput");
const clinicIdInput = document.querySelector("#clinicIdInput");
const authFields = document.querySelectorAll("[data-auth-field]");

const state = {
  busy: false,
  sessionId: createSessionId(),
};

function createSessionId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function addMessage(role, text) {
  const el = document.createElement("div");
  el.className = `message ${role}`;
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

function setBusy(value) {
  state.busy = value;
  sendButton.disabled = value;
  sendButton.textContent = value ? "Đang gửi" : "Gửi";
}

function renderTrace(payload) {
  const parserLabel = payload.parser_source === "llm" ? "LLM" : "Rule fallback";
  const answerLabel =
    payload.answer_source === "llm_grounded"
      ? "LLM grounded"
      : payload.answer_source === "llm_formatted"
        ? "LLM formatted"
        : "Template";
  const authLabel = buildAuthLabel();
  domainValue.textContent = payload.domain || "-";
  intentValue.textContent = payload.intent || "-";
  confidenceValue.textContent =
    typeof payload.confidence === "number" ? payload.confidence.toFixed(2) : "-";
  parserValue.textContent = parserLabel;
  answerSourceValue.textContent = answerLabel;
  authStateValue.textContent = authLabel;
  sourcesValue.textContent = payload.sources?.length ? payload.sources.join(", ") : "-";
  dataPreview.textContent = JSON.stringify(payload.data || [], null, 2);
  if (payload.session_id) state.sessionId = payload.session_id;
  sessionMeta.textContent = `${payload.domain || "clinic"} · ${authLabel} · ${parserLabel} · ${answerLabel} · ${state.sessionId.slice(0, 8)}`;

  intentBadge.textContent = payload.intent || "idle";
  intentBadge.className = payload.requires_auth ? "auth" : "ok";
}

function getAuthPayload() {
  const role = authRole.value || "guest";
  if (role === "guest") return null;

  const auth = { role };
  const requiredField = getRequiredAuthField(role);

  if (requiredField === "patient") {
    const patientId = patientIdInput.value.trim();
    if (patientId) auth.patient_id = patientId;
  } else if (requiredField === "doctor") {
    const doctorId = doctorIdInput.value.trim();
    if (doctorId) auth.doctor_id = doctorId;
  } else if (requiredField === "clinic") {
    const clinicId = clinicIdInput.value.trim();
    if (clinicId) auth.clinic_id = clinicId;
  }

  return auth;
}

function buildAuthLabel() {
  const role = authRole.value || "guest";
  if (role === "patient" && patientIdInput.value.trim()) return "patient";
  if (role === "doctor" && doctorIdInput.value.trim()) return "doctor";
  if (["receptionist", "clinic_admin"].includes(role) && clinicIdInput.value.trim()) {
    return role;
  }
  return role;
}

function getRequiredAuthField(role) {
  if (role === "patient") return "patient";
  if (role === "doctor") return "doctor";
  if (["receptionist", "clinic_admin"].includes(role)) return "clinic";
  return null;
}

function updateAuthFields() {
  const requiredField = getRequiredAuthField(authRole.value || "guest");

  authFields.forEach((field) => {
    const shouldShow = field.dataset.authField === requiredField;
    field.hidden = !shouldShow;
    const input = field.querySelector("input");
    if (input) input.disabled = !shouldShow;
  });

  authStateValue.textContent = buildAuthLabel();
  sessionMeta.textContent = `clinic · ${buildAuthLabel()} · parser chưa chạy`;
}

async function ask(question) {
  setBusy(true);
  addMessage("user", question);

  try {
    const requestBody = {
      question,
      domain: "clinic",
      session_id: state.sessionId,
    };
    const auth = getAuthPayload();
    if (auth) requestBody.auth = auth;

    const res = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }

    const payload = await res.json();
    addMessage("assistant", payload.answer);
    renderTrace(payload);
  } catch (error) {
    addMessage("error", error.message || "Không gọi được API.");
  } finally {
    setBusy(false);
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question || state.busy) return;
  input.value = "";
  ask(question);
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

clearButton.addEventListener("click", () => {
  messages.replaceChildren();
  intentBadge.textContent = "idle";
  intentBadge.className = "";
  domainValue.textContent = "-";
  intentValue.textContent = "-";
  confidenceValue.textContent = "-";
  parserValue.textContent = "-";
  answerSourceValue.textContent = "-";
  authStateValue.textContent = buildAuthLabel();
  sourcesValue.textContent = "-";
  state.sessionId = createSessionId();
  sessionMeta.textContent = `clinic · ${buildAuthLabel()} · parser chưa chạy`;
  dataPreview.textContent = "{}";
  input.focus();
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    const question = button.getAttribute("data-question");
    if (question && !state.busy) {
      input.value = "";
      ask(question);
    }
  });
});

[authRole, patientIdInput, doctorIdInput, clinicIdInput].forEach((field) => {
  field.addEventListener("input", () => {
    updateAuthFields();
  });
  field.addEventListener("change", () => {
    updateAuthFields();
  });
});

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    healthStatus.textContent = res.ok ? "API sẵn sàng" : "API lỗi";
  } catch {
    healthStatus.textContent = "API chưa kết nối";
  }
}

checkHealth();
updateAuthFields();
input.focus();
