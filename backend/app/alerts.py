import uuid
from typing import List, Dict, Any
from app.config import SILENCE_RISK_THRESHOLD

def generate_preparedness_alerts(
    cyclone_name: str,
    expected_landfall_time: str,
    category: str,
    zones: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Drafts a zone-wise preparedness alert per high-risk zone from templates,
    using that zone's specific risk reasons.
    STATUS: draft. Never auto-sent (Human in the loop).
    """
    drafts = []

    for z in zones:
        # Check if zone is high risk (or silent)
        if z.get("risk_score", 0.0) >= SILENCE_RISK_THRESHOLD:
            factors = z.get("risk_factors", {})
            reasons = []
            
            if factors.get("low_elevation_risk", 0) > 0.6:
                reasons.append(f"Low coastal elevation ({z.get('elevation_m')}m) susceptible to storm surge")
            if factors.get("shelter_distance_risk", 0) > 0.6:
                reasons.append(f"High distance to cyclone shelters ({z.get('dist_to_shelter_km')}km)")
            if factors.get("hospital_distance_risk", 0) > 0.6:
                reasons.append(f"Critical medical distance ({z.get('dist_to_hospital_km')}km)")
            if factors.get("isolation_risk", 0) > 0.7:
                reasons.append(f"Severe mobile network blackout risk (coverage {int(z.get('connectivity', 0)*100)}%)")

            # Compose targeted preparedness draft
            alert_text = (
                f"OFFICIAL PREPAREDNESS WARNING - CYCLONE {cyclone_name.upper()} ({category.upper()}):\n"
                f"Zone: {z['name']} (Risk Level: {round(z['risk_score']*100)}%). Expected Landfall: {expected_landfall_time}.\n"
                f"Action Directives: "
            )
            if factors.get("low_elevation_risk", 0) > 0.6:
                alert_text += "Immediate mandatory evacuation of beachfront & mud house residents to cyclone shelters. "
            if factors.get("isolation_risk", 0) > 0.7:
                alert_text += "Deploy satellite phones / HAM radio teams and VHF handhelds before landfall. "
            alert_text += f"Pre-position drinking water, dry rations, and medical kits at Panchayat centers."

            draft_item = {
                "id": f"ALT-{uuid.uuid4().hex[:8]}",
                "cyclone_name": cyclone_name,
                "expected_landfall_time": expected_landfall_time,
                "category": category,
                "zone_id": z["id"],
                "zone_name": z["name"],
                "message": alert_text,
                "reasons": reasons,
                "status": "draft"
            }
            drafts.append(draft_item)

    return drafts
