import ujson as json

# Function to convert operational state to TmnxDeviceState as per MIB definitions
def convertDeviceOperState(value: str) -> int:
    # Use match-case to map string states to integer codes
    match value:
        case "up":
            return 3  # Represents the "OK" state
        case "down":
            return 5  # Represents the "OUT OF SERVICE" state
        case "empty":
            return 2  # Represents the "NOT EQUIPPED" state
        case "failed":
            return 4  # Represents the "FAILED" state
        case _:
            return 1  # Default case for "UNKNOWN" state

# Main function to generate fan traps, aligned with SNMP Trap Handler operations
def snmp_main(in_json_str: str) -> str:
    # Parse the input JSON string into a Python dictionary
    data = json.loads(in_json_str)
    traps_out = []  # Initialize an empty list to store trap entries

    # Extract fan-tray information from the parsed data
    trays = data.get("platform", {}).get("fan-tray", [])
    if isinstance(trays, dict):
        trays = [trays]  # Ensure trays is a list for uniform processing

    # Iterate over each trap in the "_trap_info_" list from the data
    for trap in data.get("_trap_info_", []):
        trigger = trap.get("trigger", "")  # Get the trigger path
        newv = trap.get("new-value", "")  # Get the new value of the state
        oldv = trap.get("old-value", "")  # Get the old value of the state

        # Check if the trigger path is relevant for fan-tray operational state changes
        if not (trigger.startswith("/platform/fan-tray") and trigger.endswith("/oper-state")):
            continue  # Skip if not relevant

        # Iterate over each fan tray to process the trap
        for tray in trays:
            tray_id = tray.get("id")  # Get the tray ID
            if tray_id is None:
                continue  # Skip if tray ID is not available

            try:
                tray_id_int = int(tray_id)  # Convert tray ID to integer
            except ValueError:
                tray_id_int = 0  # Default to 0 if conversion fails

            # Determine the type of trap based on new and old values
            trap_name = None
            if newv == "failed":
                trap_name = "tmnxEqPhysChassFanFailure"  # Trap for fan failure
            elif newv == "up" and oldv == "failed":
                trap_name = "tmnxEqPhysChassFanFailureClear"  # Trap for clearing fan failure
            else:
                continue  # Skip unrelated events

            # Get the operational state and fan speed from the tray data
            oper_state = tray.get("oper-state", newv)
            speed = tray.get("fan", {}).get("speed", 0) if tray.get("fan") else 0

            # Generate hardware index for the fan (class 6 << 24 | id)
            hw_index = (6 << 24) + tray_id_int

            # Create a trap entry with relevant information
            trap_entry = {
                "trap": trap_name,
                "indexes": {
                    "tmnxChassisIndex": 1,  # Static index for chassis
                    "tmnxHwIndex": hex(hw_index),  # Hardware index in hexadecimal
                    "tmnxPhysChassisClass": 3,  # Static class index
                    "tmnxPhysChassisNum": 1,  # Static chassis number
                    "tmnxPhysChassisFanIndex": tray_id_int  # Fan index
                },
                "objects": {
                    "tmnxHwClass": 6,  # Hardware class for fan
                    "tmnxPhysChassisFanOperStatus": convertDeviceOperState(oper_state),  # Converted operational state
                    "tmnxPhysChassisFanSpeedPercent": speed  # Fan speed percentage
                }
            }

            # Append the trap entry to the output list
            traps_out.append(trap_entry)

    # Return the list of traps as a JSON string
    return json.dumps({"traps": traps_out})