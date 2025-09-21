import re
from typing import List, Dict

# Valid keys and zones for SomaJSON parsing
KEYS = {"heat","press","angle","dist","gaze","weight","rhythm","hold"}
ZONES = {
    "cheek_L","cheek_R","ear_L","ear_R","hairline_L","hairline_R",
    "neck_ant","neck_lat_L","neck_lat_R","jaw_L","jaw_R",
    "sternum","clav_L","clav_R"
}

# Regular expression to match strict tags: [key:zone:val(:dur)?]
TAG = re.compile(
    r"\[(?P<key>[a-z]+):(?P<zone>[A-Za-z_]*):(?P<val>[^:\]]+)(?::(?P<dur>\d+(?:ms|s)))?\]"
)

# Glyph aliases provide a unique but deterministic shorthand
# Examples: ♡66 -> rhythm (bpm), ●0.3@sternum -> weight, ~0.4@neck_lat_L:2s -> press,
# ◔0.7@gaze -> gaze, ↘8-5@angle -> angle (neck_ant)
GLYPH = [
    (re.compile(r"♡(?P<bpm>\d{2,3})"), lambda m: {"key":"rhythm","zone":"","val":m["bpm"]}),
    (re.compile(r"●(?P<v>\d(?:\.\d+)?)@(?P<zone>[A-Za-z_]+)"),
        lambda m: {"key":"weight","zone":m["zone"],"val":m["v"]}),
    (re.compile(r"~(?P<v>\d(?:\.\d+)?)@(?P<zone>[A-Za-z_]+):(?P<dur>\d+(?:ms|s))"),
        lambda m: {"key":"press","zone":m["zone"],"val":m["v"],"dur":m["dur"]}),
    (re.compile(r"◔(?P<v>\d(?:\.\d+)?)@gaze"),
        lambda m: {"key":"gaze","zone":"","val":m["v"]}),
    (re.compile(r"↘(?P<deg>-?\d+?)@angle"),
        lambda m: {"key":"angle","zone":"neck_ant","val":m["deg"]}),
]

def parse_events(text: str) -> List[Dict]:
    """Parse a text string into a list of event dicts based on SomaJSON tags and glyphs."""
    events: List[Dict] = []
    # Strict tags
    for m in TAG.finditer(text):
        key, zone, val, dur = m["key"], m["zone"], m["val"], m["dur"]
        if key not in KEYS:
            continue
        if zone and zone not in ZONES:
            continue
        events.append({"key": key, "zone": zone, "val": val, "dur": dur or ""})
    # Glyphs
    for rx, fx in GLYPH:
        for m in rx.finditer(text):
            ev = fx(m)
            if ev["key"] in KEYS and (not ev["zone"] or ev["zone"] in ZONES):
                events.append(ev)
    return events
