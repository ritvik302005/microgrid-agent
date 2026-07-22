from config import CYCLE_HOURS, BATTERY_RESERVE_PCT, BATTERY_MAX_CHARGE_KW, BATTERY_MAX_DISCHARGE_KW

def enforce_safety_node(state):
    decision = dict(state["decision"])  # copy so we don't mutate the LLM's original response
    alerts = list(state.get("alerts", []))

    solar_used = decision.get("solar_used_kw", 0)
    battery_used = decision.get("battery_used_kw", 0)
    grid_used = decision.get("grid_used_kw", 0)

    if battery_used >= 0:
        # --- Check 1: discharge — reserve floor AND an absolute rate ceiling ---
        available_kwh = max(0, (state["battery_soc_pct"] - BATTERY_RESERVE_PCT) / 100 * state["battery_capacity_kwh"])
        max_battery_kw = min(available_kwh / CYCLE_HOURS, BATTERY_MAX_DISCHARGE_KW)

        if battery_used > max_battery_kw:
            shortfall = round(battery_used - max_battery_kw, 2)
            battery_used = round(max_battery_kw, 2)
            grid_used += shortfall
            alerts.append(f"Safety override: capped battery discharge to protect {BATTERY_RESERVE_PCT}% reserve / {BATTERY_MAX_DISCHARGE_KW} kW rate limit, shifted {shortfall} kW to grid.")
    else:
        # --- Check 1B: charging — can't push SOC above 100%, can't exceed max charge rate ---
        charge_kw = -battery_used
        room_kwh = max(0, (100.0 - state["battery_soc_pct"]) / 100 * state["battery_capacity_kwh"])
        max_charge_kw = min(room_kwh / CYCLE_HOURS, BATTERY_MAX_CHARGE_KW)

        if charge_kw > max_charge_kw:
            curtailed = round(charge_kw - max_charge_kw, 2)
            battery_used = round(-max_charge_kw, 2)
            # that surplus solar has nowhere to go — it's curtailed, not "used"
            solar_used = round(max(0, solar_used - curtailed), 2)
            alerts.append(f"Safety override: capped battery charging at {max_charge_kw:.2f} kW (100% SOC or {BATTERY_MAX_CHARGE_KW} kW rate limit) — {curtailed} kW of surplus solar curtailed.")

    # --- Check 2: critical load must always be met ---
    # (battery_used may be negative here if charging — that's fine, it simply
    # doesn't contribute to serving load, same as it contributing 0)
    critical_supplied = solar_used + max(0, battery_used) + grid_used
    if critical_supplied < state["critical_load_kw"]:
        shortfall = round(state["critical_load_kw"] - critical_supplied, 2)
        grid_used = round(grid_used + shortfall, 2)
        alerts.append(f"Safety override: critical load underserved by allocator, forced additional {shortfall} kW from grid.")

    decision["solar_used_kw"] = round(solar_used, 2)
    decision["battery_used_kw"] = round(battery_used, 2)
    decision["grid_used_kw"] = round(grid_used, 2)

    return {
        **state,
        "decision": decision,
        "alerts": alerts
    }