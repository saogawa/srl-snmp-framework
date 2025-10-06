import ujson as json

def _state_to_int(s: str) -> int:
    """
    Convert fan-tray oper-state string to integer based on TmnxDeviceState.
    """
    try:
        return int(s)
    except ValueError:
        return 1  # Default to deviceStateUnknown if conversion fails

def snmp_main(in_json_str: str) -> str:
    """
    SNMP trap generation entry point for Fan Tray oper-state.
    """
    d = json.loads(in_json_str)
    traps_out = []

    for t in d.get("_trap_info_", []):
        trig = t.get("trigger")
        newv = t.get("new-value")

        if trig.startswith("/platform/fan-tray") and trig.endswith("/oper-state"):
            trays = d.get("platform", {}).get("fan-tray", [])
            if isinstance(trays, dict):
                trays = [trays]
            for tray in trays or []:
                tray_id = tray.get("id")
                if tray_id is None:
                    continue
                try:
                    tray_id_int = int(tray_id)
                except ValueError:
                    tray_id_int = 0
                obj = {
                    "fanTrayID": tray_id_int,
                    "fanTrayOperState": _state_to_int(newv),
                }
                traps_out.append({
                    "trap": "tmnxPhysChassisFanOperStatus",
                    "indexes": {"fanTrayID": tray_id_int},
                    "objects": obj
                })

    return json.dumps({"traps": traps_out})
