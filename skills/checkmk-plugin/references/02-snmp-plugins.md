# CheckMK SNMP Plugin Development
## Network Device Monitoring via SNMP

### Quick Start - Minimal SNMP Plugin

```python
from cmk.agent_based.v2 import (
    SimpleSNMPSection,
    SNMPTree,
    SNMPDetectSpecification,
    CheckPlugin,
    Result,
    Service,
    State,
    exists,
)

def parse_my_device(string_table):
    if not string_table or not string_table[0]:
        return {}
    return {"value": string_table[0][0]}

# CRITICAL: Must start with snmp_section_
snmp_section_my_device = SimpleSNMPSection(
    name="my_device",
    parse_function=parse_my_device,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.12345",
        oids=["1.0"],  # Fetches .1.3.6.1.4.1.12345.1.0
    ),
    detect=SNMPDetectSpecification(
        exists(".1.3.6.1.4.1.12345.1.0")
    ),
)

def discover_my_device(section):
    if section:
        yield Service()

def check_my_device(section):
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data")
        return
    yield Result(state=State.OK, summary=f"Value: {section['value']}")

check_plugin_my_device = CheckPlugin(
    name="my_device",
    service_name="My Device",
    sections=["my_device"],
    discovery_function=discover_my_device,
    check_function=check_my_device,
)
```

### SimpleSNMPSection vs SNMPSection

| Feature | SimpleSNMPSection | SNMPSection |
|---------|------------------|-------------|
| Tables | Single table/OIDs | Multiple tables |
| Parse function | `parse(string_table)` | `parse(string_tables)` |
| Use case | Simple devices | Complex devices |

### SimpleSNMPSection - Single Table

```python
from cmk.agent_based.v2 import SimpleSNMPSection, SNMPTree, OIDEnd

def parse_interfaces(string_table):
    """Parse interface table"""
    interfaces = {}
    for line in string_table:
        if len(line) >= 4:
            index = line[0]  # From OIDEnd()
            interfaces[f"if_{index}"] = {
                "name": line[1],
                "status": line[2],
                "speed": int(line[3]) if line[3].isdigit() else 0,
            }
    return interfaces

snmp_section_interfaces = SimpleSNMPSection(
    name="interfaces",
    parse_function=parse_interfaces,
    fetch=SNMPTree(
        base=".1.3.6.1.2.1.2.2.1",  # IF-MIB
        oids=[
            OIDEnd(),    # Index from OID
            "2",         # ifDescr
            "8",         # ifOperStatus
            "5",         # ifSpeed
        ],
    ),
    detect=SNMPDetectSpecification(
        exists(".1.3.6.1.2.1.1.1.0")  # sysDescr
    ),
)
```

### SNMPSection - Multiple Tables

```python
from cmk.agent_based.v2 import SNMPSection

def parse_complex(string_tables):
    """Parse multiple tables
    Args:
        string_tables: List of tables, one per SNMPTree
    """
    parsed = {}
    
    # First table
    if string_tables[0]:
        parsed["system"] = {
            "name": string_tables[0][0][0],
            "location": string_tables[0][0][1],
        }
    
    # Second table
    if len(string_tables) > 1:
        parsed["components"] = {}
        for line in string_tables[1]:
            parsed["components"][line[0]] = {
                "name": line[1],
                "status": line[2],
            }
    
    return parsed

snmp_section_complex = SNMPSection(
    name="complex",
    parse_function=parse_complex,
    fetch=[
        SNMPTree(
            base=".1.3.6.1.2.1.1",
            oids=["5.0", "6.0"],  # sysName, sysLocation
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.12345.2.1",
            oids=[OIDEnd(), "2", "3"],  # ID, name, status
        ),
    ],
    detect=SNMPDetectSpecification(
        exists(".1.3.6.1.4.1.12345.1.0")
    ),
)
```

### Detection Specifications

**⚠️ CRITICAL**: Make your detection specific to avoid false positives! A generic detection like `exists(".1.3.6.1.2.1.1.1.0")` will match ALL SNMP devices. Always use vendor-specific OIDs or unique string patterns.

```python
from cmk.agent_based.v2 import (
    all_of, any_of, exists, equals, contains,
    startswith, endswith, matches,
    not_exists, not_contains, not_equals,
)

# ❌ BAD - Too generic, matches any SNMP device
detect=SNMPDetectSpecification(
    exists(".1.3.6.1.2.1.1.1.0")  # sysDescr exists on everything!
)

# ✅ GOOD - Specific to device/vendor
detect=SNMPDetectSpecification(
    contains(".1.3.6.1.2.1.1.1.0", "Wiseway3")  # Specific model
)

# ✅ GOOD - Vendor-specific OID
detect=SNMPDetectSpecification(
    exists(".1.3.6.1.4.1.12345.1.0")  # Enterprise OID unique to vendor
)

# Value check
detect=SNMPDetectSpecification(
    equals(".1.3.6.1.2.1.1.1.0", "MyDevice v1.0")
)

# Multiple conditions for specificity
detect=SNMPDetectSpecification(
    all_of(
        exists(".1.3.6.1.2.1.1.1.0"),
        contains(".1.3.6.1.2.1.1.1.0", "Switch"),
        not_contains(".1.3.6.1.2.1.1.1.0", "obsolete"),
    )
)

# Alternative models from same vendor
detect=SNMPDetectSpecification(
    any_of(
        startswith(".1.3.6.1.2.1.1.1.0", "Cisco"),
        matches(".1.3.6.1.2.1.1.1.0", r".*[Cc]isco.*"),
    )
)

# Nested conditions for exact matching
detect=SNMPDetectSpecification(
    all_of(
        exists(".1.3.6.1.4.1.9.1.1.0"),  # Cisco enterprise OID
        any_of(
            contains(".1.3.6.1.2.1.1.1.0", "IOS"),
            contains(".1.3.6.1.2.1.1.1.0", "NX-OS"),
        ),
    )
)
```

### Special OID Types

#### OIDEnd - Get Index/Suffix
```python
# Walking .1.3.6.1.4.1.12345.1.2.1:
# .1.3.6.1.4.1.12345.1.2.1.1 → OIDEnd = "1"
# .1.3.6.1.4.1.12345.1.2.1.2 → OIDEnd = "2"

fetch=SNMPTree(
    base=".1.3.6.1.4.1.12345.1.2.1",
    oids=[
        OIDEnd(),  # Gets index
        "2",       # Gets .../2.<index>
    ],
)
```

#### OIDBytes - Binary Data
```python
from cmk.agent_based.v2 import OIDBytes

# For MAC addresses
fetch=SNMPTree(
    base=".1.3.6.1.2.1.2.2.1",
    oids=[
        OIDBytes("6"),  # MAC as byte list
    ],
)

def parse_mac(string_table):
    for line in string_table:
        if line[0]:  # List of integers
            mac = ":".join(f"{b:02x}" for b in line[0])
```

#### OIDCached - Large/Static Data
```python
from cmk.agent_based.v2 import OIDCached

fetch=SNMPTree(
    base=".1.3.6.1.4.1.12345",
    oids=[
        "1.0",                # Normal fetch
        OIDCached("2.0"),     # Cached
    ],
)
```

### Multi-Item Services

```python
def discover_interfaces(section):
    """One service per interface"""
    for if_name, if_data in section.items():
        if if_data.get("status") != "down":
            yield Service(
                item=if_name,
                parameters={"speed": if_data.get("speed", 0)},
            )

def check_interface(item, params, section):
    """Check specific interface"""
    if item not in section:
        yield Result(state=State.UNKNOWN, summary=f"{item} not found")
        return
    
    if_data = section[item]
    status = if_data.get("status")
    
    state = State.OK if status == "up" else State.CRIT
    yield Result(state=state, summary=f"Status: {status}")
    yield Metric("speed", if_data.get("speed", 0))

check_plugin_interfaces = CheckPlugin(
    name="interfaces",
    service_name="Interface %s",  # %s = item
    discovery_function=discover_interfaces,
    check_function=check_interface,
    sections=["interfaces"],
)
```

### Complete UPS Example

```python
from cmk.agent_based.v2 import (
    SimpleSNMPSection, SNMPTree, SNMPDetectSpecification,
    CheckPlugin, Result, Service, State, Metric,
    check_levels, render, all_of, contains, exists,
)

def parse_ups(string_table):
    if not string_table or not string_table[0]:
        return {}
    
    row = string_table[0]
    status_map = {
        "1": "unknown", "2": "onLine", "3": "onBattery",
        "4": "onBoost", "5": "sleeping", "6": "bypass",
    }
    
    return {
        "status": status_map.get(row[0], "unknown"),
        "battery_charge": int(row[1]) if row[1] else 0,
        "runtime_minutes": int(row[2]) if row[2] else 0,
        "input_voltage": float(row[3]) / 10 if row[3] else 0,
    }

snmp_section_ups = SimpleSNMPSection(
    name="ups",
    parse_function=parse_ups,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.318.1.1.1",  # APC MIB
        oids=[
            "4.1.1.0",   # Status
            "2.2.1.0",   # Battery %
            "2.2.3.0",   # Runtime (min)
            "3.3.1.0",   # Input (decivolts)
        ],
    ),
    detect=SNMPDetectSpecification(
        all_of(
            exists(".1.3.6.1.4.1.318.1.1.1.1.1.1.0"),
            contains(".1.3.6.1.2.1.1.1.0", "APC"),
        ),
    ),
)

def check_ups(params, section):
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data")
        return
    
    # Status
    status = section.get("status")
    if status == "onLine":
        state = State.OK
    elif status in ["onBattery", "onBoost"]:
        state = State.WARN
    else:
        state = State.CRIT
    yield Result(state=state, summary=f"Status: {status}")
    
    # Battery charge
    yield from check_levels(
        section.get("battery_charge", 0),
        levels_lower=params.get("battery_lower", ("fixed", (20, 10))),
        metric_name="battery_charge",
        label="Battery",
        render_func=render.percent,
        boundaries=(0, 100),
    )
    
    # Runtime
    runtime_s = section.get("runtime_minutes", 0) * 60
    yield from check_levels(
        runtime_s,
        levels_lower=params.get("runtime_lower", ("fixed", (600, 300))),
        metric_name="runtime",
        label="Runtime",
        render_func=render.timespan,
    )

check_plugin_ups = CheckPlugin(
    name="ups",
    service_name="UPS Status",
    discovery_function=lambda section: [Service()] if section else [],
    check_function=check_ups,
    check_default_parameters={
        "battery_lower": ("fixed", (20, 10)),
        "runtime_lower": ("fixed", (600, 300)),
    },
    sections=["ups"],
)
```

### Testing SNMP Plugins

```bash
# Test connectivity
snmpget -v2c -c public 192.168.1.100 .1.3.6.1.2.1.1.1.0

# Walk tree
snmpwalk -v2c -c public 192.168.1.100 .1.3.6.1.2.1.2.2.1

# CheckMK discovery
cmk --debug -vvI --detect-plugins=my_device hostname

# Force check
cmk --debug -vv --check=my_device hostname
```

### Advanced Pattern: OID Metadata Table

For complex SNMP plugins with many OIDs, use a metadata-driven approach to keep code DRY and maintainable:

```python
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass

# Define conversion functions
def decivolts_to_volts(value: str) -> float:
    return float(value) / 10 if value else 0.0

def centihertz_to_hertz(value: str) -> float:
    return float(value) / 100 if value else 0.0

def minutes_to_seconds(value: str) -> float:
    return float(value) * 60 if value else 0.0

# Value mappings
BATTERY_STATUS_MAP = {
    "1": "unknown",
    "2": "normal",
    "3": "low",
    "4": "depleted",
}

@dataclass
class OIDDefinition:
    """Complete OID metadata"""
    key: str                           # Internal key
    oid: str                          # OID suffix
    description: str                  # Documentation
    output_key: str                   # Key in parsed output
    converter: Optional[Callable] = None  # Scaling function
    mapper: Optional[Dict] = None        # Value mapping
    fallback_for: Optional[str] = None   # Fallback relationship

# Define all OIDs with metadata - ORDER MATTERS!
OID_DEFINITIONS: List[OIDDefinition] = [
    OIDDefinition("model", "2.1.33.1.1.2.0", "upsIdentModel",
                  "model", converter=str),
    OIDDefinition("battery_status", "2.1.33.1.2.1.0", "upsBatteryStatus",
                  "battery_status", mapper=BATTERY_STATUS_MAP),
    OIDDefinition("battery_voltage", "2.1.33.1.2.5.0", "upsBatteryVoltage",
                  "battery_voltage", converter=decivolts_to_volts),
    OIDDefinition("runtime_primary", "4.1.44782.1.4.4.1.17.0", "Runtime (enterprise)",
                  "runtime_seconds", converter=minutes_to_seconds),
    OIDDefinition("runtime_fallback", "2.1.33.1.2.3.0", "Runtime (standard)",
                  "runtime_seconds", converter=minutes_to_seconds,
                  fallback_for="runtime_primary"),
    OIDDefinition("input_frequency", "2.1.33.1.3.3.1.2.1", "Input frequency",
                  "input_frequency", converter=centihertz_to_hertz),
]

def parse_with_metadata(string_table):
    """Generic parser using metadata"""
    if not string_table or not string_table[0]:
        return {}
    
    # Map values to keys
    raw_data = {}
    for idx, value in enumerate(string_table[0]):
        if idx < len(OID_DEFINITIONS):
            raw_data[OID_DEFINITIONS[idx].key] = value
    
    # Process with metadata
    parsed = {}
    for oid_def in OID_DEFINITIONS:
        value = raw_data.get(oid_def.key, "")
        
        # Handle fallbacks
        if oid_def.fallback_for and (not value or value == "0"):
            continue  # Will be handled by primary
        
        if not value or value == "0":
            # Check for fallback
            fallback = next((d for d in OID_DEFINITIONS 
                           if d.fallback_for == oid_def.key), None)
            if fallback:
                value = raw_data.get(fallback.key, "")
        
        # Apply conversion/mapping
        if value and value != "0":
            if oid_def.mapper:
                parsed[oid_def.output_key] = oid_def.mapper.get(value, "unknown")
            elif oid_def.converter:
                try:
                    parsed[oid_def.output_key] = oid_def.converter(value)
                except (ValueError, TypeError):
                    parsed[oid_def.output_key] = 0.0 if oid_def.converter != str else ""
    
    return parsed

snmp_section_ups = SimpleSNMPSection(
    name="ups",
    parse_function=parse_with_metadata,
    fetch=SNMPTree(
        base=".1.3.6.1",
        # OIDs fetched in exact order of definitions
        oids=[oid_def.oid for oid_def in OID_DEFINITIONS],
    ),
    detect=SNMPDetectSpecification(
        contains(".1.3.6.1.2.1.1.1.0", "MyUPS")  # Be specific!
    ),
)
```

**Benefits of this pattern:**
- **Single source of truth**: All OID knowledge in one table
- **DRY**: Conversion functions defined once and reused
- **Maintainable**: Add/remove OIDs by updating the table
- **Self-documenting**: Metadata serves as documentation
- **Type-safe**: Using dataclasses provides structure
- **Order-guaranteed**: List preserves order (unlike dict pre-3.7)

### Best Practices

#### ✅ DO
- Make detection specific to your device/vendor
- Use metadata tables for complex SNMP plugins
- Check sysDescr first (`.1.3.6.1.2.1.1.1.0`) - cached
- Fetch only needed OIDs
- Handle SNMP special values (2147483647 = no data)
- Use enterprise OIDs for detection
- Parse robustly with error handling
- Store metrics in base SI units (seconds, bytes, hertz)

#### ❌ DON'T
- Use generic detection that matches all SNMP devices
- Rely on dictionary ordering without explicit lists
- Fetch entire subtrees unnecessarily
- Use complex regex in detection
- Assume data types
- Forget to check line lengths
- Store non-base units (milliseconds, kilobytes)

### Common OIDs Reference

```python
# System
SYS_DESCR    = ".1.3.6.1.2.1.1.1.0"   # Description
SYS_NAME     = ".1.3.6.1.2.1.1.5.0"   # Name
SYS_LOCATION = ".1.3.6.1.2.1.1.6.0"   # Location

# Interfaces
IF_TABLE     = ".1.3.6.1.2.1.2.2.1"   # Table
IF_DESCR     = ".1.3.6.1.2.1.2.2.1.2" # Description
IF_SPEED     = ".1.3.6.1.2.1.2.2.1.5" # Speed
IF_STATUS    = ".1.3.6.1.2.1.2.2.1.8" # Status

# Host Resources
HR_STORAGE   = ".1.3.6.1.2.1.25.2.3.1"  # Storage
HR_CPU_LOAD  = ".1.3.6.1.2.1.25.3.3.1.2" # CPU
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Not discovered | Check `snmp_section_` prefix, verify OIDs exist |
| No data | Test with snmpwalk, check community/firewall |
| Parse errors | Add logging, check data types |
| Slow discovery | Reduce OIDs, optimize detection |

### See Also
- [04-check-plugins.md](04-check-plugins.md) - Check logic
- [05-metrics-graphing.md](05-metrics-graphing.md) - Visualizations
- [08-testing-debugging.md](08-testing-debugging.md) - Debug techniques