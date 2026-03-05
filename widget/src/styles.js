/**
 * Widget styles injected into Shadow DOM for CSS isolation.
 * Uses CSS custom properties for theming.
 */
export const WIDGET_STYLES = (themeColor = "#6366f1", position = "right") => `
  :host {
    --cb-primary: ${themeColor};
    --cb-primary-hover: color-mix(in srgb, ${themeColor} 85%, black);
    --cb-primary-light: color-mix(in srgb, ${themeColor} 15%, white);
    --cb-bg: #ffffff;
    --cb-bg-secondary: #f8f9fa;
    --cb-text: #1a1a2e;
    --cb-text-secondary: #6b7280;
    --cb-border: #e5e7eb;
    --cb-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    --cb-radius: 16px;
    --cb-font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

    font-family: var(--cb-font);
    font-size: 14px;
    line-height: 1.5;
    color: var(--cb-text);
  }

  *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  .cb-wrapper {
    position: fixed;
    bottom: 20px;
    ${position === "left" ? "left: 20px;" : "right: 20px;"}
    z-index: 2147483647;
    font-family: var(--cb-font);
  }

  /* ── Toggle Button ───────────────────────────────────────── */

  .cb-toggle-btn {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: var(--cb-primary);
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    color: white;
  }

  .cb-toggle-btn:hover {
    transform: scale(1.08);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
  }

  .cb-toggle-btn.cb-active {
    transform: scale(0.95);
  }

  .cb-toggle-btn svg {
    width: 28px;
    height: 28px;
  }

  .cb-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: #ef4444;
    color: white;
    font-size: 11px;
    font-weight: 600;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid white;
  }

  /* ── Chat Window ─────────────────────────────────────────── */

  .cb-chat-window {
    position: absolute;
    bottom: 75px;
    ${position === "left" ? "left: 0;" : "right: 0;"}
    width: 400px;
    height: 600px;
    max-height: calc(100vh - 120px);
    background: var(--cb-bg);
    border-radius: var(--cb-radius);
    box-shadow: var(--cb-shadow);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    opacity: 0;
    visibility: hidden;
    transform: translateY(20px) scale(0.95);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid var(--cb-border);
  }

  .cb-chat-window.cb-open {
    opacity: 1;
    visibility: visible;
    transform: translateY(0) scale(1);
  }

  @media (max-width: 480px) {
    .cb-chat-window {
      width: calc(100vw - 20px);
      height: calc(100vh - 100px);
      bottom: 70px;
      ${position === "left" ? "left: -10px;" : "right: -10px;"}
      border-radius: 12px;
    }
  }

  /* ── Header ──────────────────────────────────────────────── */

  .cb-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    background: var(--cb-primary);
    color: white;
    flex-shrink: 0;
  }

  .cb-header-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .cb-header-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    flex-shrink: 0;
  }

  .cb-header-avatar svg {
    width: 20px;
    height: 20px;
  }

  .cb-header-logo {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 50%;
  }

  .cb-header-title {
    font-size: 15px;
    font-weight: 600;
  }

  .cb-header-status {
    font-size: 12px;
    opacity: 0.85;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .cb-header-status::before {
    content: '';
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #4ade80;
    display: inline-block;
  }

  .cb-header-actions {
    display: flex;
    gap: 4px;
  }

  .cb-btn-icon {
    width: 34px;
    height: 34px;
    border: none;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    transition: background 0.2s;
  }

  .cb-btn-icon:hover {
    background: rgba(255, 255, 255, 0.25);
  }

  .cb-btn-icon svg {
    width: 18px;
    height: 18px;
  }

  .cb-btn-icon.cb-authenticated {
    background: rgba(74, 222, 128, 0.3);
  }

  /* ── Messages Area ───────────────────────────────────────── */

  .cb-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    scroll-behavior: smooth;
  }

  .cb-messages::-webkit-scrollbar {
    width: 5px;
  }

  .cb-messages::-webkit-scrollbar-track {
    background: transparent;
  }

  .cb-messages::-webkit-scrollbar-thumb {
    background: var(--cb-border);
    border-radius: 10px;
  }

  /* ── Welcome ─────────────────────────────────────────────── */

  .cb-welcome {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;
    flex: 1;
  }

  .cb-welcome-icon {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: var(--cb-primary-light);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
    color: var(--cb-primary);
  }

  .cb-welcome-icon svg {
    width: 32px;
    height: 32px;
  }

  .cb-welcome-text {
    color: var(--cb-text);
    font-size: 14px;
    line-height: 1.7;
    max-width: 300px;
  }

  .cb-welcome-text strong {
    color: var(--cb-primary);
  }

  /* ── Message Bubbles ─────────────────────────────────────── */

  .cb-message {
    display: flex;
    max-width: 85%;
    animation: cb-fade-in 0.3s ease-out;
  }

  @keyframes cb-fade-in {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .cb-message-user {
    align-self: flex-end;
  }

  .cb-message-assistant {
    align-self: flex-start;
  }

  .cb-message-system {
    align-self: center;
    max-width: 100%;
  }

  .cb-bubble {
    padding: 10px 16px;
    border-radius: 14px;
    font-size: 14px;
    line-height: 1.6;
    word-break: break-word;
  }

  .cb-message-user .cb-bubble {
    background: var(--cb-primary);
    color: white;
    border-bottom-right-radius: 4px;
  }

  .cb-message-assistant .cb-bubble {
    background: var(--cb-bg-secondary);
    color: var(--cb-text);
    border-bottom-left-radius: 4px;
    border: 1px solid var(--cb-border);
  }

  .cb-bubble strong {
    font-weight: 600;
  }

  .cb-bubble code {
    background: rgba(0, 0, 0, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
    font-family: 'SF Mono', Monaco, Consolas, monospace;
  }

  .cb-message-user .cb-bubble code {
    background: rgba(255, 255, 255, 0.2);
  }

  .cb-bubble ul, .cb-bubble ol {
    padding-left: 20px;
    margin: 6px 0;
  }

  .cb-bubble li {
    margin: 3px 0;
  }

  .cb-system-text {
    font-size: 12px;
    color: var(--cb-text-secondary);
    text-align: center;
    padding: 4px 12px;
    background: var(--cb-bg-secondary);
    border-radius: 12px;
  }

  /* ── Typing Indicator ────────────────────────────────────── */

  .cb-typing-bubble {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 14px 20px;
  }

  .cb-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--cb-text-secondary);
    opacity: 0.4;
    animation: cb-bounce 1.4s ease-in-out infinite;
  }

  .cb-dot:nth-child(2) { animation-delay: 0.2s; }
  .cb-dot:nth-child(3) { animation-delay: 0.4s; }

  @keyframes cb-bounce {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.4; }
    40% { transform: scale(1.2); opacity: 1; }
  }

  /* ── Streaming cursor ────────────────────────────────────── */

  .cb-cursor {
    animation: cb-blink 0.7s step-end infinite;
    color: var(--cb-primary);
    font-weight: 300;
  }

  @keyframes cb-blink {
    50% { opacity: 0; }
  }

  /* ── Input Area ──────────────────────────────────────────── */

  .cb-input-area {
    padding: 12px 16px;
    border-top: 1px solid var(--cb-border);
    background: var(--cb-bg);
    flex-shrink: 0;
  }

  .cb-input-wrapper {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    background: var(--cb-bg-secondary);
    border: 1px solid var(--cb-border);
    border-radius: 12px;
    padding: 8px 12px;
    transition: border-color 0.2s;
  }

  .cb-input-wrapper:focus-within {
    border-color: var(--cb-primary);
    box-shadow: 0 0 0 3px var(--cb-primary-light);
  }

  .cb-input-area textarea {
    flex: 1;
    border: none;
    background: transparent;
    resize: none;
    outline: none;
    font-family: var(--cb-font);
    font-size: 14px;
    color: var(--cb-text);
    line-height: 1.5;
    max-height: 120px;
    min-height: 22px;
  }

  .cb-input-area textarea::placeholder {
    color: var(--cb-text-secondary);
  }

  .cb-send-btn {
    width: 36px;
    height: 36px;
    min-width: 36px;
    border-radius: 10px;
    border: none;
    background: var(--cb-primary);
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .cb-send-btn:hover:not(:disabled) {
    background: var(--cb-primary-hover);
    transform: scale(1.05);
  }

  .cb-send-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .cb-send-btn svg {
    width: 18px;
    height: 18px;
  }

  .cb-powered {
    text-align: center;
    font-size: 11px;
    color: var(--cb-text-secondary);
    margin-top: 8px;
    opacity: 0.7;
  }

  /* ── Auth Modal ──────────────────────────────────────────── */

  .cb-auth-modal {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
    backdrop-filter: blur(4px);
    border-radius: var(--cb-radius);
  }

  .cb-auth-card {
    background: var(--cb-bg);
    border-radius: 16px;
    padding: 28px 24px;
    width: 85%;
    max-width: 340px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
    position: relative;
  }

  .cb-auth-card h3 {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 20px;
    color: var(--cb-text);
  }

  .cb-auth-card label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--cb-text-secondary);
    margin-bottom: 4px;
    margin-top: 12px;
  }

  .cb-auth-card input {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid var(--cb-border);
    border-radius: 10px;
    font-size: 14px;
    font-family: var(--cb-font);
    outline: none;
    transition: border-color 0.2s;
    background: var(--cb-bg);
    color: var(--cb-text);
  }

  .cb-auth-card input:focus {
    border-color: var(--cb-primary);
    box-shadow: 0 0 0 3px var(--cb-primary-light);
  }

  .cb-auth-error {
    margin-top: 12px;
    padding: 8px 12px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #dc2626;
    border-radius: 8px;
    font-size: 13px;
  }

  .cb-auth-submit {
    width: 100%;
    padding: 12px;
    margin-top: 20px;
    background: var(--cb-primary);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    font-family: var(--cb-font);
    transition: all 0.2s;
  }

  .cb-auth-submit:hover:not(:disabled) {
    background: var(--cb-primary-hover);
  }

  .cb-auth-submit:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .cb-auth-toggle {
    text-align: center;
    margin-top: 16px;
    font-size: 13px;
    color: var(--cb-text-secondary);
  }

  .cb-auth-toggle a {
    color: var(--cb-primary);
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
  }

  .cb-auth-toggle a:hover {
    text-decoration: underline;
  }

  .cb-auth-close {
    position: absolute;
    top: 10px;
    right: 14px;
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: var(--cb-text-secondary);
    padding: 4px;
  }

  .cb-auth-close:hover {
    color: var(--cb-text);
  }

  /* ── Agent Mode ──────────────────────────────────────────── */

  .cb-agent-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 10px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #065f46;
  }

  .cb-agent-bar-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    animation: cb-pulse 2s ease-in-out infinite;
    flex-shrink: 0;
  }

  @keyframes cb-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .cb-agent-bar-end {
    margin-left: auto;
    background: none;
    border: none;
    color: #6b7280;
    cursor: pointer;
    font-size: 14px;
    padding: 2px 6px;
    border-radius: 4px;
    transition: all 0.2s;
  }

  .cb-agent-bar-end:hover {
    background: #fee2e2;
    color: #dc2626;
  }

  .cb-input-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 8px;
  }

  .cb-human-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: none;
    border: 1px solid var(--cb-border);
    color: var(--cb-text-secondary);
    font-size: 11px;
    font-family: var(--cb-font);
    cursor: pointer;
    padding: 4px 10px;
    border-radius: 14px;
    transition: all 0.2s;
  }

  .cb-human-btn:hover {
    border-color: var(--cb-primary);
    color: var(--cb-primary);
    background: var(--cb-primary-light);
  }

  .cb-human-btn svg {
    width: 13px;
    height: 13px;
  }
`;
