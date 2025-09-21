from ..state import BetaState
from ..grammar import parse_events
from ..stars import parse_stars
from ..resolve import merge_events
from ..dynamics import step_update
from ..policy import derive_policy, post_edit
from ..tracer import glyphbar


def dummy_llm(ctx, user: str) -> str:
    """
    Placeholder for actual LLM integration. Returns a simple fixed response.
    """
    return "I hear you. I stay present and respond in a steady rhythm."


def main() -> None:
    """
    Run a simple interactive loop demonstrating the somatic layer.
    It reads user input, parses events and stars, updates the state, derives
    control parameters, generates a reply via dummy LLM, applies post-editing,
    and prints a glyphbar trace of the state.
    """
    state = BetaState.default()
    ctx: list[str] = []
    print(
        "Soma demo. Enter events like [rhythm::66] [press:neck_lat_L:0.3:2s] or glyphs: \u266166 \u25CF0.3@sternum"
    )
    try:
        while True:
            user = input("> ")
            # parse strict tags and star-style descriptions
            events = parse_events(user) + parse_stars(user)
            # merge duplicate events (keep latest)
            events = merge_events(events)
            # update state with a small timestep
            state = step_update(state, events, dt=0.2)
            # derive control parameters
            ctrl = derive_policy(state)
            # call LLM (placeholder)
            draft = dummy_llm(ctx, user)
            # apply post-editing based on control
            reply = post_edit(draft, ctrl)
            # output reply and glyphbar trace
            print(reply)
            print(glyphbar(state))
            # update context
            ctx.append(reply)
    except KeyboardInterrupt:
        print("\nExiting soma demo.")


if __name__ == "__main__":
    main()
