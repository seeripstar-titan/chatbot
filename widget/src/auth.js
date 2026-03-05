/**
 * Authentication manager for the widget.
 * Handles login, registration, token storage, and refresh.
 */
const STORAGE_KEY = "chatbot_auth";

export class AuthManager {
  constructor(api) {
    this.api = api;
    this._user = null;
  }

  isAuthenticated() {
    return !!this.api.accessToken;
  }

  getAuthHeaders() {
    if (this.api.accessToken) {
      return { Authorization: `Bearer ${this.api.accessToken}` };
    }
    return {};
  }

  async login(email, password) {
    const result = await this.api.login(email, password);
    this._saveTokens(result);
    return result;
  }

  async register(email, password, name) {
    const result = await this.api.register(email, password, name);
    this._saveTokens(result);
    return result;
  }

  logout() {
    this.api.clearTokens();
    this._user = null;
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      // localStorage may not be available
    }
  }

  restore() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        if (data.accessToken && data.refreshToken) {
          this.api.setTokens(data.accessToken, data.refreshToken);
          // Try to refresh token in background
          this._refreshInBackground(data.refreshToken);
          return true;
        }
      }
    } catch (e) {
      // Ignore storage errors
    }
    return false;
  }

  _saveTokens(result) {
    this.api.setTokens(result.access_token, result.refresh_token);
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          accessToken: result.access_token,
          refreshToken: result.refresh_token,
        })
      );
    } catch (e) {
      // localStorage may not be available
    }
  }

  async _refreshInBackground(refreshToken) {
    try {
      const result = await this.api.refreshAccessToken(refreshToken);
      this._saveTokens(result);
    } catch (e) {
      // Token expired, clear auth
      this.logout();
    }
  }
}
