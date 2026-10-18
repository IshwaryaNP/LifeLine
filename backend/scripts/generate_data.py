import json
import random
import hashlib
from typing import List, Dict, Any
from pathlib import Path

# Deterministic random seed
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 1. Generate 12 Fictional Coastal District Zones (Sundarbari Coastal District)
# 4 rows x 3 columns roughly centered at lat: 17.5 to 17.9, lon: 82.8 to 83.4
BASE_LAT = 17.50
BASE_LON = 82.80

ZONES_META = [
    # Silent Zone 1: Z01 (Fishing coast, barrier island, severed lines)
    {"id": "Z01", "name": "Kalingapatnam Sands", "pop": 18000, "area": 32.0, "elev": 1.8, "shelter": 9.5, "hosp": 16.0, "conn": 0.15, "silent": True,
     "landmarks": [("Light Point", 17.52, 82.83, ["old lighthouse", "light point post", "batti ghar"]), ("Fish Landing Jetty", 17.54, 82.85, ["jetty ghat", "boat dock", "machli landing"])]},
    
    # Well-connected coastal town
    {"id": "Z02", "name": "Bhimunipat Port", "pop": 65000, "area": 22.0, "elev": 4.5, "shelter": 2.1, "hosp": 3.0, "conn": 0.95, "silent": False,
     "landmarks": [("Central Wharf", 17.53, 82.95, ["port gate", "wharf road", "godown 3"]), ("Clock Tower Chowk", 17.55, 82.98, ["ghanta ghar", "clock tower", "bazaar square"])]},

    # Well-connected administrative center
    {"id": "Z03", "name": "Sagarmatha Town", "pop": 85000, "area": 28.0, "elev": 8.0, "shelter": 1.5, "hosp": 1.2, "conn": 0.98, "silent": False,
     "landmarks": [("Civil Hospital Gate", 17.54, 83.12, ["district hospital", "civil hospital", "red cross clinic"]), ("Dak Bungalow", 17.56, 83.15, ["guest house", "bungalow junction"])]},

    # Silent Zone 2: Z04 (Estuary mangrove inlet, severely vulnerable)
    {"id": "Z04", "name": "Dhamra Creek Estuary", "pop": 24000, "area": 40.0, "elev": 1.2, "shelter": 11.0, "hosp": 18.5, "conn": 0.20, "silent": True,
     "landmarks": [("Mangrove Watchtower", 17.62, 82.82, ["forest post", "mangrove tower", "watch post"]), ("Creek Bund", 17.65, 82.86, ["creek embankment", "bund road", "nadi bandh"])]},

    # Mid-urban sector
    {"id": "Z05", "name": "Devunalt Ward", "pop": 52000, "area": 25.0, "elev": 5.2, "shelter": 3.0, "hosp": 4.5, "conn": 0.88, "silent": False,
     "landmarks": [("Mandal High School", 17.63, 82.94, ["high school shelter", "govt school ground", "vidyalaya"]), ("Shiva Temple Pond", 17.66, 82.97, ["mandir talaab", "temple pond", "shivalayam"])]},

    # Commercial suburb
    {"id": "Z06", "name": "Rushi Valley Junction", "pop": 48000, "area": 30.0, "elev": 12.0, "shelter": 2.8, "hosp": 5.0, "conn": 0.90, "silent": False,
     "landmarks": [("Overbridge Intersection", 17.64, 83.10, ["flyover junction", "railway bridge", "bypass"]), ("Grain Market Yard", 17.67, 83.14, ["apmc yard", "mandi", "grain depot"])]},

    # Silent Zone 3: Z07 (Remote tidal creek peninsula, flood plain)
    {"id": "Z07", "name": "Baruva Lowlands", "pop": 21000, "area": 45.0, "elev": 1.5, "shelter": 10.2, "hosp": 19.0, "conn": 0.18, "silent": True,
     "landmarks": [("Salt Pan Colony", 17.72, 82.81, ["salt pans", "namak karkhana", "salt works"]), ("Old Tidal Sluice Gate", 17.75, 82.85, ["sluice gate", "canal lock", "naala phatak"])]},

    # Inland rural transit
    {"id": "Z08", "name": "Penta Highway Corridor", "pop": 35000, "area": 35.0, "elev": 15.0, "shelter": 4.0, "hosp": 6.5, "conn": 0.85, "silent": False,
     "landmarks": [("Toll Plaza 4", 17.73, 82.95, ["highway toll gate", "toll booth", "nh plaza"]), ("Petrol Bunk Square", 17.76, 82.98, ["iocl pump", "petrol bunk", "highway dhaba"])]},

    # Agricultural belt
    {"id": "Z09", "name": "Kasimkota Farmlands", "pop": 29000, "area": 38.0, "elev": 18.0, "shelter": 4.5, "hosp": 8.0, "conn": 0.75, "silent": False,
     "landmarks": [("Panchayat Bhavan", 17.74, 83.11, ["panchayat office", "gram sabha hall"]), ("Canal Bridge Siphon", 17.77, 83.16, ["canal pulla", "water siphon", "canal bridge"])]},

    # Inland upland ridge
    {"id": "Z10", "name": "Simhachalam Foothills", "pop": 32000, "area": 42.0, "elev": 35.0, "shelter": 5.0, "hosp": 9.0, "conn": 0.82, "silent": False,
     "landmarks": [("Hill Temple Steps", 17.82, 82.84, ["temple stairs", "ghat road curve"]), ("Forest Check Post", 17.85, 82.87, ["forest barrier", "jungle naka"])]},

    # Sub-urban residential
    {"id": "Z11", "name": "Anakapalle West", "pop": 41000, "area": 29.0, "elev": 22.0, "shelter": 3.5, "hosp": 7.0, "conn": 0.84, "silent": False,
     "landmarks": [("Railway Goods Shed", 17.83, 82.96, ["railway godown", "station goods yard"]), ("Community Hall", 17.86, 82.99, ["kalyana mandapam", "shadi mahal", "hall"])]},

    # High ground interior
    {"id": "Z12", "name": "Gajuwaka Industrial Belt", "pop": 58000, "area": 26.0, "elev": 28.0, "shelter": 3.0, "hosp": 5.2, "conn": 0.92, "silent": False,
     "landmarks": [("Substation Grid", 17.84, 83.12, ["power substation", "bijli office"]), ("Labour Colony Gate", 17.87, 83.15, ["colony gate", "worker quarters", "mill road"])]}
]

def generate_district_data() -> Dict[str, Any]:
    # Calculate zone risk scores and polygon bounds
    zones = []
    
    # Find min/max for normalization across 12 zones
    elevs = [z["elev"] for z in ZONES_META]
    densities = [z["pop"] / z["area"] for z in ZONES_META]
    shelters = [z["shelter"] for z in ZONES_META]
    hosps = [z["hosp"] for z in ZONES_META]
    conns = [z["conn"] for z in ZONES_META]

    min_elev, max_elev = min(elevs), max(elevs)
    min_den, max_den = min(densities), max(densities)
    min_sh, max_sh = min(shelters), max(shelters)
    min_hosp, max_hosp = min(hosps), max(hosps)
    min_conn, max_conn = min(conns), max(conns)

    # Weights from config (starting values, not validated)
    w = {
        "elevation": 0.25,
        "population_density": 0.25,
        "dist_to_shelter": 0.20,
        "dist_to_hospital": 0.15,
        "connectivity": 0.15
    }

    step_lat = 0.09
    step_lon = 0.11

    idx = 0
    for row in range(4):
        for col in range(3):
            meta = ZONES_META[idx]
            z_lat = BASE_LAT + row * step_lat
            z_lon = BASE_LON + col * step_lon
            
            # Simple polygon box
            poly = [
                [round(z_lat, 4), round(z_lon, 4)],
                [round(z_lat, 4), round(z_lon + step_lon, 4)],
                [round(z_lat + step_lat, 4), round(z_lon + step_lon, 4)],
                [round(z_lat + step_lat, 4), round(z_lon, 4)],
                [round(z_lat, 4), round(z_lon, 4)]
            ]

            # Factors (0 to 1 where 1 is maximum risk)
            # low elevation -> higher risk
            f_elev = (max_elev - meta["elev"]) / (max_elev - min_elev)
            # high density -> higher risk
            den = meta["pop"] / meta["area"]
            f_den = (den - min_den) / (max_den - min_den)
            # far from shelter -> higher risk
            f_sh = (meta["shelter"] - min_sh) / (max_sh - min_sh)
            # far from hospital -> higher risk
            f_hosp = (meta["hosp"] - min_hosp) / (max_hosp - min_hosp)
            # low connectivity -> higher risk
            f_conn = (max_conn - meta["conn"]) / (max_conn - min_conn)

            risk_score = (
                w["elevation"] * f_elev +
                w["population_density"] * f_den +
                w["dist_to_shelter"] * f_sh +
                w["dist_to_hospital"] * f_hosp +
                w["connectivity"] * f_conn
            )

            landmarks = []
            for name, lat, lon, aliases in meta["landmarks"]:
                landmarks.append({
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "aliases": aliases
                })

            zone_dict = {
                "id": meta["id"],
                "name": meta["name"],
                "population": meta["pop"],
                "area_km2": meta["area"],
                "elevation_m": meta["elev"],
                "dist_to_shelter_km": meta["shelter"],
                "dist_to_hospital_km": meta["hosp"],
                "connectivity": meta["conn"],
                "landmarks": landmarks,
                "polygon": poly,
                "risk_score": round(risk_score, 4),
                "risk_factors": {
                    "low_elevation_risk": round(f_elev, 3),
                    "density_risk": round(f_den, 3),
                    "shelter_distance_risk": round(f_sh, 3),
                    "hospital_distance_risk": round(f_hosp, 3),
                    "isolation_risk": round(f_conn, 3)
                },
                "is_silent": meta["silent"]
            }
            zones.append(zone_dict)
            idx += 1

    return {"district_name": "Sundarbari Coastal District", "zones": zones}

# Ground truth incident templates
NEEDS = ["rescue", "medical", "food", "water", "shelter"]
VULN_POOL = [["children"], ["elderly"], ["pregnant"], ["disabled"], ["children", "elderly"], ["elderly", "disabled"], []]

TEXT_TEMPLATES = {
    "rescue": [
        "Water level rising rapidly inside homes near {place}! {count} people trapped on tin rooftop including {vuln}. Send boat ASAP!!",
        "EMERGENCY: {place} completely flooded up to 7 feet. {count} persons stuck in dark, water level still rising!",
        "Bachao! Paani bohot tez badh raha hai at {place}. We are {count} people with {vuln}, please send rescue team now!",
        "Urgent rescue needed at {place}! Building collapsing due to tidal storm surge, {count} individuals stranded on upper floor."
    ],
    "medical": [
        "Severe injuries after wall collapse near {place}. {count} patients bleeding, need urgent ambulance or medical relief!",
        "Medical crisis at {place}: {count} people sick, oxygen and saline urgently required for {vuln}. Urgent doctor needed!",
        "Doctor needed immediately near {place}. {count} persons hurt badly by falling electric pole, elderly condition critical.",
        "Emergency ambulance request: {place} has {count} injured victims including {vuln} trapped in mudslide."
    ],
    "food": [
        "Drinking supplies exhausted and no rations left near {place}. {count} people starving for 24 hours with small kids.",
        "Food packet airdrop required at {place}! Entire colony surrounded by flood water, {count} hungry people crying.",
        "No ration or milk since cyclone landfall near {place}. {count} stranded residents including {vuln} in desperate need of dry food."
    ],
    "water": [
        "Contaminated saline water in all borewells at {place}. {count} villagers having no clean drinking water since morning.",
        "Need clean drinking water tanker at {place}. {count} people falling sick with diarrhea, help fast please!"
    ],
    "shelter": [
        "Roofs blown off completely by cyclone gusts at {place}. {count} families homeless in heavy rain, need emergency tarpaulin.",
        "Cyclone shelter at {place} overcrowded and door damaged. {count} persons standing outside in storm with {vuln}."
    ]
}

NOISE_VARIATIONS = [
    lambda s: s.upper(),
    lambda s: s.lower(),
    lambda s: s + " 🙏🚨 PLS HELP ASAP",
    lambda s: s.replace("urgent", "urgnt").replace("people", "ppl").replace("please", "pls"),
    lambda s: s.replace("flooded", "floded").replace("water", "wtr"),
    lambda s: s + " !! Call disconnected network going down.."
]

def generate_simulation_dataset(district_data: Dict[str, Any]):
    zones = district_data["zones"]
    zone_by_id = {z["id"]: z for z in zones}

    # Generate ~45 true incidents
    true_incidents = []
    inc_counter = 1

    # Ensure the 3 silent zones (Z01, Z04, Z07) get high-severity true incidents
    for z in zones:
        if z["is_silent"]:
            # 2 severe incidents each in silent zones
            for _ in range(2):
                true_incidents.append({
                    "true_incident_id": f"INC-{inc_counter:03d}",
                    "true_zone": z["id"],
                    "true_need": random.choice(["rescue", "medical"]),
                    "true_severity": random.choice([4, 5]),
                    "true_people": random.randint(12, 35),
                    "true_vulnerable": random.choice([["children", "elderly"], ["pregnant", "children"], ["disabled"]]),
                    "landmarks": z["landmarks"],
                    "is_silent_zone": True
                })
                inc_counter += 1
        else:
            # 4-5 incidents in regular zones
            num_inc = random.randint(4, 5)
            for _ in range(num_inc):
                true_incidents.append({
                    "true_incident_id": f"INC-{inc_counter:03d}",
                    "true_zone": z["id"],
                    "true_need": random.choice(NEEDS),
                    "true_severity": random.randint(1, 5),
                    "true_people": random.randint(3, 25),
                    "true_vulnerable": random.choice(VULN_POOL),
                    "landmarks": z["landmarks"],
                    "is_silent_zone": False
                })
                inc_counter += 1

    # Exactly 45 incidents
    true_incidents = true_incidents[:45]

    # Generate Reports:
    # Well-connected zones produce MORE reports per capita (volume bias)
    # Silent zones produce only 0 to 2 reports TOTAL across the entire zone
    reports = []
    truth_records = {}
    report_counter = 1

    channels = ["sms", "call", "social", "volunteer"]
    channel_weights = [0.4, 0.25, 0.25, 0.10]

    # Track report count per silent zone to enforce 0-2 cap
    silent_zone_report_count = {"Z01": 0, "Z04": 0, "Z07": 0}

    for inc in true_incidents:
        zid = inc["true_zone"]
        is_silent = inc["is_silent_zone"]

        if is_silent:
            # Silent zone gets 0 or 1 report per incident, max 2 total for the zone
            if silent_zone_report_count[zid] >= 2:
                num_reps = 0
            else:
                num_reps = random.choice([0, 1])
                silent_zone_report_count[zid] += num_reps
        else:
            # Heavy-tailed duplicate distribution: 1 to 8 reports
            # Higher connectivity -> more reports
            conn = zone_by_id[zid]["connectivity"]
            weights = [5, 15, 25, 25, 15, 10, 5, 5] # heavy tailed 1..8
            num_reps = random.choices(range(1, 9), weights=weights)[0]
            if conn > 0.85:
                num_reps += random.randint(1, 3)

        # Base landmark for this incident
        chosen_lm = random.choice(inc["landmarks"])
        base_minute = random.randint(5, 180)

        for rep_idx in range(num_reps):
            rep_id = f"REP-{report_counter:04d}"
            rep_min = min(240, max(0, base_minute + random.randint(-15, 40)))
            channel = random.choices(channels, weights=channel_weights)[0]
            
            # Sender hash: some share sender (same phone), most independent
            if rep_idx > 0 and random.random() < 0.25:
                sender_hash = reports[-1]["sender_hash"]
            else:
                sender_hash = hashlib.sha256(f"user-{zid}-{rep_id}-{random.random()}".encode()).hexdigest()[:12]

            # Text synthesis
            need = inc["true_need"]
            template = random.choice(TEXT_TEMPLATES[need])
            
            # Place variation:
            # 10% no location
            # 15% vague landmark ("near the temple", "bazaar square", "near school")
            # 75% specific landmark name or alias
            loc_roll = random.random()
            if loc_roll < 0.10:
                place_str = "here"
            elif loc_roll < 0.25:
                vague_places = ["near the temple", "bazaar area", "main junction", "near government school", "coastal colony"]
                place_str = random.choice(vague_places)
            else:
                if random.random() < 0.5 and chosen_lm["aliases"]:
                    place_str = random.choice(chosen_lm["aliases"])
                else:
                    place_str = chosen_lm["name"]

            # Vulnerable string
            vuln_str = ", ".join(inc["true_vulnerable"]) if inc["true_vulnerable"] else "families"
            people_cnt = inc["true_people"]
            if random.random() < 0.2:
                # Number to word
                num_words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", 12: "twelve", 15: "fifteen", 20: "twenty"}
                count_str = num_words.get(people_cnt, str(people_cnt))
            else:
                count_str = str(people_cnt)

            text = template.format(place=place_str, count=count_str, vuln=vuln_str)

            # Apply realistic noise
            if random.random() < 0.35:
                noise_fn = random.choice(NOISE_VARIATIONS)
                text = noise_fn(text)

            rep_obj = {
                "id": rep_id,
                "minute": rep_min,
                "channel": channel,
                "sender_hash": sender_hash,
                "text": text
            }
            reports.append(rep_obj)

            truth_records[rep_id] = {
                "true_incident_id": inc["true_incident_id"],
                "is_fake": False,
                "true_zone": zid,
                "true_people": inc["true_people"],
                "true_need": inc["true_need"],
                "true_severity": inc["true_severity"],
                "true_vulnerable": inc["true_vulnerable"]
            }
            report_counter += 1

    # Add ~5% fake or empty reports (spam/hoax/exaggeration)
    num_fake = int(len(reports) * 0.05) + 3
    fake_texts = [
        "EVERYTHING DESTROYED IN ENTIRE STATE!!! NO ONE SURVIVED HELP AHHH!!!!",
        "Free recharge for storm victims visit http://scam-cyclone.in now!!!",
        "Alien spaceship spotted during cyclone over the ocean clouds!!",
        "Cyclone has completely destroyed every building everywhere disaster apocalypse!",
        "just testing the sms system 123456 hello test",
        "fake alert forwarded from whatsapp group please share to 10 groups!!!"
    ]

    for _ in range(num_fake):
        rep_id = f"REP-{report_counter:04d}"
        rep_min = random.randint(10, 230)
        channel = random.choice(channels)
        sender_hash = hashlib.sha256(f"spammer-{random.random()}".encode()).hexdigest()[:12]
        text = random.choice(fake_texts)
        if random.random() < 0.5:
            text = text.upper()

        reports.append({
            "id": rep_id,
            "minute": rep_min,
            "channel": channel,
            "sender_hash": sender_hash,
            "text": text
        })

        truth_records[rep_id] = {
            "true_incident_id": None,
            "is_fake": True,
            "true_zone": None,
            "true_people": 0,
            "true_need": "other",
            "true_severity": 0,
            "true_vulnerable": []
        }
        report_counter += 1

    # Sort reports by minute (simulation order)
    reports.sort(key=lambda x: x["minute"])

    # 3. Generate Expert Ranking for top 15 true incidents
    # Hidden score = severity * (1 + 0.05 * people) * (1 + 0.25 * num_vulnerable)
    scored_incidents = []
    for inc in true_incidents:
        vuln_len = len(inc["true_vulnerable"])
        hidden_score = inc["true_severity"] * (1.0 + 0.04 * inc["true_people"]) * (1.0 + 0.30 * vuln_len)
        scored_incidents.append((hidden_score, inc))

    scored_incidents.sort(key=lambda x: x[0], reverse=True)
    expert_ranking = [
        {
            "rank": rank + 1,
            "incident_id": inc["true_incident_id"],
            "zone_id": inc["true_zone"],
            "hidden_score": round(score, 3),
            "true_severity": inc["true_severity"],
            "true_people": inc["true_people"],
            "true_need": inc["true_need"],
            "true_vulnerable": inc["true_vulnerable"]
        }
        for rank, (score, inc) in enumerate(scored_incidents[:15])
    ]

    return reports, truth_records, expert_ranking

def main():
    print("Generating simulated district and scenario data...")
    district_data = generate_district_data()
    with open(DATA_DIR / "district.json", "w", encoding="utf-8") as f:
        json.dump(district_data, f, indent=2)
    print(f"Saved district.json with {len(district_data['zones'])} zones (3 silent).")

    reports, truth_records, expert_ranking = generate_simulation_dataset(district_data)

    # Save reports.jsonl
    with open(DATA_DIR / "reports.jsonl", "w", encoding="utf-8") as f:
        for r in reports:
            f.write(json.dumps(r) + "\n")
    print(f"Saved reports.jsonl with {len(reports)} simulated reports.")

    # Save truth.json
    with open(DATA_DIR / "truth.json", "w", encoding="utf-8") as f:
        json.dump(truth_records, f, indent=2)
    print(f"Saved truth.json for {len(truth_records)} reports.")

    # Save expert_ranking.json
    with open(DATA_DIR / "expert_ranking.json", "w", encoding="utf-8") as f:
        json.dump({
            "notice": "HUMAN BENCHMARK NOTE: Generated from hidden formula (severity x people x vulnerability). In a real deployment, a domain expert/coordinator who did not build the system should replace this with a manual ground truth ranking before operational sign-off.",
            "top_15": expert_ranking
        }, f, indent=2)
    print(f"Saved expert_ranking.json with top 15 incidents.")

if __name__ == "__main__":
    main()
