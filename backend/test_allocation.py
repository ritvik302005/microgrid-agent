from dotenv import load_dotenv
load_dotenv()

from nodes.sensing import read_and_forecast_node
from nodes.allocation import plan_allocation_node

state = read_and_forecast_node({})
state = plan_allocation_node(state)

print("Sensed state:", {k: state[k] for k in ["solar_kw", "battery_soc_pct", "critical_load_kw", "flexible_loads"]})
print("Decision:", state["decision"])
print("Reasoning:", state["reasoning"])