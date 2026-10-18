import os
from typing import Dict

# Random seed for determinism across system
RANDOM_SEED = 42

# Zone Risk Weights (Starting values, not validated)
ZONE_RISK_WEIGHTS: Dict[str, float] = {
    "elevation": 0.25,        # Lower elevation -> higher risk
    "population_density": 0.25,# Higher density -> higher risk
    "dist_to_shelter": 0.20,  # Greater distance -> higher risk
    "dist_to_hospital": 0.15, # Greater distance -> higher risk
    "connectivity": 0.15      # Lower connectivity -> higher risk
}

# Incident Priority Scoring Weights (Starting values, not validated)
INCIDENT_SCORE_WEIGHTS: Dict[str, float] = {
    "need_severity": 0.30,
    "people": 0.25,
    "vulnerable": 0.20,
    "time_criticality": 0.15,
    "corroboration": 0.10
}

# Need severity scale mapping
NEED_SEVERITY_MAP: Dict[str, float] = {
    "rescue": 1.0,
    "medical": 0.85,
    "shelter": 0.65,
    "water": 0.50,
    "food": 0.40,
    "other": 0.20
}

# Merge clustering thresholds
MERGE_CONFIG = {
    "tfidf_char_ngram_min": 3,
    "tfidf_char_ngram_max": 5,
    "text_similarity_threshold": 0.55,
    "geo_distance_meters_threshold": 1200.0, # overlap or close radius
    "time_window_minutes": 90.0,
    "unresolved_text_similarity_threshold": 0.70
}

# Gazeteer location match threshold
LOCATION_CONFIDENCE_THRESHOLD = 0.65

# Silence zone criteria
SILENCE_RISK_THRESHOLD = 0.60
SILENCE_REPORT_RATIO_THRESHOLD = 0.30
HIGH_CONNECTIVITY_BENCHMARK = 0.70

# Environment Flags
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"
