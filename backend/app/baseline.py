from typing import List, Dict, Any
from collections import Counter

def compute_baseline_ranking(reports: List[Dict[str, Any]], zones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Baseline ranking:
    - Pure report count per place/zone
    - No duplicate merging
    - No factor explanations/reasons
    - Only includes zones that actually have reports
    """
    zone_by_id = {z["id"]: z["name"] for z in zones}
    
    # Count raw reports per zone (or place text)
    counts = Counter()
    for r in reports:
        zid = r.get("zone_id")
        if zid:
            counts[zid] += 1
        elif r.get("place_text") and r.get("place_text") != "Unknown":
            counts[r["place_text"]] += 1

    ranking = []
    for rank, (target, count) in enumerate(counts.most_common(), start=1):
        name = zone_by_id.get(target, target)
        ranking.append({
            "rank": rank,
            "target": target,
            "target_name": name,
            "raw_report_count": count,
            "method": "raw_volume_count",
            "is_zone": target in zone_by_id
        })

    return ranking
