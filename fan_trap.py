import json

def _state_to_int(s):
    """
    Convert a state string to an integer for SNMP trap codes.

    In this simplified mapping, any value equal to "up" (case‑insensitive)
    returns 1. All other values return 2. This matches the user's request to
    map only the "up" state to 1 and everything else to 2.

    Args:
        s: The state value to convert (string or any type convertible to string).

    Returns:
        1 if the state is "up" (case‑insensitive), otherwise 2.
    """
    sl = str(s).lower()
    if sl in ("up",):
        return 1
    else:
        return 2

def snmp_main(in_json_str: str) -> str:
    """
    SNMP trap generation entry point.

    Args:
        in_json_str: JSON string containing '_trap_info_' and 'context' data.

    Returns:
        A JSON string describing one or more traps to be sent.
    """
    d = json.loads(in_json_str)
    traps_out = []

    for t in d.get("_trap_info_", []):
        trig = t.get("trigger")
        newv = t.get("new-value")
        # Only handle fan-tray oper-state triggers
        if trig.startswith("/platform/fan-tray") and trig.endswith("/oper-state"):
            trays = d.get("platform", {}).get("fan-tray", [])
            # Ensure trays is a list
            if isinstance(trays, dict):
                trays = [trays]
            for tray in trays or []:
                tray_id = tray.get("id")
                if tray_id is None:
                    continue

                # Build varbind data
                obj = {
                    "fanTrayID": str(tray_id),
                    "fanTrayOperState": _state_to_int(newv),
                }
                traps_out.append({
                    # Use state value to determine trap name
                    "trap": "FanTrayDown" if _state_to_int(newv) == 2 else "FanTrayUp",
                    "indexes": {"fanTrayID": str(tray_id)},
                    "objects": obj
                })

    return json.dumps({"traps": traps_out})
