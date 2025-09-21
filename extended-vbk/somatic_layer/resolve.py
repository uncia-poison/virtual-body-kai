from typing import List, Dict

def merge_events(events: List[Dict]) -> List[Dict]:
    """
    Merge duplicate events on the same key and zone into one.
    Keeps only the last event for each (key, zone) tuple.
    """
    merged: Dict[tuple, Dict] = {}
    for e in events:
        key_zone = (e.get("key"), e.get("zone", ""))
        merged[key_zone] = e
    return list(merged.values())
