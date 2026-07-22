import os
import json
import config
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",  # was openai/gpt-oss-120b — much faster on Groq's
                                    # hardware (~650 tok/s vs. a fraction of that for
                                    # a 120B model), and safe to use here because
                                    # safety.py re-validates every decision regardless
                                    # of which model proposed it. The model only needs
                                    # to be good enough to reason about a fixed JSON
                                    # shape, not to be maximally capable.
    temperature=0,
    max_tokens=200,  # the response is a small JSON object + one short sentence —
                      # capping this prevents the model from rambling and paying
                      # for (and waiting on) tokens nobody reads
)

SYSTEM_PROMPT = f"""You are a microgrid energy allocator. Given current solar generation,
battery state, critical load, flexible loads, and grid price, decide how to meet total
demand while minimizing grid usage, protecting battery health, and not wasting surplus solar.

Rules:
- Critical load must always be met, prioritizing solar, then battery, then grid.
- Never suggest discharging the battery below a 20% state of charge reserve.
- If solar generation exceeds current demand, charge the battery with the surplus instead
  of wasting it — represent charging as a NEGATIVE battery_used_kw (e.g. -2.5 means 2.5 kW
  going INTO the battery). Charging is capped at {config.BATTERY_MAX_CHARGE_KW} kW and cannot
  push the battery above 100% — you don't need to compute that limit yourself, just propose
  the sensible amount, a hard safety rule enforces the exact ceiling afterward.
- Flexible loads may be deferred if solar and battery (above reserve) cannot cover them
  without using the grid. If multiple loads must be deferred, defer the one with the
  soonest deadline_hour LAST (defer the ones you have the most slack on first).
- Prefer solar over battery, and battery over grid, in that order, for serving load.

Respond with ONLY valid JSON in exactly this format, no extra text, no markdown fences:
{{"solar_used_kw": <number>, "battery_used_kw": <number, negative means charging>, "grid_used_kw": <number>, "defer_loads": [<load names>], "reasoning": "<one sentence>"}}
"""


def _fallback_decision(state, reason):
    """Shared safe default for both 'the API call itself failed' and 'the
    response wasn't valid JSON' — same philosophy as the hard safety rules:
    when in doubt, do the least clever thing and let solar+grid cover critical
    load, deferring everything flexible."""
    return {
        "solar_used_kw": state["solar_kw"],
        "battery_used_kw": 0,
        "grid_used_kw": max(0, state["critical_load_kw"] - state["solar_kw"]),
        "defer_loads": [l["name"] for l in state["flexible_loads"]],
        "reasoning": f"Fallback: {reason}, defaulting to safe minimal allocation."
    }


def plan_allocation_node(state):
    flexible_summary = [
        {"name": l["name"], "power_kw": l["power_kw"], "deadline_hour": l["deadline_hour"]}
        for l in state["flexible_loads"]
    ]

    human_prompt = f"""
Weather scenario: {state.get('scenario', 'normal')}
Simulated hour: {state.get('sim_hour', 0)} (hour-of-day {state.get('sim_hour', 0) % 24})
Solar available: {state['solar_kw']} kW
Forecast next hour: {state['forecast_solar_kw']} kW
Battery: {state['battery_soc_pct']}% of {state['battery_capacity_kwh']} kWh capacity
Critical load: {state['critical_load_kw']} kW
Flexible loads: {flexible_summary}
Grid price: Rs {state['grid_price_per_kwh']}/kWh
"""

    if state.get("replanned"):
        human_prompt += "\nNote: last cycle's forecast turned out inaccurate. Act more conservatively this time — prefer grid over deep battery discharge to preserve reserve for uncertainty.\n"

    # Two independent failure modes, both handled the same safe way:
    # (1) the API call itself throws (network error, auth, rate limit, timeout)
    # (2) the call succeeds but the response isn't valid JSON
    # The original code only handled (2) — a Groq hiccup would crash /cycle entirely.
    try:
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=human_prompt)])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json", "", 1).strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = _fallback_decision(state, "could not parse LLM response")
    except Exception as e:
        parsed = _fallback_decision(state, f"LLM call failed ({e})")

    return {
        **state,
        "decision": parsed,
        "reasoning": parsed.get("reasoning", "")
    }