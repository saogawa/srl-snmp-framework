import ujson as json
import re
from typing import Optional

# Constants representing hardware class and device states
TMNXHWCLASS_POWERSUPPLY = 5

# Device state constants
TMNXDEVICESTATE_UNKNOWN      = 1
TMNXDEVICESTATE_NOT_EQUIPPED = 2
TMNXDEVICESTATE_OK           = 3
TMNXDEVICESTATE_FAILED       = 4
TMNXDEVICESTATE_OUTOFSERVICE = 5

def convert_device_oper_state(value: str) -> int:
    # Convert a string representation of device state to its corresponding integer constant
    if value == 'up': return TMNXDEVICESTATE_OK
    if value == 'down': return TMNXDEVICESTATE_OUTOFSERVICE
    if value == 'empty': return TMNXDEVICESTATE_NOT_EQUIPPED
    if value == 'failed': return TMNXDEVICESTATE_FAILED
    return TMNXDEVICESTATE_UNKNOWN

def is_ac_power_supply(psu: dict) -> Optional[bool]:
    # Determine if the power supply unit (PSU) is AC based on its type and voltage
    psu_type = str(psu.get('type', '')).lower()
    # Check if the PSU type contains any DC indicators and not AC
    if any(x in psu_type for x in ['hvdc', 'lvdc', 'dc']) and 'ac' not in psu_type:
        return False
    if 'ac' in psu_type:
        return True

    try:
        # Attempt to retrieve and convert the voltage to a float
        volt = float(psu.get('volt', 0))
        if volt <= 0.1:
            return None
        return volt > 64  # Consider it AC if voltage is greater than 64
    except (ValueError, TypeError):
        return None

def calc_hw_index(psu_id: str) -> int:
    # Calculate the hardware index for a given PSU ID
    try:
        idx = int(psu_id)
    except:
        idx = 0  # Default to 0 if conversion fails
    return (TMNXHWCLASS_POWERSUPPLY << 24) + idx

def snmp_main(in_json_str: str) -> str:
    # Main function to process SNMP traps from input JSON string
    d = json.loads(in_json_str)
    traps_out = []

    # Extract power supply information from the input JSON
    supplies = d.get("platform", {}).get("power-supply", [])
    if isinstance(supplies, dict):
        supplies = [supplies]  # Ensure supplies is a list

    # Extract trap information
    trap_info = d.get("_trap_info_", [])
    # Create a map of PSU IDs to their corresponding PSU data
    psu_map = {str(s.get("id")): s for s in supplies if "id" in s}

    for trap in trap_info:
        # Process each trap to determine if it relates to a power supply operational state change
        trig = trap.get("trigger", "")
        if not trig.startswith("/platform/power-supply") or not trig.endswith("/oper-state"):
            continue

        xpath = trap.get("xpath", "")
        m = re.search(r"\[id=([^\]]+)\]", xpath)
        psu_id = m.group(1) if m else None

        if psu_id is None or psu_id not in psu_map:
            continue

        psu = psu_map[psu_id]
        is_ac = is_ac_power_supply(psu)
        if is_ac is not True:
            continue  # Skip if PSU is DC or unknown

        newv = trap.get("new-value", "")
        oldv = trap.get("old-value", "")

        # Determine the appropriate trap name based on the new and old values
        if newv in ("failed", "down"):
            trap_name = "tmnxEqPhysChassPowerSupAcFail"
        elif newv == "up" and oldv in ("failed", "down"):
            trap_name = "tmnxEqPhysChassPowerSupAcFailClear"
        else:
            continue  # Skip if not a relevant event

        dev_state = convert_device_oper_state(newv)
        feed1, feed2 = None, None

        # Determine the status of power feeds
        if psu.get("dual_feeds"):
            try:
                v1 = float(psu.get("feed_a_volt", 0))
            except: v1 = 0
            try:
                v2 = float(psu.get("feed_b_volt", 0))
            except: v2 = 0
            feed1 = TMNXDEVICESTATE_FAILED if v1 == 0 else dev_state
            feed2 = TMNXDEVICESTATE_FAILED if v2 == 0 else dev_state
        else:
            try:
                v = float(psu.get("volt", 0))
            except: v = 0
            feed1 = TMNXDEVICESTATE_FAILED if v == 0 else dev_state
            feed2 = TMNXDEVICESTATE_NOT_EQUIPPED

        # Calculate the hardware index and append the trap information to the output list
        hw_index = calc_hw_index(psu_id)
        traps_out.append({
            "trap": trap_name,
            "indexes": {
                "tmnxChassisIndex": 1,
                "tmnxHwIndex": hex(hw_index),
                "tmnxPhysChassPowerSupId": psu_id
            },
            "objects": {
                "tmnxHwClass": TMNXHWCLASS_POWERSUPPLY,
                "tmnxPhysChassPowerSupACStatus": dev_state,
                "tmnxPhysChassPowerSup1Status": feed1,
                "tmnxPhysChassPowerSup2Status": feed2
            }
        })

    return json.dumps({"traps": traps_out})  # Return the JSON representation of the traps