def snmp_main(in_json_str: str) -> str:
    d = json.loads(in_json_str)
    traps_out = []

    trays = d.get("platform", {}).get("fan-tray", [])
    if isinstance(trays, dict):
        trays = [trays]

    for trap in d.get("_trap_info_", []):
        trig = trap.get("trigger", "")
        newv = trap.get("new-value", "")
        oldv = trap.get("old-value", "")
        xpath = trap.get("xpath", "")

        if not trig.startswith("/platform/fan-tray") or not trig.endswith("/oper-state"):
            continue

        # parse fan id from xpath
        m = re.search(r"\[id=([^\]]+)\]", xpath)
        tray_id = m.group(1) if m else None
        if tray_id is None:
            continue

        try:
            tray_id_int = int(tray_id)
        except:
            tray_id_int = 0

        trap_name = None
        if newv == "failed":
            trap_name = "tmnxEqPhysChassFanFailure"
        elif newv == "up" and oldv == "failed":
            trap_name = "tmnxEqPhysChassFanFailureClear"
        else:
            continue


        # fan speed
        tray = next((t for t in trays if str(t.get("id")) == tray_id), {})
        speed = tray.get("fan", {}).get("speed", 0)
        oper_state = tray.get("oper-state", newv)

        hw_index = (6 << 24) + tray_id_int

        traps_out.append({
            "trap": trap_name,
            "indexes": {
                "tmnxChassisIndex": 1,
                "tmnxHwIndex": hex(hw_index),
                "tmnxPhysChassisClass": 3,
                "tmnxPhysChassisNum": 1,
                "tmnxPhysChassisFanIndex": tray_id_int
            },
            "objects": {
                "tmnxHwClass": 6,
                "tmnxPhysChassisFanOperStatus": convertDeviceOperState(oper_state),
                "tmnxPhysChassisFanSpeedPercent": speed
            }
        })

    return json.dumps({"traps": traps_out})