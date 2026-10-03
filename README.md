# DecisionOS - Autonomous AI Research & Decision-Support Engine

DecisionOS is an AI-powered autonomous research and decision-support application that converts natural language research goals into verified decision reports by analyzing real-time web evidence, detecting conflicting claims, and evaluating trade-offs.

---

## 🛠️ Architecture & Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS (Off-white/beige aesthetic system)
- **Backend**: Python, FastAPI, Pydantic v2, SQLAlchemy
- **Search Engine**: SerpApi (Backend integration for organic web, Google Shopping, and YouTube)
- **Database**: SQLite (modular design, ready for PostgreSQL upgrade)
- **AI/LLM Layer**: Configurable LLM provider interface (OpenAI, Groq, Anthropic, Gemini)

---

## 🔑 Obtaining a SerpApi API Key

1. Visit [https://serpapi.com](https://serpapi.com) and register for an account.
2. Log in and navigate to your **Dashboard**.
3. Copy your private **API Key**.
4. **Important**: Store `SERPAPI_API_KEY` *only* in your backend `.env` file. Never expose or commit this key to the frontend.

---

## ⚙️ Environment Setup

1. Copy `.env.example` to create your local `.env` file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and set your key:
   ```env
   SERPAPI_API_KEY=your_actual_serpapi_key_here
   ```

---

## 🚀 Running the Application

### 1. Backend Server Setup & Start

```bash
cd backend

# Create virtual environment & install dependencies (if not already done)
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Start FastAPI development server
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Documentation: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`
- Backend Search Test Endpoint: `http://localhost:8000/api/v1/search/test?q=laptop+for+AI+programming&engine=google`

### 2. Frontend Development Server

```bash
cd frontend

# Install node packages (if not already done)
npm install

# Start Vite dev server
npm run dev
```

- Web Interface: `http://localhost:5173`

---

## 🧪 Running Unit Tests

Backend unit tests use mocked HTTP responses so they do not consume your real SerpApi search quota:

```bash
cd backend
PYTHONPATH=. ./venv/bin/pytest tests/
```

---

## 🔒 Security Principles

- **No Exposed API Keys**: `SERPAPI_API_KEY` is loaded strictly by backend Python modules.
- **No Dummy Data**: Live web results are normalized into python dictionaries/schemas (`NormalizedSearchResponse`).
- **Explainable Decision Reports**: Claims link directly to verified web sources.
