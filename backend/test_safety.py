from dotenv import load_dotenv
load_dotenv()

from nodes.sensing import read_and_forecast_node
from nodes.allocation import plan_allocation_node
from nodes.safety import enforce_safety_node

# Case 1: real pipeline — should pass through with no alerts
state = read_and_forecast_node({})
state = plan_allocation_node(state)
state = enforce_safety_node(state)

print("=== Normal case ===")
print("Decision:", state["decision"])
print("Alerts:", state["alerts"])

# Case 2: deliberately unsafe decision, to prove the override actually fires
bad_state = {
    "solar_kw": 1.0,
    "battery_soc_pct": 22.0,        # already close to the 20% reserve
    "battery_capacity_kwh": 10.0,
    "critical_load_kw": 3.0,
    "flexible_loads": [],
    "decision": {
        "solar_used_kw": 1.0,
        "battery_used_kw": 8.0,     # way beyond what the reserve allows
        "grid_used_kw": 0.0,
        "defer_loads": [],
        "reasoning": "Deliberately bad decision to test the safety override."
    },
    "alerts": []
}

corrected = enforce_safety_node(bad_state)
print("\n=== Deliberately unsafe case ===")
print("Corrected decision:", corrected["decision"])
print("Alerts:", corrected["alerts"])