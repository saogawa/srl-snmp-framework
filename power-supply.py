import ujson as json

def _state_to_int(s: str) -> int:
    """
    Convert power-supply oper-state string to integer.
    up   -> 1
    down -> 2
    all others -> 2 (treated as down)
    """
    sl = str(s).lower()
    if sl == "up":
        return 1
    else:
        return 2

def snmp_main(in_json_str: str) -> str:
    """
    SNMP trap generation entry point for Power Supply oper-state.
    """
    d = json.loads(in_json_str)
    traps_out = []

    for t in d.get("_trap_info_", []):
        trig = t.get("trigger")
        newv = t.get("new-value")

        if trig.startswith("/platform/power-supply") and trig.endswith("/oper-state"):
            psus = d.get("platform", {}).get("power-supply", [])
            if isinstance(psus, dict):
                psus = [psus]
            for psu in psus or []:
                psu_id = psu.get("id")
                if psu_id is None:
                    continue
                try:
                    psu_id_int = int(psu_id)
                except ValueError:
                    psu_id_int = 0
                obj = {
                    "powerSupplyID": psu_id_int,
                    "powerSupplyOperState": _state_to_int(newv),
                }
                traps_out.append({
                    "trap": "tmnxPhysChassisPowerSupplyOperStatus",
                    "indexes": {"powerSupplyID": psu_id_int},
                    "objects": obj
                })

    return json.dumps({"traps": traps_out})
