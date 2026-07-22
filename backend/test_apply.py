from dotenv import load_dotenv
load_dotenv()

from nodes.sensing import read_and_forecast_node
from nodes.allocation import plan_allocation_node
from nodes.safety import enforce_safety_node
from nodes.apply import apply_and_check_deviation_node

# Cycle 1: no prior forecast exists yet, so deviation should be False
state = read_and_forecast_node({})
state = plan_allocation_node(state)
state = enforce_safety_node(state)
state = apply_and_check_deviation_node(state)

print("=== Cycle 1 ===")
print("Battery SOC after:", state["battery_soc_pct"])
print("Deviation detected:", state["deviation_detected"])
print("Forecast for next cycle:", state["forecast_solar_kw"])

# Cycle 2, simulated: deliberately feed in a wildly wrong "previous forecast"
# to prove the deviation check actually fires
fake_state = dict(state)
fake_state["forecast_solar_kw"] = 99.0  # unrealistic on purpose

state2 = read_and_forecast_node(fake_state)
state2 = plan_allocation_node(state2)
state2 = enforce_safety_node(state2)
state2 = apply_and_check_deviation_node(state2)

print("\n=== Cycle 2 (forecast deliberately way off) ===")
print("Actual solar now:", state2["solar_kw"])
print("What last cycle predicted:", state2["previous_forecast_kw"])
print("Deviation detected:", state2["deviation_detected"])