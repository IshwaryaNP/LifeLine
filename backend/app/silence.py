import numpy as np
from typing import List, Dict, Any
from app.config import SILENCE_RISK_THRESHOLD, SILENCE_REPORT_RATIO_THRESHOLD, HIGH_CONNECTIVITY_BENCHMARK

def compute_silence_gaps(zones: List[Dict[str, Any]], reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Computes expected reports and silence index for each zone:
    - baseline_rate = median reports per 1000 people among zones with connectivity > 0.7
    - expected_reports = (population / 1000) * baseline_rate
    - silence_index = zone_risk * (1 - min(reports / expected, 1.0))
    - Flag when zone_risk >= 0.60 and (reports / expected) < 0.30
    Message: "No or few reports, but high risk. Possible unreported need. Verify by call or scout."
    """
    # Count reports per zone
    zone_reports_count: Dict[str, int] = {z["id"]: 0 for z in zones}
    for r in reports:
        zid = r.get("zone_id")
        if zid and zid in zone_reports_count:
            zone_reports_count[zid] += 1

    # Find baseline rate from well-connected zones (connectivity > 0.7)
    rates = []
    for z in zones:
        if z.get("connectivity", 0.0) >= HIGH_CONNECTIVITY_BENCHMARK:
            pop = z.get("population", 1)
            reps = zone_reports_count[z["id"]]
            rate_per_k = (reps / (pop / 1000.0))
            rates.append(rate_per_k)

    baseline_rate = float(np.median(rates)) if rates and sum(rates) > 0 else 0.5
    if baseline_rate <= 0.01:
        baseline_rate = 0.2

    silence_alerts = []

    for z in zones:
        zid = z["id"]
        pop = z.get("population", 1)
        z_risk = z.get("risk_score", 0.0)
        reps = zone_reports_count[zid]

        expected = max(1.0, (pop / 1000.0) * baseline_rate)
        ratio = reps / expected
        silence_index = z_risk * (1.0 - min(ratio, 1.0))

        # Flag condition: high risk and severe reporting deficit
        is_flagged = (z_risk >= SILENCE_RISK_THRESHOLD and ratio < SILENCE_REPORT_RATIO_THRESHOLD)

        if is_flagged:
            silence_alerts.append({
                "zone_id": zid,
                "zone_name": z["name"],
                "risk_score": round(z_risk, 3),
                "connectivity": round(z.get("connectivity", 0.0), 2),
                "report_count": reps,
                "expected_reports": round(expected, 1),
                "silence_index": round(silence_index, 3),
                "ratio": round(ratio, 3),
                "message": "No or few reports, but high risk. Possible unreported need. Verify by call or scout."
            })

    # Sort by silence_index descending
    silence_alerts.sort(key=lambda x: x["silence_index"], reverse=True)
    return silence_alerts
