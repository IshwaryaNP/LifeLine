import re
from typing import Dict, Any, List, Tuple
from app.config import USE_LLM

# Word-to-number mapping
WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5
}

NEED_KEYWORDS = {
    "rescue": [
        "rescue", "trapped", "stuck", "stranded", "bachao", "save", "boat", "rooftop", 
        "flood", "flooded", "floded", "rising", "surge", "collapse", "drowning"
    ],
    "medical": [
        "medical", "doctor", "ambulance", "injured", "bleeding", "hospital", "patient",
        "oxygen", "saline", "hurt", "critical", "medicine", "wound", "diarrhea"
    ],
    "food": [
        "food", "starving", "hungry", "ration", "rations", "eat", "milk", "airdrop",
        "dry food", "bhookhe"
    ],
    "water": [
        "drinking water", "water tanker", "saline water", "clean water", "borewell", 
        "peene ka paani", "thirst"
    ],
    "shelter": [
        "shelter", "homeless", "roof", "roofs", "blown off", "tarpaulin", "overcrowded",
        "camps", "tent"
    ]
}

VULNERABLE_KEYWORDS = {
    "children": ["children", "child", "kids", "kid", "baby", "infant", "bachhe", "bacche"],
    "elderly": ["elderly", "old", "grandma", "grandpa", "aged", "senior", "bujurg"],
    "pregnant": ["pregnant", "pregnancy", "expecting", "maternity"],
    "disabled": ["disabled", "handicapped", "wheelchair", "bedridden", "paralyzed"]
}

URGENCY_KEYWORDS = [
    "asap", "now", "urgent", "urgnt", "emergency", "immediately", "rising", "fast",
    "critical", "quick", "tonight", "night", "dying", "help"
]

def extract_rule_based(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    
    # 1. Need Type Extraction
    # If explicit acute medical emergency phrases appear, give medical highest boost
    if any(m in text_lower for m in ["ambulance", "doctor", "bleeding", "patient", "oxygen", "hospital"]):
        need_type = "medical"
        need_conf = 0.95
    else:
        need_scores: Dict[str, int] = {k: 0 for k in NEED_KEYWORDS}
        for need, kws in NEED_KEYWORDS.items():
            for kw in kws:
                if kw in text_lower:
                    need_scores[need] += 1
        
        sorted_needs = sorted(need_scores.items(), key=lambda x: x[1], reverse=True)
        if sorted_needs[0][1] > 0:
            need_type = sorted_needs[0][0]
            need_conf = min(1.0, 0.5 + 0.2 * sorted_needs[0][1])
        else:
            if "water" in text_lower:
                need_type = "water"
                need_conf = 0.5
            else:
                need_type = "other"
                need_conf = 0.3

    # 2. People Count Extraction
    people_count = None
    people_conf = 0.0
    
    # First priority: explicit quantity followed by person keywords (e.g. "25 residents", "8 victims", "12 people", "50 workers")
    explicit_match = re.search(r'\b(\d{1,4})\s+(people|persons|residents|patients|individuals|victims|members|ppl|families|workers|villagers)\b', text_lower)
    if explicit_match:
        people_count = int(explicit_match.group(1))
        people_conf = 0.90
    else:
        # Check any digits with context filtering (exclude 24 hours, 7 feet, Toll Plaza 4)
        for m in re.finditer(r'\b(\d{1,3})\b', text_lower):
            d_val = int(m.group(1))
            start_pos = max(0, m.start() - 15)
            end_pos = min(len(text_lower), m.end() + 15)
            snippet = text_lower[start_pos:end_pos]
            if any(x in snippet for x in ["hour", "feet", "ft", "plaza", "toll", "nh", "grid", "phase"]):
                continue
            people_count = d_val
            people_conf = 0.80
            break

    if people_count is None:
        # Check word numbers
        for w, val in WORD_NUMBERS.items():
            pattern = rf'\b{w}\s*(people|persons|residents|patients|individuals|victims|members|ppl|families)?\b'
            if re.search(pattern, text_lower):
                people_count = val
                people_conf = 0.80
                break

    if people_count is None:
        people_count = 1 # default assumption of report
        people_conf = 0.25

    # 3. Vulnerable Groups
    vulnerable_groups = []
    for grp, kws in VULNERABLE_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            vulnerable_groups.append(grp)
    vuln_conf = 0.9 if vulnerable_groups else 0.5

    # 4. Urgency Cues
    urgency_cues = [u for u in URGENCY_KEYWORDS if u in text_lower]

    # 5. Place Text extraction
    place_text = None
    place_conf = 0.0
    # Patterns like "near XYZ", "at XYZ", "in XYZ"
    place_match = re.search(r'\b(?:near|at|around|inside|outside)\s+([^!.,\?]+)', text, re.IGNORECASE)
    if place_match:
        candidate = place_match.group(1).strip()
        # Cut off punctuation or trailing verbs
        candidate = re.split(r'\b(?:completely|urgently|water|we|please|send|having|crying|is|are|need|trapped)\b', candidate, flags=re.IGNORECASE)[0].strip()
        if candidate.lower().startswith("homes near "):
            candidate = candidate[11:].strip()
        if len(candidate) > 2:
            place_text = candidate
            place_conf = 0.75
    
    if not place_text:
        place_text = "Unknown"
        place_conf = 0.1

    return {
        "need_type": need_type,
        "people_count": people_count,
        "vulnerable_groups": vulnerable_groups,
        "urgency_cues": urgency_cues,
        "place_text": place_text,
        "extraction_confidences": {
            "need_type": round(need_conf, 2),
            "people_count": round(people_conf, 2),
            "vulnerable_groups": round(vuln_conf, 2),
            "place_text": round(place_conf, 2)
        }
    }

def extract_report_info(text: str) -> Dict[str, Any]:
    """Default extractor (rule-based). If USE_LLM is enabled, falls back safely to cached/rule extractor."""
    # Strict offline requirement: USE_LLM=False is the default.
    return extract_rule_based(text)
