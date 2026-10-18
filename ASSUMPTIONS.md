# Assumptions for Lifeline Triage System

All assumptions made during the design, architecture, and implementation of Lifeline Triage are documented here:

1. **Synthetic Environment & Coordinate Frame:**
   - The coastal geography is fictional ("Sundarbari Coastal District") with 12 polygonal zones situated along a simulated coastline (latitude ~17.5°N - 17.9°N, longitude ~82.8°E - 83.4°E).
   - Zone coordinates and landmark aliases are modeled after typical Bay of Bengal coastal districts.

2. **Offline-First Vector Mapping:**
   - In emergency disaster response control rooms, broadband internet frequently drops due to optical fiber and tower destruction.
   - The primary map visualizer renders district zone boundary polygons and incident uncertainty circles completely offline using Leaflet vector overlays (no external tile layer dependency required by default).
   - An optional toggle allows loading OpenStreetMap tiles when internet connectivity is present.

3. **Planted Silent Zones (Z01, Z04, Z07):**
   - Exactly 3 zones were designated as high-risk with low connectivity (<= 0.20 mobile coverage) and 0 to 2 total reports:
     - `Z01`: Kalingapatnam Sands (barrier fishing coastline)
     - `Z04`: Dhamra Creek Estuary (tidal mangrove inlet)
     - `Z07`: Baruva Lowlands (remote tidal sluice peninsula)
   - These zones conceal severe ground truth emergencies in `truth.json` (ratios < 0.30 of baseline rate).

4. **Rule-Based Extraction as Primary Default:**
   - In adherence to strict offline constraints and low latency requirements, `extract.py` utilizes deterministic keyword tokenizers and regular expressions rather than network-dependent LLMs.
   - An optional `USE_LLM=false` environment flag exists in `config.py`.

5. **Clustering & De-duplication Logic:**
   - Character n-grams (`char_wb`, range 3-5) TF-IDF cosine similarity combined with geographic uncertainty circle overlap and identical emergency need type defines duplicate reports.
   - For reports lacking precise coordinates, high text similarity (>= 0.70) within the same zone hint or >= 0.88 overall is required to prevent incorrect cross-zone merges.

6. **Prioritization Scoring Weights:**
   - Initial weights defined in `backend/app/config.py` are explicitly labelled:
     `"Starting values, not validated"`.
   - Priority score is calculated as:
     `Priority = (0.30*Need + 0.25*People + 0.20*Vulnerable + 0.15*Time + 0.10*Corroboration) * (0.5 + 0.5 * Reliability)`
   - Corroboration is capped at 5 independent sources with a low weight (0.10) to prevent densely connected urban centers from drowning out silent, isolated communities.

7. **Human-in-the-Loop Policy:**
   - The system is decision-support only and never automatically dispatches or modifies rankings without coordinator authorization.
   - All coordinator actions (`approve`, `override`, `merge`, `split`, `dismiss`) require a mandatory text reason and are permanently preserved in the SQLite audit log.
