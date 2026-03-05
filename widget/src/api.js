/**
 * API client for the chatbot backend.
 */
export class ChatbotAPI {
  constructor(serverUrl, apiKey) {
    this.serverUrl = serverUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.accessToken = null;
    this.refreshToken = null;
  }

  get baseHeaders() {
    const headers = {
      "Content-Type": "application/json",
      "X-API-Key": this.apiKey,
    };
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    return headers;
  }

  async getWidgetConfig() {
    const res = await fetch(`${this.serverUrl}/api/v1/widget/config`, {
      headers: this.baseHeaders,
    });
    if (!res.ok) throw new Error("Failed to load widget config");
    return res.json();
  }

  async sendMessage(message, conversationId = null) {
    const res = await fetch(`${this.serverUrl}/api/v1/chat/message`, {
      method: "POST",
      headers: this.baseHeaders,
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  async register(email, password, name) {
    const res = await fetch(`${this.serverUrl}/api/v1/auth/register`, {
      method: "POST",
      headers: this.baseHeaders,
      body: JSON.stringify({ email, password, name }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }
    return res.json();
  }

  async login(email, password) {
    const res = await fetch(`${this.serverUrl}/api/v1/auth/login`, {
      method: "POST",
      headers: this.baseHeaders,
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }
    return res.json();
  }

  async refreshAccessToken(refreshToken) {
    const res = await fetch(`${this.serverUrl}/api/v1/auth/refresh`, {
      method: "POST",
      headers: this.baseHeaders,
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) throw new Error("Token refresh failed");
    return res.json();
  }

  setTokens(accessToken, refreshToken) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
  }

  /**
   * Build a WebSocket URL for live agent chat.
   * @param {string} conversationId
   * @returns {string} WebSocket URL
   */
  getAgentWebSocketUrl(conversationId) {
    const wsProtocol = this.serverUrl.startsWith("https") ? "wss" : "ws";
    const host = this.serverUrl.replace(/^https?:\/\//, "");
    return `${wsProtocol}://${host}/api/v1/ws/chat/${conversationId}?api_key=${encodeURIComponent(this.apiKey)}`;
  }
}
