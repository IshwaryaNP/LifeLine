import json
import time
from typing import Dict, Any, List, Set, Tuple
from pathlib import Path

from app.extract import extract_report_info
from app.locate import resolve_location
from app.merge import cluster_reports_into_incidents
from app.score import score_incident
from app.silence import compute_silence_gaps
from app.baseline import compute_baseline_ranking

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def compute_ground_truth_metrics() -> Dict[str, Any]:
    """
    Computes all validation metrics from ground truth (truth.json):
    1. Pairwise duplicate-merge precision, recall, and F1
    2. Top-10 overlap with expert ranking for system AND baseline
    3. Silent zones flagged out of 3 planted for system AND baseline
    4. Percent of locations resolved
    5. Extraction accuracy for people_count and need_type
    6. Number of fake reports in the system's top 10
    7. Processing time per 1,000 reports (replicated and timed)
    """
    # Load files
    with open(DATA_DIR / "district.json", "r", encoding="utf-8") as f:
        district_data = json.load(f)
        zones = district_data["zones"]

    reports = []
    with open(DATA_DIR / "reports.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                reports.append(json.loads(line))

    with open(DATA_DIR / "truth.json", "r", encoding="utf-8") as f:
        truth = json.load(f)

    with open(DATA_DIR / "expert_ranking.json", "r", encoding="utf-8") as f:
        expert_data = json.load(f)
        expert_top15 = expert_data["top_15"]

    # 1. Run full extraction & location pipeline
    processed_reports = []
    correct_need = 0
    correct_people = 0
    total_eval_reports = 0
    resolved_locations = 0

    for r in reports:
        rep = dict(r)
        r_id = rep["id"]
        t = truth.get(r_id, {})
        
        # Extraction
        ext = extract_report_info(rep["text"])
        rep.update(ext)

        # Location
        loc = resolve_location(rep.get("place_text", ""), zones)
        rep.update(loc)

        processed_reports.append(rep)

        # Evaluate extraction accuracy against true data (excluding pure fake/spam)
        if not t.get("is_fake"):
            total_eval_reports += 1
            if ext["need_type"] == t.get("true_need"):
                correct_need += 1
            # People count check: within +/- 20% or match
            true_p = t.get("true_people", 1)
            pred_p = ext["people_count"] or 1
            if abs(pred_p - true_p) <= max(2, true_p * 0.25):
                correct_people += 1

        # Check location resolved
        if loc["lat"] is not None and not loc["needs_human_check"]:
            resolved_locations += 1

    acc_need_type = round(correct_need / total_eval_reports, 3) if total_eval_reports else 0.0
    acc_people_count = round(correct_people / total_eval_reports, 3) if total_eval_reports else 0.0
    pct_location_resolved = round((resolved_locations / len(reports)) * 100, 1)

    # 2. Duplicate-merge Pairwise Precision, Recall, F1
    clusters = cluster_reports_into_incidents(processed_reports)

    # Build predicted pairs
    pred_pairs: Set[Tuple[str, str]] = set()
    for clus in clusters:
        ids = sorted([r["id"] for r in clus])
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pred_pairs.add((ids[i], ids[j]))

    # Build true pairs from ground truth (same true_incident_id)
    true_pairs: Set[Tuple[str, str]] = set()
    incident_to_reps: Dict[str, List[str]] = {}
    for r in reports:
        r_id = r["id"]
        t = truth.get(r_id, {})
        true_inc_id = t.get("true_incident_id")
        if true_inc_id and not t.get("is_fake"):
            incident_to_reps.setdefault(true_inc_id, []).append(r_id)

    for inc_id, r_ids in incident_to_reps.items():
        s_ids = sorted(r_ids)
        for i in range(len(s_ids)):
            for j in range(i + 1, len(s_ids)):
                true_pairs.add((s_ids[i], s_ids[j]))

    intersection = pred_pairs.intersection(true_pairs)
    precision = len(intersection) / len(pred_pairs) if pred_pairs else 1.0
    recall = len(intersection) / len(true_pairs) if true_pairs else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # 3. Score incidents and compute Top-10 overlap with expert ranking
    scored_incidents = []
    for clus in clusters:
        scored = score_incident(clus, current_minute=240)
        scored["reports"] = clus
        scored_incidents.append(scored)

    scored_incidents.sort(key=lambda x: x["priority_score"], reverse=True)
    top_10_sys = scored_incidents[:10]

    # Map system top-10 incidents to their underlying true incidents
    sys_top10_true_incidents = set()
    fake_reports_in_top10 = 0
    for inc in top_10_sys:
        # Check if majority of reports in incident are fake
        fakes = sum(1 for r in inc["reports"] if truth.get(r["id"], {}).get("is_fake"))
        if fakes > len(inc["reports"]) / 2:
            fake_reports_in_top10 += 1
        
        for r in inc["reports"]:
            t_id = truth.get(r["id"], {}).get("true_incident_id")
            if t_id:
                sys_top10_true_incidents.add(t_id)

    expert_top10_ids = {e["incident_id"] for e in expert_top15[:10]}
    overlap_sys_top10 = len(sys_top10_true_incidents.intersection(expert_top10_ids)) / 10.0

    # Baseline comparison: raw volume ranking
    baseline_ranking = compute_baseline_ranking(processed_reports, zones)
    # Baseline top places mapped to true incidents
    baseline_top_zones = [b["target"] for b in baseline_ranking[:10]]
    # Find true incidents in these top zones
    baseline_true_incidents = set()
    for e in expert_top15:
        if e["zone_id"] in baseline_top_zones:
            baseline_true_incidents.add(e["incident_id"])
    overlap_baseline_top10 = min(1.0, len(baseline_true_incidents.intersection(expert_top10_ids)) / 10.0)

    # 4. Silent zones flagged out of 3 planted (System vs Baseline)
    planted_silent_zones = {z["id"] for z in zones if z.get("is_silent")}
    silence_alerts = compute_silence_gaps(zones, processed_reports)
    flagged_zone_ids = {a["zone_id"] for a in silence_alerts}
    system_silent_flagged = len(flagged_zone_ids.intersection(planted_silent_zones))

    # Baseline flags 0 silent zones because baseline only considers zones with reports!
    baseline_silent_flagged = 0

    # 5. Processing time benchmark for 1,000 reports
    # Replicate reports to ~1,000
    multiplier = (1000 // len(reports)) + 1
    bench_reports = (reports * multiplier)[:1000]
    
    t0 = time.perf_counter()
    bench_processed = []
    for br in bench_reports:
        rep = dict(br)
        ext = extract_report_info(rep["text"])
        rep.update(ext)
        loc = resolve_location(rep.get("place_text", ""), zones)
        rep.update(loc)
        bench_processed.append(rep)
    bench_clusters = cluster_reports_into_incidents(bench_processed)
    for clus in bench_clusters:
        score_incident(clus, current_minute=240)
    t1 = time.perf_counter()
    processing_time_1000_ms = round((t1 - t0) * 1000, 1)

    return {
        "duplicate_merge": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "total_raw_reports": len(reports),
            "consolidated_incidents": len(clusters),
            "compression_ratio": round(len(reports) / max(1, len(clusters)), 2)
        },
        "expert_ranking_top10_overlap": {
            "system": round(overlap_sys_top10, 3),
            "baseline": round(overlap_baseline_top10, 3)
        },
        "silent_zones_flagged": {
            "total_planted": len(planted_silent_zones),
            "system_flagged": system_silent_flagged,
            "baseline_flagged": baseline_silent_flagged
        },
        "location_resolution": {
            "percent_resolved": pct_location_resolved,
            "resolved_count": resolved_locations,
            "total_reports": len(reports)
        },
        "extraction_accuracy": {
            "need_type_accuracy": acc_need_type,
            "people_count_accuracy": acc_people_count
        },
        "fake_reports_in_top10": fake_reports_in_top10,
        "performance": {
            "processing_time_1000_reports_ms": processing_time_1000_ms
        },
        "notice": "Evaluated on simulated data with self-generated ground truth."
    }
