from dotenv import load_dotenv
load_dotenv()

from graph import graph

# Deliberately start with a wildly wrong "previous forecast" so the very first
# sense→apply cycle detects a deviation and the graph loops back to replan —
# proving the conditional edge actually fires, not just exists on paper.
result = graph.invoke({"forecast_solar_kw": 99.0})

print("Final decision:", result["decision"])
print("Reasoning:", result["reasoning"])
print("Replanned this cycle:", result["report"]["replanned_this_cycle"])
print("Report:", result["report"])