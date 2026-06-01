const API_BASE_URL = window.API_BASE_URL || "http://localhost:8000";

const loginScreen = document.querySelector("#loginScreen");
const workspace = document.querySelector("#workspace");
const loginForm = document.querySelector("#loginForm");
const loginEmailInput = document.querySelector("#loginEmailInput");
const loginPasswordInput = document.querySelector("#loginPasswordInput");
const loginSubmitButton = document.querySelector("#loginSubmitButton");
const guestButton = document.querySelector("#guestButton");
const loginError = document.querySelector("#loginError");
const forgotPasswordToggle = document.querySelector("#forgotPasswordToggle");
const resetPanel = document.querySelector("#resetPanel");
const resetRequestForm = document.querySelector("#resetRequestForm");
const resetEmailInput = document.querySelector("#resetEmailInput");
const resetRequestButton = document.querySelector("#resetRequestButton");
const resetCompleteForm = document.querySelector("#resetCompleteForm");
const resetTokenInput = document.querySelector("#resetTokenInput");
const resetNewPasswordInput = document.querySelector("#resetNewPasswordInput");
const resetCompleteButton = document.querySelector("#resetCompleteButton");
const resetMessage = document.querySelector("#resetMessage");

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
const changePasswordToggle = document.querySelector("#changePasswordToggle");
const changePasswordForm = document.querySelector("#changePasswordForm");
const currentPasswordInput = document.querySelector("#currentPasswordInput");
const newPasswordInput = document.querySelector("#newPasswordInput");
const changePasswordButton = document.querySelector("#changePasswordButton");
const changePasswordMessage = document.querySelector("#changePasswordMessage");

const state = {
  busy: false,
  loginBusy: false,
  resetBusy: false,
  changePasswordBusy: false,
  sessionId: createSessionId(),
  authToken: localStorage.getItem("robo_auth_token") || "",
  refreshToken: localStorage.getItem("robo_refresh_token") || "",
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

function saveAuth(token, authContext, refreshToken = "") {
  state.authToken = token || "";
  state.refreshToken = refreshToken || "";
  state.authContext = authContext || null;

  if (state.authToken) {
    localStorage.setItem("robo_auth_token", state.authToken);
    localStorage.setItem("robo_auth_context", JSON.stringify(state.authContext));
    if (state.refreshToken) {
      localStorage.setItem("robo_refresh_token", state.refreshToken);
    }
  } else {
    localStorage.removeItem("robo_auth_token");
    localStorage.removeItem("robo_refresh_token");
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

function setResetBusy(value) {
  state.resetBusy = value;
  resetRequestButton.disabled = value;
  resetCompleteButton.disabled = value;
}

function setChangePasswordBusy(value) {
  state.changePasswordBusy = value;
  changePasswordButton.disabled = value;
  changePasswordButton.textContent = value ? "Đang lưu" : "Lưu mật khẩu";
}

function setLoginError(message = "") {
  loginError.textContent = message;
}

function setResetMessage(message = "", type = "") {
  resetMessage.textContent = message;
  resetMessage.dataset.type = type;
}

function setChangePasswordMessage(message = "", type = "") {
  changePasswordMessage.textContent = message;
  changePasswordMessage.dataset.type = type;
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
  const requestLabel = payload.request_id ? ` · req ${payload.request_id.slice(0, 8)}` : "";
  const latencyLabel =
    typeof payload.latency_ms === "number" ? ` · ${payload.latency_ms.toFixed(0)}ms` : "";
  sessionMeta.textContent = `${payload.domain || "clinic"} · ${authLabel} · ${parserLabel} · ${answerLabel} · ${state.sessionId.slice(0, 8)}${requestLabel}${latencyLabel}`;

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
    changePasswordToggle.hidden = false;
  } else {
    authSessionStatus.textContent = "Đang dùng guest";
    logoutButton.disabled = false;
    changePasswordToggle.hidden = true;
    changePasswordForm.hidden = true;
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
    saveAuth(body.access_token || "", body.auth || null, body.refresh_token || "");
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

async function requestPasswordReset() {
  const email = resetEmailInput.value.trim();
  if (!email) {
    setResetMessage("Vui lòng nhập email.", "error");
    resetEmailInput.focus();
    return;
  }

  setResetBusy(true);
  setResetMessage();

  try {
    const res = await fetch(`${API_BASE_URL}/auth/password-reset/request`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }
    const body = await res.json();
    if (body.reset_token) {
      resetTokenInput.value = body.reset_token;
      setResetMessage("Token reset đã được tạo cho môi trường local/dev.", "ok");
      resetTokenInput.focus();
    } else {
      setResetMessage(
        "Nếu email tồn tại, yêu cầu reset đã được ghi nhận. Kênh gửi token/email cần được cấu hình riêng.",
        "ok",
      );
    }
  } catch (error) {
    setResetMessage(extractErrorMessage(error.message) || "Không tạo được yêu cầu reset.", "error");
  } finally {
    setResetBusy(false);
  }
}

async function completePasswordReset() {
  const resetToken = resetTokenInput.value.trim();
  const newPassword = resetNewPasswordInput.value;
  if (!resetToken) {
    setResetMessage("Vui lòng nhập reset token.", "error");
    resetTokenInput.focus();
    return;
  }
  if (!newPassword) {
    setResetMessage("Vui lòng nhập mật khẩu mới.", "error");
    resetNewPasswordInput.focus();
    return;
  }

  setResetBusy(true);
  setResetMessage();

  try {
    const res = await fetch(`${API_BASE_URL}/auth/password-reset/complete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        reset_token: resetToken,
        new_password: newPassword,
      }),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }
    resetTokenInput.value = "";
    resetNewPasswordInput.value = "";
    setResetMessage("Đã đặt lại mật khẩu. Bạn có thể đăng nhập bằng mật khẩu mới.", "ok");
    loginEmailInput.value = resetEmailInput.value.trim() || loginEmailInput.value;
    loginPasswordInput.focus();
  } catch (error) {
    setResetMessage(extractErrorMessage(error.message) || "Không đặt lại được mật khẩu.", "error");
  } finally {
    setResetBusy(false);
  }
}

async function changePassword() {
  const currentPassword = currentPasswordInput.value;
  const newPassword = newPasswordInput.value;
  if (!state.authToken) {
    setChangePasswordMessage("Bạn cần đăng nhập trước khi đổi mật khẩu.", "error");
    return;
  }
  if (!currentPassword || !newPassword) {
    setChangePasswordMessage("Vui lòng nhập đủ mật khẩu hiện tại và mật khẩu mới.", "error");
    return;
  }

  setChangePasswordBusy(true);
  setChangePasswordMessage();

  try {
    let res = await fetch(`${API_BASE_URL}/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${state.authToken}`,
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
    if (!res.ok && res.status === 401) {
      const refreshed = await refreshAuth();
      if (refreshed) {
        res = await fetch(`${API_BASE_URL}/auth/change-password`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${state.authToken}`,
          },
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
          }),
        });
      }
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }
    currentPasswordInput.value = "";
    newPasswordInput.value = "";
    setChangePasswordMessage("Đã đổi mật khẩu. Các phiên khác đã bị thu hồi.", "ok");
  } catch (error) {
    setChangePasswordMessage(extractErrorMessage(error.message) || "Không đổi được mật khẩu.", "error");
  } finally {
    setChangePasswordBusy(false);
  }
}

function continueAsGuest() {
  saveAuth("", null);
  state.sessionId = createSessionId();
  messages.replaceChildren();
  showApp();
}

async function logout() {
  const token = state.authToken;
  if (token) {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch {
      // Local logout must still work if the API is already unreachable.
    }
  }
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

async function refreshAuth() {
  if (!state.refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: state.refreshToken }),
    });
    if (!res.ok) return false;
    const body = await res.json();
    saveAuth(body.access_token || "", body.auth || null, body.refresh_token || "");
    return Boolean(state.authToken);
  } catch {
    return false;
  }
}

async function ask(question) {
  setBusy(true);
  addMessage("user", question);

  try {
    let res = await sendAskRequest(question);

    if (!res.ok) {
      if (res.status === 401) {
        const refreshed = await refreshAuth();
        if (refreshed) {
          res = await sendAskRequest(question);
          if (res.ok) {
            const payload = await res.json();
            addMessage("assistant", payload.answer);
            renderTrace(payload);
            return;
          }
        }
        const message = "Phiên đăng nhập hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại.";
        await logout();
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

async function sendAskRequest(question) {
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

  return fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers,
    body: JSON.stringify(requestBody),
  });
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

forgotPasswordToggle.addEventListener("click", () => {
  resetPanel.hidden = !resetPanel.hidden;
  if (!resetPanel.hidden) {
    resetEmailInput.value = loginEmailInput.value.trim();
    setResetMessage();
    resetEmailInput.focus();
  }
});

resetRequestForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!state.resetBusy) requestPasswordReset();
});

resetCompleteForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!state.resetBusy) completePasswordReset();
});

changePasswordToggle.addEventListener("click", () => {
  changePasswordForm.hidden = !changePasswordForm.hidden;
  if (!changePasswordForm.hidden) {
    setChangePasswordMessage();
    currentPasswordInput.focus();
  }
});

changePasswordForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!state.changePasswordBusy) changePassword();
});

logoutButton.addEventListener("click", () => {
  logout();
});

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
      const refreshed = await refreshAuth();
      if (refreshed) {
        showApp();
        return;
      }
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
