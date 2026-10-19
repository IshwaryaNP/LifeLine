import math
from typing import Dict, Any, List

# Simulated Cyclone Data: Track from offshore Bay of Bengal towards Sundarbari Coastal District
CYCLONE_INFO = {
    "name": "Biparjoy-II",
    "category": "Category 4 Very Severe Cyclonic Storm",
    "central_pressure_hpa": 948,
    "max_sustained_winds_kmh": 185,
    "gusts_kmh": 220,
    "movement_speed_kmh": 16,
    "movement_direction": "North-North-West (NNW)",
    "sea_surface_temp_c": 30.5,
    "storm_surge_m": 4.5,
    "landfall_point_name": "Kalingapatnam Sands (Z01)",
    "landfall_target_coords": [17.52, 82.83],
    "bulletin_number": "IMD-RSMC-CYC-2026-B8",
    "advisory_level": "RED / EMERGENCY EVACUATION",
}

# 10 Track Waypoints progressing from minute 0 to minute 240
# Coordinates: [lat, lon]
TRACK_POINTS = [
    {
        "step": 0,
        "minute": 0,
        "lat": 16.65,
        "lon": 83.95,
        "hours_to_landfall": 12.0,
        "distance_km": 145.0,
        "wind_speed_kmh": 150,
        "category": "Cat 3 Severe",
        "description": "Deep depression intensifying over Bay of Bengal, 145km offshore."
    },
    {
        "step": 1,
        "minute": 24,
        "lat": 16.78,
        "lon": 83.78,
        "hours_to_landfall": 10.5,
        "distance_km": 125.0,
        "wind_speed_kmh": 160,
        "category": "Cat 3 Severe",
        "description": "Outer spiral rainbands begin affecting coastal radar."
    },
    {
        "step": 2,
        "minute": 48,
        "lat": 16.92,
        "lon": 83.60,
        "hours_to_landfall": 9.0,
        "distance_km": 105.0,
        "wind_speed_kmh": 170,
        "category": "Cat 4 Very Severe",
        "description": "Rapid intensification; storm eye forming clearly on satellite imagery."
    },
    {
        "step": 3,
        "minute": 72,
        "lat": 17.06,
        "lon": 83.42,
        "hours_to_landfall": 7.5,
        "distance_km": 85.0,
        "wind_speed_kmh": 175,
        "category": "Cat 4 Very Severe",
        "description": "Telecom towers report intermittent signal degradation along Z01 and Z05."
    },
    {
        "step": 4,
        "minute": 96,
        "lat": 17.18,
        "lon": 83.25,
        "hours_to_landfall": 6.0,
        "distance_km": 65.0,
        "wind_speed_kmh": 180,
        "category": "Cat 4 Very Severe",
        "description": "Gale-force winds (90-110 km/h) reaching coastal fringe. Squalls intensify."
    },
    {
        "step": 5,
        "minute": 120,
        "lat": 17.29,
        "lon": 83.10,
        "hours_to_landfall": 4.5,
        "distance_km": 48.0,
        "wind_speed_kmh": 185,
        "category": "Cat 4 Very Severe",
        "description": "Storm surge warning issued. Wave heights reaching 5-7 meters offshore."
    },
    {
        "step": 6,
        "minute": 144,
        "lat": 17.39,
        "lon": 82.98,
        "hours_to_landfall": 3.0,
        "distance_km": 30.0,
        "wind_speed_kmh": 185,
        "category": "Cat 4 Very Severe",
        "description": "Outer eye wall begins brushing Kalingapatnam coastal shelf."
    },
    {
        "step": 7,
        "minute": 168,
        "lat": 17.46,
        "lon": 82.90,
        "hours_to_landfall": 1.5,
        "distance_km": 15.0,
        "wind_speed_kmh": 185,
        "category": "Cat 4 Very Severe",
        "description": "Extreme tidal surge inundating low-lying coastal sandbars."
    },
    {
        "step": 8,
        "minute": 192,
        "lat": 17.52,
        "lon": 82.83,
        "hours_to_landfall": 0.0,
        "distance_km": 0.0,
        "wind_speed_kmh": 185,
        "category": "Cat 4 LANDFALL",
        "description": "Cyclone eye makes direct landfall at Kalingapatnam Sands (Z01)."
    },
    {
        "step": 9,
        "minute": 216,
        "lat": 17.58,
        "lon": 82.78,
        "hours_to_landfall": -1.5,
        "distance_km": 16.0,
        "wind_speed_kmh": 140,
        "category": "Cat 2 Inland Decay",
        "description": "Post-landfall movement inland; severe flooding and structural devastation."
    },
    {
        "step": 10,
        "minute": 240,
        "lat": 17.65,
        "lon": 82.72,
        "hours_to_landfall": -3.0,
        "distance_km": 32.0,
        "wind_speed_kmh": 105,
        "category": "Tropical Storm",
        "description": "System weakening over northern highlands; continuing intense precipitation."
    }
]

def get_cyclone_status(current_minute: int = 0) -> Dict[str, Any]:
    """
    Returns interpolated cyclone position, wind speed, eye coordinates,
    and alert tiers for coastal zones based on current simulation minute.
    """
    # Clamp minute
    m = max(0, min(240, current_minute))

    # Find bounding steps
    prev_pt = TRACK_POINTS[0]
    next_pt = TRACK_POINTS[-1]

    for i in range(len(TRACK_POINTS) - 1):
        if TRACK_POINTS[i]["minute"] <= m <= TRACK_POINTS[i + 1]["minute"]:
            prev_pt = TRACK_POINTS[i]
            next_pt = TRACK_POINTS[i + 1]
            break

    span = next_pt["minute"] - prev_pt["minute"]
    factor = (m - prev_pt["minute"]) / span if span > 0 else 0.0

    current_lat = prev_pt["lat"] + (next_pt["lat"] - prev_pt["lat"]) * factor
    current_lon = prev_pt["lon"] + (next_pt["lon"] - prev_pt["lon"]) * factor
    current_distance = prev_pt["distance_km"] + (next_pt["distance_km"] - prev_pt["distance_km"]) * factor
    current_wind = int(prev_pt["wind_speed_kmh"] + (next_pt["wind_speed_kmh"] - prev_pt["wind_speed_kmh"]) * factor)
    hours_to_landfall = round(prev_pt["hours_to_landfall"] + (next_pt["hours_to_landfall"] - prev_pt["hours_to_landfall"]) * factor, 1)

    # Danger radius in kilometers: Cat 4 gale radius ~180km, destructive eye-wall ~45km
    eye_wall_radius_km = 42.0
    gale_radius_km = 160.0

    return {
        "cyclone": CYCLONE_INFO,
        "current_position": {
            "lat": round(current_lat, 4),
            "lon": round(current_lon, 4),
            "distance_km": round(max(0, current_distance), 1),
            "wind_speed_kmh": current_wind,
            "hours_to_landfall": hours_to_landfall,
            "status_description": prev_pt["description"],
            "category": prev_pt["category"]
        },
        "radii": {
            "eye_wall_km": eye_wall_radius_km,
            "gale_force_km": gale_radius_km
        },
        "past_track": [
            p for p in TRACK_POINTS if p["minute"] <= m
        ],
        "projected_track": [
            p for p in TRACK_POINTS if p["minute"] >= m
        ],
        "all_waypoints": TRACK_POINTS
    }
