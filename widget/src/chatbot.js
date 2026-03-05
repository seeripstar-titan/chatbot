/**
 * Chatbot Widget – Embeddable chat widget
 *
 * Usage:
 *   <script src="https://your-domain.com/widget/chatbot-widget.js"
 *           data-api-key="YOUR_API_KEY"
 *           data-server="https://your-api-domain.com">
 *   </script>
 */

import { WIDGET_STYLES } from "./styles.js";
import { ChatbotAPI } from "./api.js";
import { AuthManager } from "./auth.js";

class ChatbotWidget {
  constructor() {
    // Read config from script tag
    const script =
      document.currentScript ||
      document.querySelector('script[data-api-key]');
    
    if (!script) {
      console.error("[Chatbot] Script tag with data-api-key not found");
      return;
    }

    this.apiKey = script.getAttribute("data-api-key");
    this.serverUrl = script.getAttribute("data-server") || window.location.origin;
    this.position = script.getAttribute("data-position") || "right";
    this.themeColor = script.getAttribute("data-theme-color") || "#6366f1";

    if (!this.apiKey) {
      console.error("[Chatbot] data-api-key attribute is required");
      return;
    }

    // State
    this.isOpen = false;
    this.isLoading = false;
    this.messages = [];
    this.conversationId = null;
    this.isStreaming = false;

    // Live agent state
    this.isAgentMode = false;
    this.agentWs = null;
    this.agentName = null;

    // Services
    this.api = new ChatbotAPI(this.serverUrl, this.apiKey);
    this.auth = new AuthManager(this.api);

    // Initialize
    this._init();
  }

  async _init() {
    this._createWidget();
    this._attachEventListeners();

    // Fetch widget config
    try {
      const config = await this.api.getWidgetConfig();
      this.welcomeMessage = config.welcome_message;
      this.tenantName = config.tenant_name;
      this._updateHeader(config.tenant_name);
    } catch (e) {
      console.error("[Chatbot] Failed to load config:", e);
      this.welcomeMessage = "Hello! How can I help you today?";
    }

    // Restore auth state
    this.auth.restore();
  }

  _createWidget() {
    // Create container with Shadow DOM for CSS isolation
    this.container = document.createElement("div");
    this.container.id = "chatbot-widget-container";
    this.shadow = this.container.attachShadow({ mode: "open" });

    // Inject styles
    const styleEl = document.createElement("style");
    styleEl.textContent = WIDGET_STYLES(this.themeColor, this.position);
    this.shadow.appendChild(styleEl);

    // Widget HTML structure
    const wrapper = document.createElement("div");
    wrapper.classList.add("cb-wrapper");
    wrapper.innerHTML = `
      <div class="cb-chat-window" id="cb-chat-window">
        <div class="cb-header">
          <div class="cb-header-info">
            <div class="cb-header-avatar">
              <img src="${this.serverUrl}/static/images/logo.png" alt="Logo" class="cb-header-logo" />
            </div>
            <div>
              <div class="cb-header-title">AI Assistant</div>
              <div class="cb-header-status">Online</div>
            </div>
          </div>
          <div class="cb-header-actions">
            <button class="cb-btn-icon cb-btn-auth" id="cb-auth-btn" title="Sign In">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </button>
            <button class="cb-btn-icon" id="cb-close-btn" title="Close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="cb-messages" id="cb-messages">
          <div class="cb-welcome" id="cb-welcome">
            <div class="cb-welcome-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 2a7 7 0 0 1 7 7v1h1a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-1a7 7 0 0 1-14 0H4a2 2 0 0 1-2-2v-2a2 2 0 0 1 2-2h1V9a7 7 0 0 1 7-7z"/>
                <circle cx="9" cy="13" r="1"/><circle cx="15" cy="13" r="1"/>
                <path d="M9 17s1.5 1 3 1 3-1 3-1"/>
              </svg>
            </div>
            <p class="cb-welcome-text">Loading...</p>
          </div>
        </div>

        <!-- Auth Modal -->
        <div class="cb-auth-modal" id="cb-auth-modal" style="display:none">
          <div class="cb-auth-card">
            <h3 id="cb-auth-title">Sign In</h3>
            <form id="cb-auth-form">
              <div id="cb-auth-name-group" style="display:none">
                <label>Name</label>
                <input type="text" id="cb-auth-name" placeholder="Your name" />
              </div>
              <div>
                <label>Email</label>
                <input type="email" id="cb-auth-email" placeholder="you@example.com" required />
              </div>
              <div>
                <label>Password</label>
                <input type="password" id="cb-auth-password" placeholder="••••••••" required />
              </div>
              <div class="cb-auth-error" id="cb-auth-error" style="display:none"></div>
              <button type="submit" class="cb-auth-submit" id="cb-auth-submit">Sign In</button>
              <p class="cb-auth-toggle">
                <span id="cb-auth-toggle-text">Don't have an account?</span>
                <a href="#" id="cb-auth-toggle-link">Sign Up</a>
              </p>
            </form>
            <button class="cb-auth-close" id="cb-auth-modal-close">✕</button>
          </div>
        </div>

        <div class="cb-input-area">
          <div class="cb-agent-bar" id="cb-agent-bar" style="display:none">
            <span class="cb-agent-bar-dot"></span>
            <span id="cb-agent-bar-text">Connected with an agent</span>
            <button class="cb-agent-bar-end" id="cb-agent-end-btn" title="End agent chat">✕</button>
          </div>
          <div class="cb-input-wrapper">
            <textarea
              id="cb-input"
              placeholder="Type your message..."
              rows="1"
              maxlength="5000"
            ></textarea>
            <button class="cb-send-btn" id="cb-send-btn" disabled>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </div>
          <div class="cb-input-footer">
            <button class="cb-human-btn" id="cb-human-btn" title="Talk to a human agent">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              Talk to a human
            </button>
            <span class="cb-powered">Powered by AI</span>
          </div>
        </div>
      </div>

      <button class="cb-toggle-btn" id="cb-toggle-btn">
        <svg class="cb-toggle-icon-open" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <svg class="cb-toggle-icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none">
          <path d="M18 6L6 18M6 6l12 12"/>
        </svg>
        <span class="cb-badge" id="cb-badge" style="display:none">1</span>
      </button>
    `;
    this.shadow.appendChild(wrapper);
    document.body.appendChild(this.container);

    // Cache DOM references inside shadow
    this.chatWindow = this.shadow.getElementById("cb-chat-window");
    this.messagesEl = this.shadow.getElementById("cb-messages");
    this.welcomeEl = this.shadow.getElementById("cb-welcome");
    this.inputEl = this.shadow.getElementById("cb-input");
    this.sendBtn = this.shadow.getElementById("cb-send-btn");
    this.toggleBtn = this.shadow.getElementById("cb-toggle-btn");
    this.closeBtn = this.shadow.getElementById("cb-close-btn");
    this.authBtn = this.shadow.getElementById("cb-auth-btn");
    this.authModal = this.shadow.getElementById("cb-auth-modal");
    this.authForm = this.shadow.getElementById("cb-auth-form");
    this.authError = this.shadow.getElementById("cb-auth-error");
    this.authModalClose = this.shadow.getElementById("cb-auth-modal-close");
    this.authToggleLink = this.shadow.getElementById("cb-auth-toggle-link");
    this.authTitle = this.shadow.getElementById("cb-auth-title");
    this.authToggleText = this.shadow.getElementById("cb-auth-toggle-text");
    this.authSubmitBtn = this.shadow.getElementById("cb-auth-submit");
    this.authNameGroup = this.shadow.getElementById("cb-auth-name-group");
    this.badge = this.shadow.getElementById("cb-badge");
    this.agentBar = this.shadow.getElementById("cb-agent-bar");
    this.agentBarText = this.shadow.getElementById("cb-agent-bar-text");
    this.agentEndBtn = this.shadow.getElementById("cb-agent-end-btn");
    this.humanBtn = this.shadow.getElementById("cb-human-btn");

    this.isSignUp = false;
  }

  _updateHeader(name) {
    const titleEl = this.shadow.querySelector(".cb-header-title");
    if (titleEl && name) {
      titleEl.textContent = name;
    }
    const welcomeText = this.shadow.querySelector(".cb-welcome-text");
    if (welcomeText) {
      welcomeText.innerHTML = this._formatMarkdown(this.welcomeMessage);
    }
  }

  _attachEventListeners() {
    // Toggle chat window
    this.toggleBtn.addEventListener("click", () => this._toggleChat());
    this.closeBtn.addEventListener("click", () => this._toggleChat());

    // Send message
    this.sendBtn.addEventListener("click", () => this._sendMessage());
    this.inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this._sendMessage();
      }
    });

    // Auto-resize textarea
    this.inputEl.addEventListener("input", () => {
      this.sendBtn.disabled = !this.inputEl.value.trim();
      this.inputEl.style.height = "auto";
      this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 120) + "px";
    });

    // Auth modal
    this.authBtn.addEventListener("click", () => {
      if (this.auth.isAuthenticated()) {
        this.auth.logout();
        this._updateAuthButton();
        this._addSystemMessage("You have been signed out.");
      } else {
        this.authModal.style.display = "flex";
      }
    });

    this.authModalClose.addEventListener("click", () => {
      this.authModal.style.display = "none";
    });

    this.authToggleLink.addEventListener("click", (e) => {
      e.preventDefault();
      this.isSignUp = !this.isSignUp;
      this._updateAuthModal();
    });

    this.authForm.addEventListener("submit", (e) => {
      e.preventDefault();
      this._handleAuth();
    });

    // Live agent controls
    this.humanBtn.addEventListener("click", () => this._requestHumanAgent());
    this.agentEndBtn.addEventListener("click", () => this._endAgentSession());
  }

  _toggleChat() {
    this.isOpen = !this.isOpen;
    this.chatWindow.classList.toggle("cb-open", this.isOpen);
    this.toggleBtn.classList.toggle("cb-active", this.isOpen);

    const openIcon = this.shadow.querySelector(".cb-toggle-icon-open");
    const closeIcon = this.shadow.querySelector(".cb-toggle-icon-close");
    openIcon.style.display = this.isOpen ? "none" : "block";
    closeIcon.style.display = this.isOpen ? "block" : "none";

    if (this.isOpen) {
      this.badge.style.display = "none";
      this.inputEl.focus();
    }
  }

  async _sendMessage() {
    const text = this.inputEl.value.trim();
    if (!text || this.isStreaming) return;

    // Clear input
    this.inputEl.value = "";
    this.inputEl.style.height = "auto";
    this.sendBtn.disabled = true;

    // Hide welcome
    if (this.welcomeEl) {
      this.welcomeEl.style.display = "none";
    }

    // Add user message
    this._addMessage("user", text);

    // If in agent mode, send via WebSocket
    if (this.isAgentMode && this.agentWs && this.agentWs.readyState === WebSocket.OPEN) {
      this.agentWs.send(JSON.stringify({ message: text }));
      return;
    }

    // Show typing indicator
    const typingEl = this._addTypingIndicator();

    // Stream response
    this.isStreaming = true;
    let assistantEl = null;

    try {
      const response = await fetch(`${this.serverUrl}/api/v1/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": this.apiKey,
          ...this.auth.getAuthHeaders(),
        },
        body: JSON.stringify({
          message: text,
          conversation_id: this.conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // Read SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            var eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));

            if (eventType === "conversation_id") {
              this.conversationId = data.conversation_id;
            } else if (eventType === "chunk") {
              // Remove typing indicator on first chunk
              if (typingEl && typingEl.parentNode) {
                typingEl.remove();
              }
              if (!assistantEl) {
                assistantEl = this._addMessage("assistant", "", true);
              }
              this._appendToMessage(assistantEl, data.text);
            } else if (eventType === "done") {
              // Finalize
              if (assistantEl) {
                this._finalizeMessage(assistantEl);
              }
            } else if (eventType === "handoff") {
              // AI triggered a handoff to a live agent
              this._enterAgentMode(data.conversation_id);
            }
          }
        }
      }
    } catch (e) {
      console.error("[Chatbot] Stream error:", e);
      if (typingEl && typingEl.parentNode) typingEl.remove();

      // Fall back to non-streaming
      try {
        const result = await this.api.sendMessage(text, this.conversationId);
        this.conversationId = result.conversation_id;
        this._addMessage("assistant", result.content);
      } catch (fallbackErr) {
        this._addMessage(
          "assistant",
          "Sorry, I'm having trouble connecting. Please try again."
        );
      }
    } finally {
      this.isStreaming = false;
      if (typingEl && typingEl.parentNode) typingEl.remove();
    }
  }

  _addMessage(role, content, isStreaming = false) {
    const msgEl = document.createElement("div");
    msgEl.classList.add("cb-message", `cb-message-${role}`);

    const bubble = document.createElement("div");
    bubble.classList.add("cb-bubble");

    if (isStreaming) {
      bubble.innerHTML = '<span class="cb-cursor">▊</span>';
    } else {
      bubble.innerHTML = this._formatMarkdown(content);
    }

    msgEl.appendChild(bubble);
    this.messagesEl.appendChild(msgEl);
    this._scrollToBottom();

    this.messages.push({ role, content });

    return msgEl;
  }

  _appendToMessage(msgEl, text) {
    const bubble = msgEl.querySelector(".cb-bubble");
    const cursor = bubble.querySelector(".cb-cursor");

    // Get current text content (without cursor)
    let currentText = bubble.textContent.replace("▊", "");
    currentText += text;

    bubble.innerHTML = this._formatMarkdown(currentText) + '<span class="cb-cursor">▊</span>';
    this._scrollToBottom();
  }

  _finalizeMessage(msgEl) {
    const bubble = msgEl.querySelector(".cb-bubble");
    const cursor = bubble.querySelector(".cb-cursor");
    if (cursor) cursor.remove();

    // Re-render with proper markdown
    const text = bubble.textContent;
    bubble.innerHTML = this._formatMarkdown(text);
  }

  _addSystemMessage(text) {
    const msgEl = document.createElement("div");
    msgEl.classList.add("cb-message", "cb-message-system");
    msgEl.innerHTML = `<div class="cb-system-text">${text}</div>`;
    this.messagesEl.appendChild(msgEl);
    this._scrollToBottom();
  }

  _addTypingIndicator() {
    const el = document.createElement("div");
    el.classList.add("cb-message", "cb-message-assistant", "cb-typing");
    el.innerHTML = `
      <div class="cb-bubble cb-typing-bubble">
        <span class="cb-dot"></span>
        <span class="cb-dot"></span>
        <span class="cb-dot"></span>
      </div>
    `;
    this.messagesEl.appendChild(el);
    this._scrollToBottom();
    return el;
  }

  _scrollToBottom() {
    this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
  }

  _formatMarkdown(text) {
    if (!text) return "";
    return text
      // Bold
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      // Italic
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      // Inline code
      .replace(/`(.+?)`/g, "<code>$1</code>")
      // Line breaks
      .replace(/\n/g, "<br>")
      // Bullet lists
      .replace(/^[-•]\s+(.+)/gm, "<li>$1</li>")
      .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
      // Numbered lists
      .replace(/^\d+\.\s+(.+)/gm, "<li>$1</li>");
  }

  // ── Live Agent Mode ──────────────────────────────────────────────

  _requestHumanAgent() {
    if (this.isAgentMode) return;

    // Send a message that triggers the AI's handoff tool
    this.inputEl.value = "I'd like to speak with a human agent please.";
    this._sendMessage();
  }

  _enterAgentMode(conversationId) {
    if (this.isAgentMode) return;

    this.isAgentMode = true;
    const wsUrl = this.api.getAgentWebSocketUrl(conversationId || this.conversationId);

    this._addSystemMessage("🔄 Connecting you with a support agent...");
    this._updateAgentUI(true, "Waiting for an agent...");

    this.agentWs = new WebSocket(wsUrl);

    this.agentWs.onopen = () => {
      console.log("[Chatbot] Agent WebSocket connected");
    };

    this.agentWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "agent_joined") {
          this._updateAgentUI(true, `Connected with ${data.agent_name || "an agent"}`);
          this._addSystemMessage(`✅ You're now chatting with ${data.agent_name || "a support agent"}.`);
          this.agentName = data.agent_name || "Support Agent";
        } else if (data.type === "agent_left") {
          this._exitAgentMode(data.message);
        } else if (data.type === "message" && data.role === "agent") {
          this._addMessage("assistant", data.content);
        }
      } catch (e) {
        console.error("[Chatbot] WS message parse error:", e);
      }
    };

    this.agentWs.onclose = () => {
      console.log("[Chatbot] Agent WebSocket closed");
      if (this.isAgentMode) {
        this._exitAgentMode("Connection to agent lost. You're back with the AI assistant.");
      }
    };

    this.agentWs.onerror = (err) => {
      console.error("[Chatbot] Agent WebSocket error:", err);
    };
  }

  _exitAgentMode(message) {
    this.isAgentMode = false;
    this.agentName = null;

    if (this.agentWs) {
      try { this.agentWs.close(); } catch (e) { /* ignore */ }
      this.agentWs = null;
    }

    this._updateAgentUI(false);
    if (message) {
      this._addSystemMessage(`ℹ️ ${message}`);
    }
  }

  _endAgentSession() {
    this._exitAgentMode("You ended the live agent chat. You're back with the AI assistant.");
  }

  _updateAgentUI(active, text) {
    if (active) {
      this.agentBar.style.display = "flex";
      this.agentBarText.textContent = text || "Connected with an agent";
      this.humanBtn.style.display = "none";

      // Update header status
      const statusEl = this.shadow.querySelector(".cb-header-status");
      if (statusEl) {
        statusEl.innerHTML = '<span style="color:#4ade80;">●</span> Live Agent';
      }
    } else {
      this.agentBar.style.display = "none";
      this.humanBtn.style.display = "inline-flex";

      const statusEl = this.shadow.querySelector(".cb-header-status");
      if (statusEl) {
        statusEl.textContent = "Online";
      }
    }
  }

  // ── Auth ────────────────────────────────────────────────────────────

  _updateAuthModal() {
    if (this.isSignUp) {
      this.authTitle.textContent = "Create Account";
      this.authSubmitBtn.textContent = "Sign Up";
      this.authToggleText.textContent = "Already have an account?";
      this.authToggleLink.textContent = "Sign In";
      this.authNameGroup.style.display = "block";
    } else {
      this.authTitle.textContent = "Sign In";
      this.authSubmitBtn.textContent = "Sign In";
      this.authToggleText.textContent = "Don't have an account?";
      this.authToggleLink.textContent = "Sign Up";
      this.authNameGroup.style.display = "none";
    }
    this.authError.style.display = "none";
  }

  _updateAuthButton() {
    const svg = this.authBtn.querySelector("svg");
    if (this.auth.isAuthenticated()) {
      this.authBtn.title = "Sign Out";
      this.authBtn.classList.add("cb-authenticated");
    } else {
      this.authBtn.title = "Sign In";
      this.authBtn.classList.remove("cb-authenticated");
    }
  }

  async _handleAuth() {
    const email = this.shadow.getElementById("cb-auth-email").value;
    const password = this.shadow.getElementById("cb-auth-password").value;
    const name = this.shadow.getElementById("cb-auth-name").value;

    this.authError.style.display = "none";
    this.authSubmitBtn.disabled = true;
    this.authSubmitBtn.textContent = "Please wait...";

    try {
      if (this.isSignUp) {
        await this.auth.register(email, password, name);
        this._addSystemMessage(`Welcome, ${name}! You're now signed in.`);
      } else {
        await this.auth.login(email, password);
        this._addSystemMessage("You're now signed in!");
      }
      this.authModal.style.display = "none";
      this._updateAuthButton();
    } catch (e) {
      this.authError.textContent = e.message || "Authentication failed";
      this.authError.style.display = "block";
    } finally {
      this.authSubmitBtn.disabled = false;
      this.authSubmitBtn.textContent = this.isSignUp ? "Sign Up" : "Sign In";
    }
  }
}

// Auto-initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => new ChatbotWidget());
} else {
  new ChatbotWidget();
}

export default ChatbotWidget;
