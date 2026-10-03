# DecisionOS — Autonomous AI Research & Decision-Support Engine

DecisionOS is an evidence-based autonomous decision assistant. It converts natural language research goals into clear, scannable decision briefs by analyzing real-time web evidence via SerpApi, detecting conflicting claims, and evaluating trade-offs.

---

## 🌐 Live Application Links

- **Frontend Application (Vercel)**: [https://decisionos-er35i84uv-harmohinis-projects.vercel.app/](https://decisionos-er35i84uv-harmohinis-projects.vercel.app/)
- **Backend API (Render)**: [https://decisionos-2.onrender.com](https://decisionos-2.onrender.com)
- **API Documentation (Swagger UI)**: [https://decisionos-2.onrender.com/docs](https://decisionos-2.onrender.com/docs)
- **GitHub Repository**: [https://github.com/harmohini/DecisionOS](https://github.com/harmohini/DecisionOS)

---

## 🌟 Key Features & UX Design

- **Concise Consumer Experience**: Understand research results in **30–60 seconds**.
- **Your Decision Brief**: Short, scannable summary highlighting *Looking for*, *Budget*, *Must-haves*, and *Main trade-offs*.
- **Top Options**: Capped at maximum 6 compact option cards with *Best for* labels, *Why it fits* bullets (`✓`), and *Watch out* lines.
- **Key Findings**: Top evidence-backed insights (`✓`).
- **Check Before Buying**: Identifies reported specification disagreements or price variations across sources.
- **Before You Decide**: Verification checklist items (`☐`) prior to purchasing.
- **Source Traceability**: Collapsible sources list (`[ View sources ]`) connecting claims to original web sources.

---

## 🛠️ Tech Stack & Architecture

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS (Clean warm beige/off-white aesthetic system)
- **Backend**: Python 3.13, FastAPI, Pydantic v2, SQLAlchemy
- **Search Engine**: SerpApi (Backend integration for Google Search, Google Shopping, and YouTube)
- **Database**: SQLite (modular design, PostgreSQL ready)
- **LLM Layer**: Configurable LLM provider interface (OpenAI, Groq, Anthropic, Gemini)

---

## 🔑 Environment Configuration

1. Copy `.env.example` to create your `.env` file:
   ```bash
   cp .env.example .env
   ```
2. Set your environment variables in `.env`:
   ```env
   SERPAPI_API_KEY=your_actual_serpapi_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

---

## 🚀 Local Development Setup

### 1. Backend Server Setup & Start

```bash
cd backend

# Create virtual environment & install dependencies
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Start FastAPI server
PYTHONPATH=. ./venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API Health Check: `http://127.0.0.1:8000/api/v1/health`
- API Documentation: `http://127.0.0.1:8000/docs`

### 2. Frontend Application Setup & Start

```bash
cd frontend

# Install Node modules
npm install

# Start Vite dev server
npm run dev -- --port 5173
```

- Local Interface: `http://localhost:5173`

---

## 🧪 Unit & Integration Tests

Run the complete 91-test suite locally (uses mocked search responses to preserve search API quotas):

```bash
cd backend
PYTHONPATH=. ./venv/bin/pytest tests/
```

---

## 🔒 Security Principles

- **Zero Key Exposure**: `SERPAPI_API_KEY` and `OPENAI_API_KEY` are executed strictly on the backend.
- **No Mock Data**: Real web research results are retrieved, normalized, and scored against requirements.
- **Provenance Preservation**: Every claim and product recommendation links directly to verified source URLs.
