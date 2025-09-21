from typing import List, Dict

# Heuristic lexicon mapping action words to event parameters
LEX = {
    "touch":  {"press": 0.2},
    "stroke": {"press": 0.3},
    "warm":   {"heat": 0.4},
    "closer": {"dist": "near"},
    "breathe":{"gaze": 0.2},
}

# Mapping natural language hints to zones
ZONE_HINT = {
    "cheek": "cheek_L",
    "ear":   "ear_L",
    "neck":  "neck_lat_L",
    "sternum": "sternum",
}

def parse_stars(text: str) -> List[Dict]:
    """Parse free-form descriptive text into heuristic event list."""
    events: List[Dict] = []
    t = text.lower()
    for word, mapping in LEX.items():
        if word in t:
            for zhint, zone in ZONE_HINT.items():
                if zhint in t:
                    for key, val in mapping.items():
                        events.append({"key": key, "zone": zone, "val": val, "dur": ""})
    return events
