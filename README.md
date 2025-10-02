# SR Linux SNMP Framework

This project provides **custom SNMP trap implementations for Nokia SR Linux**.  
It monitors the YANG state paths for **Fan Trays** and **Power Supplies**:

```bash
/platform/fan-tray[id=*]/oper-state
/platform/power-supply[id=*]/oper-state
```

and generates SNMP traps when their operational state changes (**Up = 1, Down = 2**).

---

## 📖 Background: SNMP Framework in SR Linux

Nokia SR Linux includes a flexible **SNMP framework** that allows operators to:

- Map **YANG state paths** to **SNMP OIDs**.
- Generate **custom SNMP traps** when specific conditions occur.
- Extend monitoring beyond standard MIBs by defining **YAML trap definitions** and **MicroPython scripts**.

### Why is this useful?

- **Integration**: Works with existing NMS/OSS systems that rely on SNMP traps.
- **Flexibility**: Operators can add traps for any YANG path, not only predefined MIBs.
- **Debugging support**: Optional debug mode outputs JSON input/output for troubleshooting.

---

## ✨ Features

- Watches both fan tray and power supply operational states.
- Sends:
  - **FanTrayOperState trap** (OID: `.1.3.6.1.4.1.6527.3.1.2.2.1.24.1.1.2`)  
    - `up` → 1, `down` → 2
  - **PowerSupplyOperState trap** (OID: `.1.3.6.1.4.1.6527.3.1.2.2.1.24.9.1.7`)  
    - `up` → 1, `down` → 2
- Lightweight MicroPython handlers (`fan-trap.py`, `power-supply.py`).
- YAML trap definitions separated for clarity (`fan-trap.yaml`, `power-supply.yaml`).

---

## 📂 Repository Contents

```
fan-trap.py          # MicroPython script for fan-tray oper-state
fan-trap.yaml        # Trap definition YAML for fan-tray
power-supply.py      # MicroPython script for power-supply oper-state
power-supply.yaml    # Trap definition YAML for power-supply
README.md            # This documentation
LICENSE              # MIT License (default, feel free to change)
```

---

## 🛠 Installation

### 1. Copy the files to your SR Linux node

```bash
scp fan-trap.py admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
scp fan-trap.yaml admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
scp power-supply.py admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
scp power-supply.yaml admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
```

### 2. Register the trap definitions

Edit `/etc/opt/srlinux/snmp/snmp_files_config.yaml` and add:

```yaml
trap-definitions:
  - scripts/fan-trap.yaml
  - scripts/power-supply.yaml
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

## 📑 fan-trap.yaml (Example)

```yaml
# /etc/opt/srlinux/snmp/scripts/fan-trap.yaml
python-script: fan-trap.py
enabled: true
debug: true

traps:
  - name: tmnxPhysChassisFanOperStatus
    enabled: true
    oid: .1.3.6.1.4.1.6527.3.1.2.2.1.24.1.1.2
    triggers:
      - /platform/fan-tray[id=*]/oper-state
    context:
      - /platform/fan-tray
    data:
      - indexes:
          - name: fanTrayID
            syntax: integer
        objects:
          - name: fanTrayID
            oid: .1.3.6.1.4.1.6527.3.1.2.2.1.24.1.1.2.1
            syntax: integer
          - name: fanTrayOperState
            oid: .1.3.6.1.4.1.6527.3.1.2.2.1.24.1.1.2.2
            syntax: integer
```

---

## 📑 power-supply.yaml (Example)

```yaml
# /etc/opt/srlinux/snmp/scripts/power-supply.yaml
python-script: power-supply.py
enabled: true
debug: true

traps:
  - name: tmnxPhysChassisPowerSupplyOperStatus
    enabled: true
    oid: .1.3.6.1.4.1.6527.3.1.2.2.1.24.9.1.7
    triggers:
      - /platform/power-supply[id=*]/oper-state
    context:
      - /platform/power-supply
    data:
      - indexes:
          - name: powerSupplyID
            syntax: integer
        objects:
          - name: powerSupplyID
            oid: .1.3.6.1.4.1.6527.3.1.2.2.1.24.9.1.7.1
            syntax: integer
          - name: powerSupplyOperState
            oid: .1.3.6.1.4.1.6527.3.1.2.2.1.24.9.1.7.2
            syntax: integer
```

---

## ▶️ Example Trap Output

```json
{
  "traps": [
    {
      "trap": "tmnxPhysChassisFanOperStatus",
      "indexes": {"fanTrayID": 1},
      "objects": {
        "fanTrayID": 1,
        "fanTrayOperState": 1
      }
    },
    {
      "trap": "tmnxPhysChassisPowerSupplyOperStatus",
      "indexes": {"powerSupplyID": 2},
      "objects": {
        "powerSupplyID": 2,
        "powerSupplyOperState": 2
      }
    }
  ]
}
```

---

## 📜 License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.
