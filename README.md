# Jobistan - Intelligent Job Aggregation Engine

Jobistan is a high-performance, automated job aggregation platform built to ingest, deduplicate, and present job postings from thousands of fragmented Applicant Tracking Systems (ATS) and career pages. 

The core feature of this platform is its **Self-Healing Extraction Engine**—a sophisticated data ingestion pipeline that autonomously detects when web scrapers break due to UI updates and uses Google Gemini (LLMs) to dynamically regenerate and validate new extraction rules without human intervention.

## 🚀 Key Features

### 1. Tiered Data Extraction Pipeline
Jobistan uses a multi-layered approach to maximize extraction speed while ensuring total resilience:
- **Specialized API Adapters**: Prioritizes robust, deterministic extraction using known ATS adapters (Greenhouse, Lever, Ashby, etc.) by extracting JSON-LD or intercepting API data.
- **Deterministic Rules Engine**: Falls back to deterministic CSS selectors and Playwright/BeautifulSoup automation for generic career pages.
- **LLM Self-Healing (Fallback)**: When deterministic rules break due to website layout changes, the engine falls back to an LLM to "heal" the scraper instead of dropping the data.

### 2. Autonomous Self-Healing Scrapers
Websites change constantly, which normally breaks web scrapers. Jobistan solves this:
- **Health Monitoring**: Real-time evaluation of data extraction completeness. If essential fields (Job Title, Company, etc.) are missing, the monitor flags the scraper as `BROKEN`.
- **LLM Rule Regeneration**: Feeds the broken HTML DOM and previous rules into Google Gemini to dynamically output a modernized, corrected CSS selector payload.
- **Pydantic Validation & Scoring**: The newly generated LLM rule is automatically deployed in a sandbox, scored against the live page, and if validated successfully, seamlessly replaces the broken rule in the PostgreSQL database.

### 3. Intelligent Deduplication
Jobs scraped from multiple sources (e.g., direct career pages vs. Indeed vs. Glassdoor) are heavily duplicated. Jobistan uses advanced intelligence modules to normalize and deduplicate records before they reach the user.

### 4. Advanced Anti-Bot Handling
Equipped with Playwright stealth techniques, the pipeline elegantly navigates and handles Cloudflare challenges, 403 Forbidden blocks, and rate-limits seamlessly.

---

## 🛠️ Technology Stack

**Backend:**
- Python 3.10+
- FastAPI
- PostgreSQL & SQLAlchemy (ORM)
- Alembic (Database Migrations)
- Playwright & BeautifulSoup4 (Web Scraping)
- Google GenAI / Gemini (LLM Healing)
- Pydantic (Schema Validation)
- Pytest (Automated Testing)
- APScheduler (Background Jobs)

**Frontend:**
- React (TypeScript)
- TailwindCSS
- Vite

---

## ⚙️ Local Development Setup

### 1. Prerequisites
- Python 3.10 or higher
- Node.js & npm
- PostgreSQL database

### 2. Backend Setup
Navigate to the backend directory and install the Python dependencies:

```bash
cd backend
python -m venv venv
# Activate virtual environment
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
playwright install
```

Set up your environment variables. Create a `.env` file in the root directory:
```env
PYTHONPATH=backend
DATABASE_URL=postgresql://user:password@localhost/jobistan
GEMINI_API_KEY=your_google_gemini_key
```

Run database migrations:
```bash
alembic upgrade head
```

Start the FastAPI server:
```bash
uvicorn api.main:app --reload
```

### 3. Frontend Setup
Navigate to the frontend directory:

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing

Jobistan contains a robust, mocked testing suite ensuring that API limits, LLM hallucinations, and anti-bot systems do not break the application logic.

To run the backend test suite:
```bash
cd backend
python -m pytest tests/
```

---

## 📁 Project Structure

```
Jobistan/
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── api/                  # FastAPI routes and endpoints
│   ├── core/
│   │   ├── extraction/       # Self-healing engine and rule validation
│   │   ├── ingestion/        # Adapters for ATS and generic scrapers
│   │   └── intelligence/     # Deduplication and normalizers
│   ├── db/                   # SQLAlchemy configuration
│   ├── models/               # Database tables
│   ├── schemas/              # Pydantic validation schemas
│   └── tests/                # Pytest suite
├── frontend/                 # React application
└── scratch/                  # Development and debugging scripts
```

## 📜 License
Internal / Proprietary
