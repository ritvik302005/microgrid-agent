from config import CYCLE_HOURS, DEVIATION_THRESHOLD_KW

def apply_and_check_deviation_node(state):
    decision = state["decision"]
    battery_used_kw = decision.get("battery_used_kw", 0)

    kwh_discharged = battery_used_kw * CYCLE_HOURS
    pct_change = (kwh_discharged / state["battery_capacity_kwh"]) * 100
    # battery_used_kw can now be negative (charging), which makes pct_change
    # negative, which INCREASES soc below — the old code only clamped the
    # floor (max(0, ...)), so charging could theoretically push SOC past
    # 100%. safety.py already prevents that from being requested in the
    # first place, but clamping here too costs nothing and makes this
    # function correct on its own, not just correct-because-something-
    # upstream-happens-to-protect-it.
    new_soc = min(100, max(0, state["battery_soc_pct"] - pct_change))

    defer_names = set(decision.get("defer_loads", []))
    updated_loads = [
        {**load, "deferred": load["name"] in defer_names}
        for load in state["flexible_loads"]
    ]

    previous_forecast = state.get("previous_forecast_kw")
    raw_deviation = False
    if previous_forecast is not None:
        raw_deviation = abs(state["solar_kw"] - previous_forecast) > DEVIATION_THRESHOLD_KW

    already_replanned = state.get("replanned", False)
    should_loop = raw_deviation and not already_replanned  # only loop once per cycle

    return {
        **state,
        "battery_soc_pct": round(new_soc, 2),
        "flexible_loads": updated_loads,
        "deviation_detected": should_loop,
        "replanned": already_replanned or should_loop
    }