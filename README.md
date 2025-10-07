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
timetra-fantrap.py          # MicroPython script for fan-tray oper-state
timetra-fantrap.yaml        # Trap definition YAML for fan-tray
timetra-psu.py              # MicroPython script for power-supply oper-state
timetra-psu.yaml            # Trap definition YAML for power-supply
README.md                   # This documentation
LICENSE                     # MIT License (default, feel free to change)
```

---

## 🛠 Installation

### 1. Copy the files to your SR Linux node

```bash
scp timetra-fantrap.py admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
scp timetra-fantrap.yaml admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
scp timetra-psu.py admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
scp timetra-psu.yaml admin@<srlinux-ip>:/etc/opt/srlinux/snmp/scripts/
```

### 2. Register the trap definitions

Edit `/etc/opt/srlinux/snmp/snmp_files_config.yaml` and add:

```yaml
trap-definitions:
  - scripts/timetra-fantrap.yaml
  - scripts/timetra-psu.yaml
```

### 3. Restart the SNMP server

```bash
/tools system app-management application snmp_server-mgmt restart
```

### 4. Configure SNMP trap destination

```bash
enter candidate
set / system snmp trap-group 1 network-instance mgmt
set / system snmp trap-group 1 destination 1 address 192.168.1.1
set / system snmp trap-group 1 destination 1 security-level no-auth-no-priv
set / system snmp trap-group 1 destination 1 community-entry 1 community public
set / system snmp network-instance mgmt admin-state enable
commit now
```

---

## 📜 License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.
