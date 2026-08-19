"""Fast, offline checks for allocator response handling.

Run from backend with: python test_allocation_parsing.py
"""

import nodes.allocation as allocation


STATE = {
    "solar_kw": 2.0,
    "forecast_solar_kw": 2.5,
    "battery_soc_pct": 60.0,
    "battery_capacity_kwh": 10.0,
    "critical_load_kw": 3.0,
    "flexible_loads": [{"name": "water_pump", "power_kw": 1.5, "deadline_hour": 10}],
    "grid_price_per_kwh": 8.0,
    "alerts": [],
}


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeLlm:
    def __init__(self, content):
        self.content = content

    def invoke(self, *_args, **_kwargs):
        return FakeResponse(self.content)


def check(content, expected_alert_count):
    allocation.llm = FakeLlm(content)
    result = allocation.plan_allocation_node(STATE)
    assert len(result["alerts"]) == expected_alert_count, result
    return result


valid = check(
    '```json\n{"solar_used_kw": 2, "battery_used_kw": 1, "grid_used_kw": 0, '
    '"defer_loads": [], "reasoning": "Solar and battery cover the critical load."}\n```',
    0,
)
assert valid["decision"]["battery_used_kw"] == 1.0

fallback = check("I cannot provide an allocation.", 1)
assert fallback["decision"]["grid_used_kw"] == 1.0
assert fallback["alerts"][0].startswith("Safety override:")

print("Allocator parsing and safety-intervention checks passed.")
