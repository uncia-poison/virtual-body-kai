from .state import BetaState


def json_trace(st: BetaState) -> dict:
    """Return a minimal JSON-serializable trace of current state."""
    return st.to_json()


def glyphbar(st: BetaState) -> str:
    """Return a human-readable bar chart string for key state dimensions."""
    def bar(x: float) -> str:
        # scale to 0-5 blocks
        n = int(round(x * 5))
        return "█" * n + "░" * (5 - n)
    z = st.zones
    lines = []
    lines.append(f"bpm:{st.global_.bpm} | hold:{bar(st.global_.hold)} {st.global_.hold:.2f}")
    # Example bars for neck and sternum zones; extend as needed
    lines.append(
        f"neck_L: heat {bar(z['neck_lat_L'].heat)} {z['neck_lat_L'].heat:.2f} | "
        f"press {bar(z['neck_lat_L'].press)} {z['neck_lat_L'].press:.2f}"
    )
    lines.append(
        f"sternum: weight {bar(z['sternum'].weight)} {z['sternum'].weight:.2f}"
    )
    return "\n".join(lines)
