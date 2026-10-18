# Lifeline Triage - Cyclone Response Control Room Decision-Support

> **The One-Line Idea:** Lifeline Triage consolidates noisy, duplicated community distress reports into ranked, explainable crisis incidents while actively surfacing silent, high-risk blackout zones where nobody has signal to call.

---

## Persistent Notice: Simulated Data
⚠️ **ALL DATA IS SIMULATED.** Every screen displays a persistent `SIMULATED DATA` banner. The system does NOT send real SMS messages, predict cyclone tracks, or dispatch emergency vehicles without human coordinator review.

---

## Key Capabilities
1. **Deduplication with >50% Volume Reduction:** Consolidates hundreds of raw SMS, calls, social posts, and field volunteer reports into unified incidents using TF-IDF character n-grams and uncertainty circle overlap.
2. **Transparent Multi-Factor Scoring ("Why This Rank"):** No black box. Decomposes priority into Need Severity, People Count, Vulnerability, Time Criticality, and Corroboration, weighted by a Data Reliability score.
3. **Silence Gap Analysis:** Automatically flags high-risk zones with low connectivity and a report deficit (`reports / expected < 0.30`), preventing call volume bias from starving disconnected communities.
4. **Human in the Loop:** Recommends only. Coordinator actions (`approve`, `override`, `merge`, `split`, `dismiss`) require mandatory justifications and are recorded in a tamper-resistant SQLite audit log.
5. **100% Offline Capable:** Runs without active internet access using vector district polygons and offline rule-based NLP extraction.

---

## Architecture & Folder Structure

```
lifeline-triage/
  ├── README.md               # Overview, quickstart, and limitations
  ├── ASSUMPTIONS.md          # Architectural assumptions
  ├── DEMO_SCRIPT.md          # 2-minute walkthrough path for judges & evaluators
  ├── backend/
  │   ├── app/
  │   │   ├── main.py         # FastAPI application with CORS and API endpoints
  │   │   ├── config.py       # Weights (starting values, not validated) & seed 42
  │   │   ├── models.py       # Pydantic schemas (Zone, Report, Incident, Audit, Alert)
  │   │   ├── store.py        # SQLite persistence for audit logs, alerts, state
  │   │   ├── extract.py      # Rule-based NLP extraction with confidence scoring
  │   │   ├── locate.py       # Rapidfuzz gazetteer resolution & vague location protection
  │   │   ├── merge.py        # Union-Find TF-IDF char_wb & spatial overlap clustering
  │   │   ├── score.py        # Explainable multi-factor scoring & plain-text reasons
  │   │   ├── silence.py      # Expected report baseline rate and silence gap detector
  │   │   ├── baseline.py     # Unmerged raw report volume baseline benchmark
  │   │   ├── metrics.py      # Live evaluation from ground truth (F1, top-10, silence)
  │   │   ├── alerts.py       # Pre-landfall targeted preparedness draft generator
  │   │   ├── simulation.py   # Background streaming simulation manager
  │   │   └── eval.py         # CLI runner for printing evaluation table
  │   ├── data/
  │   │   ├── district.json   # 12 fictional zones (Z01..Z12) with 3 planted silent zones
  │   │   ├── reports.jsonl   # ~200 noisy synthetic reports across channels
  │   │   ├── truth.json      # Report-level ground truth (true need, count, fake flag)
  │   │   └── expert_ranking.json # Hidden ground truth top-15 ranking benchmark
  │   ├── scripts/
  │   │   └── generate_data.py # Deterministic scenario generator (seed 42)
  │   └── tests/
  │       └── test_pipeline.py # Pytest suite (extraction, merge, silence, scoring)
  └── frontend/
      ├── index.html          # Entry HTML with Leaflet CSS
      ├── vite.config.js      # Vite dev server with proxy to backend :8000
      └── src/
          ├── main.jsx        # React DOM mount
          ├── App.jsx         # 4-tab control room dashboard
          └── index.css       # Projector-friendly dark mode styles
```

---

---

## Frontend Redesign (30-Second Evaluator & Coordinator Workflow)

The frontend was redesigned to ensure a non-technical judge or emergency coordinator understands the system within 30 seconds:
- **3-Step Intuitive Navigation:**
  1. **Prepare:** *Which areas are most at risk before the cyclone?* (Proactive monitoring of telecom blackout zones).
  2. **Respond:** *What should we do first, and why?* (Ranked dispatch queue with plain-language emergency cards).
  3. **Proof:** *Is this triage better than traditional dispatch?* (Noise reduction, expert alignment, blackout detection).
- **Zero Jargon:** Replaced all technical codes and raw decimals with clear human-actionable phrases.
- **Explainable Decisions:** "Why is this ranked here?" slide-out drawer explains life danger, vulnerable groups, and caller corroboration.
- **Human Accountability:** Any coordinator priority adjustment requires a mandatory explanation logged in the Activity Log drawer.
- **100% Offline & Calm Theme:** Uses local assets (no external CDNs or web fonts) with an accessible emergency-operations light theme.

## Setup & Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Backend Setup & Run
From the project root:
```bash
# Navigate to backend and install requirements (if not already done)
cd backend
pip install fastapi uvicorn pydantic scikit-learn rapidfuzz numpy pytest httpx

# Start the FastAPI server (runs on http://127.0.0.1:8000)
uvicorn app.main:app --reload
```

### 2. Frontend Setup & Run
In a separate terminal:
```bash
# Navigate to frontend and start Vite
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser. The Vite proxy seamlessly routes all `/api/*` requests to the FastAPI backend.

---

## Regenerating Simulation Scenario Data
To regenerate the simulated district, noisy reports, and ground truth with seed 42:
```bash
python backend/scripts/generate_data.py
```

## Running Automated Evaluation & Tests

### Print Evaluation Results Table:
```bash
cd backend
python -m app.eval
```

### Run Pytest Test Suite:
```bash
cd backend
python -m pytest tests -v
```

---

## Limitations & Honest Caveats
1. **Simulated Data & Synthetic Ground Truth:** Evaluated entirely on simulated data with self-generated ground truth. Real-world disaster telemetry contains unpredictable slang, dialect switches, and sensor anomalies.
2. **Unvalidated Weights:** Scoring weights in `backend/app/config.py` are initial starting estimates; before any real deployment, emergency response commanders must calibrate these weights against historical cyclone post-mortems.
3. **Rule-Based Extractor:** Default extraction utilizes deterministic regex and keyword gazetteers for offline reliability. Complex contextual negations ("we do NOT need food, only water") can fool keyword counters.
4. **Human-in-the-Loop Requirement:** The system should never be hooked directly to automated dispatch actuators without a trained human coordinator in the loop.
