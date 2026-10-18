from typing import Dict, Any, List, Optional, Tuple
from rapidfuzz import fuzz, process
from app.config import LOCATION_CONFIDENCE_THRESHOLD

def resolve_location(place_text: str, district_zones: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Match place_text to the zone gazetteer using rapidfuzz and alias tables.
    Returns: lat, lon, radius_m, zone_id, zone_name, confidence, needs_human_check.
    NEVER invent a location if match is poor or place_text is vague/missing.
    """
    if not place_text or place_text.lower() in ["unknown", "here", "somewhere", "anywhere", "everywhere"]:
        return {
            "lat": None,
            "lon": None,
            "radius_m": 3000.0,
            "zone_id": None,
            "zone_name": None,
            "confidence": 0.0,
            "needs_human_check": True
        }

    # Flag obvious vague locations immediately
    vague_phrases = ["near the temple", "bazaar area", "main junction", "near government school", "coastal colony", "temple", "school", "bazaar"]
    if any(place_text.lower().strip() == v for v in vague_phrases):
        return {
            "lat": None,
            "lon": None,
            "radius_m": 2500.0,
            "zone_id": None,
            "zone_name": None,
            "confidence": 0.35,
            "needs_human_check": True
        }

    best_match: Optional[Dict[str, Any]] = None
    best_score = 0.0

    # Build gazetteer target list
    for z in district_zones:
        zid = z["id"]
        zname = z["name"]

        # Check zone name match
        score_zone = fuzz.token_sort_ratio(place_text.lower(), zname.lower())
        if score_zone > best_score:
            # Zone polygon centroid roughly
            poly = z.get("polygon", [])
            avg_lat = sum(p[0] for p in poly) / len(poly) if poly else 17.5
            avg_lon = sum(p[1] for p in poly) / len(poly) if poly else 82.8
            best_score = score_zone
            best_match = {
                "lat": round(avg_lat, 4),
                "lon": round(avg_lon, 4),
                "radius_m": 2000.0,
                "zone_id": zid,
                "zone_name": zname,
                "confidence": round(score_zone / 100.0, 2)
            }

        # Check landmark matches
        for lm in z.get("landmarks", []):
            lm_name = lm["name"]
            score_lm = fuzz.token_set_ratio(place_text.lower(), lm_name.lower())
            if score_lm > best_score:
                best_score = score_lm
                best_match = {
                    "lat": lm["lat"],
                    "lon": lm["lon"],
                    "radius_m": 600.0,
                    "zone_id": zid,
                    "zone_name": zname,
                    "confidence": round(score_lm / 100.0, 2)
                }

            # Check aliases
            for alias in lm.get("aliases", []):
                score_alias = fuzz.token_set_ratio(place_text.lower(), alias.lower())
                if score_alias > best_score:
                    best_score = score_alias
                    best_match = {
                        "lat": lm["lat"],
                        "lon": lm["lon"],
                        "radius_m": 800.0,
                        "zone_id": zid,
                        "zone_name": zname,
                        "confidence": round(score_alias / 100.0, 2)
                    }

    # Threshold check
    threshold = LOCATION_CONFIDENCE_THRESHOLD * 100.0
    if best_match and best_score >= threshold:
        best_match["needs_human_check"] = False
        return best_match
    else:
        # Below threshold -> needs human check, no precise pin
        return {
            "lat": None,
            "lon": None,
            "radius_m": 2500.0,
            "zone_id": best_match["zone_id"] if (best_match and best_score >= 45) else None,
            "zone_name": best_match["zone_name"] if (best_match and best_score >= 45) else None,
            "confidence": round(best_score / 100.0, 2) if best_match else 0.0,
            "needs_human_check": True
        }
