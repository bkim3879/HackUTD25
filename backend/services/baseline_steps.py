BASELINE_TEMPLATES = {
    "thermal": [
        "Verify intake/exhaust temperatures and compare to baseline telemetry.",
        "Inspect liquid/air cooling loops for flow obstructions or leaks.",
        "Throttle workload or migrate sessions to reduce thermal load.",
        "Document readings and escalate if temperatures remain out-of-band.",
    ],
    "power": [
        "Check rack and PDU current draw against safe operating limits.",
        "Confirm redundant feeds and breakers are stable with no alarms.",
        "Inspect cabling for heat or contact issues; reseat if necessary.",
        "Coordinate with facilities before cycling affected power domains.",
    ],
    "network": [
        "Validate link status and error counters on top-of-rack switches.",
        "Capture recent packet loss/latency metrics from the fabric controller.",
        "Inspect optics and cables for seating or damage, replace if needed.",
        "Escalate to network ops if congestion persists after mitigation.",
    ],
}

DEFAULT_STEPS = [
    "Inspect sensor telemetry and confirm alert thresholds.",
    "Power cycle the affected server or sled if safe to do so.",
    "Verify airflow paths and clear obstructions.",
    "Validate coolant/air loop pressures before ramping load.",
]


def select_steps(summary: str | None, description: str | None):
    text = f"{summary or ''} {description or ''}".lower()
    if any(word in text for word in ["heat", "therm", "cool", "fan", "gpu"]):
        return BASELINE_TEMPLATES["thermal"]
    if any(word in text for word in ["power", "pdu", "voltage", "current"]):
        return BASELINE_TEMPLATES["power"]
    if any(word in text for word in ["network", "packet", "switch", "fabric"]):
        return BASELINE_TEMPLATES["network"]
    return DEFAULT_STEPS
