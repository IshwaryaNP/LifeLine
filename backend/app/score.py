from typing import List, Dict, Any, Tuple
from collections import Counter
from app.config import INCIDENT_SCORE_WEIGHTS, NEED_SEVERITY_MAP

def compute_reliability(reports: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """
    Reliability (0 to 1) uses:
    - Location specificity (known lat/lon vs vague)
    - Concrete details (number extracted, vulnerable groups specified)
    - Independent sources count
    - Channel mix (multiple channels increase trust)
    - Penalty for ALL CAPS or exclamation-heavy text
    """
    notes = []
    
    # 1. Location specificity
    resolved_locations = sum(1 for r in reports if r.get("lat") is not None and not r.get("needs_human_check"))
    loc_ratio = resolved_locations / len(reports)
    f_loc = 0.3 + 0.7 * loc_ratio
    if loc_ratio > 0.5:
        notes.append("Specific landmarks corroborated")
    else:
        notes.append("Location requires verification")

    # 2. Concrete details
    has_concrete_people = any(r.get("people_count") and r.get("people_count") > 1 for r in reports)
    has_vuln = any(len(r.get("vulnerable_groups", [])) > 0 for r in reports)
    f_detail = 0.4
    if has_concrete_people:
        f_detail += 0.3
    if has_vuln:
        f_detail += 0.3
    f_detail = min(1.0, f_detail)

    # 3. Independent sources
    senders = set(r.get("sender_hash") for r in reports if r.get("sender_hash"))
    src_cnt = len(senders)
    f_src = min(1.0, 0.4 + 0.15 * src_cnt)

    # 4. Channel mix
    channels = set(r.get("channel") for r in reports if r.get("channel"))
    f_chan = min(1.0, 0.5 + 0.25 * (len(channels) - 1))

    # 5. Penalties: Caps / Exclamation check
    penalty = 0.0
    all_caps_count = 0
    for r in reports:
        t = r.get("text", "")
        if len(t) > 10 and t.isupper():
            all_caps_count += 1
        if t.count("!") >= 4:
            penalty += 0.05
    if all_caps_count / len(reports) > 0.6:
        penalty += 0.15
        notes.append("High emotional phrasing / all-caps detected")

    raw_rel = (0.25 * f_loc + 0.25 * f_detail + 0.25 * f_src + 0.25 * f_chan) - penalty
    reliability = max(0.1, min(1.0, round(raw_rel, 3)))

    return reliability, notes

def score_incident(reports: List[Dict[str, Any]], current_minute: int = 120) -> Dict[str, Any]:
    """
    Computes priority score (0 to 1) and exact factor breakdown:
    - need_severity
    - people
    - vulnerable
    - time_criticality
    - corroboration (capped, small weight so loud areas do not dominate)
    - reliability
    priority = (sum(w_i * factor_i)) * (0.5 + 0.5 * reliability)
    """
    w = INCIDENT_SCORE_WEIGHTS

    # 1. Need severity (mode or highest)
    needs = [r.get("need_type", "other") for r in reports]
    most_common_need = Counter(needs).most_common(1)[0][0]
    need_factor = NEED_SEVERITY_MAP.get(most_common_need, 0.20)

    # 2. People (capped at 50 for max score 1.0)
    people_estimates = [r.get("people_count", 1) for r in reports if r.get("people_count")]
    est_people = max(people_estimates) if people_estimates else 1
    people_factor = min(1.0, est_people / 30.0)

    # 3. Vulnerable groups
    all_vuln = set()
    for r in reports:
        for vg in r.get("vulnerable_groups", []):
            all_vuln.add(vg)
    vuln_factor = min(1.0, len(all_vuln) * 0.35)

    # 4. Time Criticality (recent reports or high urgency cues)
    avg_min = sum(r.get("minute", 0) for r in reports) / len(reports)
    # Recency within simulation window
    time_recency = max(0.0, 1.0 - (current_minute - avg_min) / 180.0)
    has_urgency = any(len(r.get("urgency_cues", [])) > 0 for r in reports)
    time_factor = min(1.0, (0.7 * time_recency + 0.3 * (1.0 if has_urgency else 0.2)))

    # 5. Corroboration (capped at 5 independent sources, small weight 0.10)
    senders = set(r.get("sender_hash") for r in reports if r.get("sender_hash"))
    indep_count = len(senders)
    corroboration_factor = min(1.0, indep_count / 5.0)

    # 6. Reliability
    reliability, rel_notes = compute_reliability(reports)

    # Weighted base sum
    base_sum = (
        w["need_severity"] * need_factor +
        w["people"] * people_factor +
        w["vulnerable"] * vuln_factor +
        w["time_criticality"] * time_factor +
        w["corroboration"] * corroboration_factor
    )

    # Formula: priority = weighted sum * (0.5 + 0.5 * reliability)
    priority_score = base_sum * (0.5 + 0.5 * reliability)

    # Contributions for transparent breakdown
    factor_breakdown = {
        "need_severity": round(w["need_severity"] * need_factor * (0.5 + 0.5 * reliability), 4),
        "people": round(w["people"] * people_factor * (0.5 + 0.5 * reliability), 4),
        "vulnerable": round(w["vulnerable"] * vuln_factor * (0.5 + 0.5 * reliability), 4),
        "time_criticality": round(w["time_criticality"] * time_factor * (0.5 + 0.5 * reliability), 4),
        "corroboration": round(w["corroboration"] * corroboration_factor * (0.5 + 0.5 * reliability), 4),
        "reliability_mult": round(0.5 + 0.5 * reliability, 3),
        "reliability_score": round(reliability, 3),
        "priority_score": round(priority_score, 4)
    }

    # Plain-language reasons list
    reasons = [
        f"{most_common_need.capitalize()} crisis (severity factor: {round(need_factor, 2)})",
        f"Est. {est_people} people affected"
    ]
    if all_vuln:
        reasons.append(f"Vulnerable groups reported: {', '.join(sorted(all_vuln))}")
    reasons.append(f"{indep_count} independent reports across {len(set(r.get('channel') for r in reports))} channels")
    reasons.extend(rel_notes)

    # Location synthesis
    valid_coords = [(r["lat"], r["lon"]) for r in reports if r.get("lat") is not None]
    if valid_coords:
        lat = sum(c[0] for c in valid_coords) / len(valid_coords)
        lon = sum(c[1] for c in valid_coords) / len(valid_coords)
        radius = min([r.get("radius_m", 800.0) for r in reports if r.get("radius_m")])
        needs_human_check = False
    else:
        lat = None
        lon = None
        radius = 2000.0
        needs_human_check = True

    # Zone ID
    zone_ids = [r["zone_id"] for r in reports if r.get("zone_id")]
    zone_id = Counter(zone_ids).most_common(1)[0][0] if zone_ids else None

    channels = list(set(r.get("channel") for r in reports if r.get("channel")))

    return {
        "lat": round(lat, 4) if lat else None,
        "lon": round(lon, 4) if lon else None,
        "radius_m": radius,
        "zone_id": zone_id,
        "need_type": most_common_need,
        "estimated_people": est_people,
        "vulnerable_groups": sorted(list(all_vuln)),
        "independent_sources": indep_count,
        "channels": channels,
        "reliability_score": reliability,
        "priority_score": round(priority_score, 4),
        "factors": factor_breakdown,
        "reasons": reasons,
        "needs_human_check": needs_human_check
    }
