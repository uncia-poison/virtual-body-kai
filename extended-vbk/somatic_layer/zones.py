from dataclasses import dataclass
from typing import Tuple, Dict, List

ZONES: Tuple[str, ...] = (
    "cheek_L","cheek_R","ear_L","ear_R","hairline_L","hairline_R",
    "neck_ant","neck_lat_L","neck_lat_R","jaw_L","jaw_R",
    "sternum","clav_L","clav_R"
)

# Optional: simple adjacency for diffusion (off by default)
ADJ: Dict[str, Tuple[str, ...]] = {
    "cheek_L": ("hairline_L","jaw_L","ear_L"),
    "ear_L": ("hairline_L","cheek_L","neck_lat_L"),
    # ... fill out minimal neighbors...
}
