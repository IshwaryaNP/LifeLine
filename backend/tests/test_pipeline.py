import pytest
import json
from pathlib import Path
from app.extract import extract_report_info
from app.locate import resolve_location
from app.merge import cluster_reports_into_incidents
from app.score import score_incident
from app.silence import compute_silence_gaps
from app.metrics import compute_ground_truth_metrics
from app.config import RANDOM_SEED

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 1. Extraction tests on 15+ handwritten messages
HANDWRITTEN_TEST_CASES = [
    ("Water level rising rapidly inside homes near Light Point! 12 people trapped on tin rooftop including children. Send boat ASAP!!", "rescue", 12, ["children"], ["asap", "rising"]),
    ("Bachao! Paani bohot tez badh raha hai at Fish Landing Jetty. We are five people with elderly, please send rescue team now!", "rescue", 5, ["elderly"], ["now"]),
    ("Emergency: building collapsed near Central Wharf, 8 victims trapped inside debris urgently need ambulance", "medical", 8, [], ["urgent"]),
    ("Severe injuries after wall collapse near Civil Hospital Gate. 15 patients bleeding, need urgent doctor!", "medical", 15, [], ["urgent"]),
    ("Cyclone shelter overcrowded at Mandal High School. 30 persons standing in rain with pregnant women and kids.", "shelter", 30, ["children", "pregnant"], []),
    ("Contaminated water in borewells near Shiva Temple Pond. twenty villagers having diarrhea and thirst.", "water", 20, [], []),
    ("No rations or milk since morning near Grain Market Yard. 45 people starving including small kids.", "food", 45, ["children"], []),
    ("Urgent rescue needed near Mangrove Watchtower. Creek Bund breach! 10 individuals stranded.", "rescue", 10, [], ["urgent"]),
    ("Medical crisis at Salt Pan Colony: 4 bedridden disabled patients need emergency ambulance.", "medical", 4, ["disabled"], ["emergency"]),
    ("Drinking water exhausted near Toll Plaza 4. 25 residents need clean drinking water tanker fast.", "water", 25, [], ["fast"]),
    ("Roofs blown off near Panchayat Bhavan. 18 families homeless in rain, need tarpaulin.", "shelter", 18, [], []),
    ("High tension electric wire snapped near Hill Temple Steps. 3 persons injured badly.", "medical", 3, [], []),
    ("Flooding reached 5 feet near Railway Goods Shed. 14 people stuck on second floor.", "rescue", 14, [], []),
    ("No dry food or potable water at Substation Grid. 50 workers trapped inside.", "food", 50, [], ["trapped"]),
    ("Seven elderly patients stranded at Red Cross Clinic needing immediate oxygen cylinders.", "medical", 7, ["elderly"], ["immediate"]),
    ("Two children and pregnant mother stuck in flash flood near light point post help fast!", "rescue", 2, ["children", "pregnant"], ["fast"])
]

@pytest.mark.parametrize("text,expected_need,expected_people,expected_vuln,urgency_keywords", HANDWRITTEN_TEST_CASES)
def test_extraction_rules(text, expected_need, expected_people, expected_vuln, urgency_keywords):
    res = extract_report_info(text)
    assert res["need_type"] == expected_need
    if expected_people:
        assert res["people_count"] == expected_people
    for v in expected_vuln:
        assert v in res["vulnerable_groups"]

def test_location_vague_needs_human_check():
    with open(DATA_DIR / "district.json", "r", encoding="utf-8") as f:
        zones = json.load(f)["zones"]

    # Vague places must not have precise lat/lon and must flag needs_human_check
    vague_inputs = ["near the temple", "bazaar area", "main junction", "here", "somewhere"]
    for v in vague_inputs:
        loc = resolve_location(v, zones)
        assert loc["needs_human_check"] is True
        assert loc["lat"] is None
        assert loc["lon"] is None

    # Specific alias match should resolve correctly without human check
    loc_specific = resolve_location("batti ghar", zones) # alias for Light Point in Z01
    assert loc_specific["needs_human_check"] is False
    assert loc_specific["zone_id"] == "Z01"
    assert loc_specific["lat"] is not None

def test_merge_known_duplicates():
    # 3 duplicate reports describing the same rooftop rescue near Light Point in Z01
    reps = [
        {"id": "REP-T01", "minute": 20, "channel": "sms", "sender_hash": "u1", "text": "Water rising! 10 people trapped on rooftop near Light Point!", "need_type": "rescue", "people_count": 10, "lat": 17.52, "lon": 82.83, "radius_m": 600.0, "zone_id": "Z01"},
        {"id": "REP-T02", "minute": 35, "channel": "call", "sender_hash": "u2", "text": "Flood water inside homes near batti ghar, 10 people trapped on roof please rescue", "need_type": "rescue", "people_count": 10, "lat": 17.52, "lon": 82.83, "radius_m": 600.0, "zone_id": "Z01"},
        {"id": "REP-T03", "minute": 110, "channel": "social", "sender_hash": "u3", "text": "Different issue entirely: Need dry food at Substation Grid, 50 workers starving", "need_type": "food", "people_count": 50, "lat": 17.84, "lon": 83.12, "radius_m": 600.0, "zone_id": "Z12"}
    ]
    clusters = cluster_reports_into_incidents(reps)
    # REP-T01 and REP-T02 must be clustered together, REP-T03 separate
    assert len(clusters) == 2
    clus_sizes = sorted([len(c) for c in clusters])
    assert clus_sizes == [1, 2]

def test_score_contributions():
    # Test that priority score equals formula and factor contributions
    clus = [
        {"id": "REP-S01", "minute": 30, "channel": "sms", "sender_hash": "s1", "text": "Trapped on roof", "need_type": "rescue", "people_count": 12, "vulnerable_groups": ["children"], "urgency_cues": ["asap"], "lat": 17.52, "lon": 82.83, "radius_m": 600.0, "zone_id": "Z01"},
        {"id": "REP-S02", "minute": 40, "channel": "call", "sender_hash": "s2", "text": "Flood rising", "need_type": "rescue", "people_count": 12, "vulnerable_groups": ["children"], "urgency_cues": ["rising"], "lat": 17.52, "lon": 82.83, "radius_m": 600.0, "zone_id": "Z01"}
    ]
    scored = score_incident(clus, current_minute=120)
    assert scored["priority_score"] > 0
    assert "need_severity" in scored["factors"]
    assert "people" in scored["factors"]
    assert "reliability_score" in scored["factors"]
    assert len(scored["reasons"]) >= 3
    # Check that priority score matches weighted sum * reliability mult
    f = scored["factors"]
    sum_factors = f["need_severity"] + f["people"] + f["vulnerable"] + f["time_criticality"] + f["corroboration"]
    assert abs(scored["priority_score"] - sum_factors) < 0.001

def test_silence_detection():
    with open(DATA_DIR / "district.json", "r", encoding="utf-8") as f:
        zones = json.load(f)["zones"]
    # Provide synthetic reports where well-connected zones have many reports and Z01, Z04, Z07 have <= 1
    mock_reports = []
    # 20 reports in Z02, Z03, Z05
    for i in range(30):
        mock_reports.append({"id": f"R-{i}", "zone_id": "Z02", "minute": 10})
        mock_reports.append({"id": f"R2-{i}", "zone_id": "Z03", "minute": 10})
    # Only 1 report in Z01, 0 in Z04, 1 in Z07
    mock_reports.append({"id": "R-Z01", "zone_id": "Z01", "minute": 10})
    mock_reports.append({"id": "R-Z07", "zone_id": "Z07", "minute": 10})

    alerts = compute_silence_gaps(zones, mock_reports)
    flagged_ids = {a["zone_id"] for a in alerts}
    assert "Z01" in flagged_ids
    assert "Z04" in flagged_ids
    assert "Z07" in flagged_ids

def test_metrics_reproducibility():
    assert RANDOM_SEED == 42
    m1 = compute_ground_truth_metrics()
    m2 = compute_ground_truth_metrics()
    assert m1["duplicate_merge"]["f1"] == m2["duplicate_merge"]["f1"]
    assert m1["silent_zones_flagged"]["system_flagged"] == 3
    assert m1["silent_zones_flagged"]["baseline_flagged"] == 0
