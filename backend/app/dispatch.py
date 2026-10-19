import uuid
import datetime
from typing import Dict, Any, List, Optional

# Inventory of emergency rescue teams, NDRF battalions, helicopters, boats, and medical units
INITIAL_RESOURCES = [
    {
        "id": "RES-NDRF-01",
        "name": "NDRF Battalion 10 (Inflatable Motor Boats)",
        "type": "rescue_boat",
        "type_label": "NDRF Flood Inundation Team",
        "capacity_people": 45,
        "base_station": "Bhimunipat Port Hub",
        "base_coords": [17.53, 82.95],
        "status": "ready", # ready | dispatched | on_scene
        "assigned_incident_id": None,
        "assigned_zone": None,
        "eta_minutes": None
    },
    {
        "id": "RES-NDRF-02",
        "name": "NDRF Deep Water Rescue Platoon",
        "type": "rescue_boat",
        "type_label": "Flood Response Boat Unit",
        "capacity_people": 60,
        "base_station": "Sagarmatha Civil Base",
        "base_coords": [17.55, 83.05],
        "status": "ready",
        "assigned_incident_id": None,
        "assigned_zone": None,
        "eta_minutes": None
    },
    {
        "id": "RES-HELI-01",
        "name": "Indian Coast Guard ALH Helicopter",
        "type": "helicopter",
        "type_label": "Air Recon & Winch Rescue",
        "capacity_people": 14,
        "base_station": "INS Dega Airfield",
        "base_coords": [17.72, 83.22],
        "status": "ready",
        "assigned_incident_id": None,
        "assigned_zone": None,
        "eta_minutes": None
    },
    {
        "id": "RES-MED-01",
        "name": "District Mobile Trauma & ICU Ambulance Team",
        "type": "medical_unit",
        "type_label": "Advanced Mobile Clinic",
        "capacity_people": 25,
        "base_station": "District Civil Hospital",
        "base_coords": [17.51, 82.99],
        "status": "ready",
        "assigned_incident_id": None,
        "assigned_zone": None,
        "eta_minutes": None
    },
    {
        "id": "RES-RELIEF-01",
        "name": "State Disaster Relief Heavy Amphibious Truck",
        "type": "relief_truck",
        "type_label": "Water Purification & Food Transport",
        "capacity_people": 200,
        "base_station": "Central Logistics Warehouse",
        "base_coords": [17.48, 82.90],
        "status": "ready",
        "assigned_incident_id": None,
        "assigned_zone": None,
        "eta_minutes": None
    },
    {
        "id": "RES-HAM-01",
        "name": "Amateur Radio (HAM) & Satellite Scout Team",
        "type": "telecom_scout",
        "type_label": "Blackout Communications Unit",
        "capacity_people": 0,
        "base_station": "Collectorate Emergency Center",
        "base_coords": [17.58, 83.01],
        "status": "ready",
        "assigned_incident_id": None,
        "assigned_zone": None,
        "eta_minutes": None
    }
]

class DispatchManager:
    def __init__(self):
        self.resources = [dict(r) for r in INITIAL_RESOURCES]

    def get_resources(self) -> List[Dict[str, Any]]:
        return self.resources

    def recommend_dispatch(self, incident: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        AI Dispatch Recommendation engine:
        Matches highest-priority incident needs (rescue, medical, blackout)
        against currently available units and calculates estimated transit time.
        """
        recommendations = []
        need_type = incident.get("need_type", "rescue")
        inc_lat = incident.get("lat") or 17.52
        inc_lon = incident.get("lon") or 82.83

        # Match resource type
        preferred_type = "rescue_boat"
        if need_type == "medical":
            preferred_type = "medical_unit"
        elif need_type in ["water", "food"]:
            preferred_type = "relief_truck"
        elif incident.get("factors", {}).get("isolation_risk", 0) > 0.6:
            preferred_type = "telecom_scout"

        for r in self.resources:
            # Estimate transit distance in km
            d_lat = abs(r["base_coords"][0] - inc_lat) * 111.0
            d_lon = abs(r["base_coords"][1] - inc_lon) * 105.0
            dist_km = round((d_lat**2 + d_lon**2)**0.5, 1)

            # Speed assumption: Heli 180 km/h, Boat 30 km/h, Ambulance 45 km/h
            speed = 180 if r["type"] == "helicopter" else (45 if "unit" in r["type"] or "truck" in r["type"] else 30)
            transit_mins = max(8, int((dist_km / speed) * 60) + 5)

            is_match = (r["type"] == preferred_type) or (r["type"] == "helicopter" and incident.get("priority_score", 0) >= 0.8)
            suitability_score = 0.95 if is_match else 0.65

            recommendations.append({
                "resource_id": r["id"],
                "resource_name": r["name"],
                "type": r["type"],
                "type_label": r["type_label"],
                "status": r["status"],
                "distance_km": dist_km,
                "eta_minutes": transit_mins,
                "suitability_score": suitability_score,
                "rationale": f"Fastest response unit stationed {dist_km}km away at {r['base_station']}."
            })

        recommendations.sort(key=lambda x: (x["status"] != "ready", -x["suitability_score"], x["eta_minutes"]))
        return recommendations

    def dispatch_unit(self, resource_id: str, incident_id: str, zone_name: str, eta_minutes: int) -> Dict[str, Any]:
        for r in self.resources:
            if r["id"] == resource_id:
                r["status"] = "dispatched"
                r["assigned_incident_id"] = incident_id
                r["assigned_zone"] = zone_name
                r["eta_minutes"] = eta_minutes
                return {
                    "success": True,
                    "resource": r,
                    "dispatched_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
        return {"success": False, "message": "Resource not found"}

    def recall_unit(self, resource_id: str) -> Dict[str, Any]:
        for r in self.resources:
            if r["id"] == resource_id:
                r["status"] = "ready"
                r["assigned_incident_id"] = None
                r["assigned_zone"] = None
                r["eta_minutes"] = None
                return {"success": True, "resource": r}
        return {"success": False, "message": "Resource not found"}

dispatch_manager = DispatchManager()
