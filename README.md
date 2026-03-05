# 🤖 AI Chatbot — Powered by Google Gemini

A production-grade, embeddable AI chatbot for **product inquiries**, **customer support**, **order tracking**, and **live agent handoff**. Drop a single `<script>` tag into any website and get a fully functional chat widget — no frontend coding required.

![Stack](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square)
![LLM](https://img.shields.io/badge/LLM-Google%20Gemini-4285F4?style=flat-square)
![DB](https://img.shields.io/badge/DB-PostgreSQL%20%7C%20SQLite-336791?style=flat-square)
![Agent](https://img.shields.io/badge/Feature-Live%20Agent%20Handoff-10b981?style=flat-square)

---

## 📖 Table of Contents

- [How It Works](#-how-it-works)
- [Quick Start](#-quick-start)
- [Integrating Into Your Website](#-integrating-into-your-website)
- [Live Agent Handoff](#-live-agent-handoff)
- [Widget Integration](#-widget-integration)
- [Customization Guide](#-customization-guide)
- [Environment Variables](#-environment-variables)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Production Deployment](#-production-deployment)

---

## 🎯 How It Works

```
Your Website                    Chatbot Server                  Google Gemini
┌──────────────┐   API calls   ┌──────────────────┐  LLM API  ┌──────────────┐
│  <script>    │ ───────────▸  │  FastAPI Backend  │ ────────▸ │  Gemini 2.5  │
│  Chat Bubble │ ◂───────────  │  + SQLite/PG DB   │ ◂──────── │  Flash       │
│  (auto)      │   SSE stream  │  + Function Tools │           │              │
└──────────────┘               └──────────────────┘           └──────────────┘
                                        ▲
                                        │ WebSocket
                                        ▼
                               ┌──────────────────┐
                               │  Agent Dashboard  │
                               │  (Live Agents)    │
                               └──────────────────┘
```

1. You add **one `<script>` tag** to your website
2. A **floating chat bubble** automatically appears (bottom-right corner)
3. Users click it → chat window opens inside an isolated **Shadow DOM** (won't break your CSS)
4. Messages are sent to your backend → Gemini processes them with **function calling**
5. Responses stream back in **real-time via SSE** (Server-Sent Events)
6. If the user needs a human, the AI (or the user) can trigger a **live agent handoff** — the conversation switches to a real-time **WebSocket** channel where a support agent replies directly

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for building the widget)
- A [Google Gemini API key](https://aistudio.google.com/apikey)

### Setup

```bash
# 1. Clone & enter
cd chatbot

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Build the widget
cd widget && npm install && npm run build && cd ..

# 5. Configure environment
cp .env.example .env
# Edit .env → set your GEMINI_API_KEY

# 6. Seed the database
python -m backend.seed

# 7. Start the server
uvicorn backend.main:app --reload
```

Open **http://localhost:8000** to see the demo page with the chatbot.
Open **http://localhost:8000/agent** to open the agent dashboard.

---

## 🔗 Integrating Into Your Website

> **Scenario:** You have an existing project (e.g. a React / Next.js / plain HTML site) running locally and you want to add this chatbot to it during development.

### Step 1: Run the chatbot server

In the `chatbot/` folder, start the backend:

```bash
cd chatbot
source .venv/bin/activate
uvicorn backend.main:app --reload
# Server runs at http://localhost:8000
```

### Step 2: Add the script tag to your frontend

In your website's HTML (e.g. `index.html`, or your framework's root layout), add this **single script tag** before `</body>`:

```html
<script
    src="http://localhost:8000/widget/chatbot-widget.js"
    data-api-key="YOUR_API_KEY"
    data-server="http://localhost:8000"
    data-position="right"
    data-theme-color="#6366f1">
</script>
```

> **`YOUR_API_KEY`** — this is the key printed when you ran `python -m backend.seed`. It starts with `cb_`. If you lost it, re-run the seed command or create a new one via the Admin API.

### Step 3: Handle CORS (if your frontend runs on a different port)

If your frontend runs on, say, `http://localhost:3000` or `http://localhost:5173`, the chatbot server needs to allow cross-origin requests. This is already handled — in development mode the server allows all origins. If you need to be explicit, set this in your `.env`:

```env
APP_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Example: folder structure side by side

```
my-project/
├── my-website/          ← Your existing frontend/backend
│   ├── src/
│   ├── index.html       ← Add the <script> tag here
│   └── ...
└── chatbot/             ← This chatbot project
    ├── backend/
    ├── widget/
    ├── .env
    └── ...
```

Both run simultaneously on different ports:
- Your website: `http://localhost:3000` (or whatever port)
- Chatbot server: `http://localhost:8000`

The `<script>` tag in your website loads the widget JS from `localhost:8000` and all API calls go to `localhost:8000` — your frontend doesn't need any code changes beyond that one tag.

### Framework-specific examples

**React (public/index.html or index.html):**
```html
<body>
  <div id="root"></div>
  <!-- Add before closing body tag -->
  <script
      src="http://localhost:8000/widget/chatbot-widget.js"
      data-api-key="cb_your_key_here"
      data-server="http://localhost:8000">
  </script>
</body>
```

**Next.js (app/layout.tsx or pages/_document.tsx):**
```tsx
import Script from 'next/script'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Script
          src="http://localhost:8000/widget/chatbot-widget.js"
          data-api-key="cb_your_key_here"
          data-server="http://localhost:8000"
          strategy="lazyOnload"
        />
      </body>
    </html>
  )
}
```

**Vue / Vite (index.html):**
```html
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
  <script
      src="http://localhost:8000/widget/chatbot-widget.js"
      data-api-key="cb_your_key_here"
      data-server="http://localhost:8000">
  </script>
</body>
```

**Angular (src/index.html):**
```html
<body>
  <app-root></app-root>
  <script
      src="http://localhost:8000/widget/chatbot-widget.js"
      data-api-key="cb_your_key_here"
      data-server="http://localhost:8000">
  </script>
</body>
```

---

## 🤝 Live Agent Handoff

The chatbot can seamlessly transfer a conversation to a real human support agent. The conversation continues in the same chat window — the user doesn't leave the page or lose context.

### How it works

1. **AI detects the need** — When a user asks to "speak to a human", is frustrated, or has a complex issue the bot can't resolve, the AI calls the `handoff_to_agent` tool
2. **User can also trigger it** — A "Talk to a human" button is visible below the chat input
3. **Conversation is queued** — The conversation status changes to `queued` and appears in the Agent Dashboard
4. **Agent connects** — A support agent opens the dashboard, sees the queue, and clicks "Connect"
5. **Real-time chat via WebSocket** — Messages between the user and agent are relayed in real time. All messages are persisted to the same conversation history
6. **Agent closes session** — When done, the agent clicks "End Session" and the user returns to bot mode

### Testing live agent handoff locally

**Terminal 1 — Run the chatbot server:**
```bash
cd chatbot
source .venv/bin/activate
uvicorn backend.main:app --reload
```

**Browser Tab 1 — Open the demo page (acts as the customer):**
```
http://localhost:8000
```

**Browser Tab 2 — Open the agent dashboard (acts as the support agent):**
```
http://localhost:8000/agent
```

**Test flow:**
1. In the **agent dashboard**, enter your name (e.g. "Alice") and click "Start Accepting Chats"
2. In the **demo page**, open the chat widget and either:
   - Click the **"Talk to a human"** button at the bottom, or
   - Type *"I want to speak with a real person"*
3. The AI will acknowledge the request and trigger the handoff
4. In the **agent dashboard**, click **↻ Refresh** — the conversation appears in the queue
5. Click the conversation → click **Connect**
6. Type messages on both sides — they appear in real time
7. Click **End Session** in the dashboard — the user sees a message that they're back with the AI

### Agent Dashboard

The agent dashboard is available at `/agent` and provides:
- **Queue view** — all conversations waiting for or connected to an agent
- **Full history** — see the entire conversation (AI + user messages) before connecting
- **Real-time messaging** — bidirectional WebSocket communication
- **Session management** — connect to / end live sessions
- **Auto-refresh** — queue updates every 5 seconds

---

## 🔌 Widget Integration

### The chat bubble is fully automatic

Just add this tag to **any** HTML page. The widget creates itself — a floating bubble appears, and clicking it opens the full chat interface. **No additional frontend code needed.**

```html
<!-- For local development -->
<script
    src="http://localhost:8000/widget/chatbot-widget.js"
    data-api-key="YOUR_API_KEY"
    data-server="http://localhost:8000"
    data-position="right"
    data-theme-color="#6366f1">
</script>

<!-- For production (replace with your deployed server URL) -->
<script
    src="https://your-server.com/widget/chatbot-widget.js"
    data-api-key="YOUR_API_KEY"
    data-server="https://your-server.com"
    data-position="right"
    data-theme-color="#6366f1">
</script>
```

### What gets injected automatically:
- ✅ **Floating chat bubble** (bottom corner of the page)
- ✅ **Chat window** with message history, typing indicators, streaming responses
- ✅ **Sign-in modal** for authenticated features (order tracking)
- ✅ **"Talk to a human" button** for live agent handoff
- ✅ **Live agent mode** — real-time WebSocket chat when an agent connects
- ✅ **Markdown rendering** in bot responses
- ✅ All wrapped in **Shadow DOM** — zero CSS/JS conflicts with your site

### Script Tag Attributes

| Attribute | Required | Default | Description |
|-----------|----------|---------|-------------|
| `data-api-key` | ✅ | — | Your tenant API key (starts with `cb_`) |
| `data-server` | ✅ | — | URL of your chatbot backend server |
| `data-position` | ❌ | `right` | Bubble position: `right` or `left` |
| `data-theme-color` | ❌ | `#6366f1` | Primary color — match your brand |

### Example: different positions and colors

```html
<!-- Bottom-right, blue theme -->
<script src="http://localhost:8000/widget/chatbot-widget.js" data-api-key="cb_..." data-server="http://localhost:8000" data-theme-color="#3b82f6"></script>

<!-- Bottom-left, green theme -->
<script src="http://localhost:8000/widget/chatbot-widget.js" data-api-key="cb_..." data-server="http://localhost:8000" data-position="left" data-theme-color="#10b981"></script>

<!-- Red theme to match brand -->
<script src="http://localhost:8000/widget/chatbot-widget.js" data-api-key="cb_..." data-server="http://localhost:8000" data-theme-color="#e63946"></script>
```

---

## 🎨 Customization Guide

### 1. Tenant Name & Branding

The chatbot header shows your **tenant name**. Change it when creating the tenant:

```python
# In backend/seed.py — change this:
tenant = Tenant(
    name="Your Company Name",        # ← Shown in chat header
    domain="yourwebsite.com",        # ← Your domain
    ...
)
```

Or via the Admin API:
```http
POST /api/v1/admin/tenants
{
    "name": "Your Company Name",
    "domain": "yourwebsite.com"
}
```

### 2. Welcome Message

The first message shown when users open the chatbot:

```python
# In backend/seed.py
tenant = Tenant(
    ...
    welcome_message=(
        "👋 Hi there! I'm your assistant for MyCompany.\n\n"
        "I can help with:\n"
        "🔍 Finding products\n"
        "📦 Tracking your orders\n"
        "❓ Answering questions\n"
        "🤝 Connecting you with a human agent\n\n"
        "What can I do for you?"
    ),
)
```

### 3. Bot Personality (System Prompt)

Control how the bot talks, what it knows about your business, and how it behaves:

```python
# In backend/seed.py
tenant = Tenant(
    ...
    system_prompt=(
        "You are the customer assistant for MyCompany. "
        "We sell handmade furniture. Always be warm, helpful, "
        "and mention our 10-year warranty when relevant. "
        "Our tone is casual and friendly."
    ),
)
```

This gets appended to the base system prompt. The base prompt (in `backend/chat/prompts.py`) handles general chatbot behavior — your override adds business-specific context.

### 4. Products

Replace the demo products with your real catalog:

```python
# In backend/seed.py
Product(
    tenant_id=tenant.id,
    sku="YOUR-SKU-001",              # Your product SKU
    name="Your Product Name",        # Product name
    description="Detailed description...",
    category="Your Category",        # e.g., "Furniture", "Electronics"
    price=199.99,
    currency="USD",                  # Currency code
    in_stock=True,
    stock_quantity=50,
    specifications={                 # Any key-value specs
        "material": "Oak Wood",
        "dimensions": "120x60x75 cm",
        "weight": "25kg",
    },
    image_url="https://...",         # Product image URL
)
```

### 5. FAQs (Knowledge Base)

The bot searches these to answer common questions:

```python
FAQ(
    tenant_id=tenant.id,
    question="What is your return policy?",
    answer="We offer a 30-day return policy...",
    category="returns",              # Group related FAQs
    keywords=["return", "refund", "exchange"],  # Search keywords
)
```

### 6. Orders (for tracking)

For real usage, you'd integrate with your order management system. The demo uses seed data:

```python
Order(
    tenant_id=tenant.id,
    order_number="ORD-001",          # Customers use this to track
    customer_email="...",            # Verified against during tracking
    customer_name="...",
    status=OrderStatus.SHIPPED,      # PENDING | CONFIRMED | PROCESSING | SHIPPED | IN_TRANSIT | DELIVERED | CANCELLED | RETURNED
    items=[{"sku": "...", "name": "...", "quantity": 1, "price": 99.99}],
    total_amount=99.99,
    tracking_number="TRK-...",
    carrier="FedEx",
)
```

### 7. Theme Color

Change the chat bubble and UI accent color via the script tag:

```html
data-theme-color="#e63946"   <!-- Red -->
data-theme-color="#10b981"   <!-- Green -->
data-theme-color="#f59e0b"   <!-- Amber -->
data-theme-color="#8b5cf6"   <!-- Purple -->
data-theme-color="#06b6d4"   <!-- Cyan -->
```

### 8. Gemini Model Settings

In `.env`:

```env
GEMINI_MODEL=gemini-2.5-flash       # Model to use
GEMINI_MAX_TOKENS=4096               # Max response length
GEMINI_TEMPERATURE=1.0               # 0.0 = deterministic, 2.0 = creative
```

### 9. Rate Limiting

```env
RATE_LIMIT_PER_MINUTE=30             # Max requests per minute per IP
RATE_LIMIT_PER_HOUR=500              # Max requests per hour per IP
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root. All settings are optional except `GEMINI_API_KEY`.

| Variable | Default | Description |
|----------|---------|-------------|
| **App** | | |
| `APP_NAME` | `chatbot` | Application name |
| `APP_ENV` | `development` | `development` / `staging` / `production` |
| `APP_DEBUG` | `false` | Enable debug mode |
| `APP_HOST` | `0.0.0.0` | Server bind address |
| `APP_PORT` | `8000` | Server port |
| `APP_SECRET_KEY` | `change-me...` | Secret for signing (change in production!) |
| `APP_CORS_ORIGINS` | `localhost:3000,...` | Comma-separated allowed origins |
| **Database** | | |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Database connection string |
| `DATABASE_ECHO` | `false` | Log all SQL queries |
| `DATABASE_POOL_SIZE` | `20` | Connection pool size |
| **Redis** | | |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| **Gemini** | | |
| `GEMINI_API_KEY` | *(empty)* | **Required** — Your Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `GEMINI_MAX_TOKENS` | `4096` | Max output tokens |
| `GEMINI_TEMPERATURE` | `1.0` | Response creativity (0.0–2.0) |
| **JWT Auth** | | |
| `JWT_SECRET_KEY` | `change-me...` | JWT signing key (change in production!) |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| **Rate Limiting** | | |
| `RATE_LIMIT_PER_MINUTE` | `30` | Requests/min per IP |
| `RATE_LIMIT_PER_HOUR` | `500` | Requests/hour per IP |
| **Logging** | | |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | `json` | `json` (production) or `console` (dev) |

### Minimal `.env` for local development:

```env
GEMINI_API_KEY=your-gemini-api-key
DATABASE_URL=sqlite+aiosqlite:///./chatbot.db
```

---

## 📁 Project Structure

```
chatbot/
├── backend/
│   ├── main.py                  # FastAPI app factory & entry point
│   ├── config.py                # All settings (from .env)
│   ├── seed.py                  # Database seeder — EDIT THIS for your data
│   ├── api/
│   │   ├── auth_routes.py       # User registration, login, token refresh
│   │   ├── chat_routes.py       # Chat message & streaming endpoints
│   │   ├── agent_routes.py      # WebSocket endpoints + agent dashboard API
│   │   ├── admin_routes.py      # Tenant & API key management
│   │   └── widget_routes.py     # Widget config endpoint
│   ├── auth/
│   │   ├── api_keys.py          # API key generation & hashing
│   │   ├── jwt.py               # JWT token create/decode
│   │   ├── passwords.py         # bcrypt password hashing
│   │   └── dependencies.py      # FastAPI auth dependencies
│   ├── chat/
│   │   ├── engine.py            # Core Gemini chat engine + function calling
│   │   ├── tools.py             # Tool declarations (including handoff_to_agent)
│   │   └── prompts.py           # System prompts — EDIT for bot personality
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models (Tenant, Product, Order, Conversation, etc.)
│   │   └── session.py           # Async database engine & sessions
│   ├── middleware/
│   │   ├── request_id.py        # UUID per request for tracing
│   │   ├── logging_middleware.py # Structured request logging
│   │   ├── rate_limiter.py      # Rate limiting (slowapi)
│   │   └── error_handlers.py    # Global error handlers
│   └── services/
│       ├── product_service.py   # Product search & lookup
│       ├── order_service.py     # Order tracking
│       ├── faq_service.py       # FAQ search
│       ├── ticket_service.py    # Support ticket creation
│       ├── conversation_service.py  # Chat history management
│       └── agent_service.py     # WebSocket connection manager for live agent
├── widget/
│   ├── src/
│   │   ├── chatbot.js           # Main widget class (Shadow DOM, UI, agent mode)
│   │   ├── api.js               # API client for backend calls + WS URL builder
│   │   ├── auth.js              # Auth manager (JWT tokens)
│   │   └── styles.js            # All widget CSS (injected into Shadow DOM)
│   ├── vite.config.js           # Builds to single IIFE bundle
│   └── package.json
├── alembic/                     # Database migrations
│   └── versions/
│       └── 20260305_agent_handoff.py  # Migration for agent handoff fields
├── tests/                       # pytest test suite
├── demo.html                    # Demo page with widget embedded
├── agent_dashboard.html         # Agent dashboard for live chat support
├── .env                         # Your local config
├── pyproject.toml               # Python dependencies
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # Full stack: API + PostgreSQL + Redis
└── Makefile                     # Common commands
```

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check |

### Chat
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/chat/message` | API Key | Send message, get full response |
| `POST` | `/api/v1/chat/stream` | API Key | Send message, get SSE stream |
| `GET` | `/api/v1/chat/conversations` | API Key + JWT | List user conversations |

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auth/register` | API Key | Register end user |
| `POST` | `/api/v1/auth/login` | API Key | Login, get JWT tokens |
| `POST` | `/api/v1/auth/refresh` | API Key | Refresh access token |

### Agent / Live Handoff
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/agent/queue` | List conversations waiting for / connected to an agent |
| `POST` | `/api/v1/agent/close/{conversation_id}` | Agent ends the live session |
| `GET` | `/api/v1/agent/conversations/{conversation_id}/messages` | Get full conversation history |
| `WS` | `/api/v1/ws/chat/{conversation_id}?api_key=...` | User-side WebSocket for live chat |
| `WS` | `/api/v1/ws/agent/{conversation_id}?agent_name=...` | Agent-side WebSocket for live chat |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/admin/tenants` | Create tenant |
| `GET` | `/api/v1/admin/tenants/{id}` | Get tenant details |
| `POST` | `/api/v1/admin/tenants/{id}/api-keys` | Generate API key |

### Widget
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/widget/config` | API Key | Get widget config (name, welcome msg) |

### Pages
| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Demo page with chatbot widget |
| `http://localhost:8000/agent` | Agent dashboard for live support |
| `http://localhost:8000/docs` | Interactive API docs (Swagger UI) |

---

## 🐳 Production Deployment

### Using Docker Compose (Recommended)

```bash
# Set production secrets in .env
APP_ENV=production
GEMINI_API_KEY=your-key
JWT_SECRET_KEY=$(openssl rand -hex 32)
APP_SECRET_KEY=$(openssl rand -hex 32)

# Start everything
docker compose up -d --build
```

This starts:
- **PostgreSQL 16** (database)
- **Redis 7** (rate limiting cache)
- **Chatbot API** (FastAPI + widget)

### Manual Deployment

```bash
# Install production dependencies
pip install -e .

# Build widget
cd widget && npm ci && npm run build && cd ..

# Run with production server
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🧩 Key Files to Customize

| What | File | What to change |
|------|------|---------------|
| **Company name** | `backend/seed.py` → `Tenant.name` | Your brand name (shown in chat header) |
| **Welcome message** | `backend/seed.py` → `Tenant.welcome_message` | First message users see |
| **Bot personality** | `backend/seed.py` → `Tenant.system_prompt` | Business-specific instructions |
| **Products** | `backend/seed.py` → `Product(...)` | Your real product catalog |
| **FAQs** | `backend/seed.py` → `FAQ(...)` | Your real frequently asked questions |
| **Orders** | `backend/seed.py` → `Order(...)` | Connect to your order system |
| **Base bot behavior** | `backend/chat/prompts.py` | Core chatbot instructions |
| **Available tools** | `backend/chat/tools.py` | Add/remove function calling tools |
| **Tool logic** | `backend/chat/engine.py` → `_execute_tool()` | What happens when a tool is called |
| **Agent handoff logic** | `backend/services/agent_service.py` | WebSocket connection manager |
| **Theme color** | Script tag → `data-theme-color` | Match your brand colors |
| **Widget position** | Script tag → `data-position` | `right` or `left` |
| **Widget UI** | `widget/src/styles.js` | CSS variables & full styling |
| **Gemini settings** | `.env` → `GEMINI_*` | Model, temperature, max tokens |

---

## 📝 Demo Credentials

After running `python -m backend.seed`:

| Item | Value |
|------|-------|
| Demo user email | `john@example.com` |
| Demo user password | `password123` |
| Sample orders | `ORD-001`, `ORD-002`, `ORD-003`, `ORD-004` |
| API key | Printed once during seeding (starts with `cb_`) |

---

## License

MIT
