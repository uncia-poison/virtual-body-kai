from dataclasses import dataclass
from typing import List
from .state import BetaState

@dataclass
class Ctrl:
    """Container for control parameters used by the post-editor."""
    target_words: int
    pause_prob: float
    dash_peak: float
    imper_ratio: float

def derive_policy(st: BetaState) -> Ctrl:
    """Derive control parameters from the current somatic state."""
    g = st.global_
    # Focus on weight/gaze in sternum and neck zones
    w = (
        st.zones["sternum"].weight
        + st.zones["neck_lat_L"].weight
        + st.zones["neck_lat_R"].weight
    ) / 3.0
    gz = (
        st.zones["neck_lat_L"].gaze + st.zones["neck_lat_R"].gaze
    ) / 2.0
    # Base and bounds for target words per sentence
    T0, Tmin, Tmax = 18, 8, 24
    # Weights controlling influence of hold, weight, gaze, and bpm deviations
    w_hold, w_weight, w_gaze, w_bpm = 6.0, 4.0, 3.0, 4.0
    target = T0 - w_hold * g.hold - w_weight * w + w_gaze * gz - w_bpm * abs(g.bpm - 66) / 66.0
    target = max(Tmin, min(Tmax, int(round(target))))
    # Pause probability grows with hold and when bpm falls below baseline
    p0, p_hold, p_slow = 0.05, 0.35, 0.25
    pause_prob = max(
        0.0,
        min(1.0, p0 + p_hold * g.hold + p_slow * max(0, (66 - g.bpm)) / 66.0),
    )
    # Imperative ratio increases with weight but decreases when not holding
    r0, r_w, r_calm = 0.05, 0.4, 0.2
    imper_ratio = max(0.0, min(1.0, r0 + r_w * w - r_calm * (1 - g.hold)))
    return Ctrl(target_words=target, pause_prob=pause_prob, dash_peak=0.7, imper_ratio=imper_ratio)

def post_edit(text: str, ctrl: Ctrl) -> str:
    """
    Apply a simple post-edit to the generated text based on control parameters.
    Adjusts sentence length towards target_words and inserts pauses.
    This implementation is deliberately minimal to maintain meaning.
    """
    # Split on periods into rough sentences
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    new_sentences: List[str] = []
    for s in sentences:
        words = s.split()
        # Shorten overly long sentences
        if len(words) > ctrl.target_words + 4:
            s = " ".join(words[: ctrl.target_words])
        # Extend short sentences slightly and optionally add ellipses
        elif len(words) < ctrl.target_words - 4:
            if ctrl.pause_prob > 0.4:
                s = s + " ..."
        new_sentences.append(s)
    out = ". ".join(new_sentences)
    # Append trailing pause if pause_prob is high
    if ctrl.pause_prob > 0.6 and not out.endswith("..."):
        out += " ..."
    return out
