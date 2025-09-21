from enum import Enum
from .state import BetaState

class Mode(Enum):
    CALM = 0
    CLOSE = 1
    CAPTURE = 2

def infer_mode(st: BetaState) -> Mode:
    """
    Infer a coarse interaction mode based on BetaState.
    Modes:
    - CALM: no significant hold or closeness
    - CLOSE: when weight on sternum is high or distance is near
    - CAPTURE: when hold is high
    """
    # high hold triggers capture state
    if st.global_.hold >= 0.7:
        return Mode.CAPTURE
    # closeness measured by weight or distance on sternum zone
    sternum = st.zones.get("sternum")
    if sternum:
        if sternum.weight >= 0.3 or sternum.dist <= 0.5:
            return Mode.CLOSE
    return Mode.CALM
