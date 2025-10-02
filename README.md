# SR Linux SNMP Framework

This project provides a **custom SNMP trap implementation for Nokia SR Linux**.  
It monitors the YANG state path:

```bash
/platform/fan-tray[id=*]/oper-state
```

and generates SNMP traps when fan trays change their operational state (**Up** or **Down**).

---

## Background: SNMP Framework in SR Linux

Nokia SR Linux includes a flexible **SNMP framework** that allows operators to:

- Map **YANG state paths** to **SNMP OIDs**.
- Generate **custom SNMP traps** when specific conditions occur.
- Extend monitoring beyond standard MIBs by defining **YAML trap definitions** and **MicroPython scripts**.

### Why is this useful?

- **Integration**: Works with existing NMS/OSS systems that rely on SNMP traps.
- **Flexibility**: Operators can add traps for any YANG path, not only predefined MIBs.
- **Debugging support**: Optional debug mode outputs JSON input/output for troubleshooting.

---

## Features

- Watches `/platform/fan-tray[id=*]/oper-state`.
- Sends:
  - **FanTrayUp trap** when state = `up`
  - **FanTrayDown trap** for all other states
- Lightweight MicroPython handler (`snmp_main()`).
- Example YAML trap definition included.
- Easy to extend for other hardware sensors (PSU, temperature, etc.).

---

## Repository Contents

```
fan_trap.py      # MicroPython script that converts YANG data into SNMP traps
fan_trap.yaml    # Trap definition YAML mapping YANG path to OIDs
README.md        # This documentation
LICENSE          # MIT License (default, feel free to change)
```

---

## Installation

### 1. Copy the files to your SR Linux node

```bash
scp fan_trap.py admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
scp fan_trap.yaml admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
```

### 2. Register the trap definition

Edit `/etc/opt/srlinux/snmp/snmp_files_config.yaml` and add:

```yaml
trap-definitions:
  - scripts/fan_trap.yaml
```

### 3. Restart the SNMP server

```bash
/tools system app-management application snmp_server-mgmt restart
```

### 4. Configure SNMP trap destination

```bash
enter candidate
configure system snmp
  trap-group tg1 admin-state enable network-instance default
    destination d1 admin-state enable
      address 192.0.2.10
      community-entry ce1
        community "s3cr3t"
commit now
```

---

## fan_trap.yaml

```yaml
# /etc/opt/srlinux/snmp/scripts/fan_trap.yaml
python-script: fan_trap.py
enabled: true
debug: true

traps:
  - name: FanTrayDown
    enabled: true
    oid: 1.3.6.1.4.1.6527.115.114.108.105.110.117.120.10.1
    triggers:
      - /platform/fan-tray[id=*]/oper-state
    context:
      - /platform/fan-tray
    data:
      - indexes:
          - name: fanTrayID
            syntax: octet string
        objects:
          - name: fanTrayID
            oid: 1.3.6.1.4.1.6527.115.114.108.105.110.117.120.10.2
            syntax: octet string
          - name: fanTrayOperState
            oid: 1.3.6.1.4.1.6527.115.114.108.105.110.117.120.10.3
            syntax: integer

  - name: FanTrayUp
    enabled: true
    oid: 1.3.6.1.4.1.6527.115.114.108.105.110.117.120.10.4
    startup: true
    triggers:
      - /platform/fan-tray[id=*]/oper-state
    context:
      - /platform/fan-tray
    data:
      - indexes:
          - name: fanTrayID
            syntax: octet string
        objects:
          - name: fanTrayID
            oid: 1.3.6.1.4.1.6527.115.114.108.105.110.117.120.10.5
            syntax: octet string
          - name: fanTrayOperState
            oid: 1.3.6.1.4.1.6527.115.114.108.105.110.117.120.10.6
            syntax: integer
```

---

## Example Trap Output

```json
{
  "traps": [
    {
      "trap": "FanTrayDown",
      "indexes": {"fanTrayID": "1"},
      "objects": {
        "fanTrayID": "1",
        "fanTrayOperState": 2
      }
    }
  ]
}
```
---

## License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.
