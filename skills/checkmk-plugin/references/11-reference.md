# CheckMK API Reference
## Quick Reference Guide

### Import Reference

```python
# CheckMK 2.3.0 - Agent-Based API v2
from cmk.agent_based.v2 import (
    # Sections
    AgentSection,
    SimpleSNMPSection,
    SNMPSection,
    
    # Plugins
    CheckPlugin,
    InventoryPlugin,
    
    # Results
    Result,
    Service,
    State,
    Metric,
    HostLabel,
    
    # Types
    CheckResult,
    DiscoveryResult,
    InventoryResult,
    
    # Helpers
    check_levels,
    get_rate,
    get_value_store,
    render,
    
    # SNMP
    SNMPTree,
    SNMPDetectSpecification,
    OIDEnd,
    OIDBytes,
    OIDCached,
    
    # Detection
    exists,
    equals,
    contains,
    startswith,
    endswith,
    matches,
    all_of,
    any_of,
    not_exists,
    not_contains,
)

# Graphing API v1
from cmk.graphing.v1 import (
    Title,
    graphs,
    metrics,
    perfometers,
)

from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
    IECNotation,
    TimeNotation,
    Metric,
    Unit,
)

from cmk.graphing.v1.graphs import (
    Graph,
    MinimalRange,
    Bidirectional,
)

from cmk.graphing.v1.perfometers import (
    Perfometer,
    FocusRange,
    Closed,
    Stacked,
)

# Rulesets API v1
from cmk.rulesets.v1 import (
    Title,
    Help,
    Label,
    rule_specs,
    form_specs,
)

from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    Integer,
    Float,
    String,
    BooleanChoice,
    SimpleLevels,
    LevelDirection,
    DefaultValue,
    CascadingSingleChoice,
    CascadingSingleChoiceElement,
    List,
    MultipleChoice,
    MultipleChoiceElement,
    RegularExpression,
    TimeSpan,
    TimeMagnitude,
    DataSize,
    validators,
)

from cmk.rulesets.v1.rule_specs import (
    CheckParameters,
    AgentConfig,
    Topic,
    HostAndServiceCondition,
    HostAndItemCondition,
)

# Bakery API v1
from cmk.base.plugins.bakery.bakery_api.v1 import (
    register,
    Plugin,
    PluginConfig,
    OS,
    WindowsConfigEntry,
    FileGenerator,
    ScriptletGenerator,
)
```

### State Constants

```python
State.OK = 0     # Green
State.WARN = 1   # Yellow
State.CRIT = 2   # Red
State.UNKNOWN = 3  # Gray
```

### Color Constants

```python
# Basic colors
Color.BLUE, Color.GREEN, Color.RED
Color.ORANGE, Color.YELLOW, Color.PURPLE
Color.CYAN, Color.PINK, Color.BROWN
Color.GRAY, Color.BLACK, Color.WHITE

# Light variants
Color.LIGHT_BLUE, Color.LIGHT_GREEN, Color.LIGHT_RED
Color.LIGHT_ORANGE, Color.LIGHT_YELLOW, Color.LIGHT_PURPLE
Color.LIGHT_CYAN, Color.LIGHT_PINK, Color.LIGHT_BROWN
Color.LIGHT_GRAY

# Dark variants
Color.DARK_BLUE, Color.DARK_GREEN, Color.DARK_RED
Color.DARK_ORANGE, Color.DARK_YELLOW, Color.DARK_PURPLE
Color.DARK_CYAN, Color.DARK_PINK, Color.DARK_BROWN
Color.DARK_GRAY
```

### Common SNMP OIDs

```python
# System MIB-2
SYS_DESCR    = ".1.3.6.1.2.1.1.1.0"   # System description
SYS_OBJECTID = ".1.3.6.1.2.1.1.2.0"   # System OID
SYS_UPTIME   = ".1.3.6.1.2.1.1.3.0"   # Uptime
SYS_CONTACT  = ".1.3.6.1.2.1.1.4.0"   # Contact
SYS_NAME     = ".1.3.6.1.2.1.1.5.0"   # Name
SYS_LOCATION = ".1.3.6.1.2.1.1.6.0"   # Location

# Interface MIB
IF_TABLE     = ".1.3.6.1.2.1.2.2.1"    # Interface table
IF_DESCR     = ".1.3.6.1.2.1.2.2.1.2"  # Description
IF_TYPE      = ".1.3.6.1.2.1.2.2.1.3"  # Type
IF_MTU       = ".1.3.6.1.2.1.2.2.1.4"  # MTU
IF_SPEED     = ".1.3.6.1.2.1.2.2.1.5"  # Speed
IF_PHYS_ADDR = ".1.3.6.1.2.1.2.2.1.6"  # MAC address
IF_ADMIN_STATUS = ".1.3.6.1.2.1.2.2.1.7"  # Admin status
IF_OPER_STATUS  = ".1.3.6.1.2.1.2.2.1.8"  # Operational status
IF_IN_OCTETS    = ".1.3.6.1.2.1.2.2.1.10" # In bytes
IF_OUT_OCTETS   = ".1.3.6.1.2.1.2.2.1.16" # Out bytes
IF_IN_ERRORS    = ".1.3.6.1.2.1.2.2.1.14" # In errors
IF_OUT_ERRORS   = ".1.3.6.1.2.1.2.2.1.20" # Out errors

# Host Resources MIB
HR_STORAGE_TABLE = ".1.3.6.1.2.1.25.2.3.1"  # Storage
HR_DEVICE_TABLE  = ".1.3.6.1.2.1.25.3.2.1"  # Devices
HR_CPU_LOAD      = ".1.3.6.1.2.1.25.3.3.1.2" # CPU load

# UPS MIB (RFC 1628)
UPS_BATTERY_STATUS    = ".1.3.6.1.2.1.33.1.2.1.0"
UPS_SECONDS_ON_BATTERY = ".1.3.6.1.2.1.33.1.2.2.0"
UPS_BATTERY_VOLTAGE   = ".1.3.6.1.2.1.33.1.2.5.0"
UPS_BATTERY_CURRENT   = ".1.3.6.1.2.1.33.1.2.6.0"
UPS_OUTPUT_VOLTAGE    = ".1.3.6.1.2.1.33.1.4.4.1.2"
UPS_OUTPUT_CURRENT    = ".1.3.6.1.2.1.33.1.4.4.1.3"
UPS_OUTPUT_POWER      = ".1.3.6.1.2.1.33.1.4.4.1.4"
```

### Checkman Documentation Format

```
title: Check Title: Description
agents: linux, windows, snmp
catalog: os/storage
license: GPL
distribution: check_mk
description:
 Detailed description of what the check does.
 Multiple paragraphs supported.
 
 Use {braces} for tool/command names.
 
item:
 Description of the item if check uses items
 
discovery:
 How services are discovered
 
perfdata:
 Description of performance data/metrics
 
parameters:
 Description of configurable parameters
```

### Useful Commands

```bash
# Plugin development
cmk -R                    # Reload configuration
cmk -II hostname         # Rediscover services
cmk -v --debug hostname  # Debug check execution
cmk -d hostname          # Dump agent output
cmk --detect-plugins=name hostname  # Test detection

# SNMP testing
snmpget -v2c -c public host OID
snmpwalk -v2c -c public host OID
snmpbulkwalk -v2c -c public host OID

# Bakery
cmk -P bake --force      # Bake all agents
cmk -P bake --host name  # Bake specific host
cmk -P deploy --host name # Deploy agent

# Testing
pytest plugin_test.py -v
python3 -m py_compile plugin.py  # Syntax check

# Debugging
cmk --debug -vvI hostname
cmk --debug --checks=my_check hostname
tail -f ~/var/log/cmc.log
```

### Directory Quick Reference

```
~/local/lib/python3/
├── cmk_addons/plugins/<name>/
│   ├── agent_based/     # Check plugins
│   ├── graphing/        # Graphs
│   ├── rulesets/        # GUI config
│   └── checkman/        # Documentation
└── cmk/base/cee/plugins/bakery/  # Bakery

~/local/share/check_mk/
└── agents/plugins/      # Agent plugins
```

### Entry Point Prefixes

| Prefix | Purpose |
|--------|---------|
| `agent_section_` | Agent data parser |
| `snmp_section_` | SNMP data parser |
| `check_plugin_` | Check logic |
| `inventory_plugin_` | Inventory |
| `rule_spec_` | Ruleset |
| `metric_` | Metric definition |
| `graph_` | Graph definition |
| `perfometer_` | Perfometer |

### SimpleLevels Format

```python
# From GUI/ruleset
("fixed", (warn, crit))  # Configured levels
None                     # No levels

# Usage - pass directly!
yield from check_levels(
    value,
    levels_upper=params.get('levels'),  # Don't unwrap!
    metric_name="metric",
)
```

### Render Functions

```python
render.percent(50.5)     # "50.5%"
render.bytes(1024)       # "1.00 KiB"
render.timespan(3661)    # "1 hour 1 minute"
render.date(1640000000)  # "2021-12-20"
render.datetime(1640000000)  # "2021-12-20 12:00:00"
```

### See Also
- [00-index.md](00-index.md) - Document index
- [01-quickstart.md](01-quickstart.md) - Quick start
- [08-testing-debugging.md](08-testing-debugging.md) - Debug commands