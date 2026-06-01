const API_BASE_URL = window.API_BASE_URL || "http://localhost:8000";

const loginScreen = document.querySelector("#loginScreen");
const workspace = document.querySelector("#workspace");
const loginForm = document.querySelector("#loginForm");
const loginEmailInput = document.querySelector("#loginEmailInput");
const loginPasswordInput = document.querySelector("#loginPasswordInput");
const loginSubmitButton = document.querySelector("#loginSubmitButton");
const guestButton = document.querySelector("#guestButton");
const loginError = document.querySelector("#loginError");

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
const logoutButton = document.querySelector("#logoutButton");
const authSessionStatus = document.querySelector("#authSessionStatus");

const state = {
  busy: false,
  loginBusy: false,
  sessionId: createSessionId(),
  authToken: localStorage.getItem("robo_auth_token") || "",
  authContext: loadAuthContext(),
};

function setScreenMode(mode) {
  document.body.classList.toggle("auth-mode-login", mode === "login");
  document.body.classList.toggle("auth-mode-app", mode === "app");
}

function createSessionId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function loadAuthContext() {
  try {
    return JSON.parse(localStorage.getItem("robo_auth_context") || "null");
  } catch {
    return null;
  }
}

function saveAuth(token, authContext) {
  state.authToken = token || "";
  state.authContext = authContext || null;

  if (state.authToken) {
    localStorage.setItem("robo_auth_token", state.authToken);
    localStorage.setItem("robo_auth_context", JSON.stringify(state.authContext));
  } else {
    localStorage.removeItem("robo_auth_token");
    localStorage.removeItem("robo_auth_context");
  }
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

function setLoginBusy(value) {
  state.loginBusy = value;
  loginSubmitButton.disabled = value;
  guestButton.disabled = value;
  loginSubmitButton.textContent = value ? "Đang đăng nhập" : "Đăng nhập";
}

function setLoginError(message = "") {
  loginError.textContent = message;
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

function resetTrace() {
  intentBadge.textContent = "idle";
  intentBadge.className = "";
  domainValue.textContent = "-";
  intentValue.textContent = "-";
  confidenceValue.textContent = "-";
  parserValue.textContent = "-";
  answerSourceValue.textContent = "-";
  authStateValue.textContent = buildAuthLabel();
  sourcesValue.textContent = "-";
  dataPreview.textContent = "{}";
  sessionMeta.textContent = `clinic · ${buildAuthLabel()} · parser chưa chạy`;
}

function buildAuthLabel() {
  if (state.authToken && state.authContext?.role) {
    return `${state.authContext.role} token`;
  }
  return "guest";
}

function resetLoginFormMessage() {
  setLoginError();
}

function renderAuthSession() {
  if (state.authToken && state.authContext?.role) {
    authSessionStatus.textContent = `Đã đăng nhập: ${state.authContext.role}`;
    logoutButton.disabled = false;
  } else {
    authSessionStatus.textContent = "Đang dùng guest";
    logoutButton.disabled = false;
  }
  authStateValue.textContent = buildAuthLabel();
}

function showLogin() {
  setScreenMode("login");
  workspace.hidden = true;
  loginScreen.hidden = false;
  renderAuthSession();
  resetLoginFormMessage();
  loginEmailInput.focus();
}

function showApp() {
  setScreenMode("app");
  loginScreen.hidden = true;
  workspace.hidden = false;
  renderAuthSession();
  resetTrace();
  input.focus();
}

function buildLoginPayload() {
  return {
    email: loginEmailInput.value.trim(),
    password: loginPasswordInput.value,
  };
}

async function login() {
  const payload = buildLoginPayload();
  if (!payload.email) {
    setLoginError("Vui lòng nhập email.");
    loginEmailInput.focus();
    return;
  }
  if (!payload.password) {
    setLoginError("Vui lòng nhập mật khẩu.");
    loginPasswordInput.focus();
    return;
  }

  setLoginBusy(true);
  setLoginError();

  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }
    const body = await res.json();
    saveAuth(body.access_token || "", body.auth || null);
    state.sessionId = createSessionId();
    messages.replaceChildren();
    loginPasswordInput.value = "";
    showApp();
  } catch (error) {
    setLoginError(extractErrorMessage(error.message) || "Đăng nhập thất bại.");
  } finally {
    setLoginBusy(false);
  }
}

function continueAsGuest() {
  saveAuth("", null);
  state.sessionId = createSessionId();
  messages.replaceChildren();
  showApp();
}

function logout() {
  saveAuth("", null);
  state.sessionId = createSessionId();
  messages.replaceChildren();
  resetTrace();
  showLogin();
}

function extractErrorMessage(message = "") {
  try {
    const parsed = JSON.parse(message);
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // Keep the original error text below.
  }
  return message;
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

    const headers = {
      "Content-Type": "application/json",
    };
    if (state.authToken) {
      headers.Authorization = `Bearer ${state.authToken}`;
    }

    const res = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers,
      body: JSON.stringify(requestBody),
    });

    if (!res.ok) {
      if (res.status === 401) {
        const message = "Phiên đăng nhập hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại.";
        logout();
        setLoginError(message);
        return;
      }
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }

    const payload = await res.json();
    addMessage("assistant", payload.answer);
    renderTrace(payload);
  } catch (error) {
    addMessage("error", extractErrorMessage(error.message) || "Không gọi được API.");
  } finally {
    setBusy(false);
    if (!workspace.hidden) input.focus();
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
  state.sessionId = createSessionId();
  resetTrace();
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

loginForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!state.loginBusy) login();
});

guestButton.addEventListener("click", () => {
  if (!state.loginBusy) continueAsGuest();
});

logoutButton.addEventListener("click", logout);

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    healthStatus.textContent = res.ok ? "API sẵn sàng" : "API lỗi";
  } catch {
    healthStatus.textContent = "API chưa kết nối";
  }
}

async function bootstrapSession() {
  if (!state.authToken || !state.authContext?.role) {
    showLogin();
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${state.authToken}`,
      },
    });
    if (!res.ok) {
      saveAuth("", null);
      showLogin();
      setLoginError("Phiên đăng nhập cũ không còn hợp lệ. Vui lòng đăng nhập lại.");
      return;
    }
    const body = await res.json();
    saveAuth(state.authToken, body.auth || state.authContext);
  } catch {
    healthStatus.textContent = "API chưa kết nối";
  }

  showApp();
}

checkHealth();
bootstrapSession();
