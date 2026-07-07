const BASE = import.meta.env.VITE_API_URL || "/api";

let authToken = null;
export function setAuthToken(token) {
  authToken = token;
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, options = {}) {
  let res;
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  try {
    res = await fetch(`${BASE}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(
      "Could not reach the server. Is the backend running on port 8000?",
      0
    );
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore parse errors */
    }
    if (res.status === 401) {
      setAuthToken(null);
      localStorage.removeItem("zy_token");
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  signup: (payload) =>
    request("/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) =>
    request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/auth/me"),

  createSession: (payload) =>
    request("/sessions", { method: "POST", body: JSON.stringify(payload) }),
  listSessions: () => request("/sessions"),
  getSession: (id) => request(`/sessions/${id}`),
  getProgress: (id) => request(`/sessions/${id}/progress`),
  rerunSession: (id) => request(`/sessions/${id}/rerun`, { method: "POST" }),
  deleteSession: (id) => request(`/sessions/${id}`, { method: "DELETE" }),
  getChatHistory: (id) => request(`/sessions/${id}/chat`),
  sendChatMessage: (id, message) =>
    request(`/sessions/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
};

export { ApiError };