import ujson as json

def _state_to_int(s):
    """
    Convert a state string to an integer for SNMP trap codes.
    "up" => 1, everything else => 2
    """
    sl = str(s).lower()
    if sl in ("up",):
        return 1
    else:
        return 2

def snmp_main(in_json_str: str) -> str:
    """
    SNMP trap generation entry point for fan-tray oper-state.
    """
    d = json.loads(in_json_str)
    traps_out = []

    for t in d.get("_trap_info_", []):
        trig = t.get("trigger")
        newv = t.get("new-value")
        # Only handle fan-tray oper-state triggers
        if trig.startswith("/platform/fan-tray") and trig.endswith("/oper-state"):
            trays = d.get("platform", {}).get("fan-tray", [])
            if isinstance(trays, dict):
                trays = [trays]
            for tray in trays or []:
                tray_id = tray.get("id")
                if tray_id is None:
                    continue

                # Ensure tray_id is integer
                try:
                    tray_id_int = int(tray_id)
                except ValueError:
                    # fallback if tray_id is not numeric
                    tray_id_int = 0

                obj = {
                    "fanTrayID": tray_id_int,
                    "fanTrayOperState": _state_to_int(newv),
                }
                traps_out.append({
                    "trap": "FanTrayDown" if _state_to_int(newv) == 2 else "FanTrayUp",
                    "indexes": {"fanTrayID": tray_id_int},
                    "objects": obj
                })

    return json.dumps({"traps": traps_out})
