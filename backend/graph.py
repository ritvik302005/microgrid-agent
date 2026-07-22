from langgraph.graph import StateGraph, END
from state import GridState
from nodes.sensing import read_and_forecast_node
from nodes.allocation import plan_allocation_node
from nodes.safety import enforce_safety_node
from nodes.apply import apply_and_check_deviation_node
from nodes.report import generate_report_node

def route_after_apply(state):
    return "replan" if state["deviation_detected"] else "done"

builder = StateGraph(GridState)

builder.add_node("sense", read_and_forecast_node)
builder.add_node("allocate", plan_allocation_node)
builder.add_node("safety", enforce_safety_node)
builder.add_node("apply", apply_and_check_deviation_node)
builder.add_node("report", generate_report_node)

builder.set_entry_point("sense")
builder.add_edge("sense", "allocate")
builder.add_edge("allocate", "safety")
builder.add_edge("safety", "apply")
builder.add_conditional_edges("apply", route_after_apply, {"replan": "allocate", "done": "report"})
builder.add_edge("report", END)

graph = builder.compile()