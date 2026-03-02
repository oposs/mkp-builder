# Checkmk Metric Renaming Guide

> **Prerequisites**: Understand CheckMK naming conventions first! See **[01-quickstart.md](01-quickstart.md#naming-conventions-critical)** for why proper metric naming matters.

## Quick Reference: Rename Metrics While Preserving History

### Core Concept
Checkmk's Translation system allows metric renaming without data loss. RRD files keep original names; translations map old→new during retrieval.

### When You Need This
- Adding prefixes to old unprefixed metrics (e.g., `temp` → `acme_device_temp`)
- Fixing wrong units (e.g., milliseconds → seconds)
- Standardizing metric names across plugin versions
- See [01-quickstart.md](01-quickstart.md) for proper naming from the start!

---

## Implementation Steps

### 1. Create Translation File

**Location:** `cmk/plugins/<your_plugin>/graphing/translations.py`

**Template:**
```python
from cmk.graphing.v1 import translations

translation_<check_name> = translations.Translation(
    name="<check_name>",
    check_commands=[translations.PassiveCheck("<check_name>")],
    translations={
        "old_name": translations.RenameToAndScaleBy("new_name", scale_factor),
    },
)
```

### 2. Translation Types

| Operation | Class | Example |
|-----------|-------|---------|
| Rename only | `RenameTo("new")` | `"rpm": RenameTo("fan")` |
| Scale only | `ScaleBy(factor)` | `"lat": ScaleBy(0.001)` # ms→s |
| Both | `RenameToAndScaleBy("new", factor)` | `"perf": RenameToAndScaleBy("cpu_load", 0.01)` |

---

## Real-World Examples

### Example 1: Simple Rename
```python
translation_genau_fan = translations.Translation(
    name="genau_fan",
    check_commands=[translations.PassiveCheck("genau_fan")],
    translations={"rpm": translations.RenameTo("fan")},
)
```

### Example 2: Multiple Metrics with Scaling
```python
translation_ibm_svc_nodestats_disk_latency = translations.Translation(
    name="ibm_svc_nodestats_disk_latency",
    check_commands=[translations.PassiveCheck("ibm_svc_nodestats_disk_latency")],
    translations={
        "read_latency": translations.ScaleBy(0.001),   # ms → seconds
        "write_latency": translations.ScaleBy(0.001),
    },
)
```

### Example 3: Rename + Scale
```python
translation_citrix_serverload = translations.Translation(
    name="citrix_serverload",
    check_commands=[translations.PassiveCheck("citrix_serverload")],
    translations={"perf": translations.RenameToAndScaleBy("citrix_load", 0.01)},
)
```

### Example 4: Adding Prefixes to Multiple Metrics
```python
translation_tcp_conn_stats = translations.Translation(
    name="tcp_conn_stats",
    check_commands=[translations.PassiveCheck("tcp_conn_stats")],
    translations={
        "ESTABLISHED": translations.RenameTo("tcp_established"),
        "LISTEN": translations.RenameTo("tcp_listen"),
        "CLOSE_WAIT": translations.RenameTo("tcp_close_wait"),
        "SYN_SENT": translations.RenameTo("tcp_syn_sent"),
    },
)
```

---

## Common Unit Conversions

| From | To | Scale Factor |
|------|-----|--------------|
| milliseconds | seconds | `0.001` |
| seconds | milliseconds | `1000` |
| bytes | kilobytes | `1/1024` or `0.0009765625` |
| kilobytes | bytes | `1024` |
| percent (0-100) | ratio (0-1) | `0.01` |
| ratio (0-1) | percent (0-100) | `100` |
| watts | kilowatts | `0.001` |

---

## Check Command Types

```python
# For standard check plugins (most common)
translations.PassiveCheck("check_name")          # Prefix: check_mk-

# For active checks
translations.ActiveCheck("http")                 # Prefix: check_mk_active-

# For host checks
translations.HostCheckCommand("host-ping")       # Prefix: check-mk-

# For Nagios plugins
translations.NagiosPlugin("check_http")          # Prefix: check_
```

---

## LLM Refactoring Pattern

### Task: "Add plugin-specific prefix to all metrics + fix units"

**Input to LLM:**
```
Plugin: my_device_check
Current metrics:
- temp (Celsius, no prefix)
- load (0-100, should be 0-1)
- latency (ms, should be seconds)
- rpm (no prefix needed)

Required:
1. Add "my_device_" prefix to: temp, load, latency
2. Convert load: 0-100 → 0-1 (scale by 0.01)
3. Convert latency: ms → seconds (scale by 0.001)
4. Keep rpm as-is (already good name)
```

**Expected Output:**
```python
translation_my_device_check = translations.Translation(
    name="my_device_check",
    check_commands=[translations.PassiveCheck("my_device_check")],
    translations={
        "temp": translations.RenameTo("my_device_temp"),
        "load": translations.RenameToAndScaleBy("my_device_load", 0.01),
        "latency": translations.RenameToAndScaleBy("my_device_latency", 0.001),
    },
)
```

---

## Verification Checklist

After creating translation:

1. ✅ Object name starts with `translation_`
2. ✅ File placed in `cmk/plugins/<plugin>/graphing/translations.py`
3. ✅ Imported: `from cmk.graphing.v1 import translations`
4. ✅ Check command name matches your check plugin name
5. ✅ Scale factors are correct (test: old_value × scale = new_value)

**Testing:**
```bash
# Reload GUI
sudo omd restart apache

# Check translation loaded
cmk -vv --list-graphing-plugins | grep translation_<your_name>

# View service graph - verify:
# - New metric names appear
# - Historical data visible
# - Values correct (if scaled)
```

---

## How It Works (Brief)

1. **Collection**: Check outputs metric (old or new name) → RRD stores with original name
2. **Translation Load**: At startup, translations registered to `check_metrics` dict
3. **Retrieval**: When graphing metric "new_name":
   - Reverse translate: find all old names mapping to "new_name"
   - Query ALL relevant RRD datasources (old + new)
   - Merge time series chronologically
   - Apply scaling to each value
4. **Result**: Seamless graph showing all historical data

**Key Insight:** RRD files never renamed. Translation is query-time mapping only.

---

## Plugin Author Use Case: Updating Metric Names in New Plugin Version

### Why Add Translations When Changing Your Plugin?

When you release a new version of your plugin with better metric names, you want:
- **New installations**: Use clean, well-named metrics from the start
- **Existing installations**: See historical data merge seamlessly with new data

### The Data Flow During Transition

```
Timeline: Old Plugin → Translation Added → New Plugin Released
          ────────────────────────────────────────────────────>

Old Plugin (v1.0):
├─ Outputs: Metric("temp", 45.0)
└─ RRD created: service_temp.rrd
   Data: [Day 1 ... Day 100]

Translation Added (with new plugin v2.0):
├─ Plugin now outputs: Metric("device_temperature", 45.0)
├─ Translation: "temp" → "device_temperature"
└─ What happens:
   ├─ OLD RRD (service_temp.rrd) still exists with historical data
   ├─ NEW RRD (service_device_temperature.rrd) created for new data
   └─ Users upgrading from v1.0:
      ├─ Day 1-100: Data in service_temp.rrd (old plugin)
      ├─ Day 101+:  Data in service_device_temperature.rrd (new plugin)
      └─ Graph shows: Continuous line from Day 1 to present!

Retrieval (when user views "device_temperature" graph):
├─ Reverse translation finds: {"device_temperature", "temp"}
├─ Queries BOTH RRD files:
│  ├─ service_temp.rrd → [Day 1 to Day 100 data] (scaled if needed)
│  └─ service_device_temperature.rrd → [Day 101+ data]
├─ Merges chronologically: old RRD fills the gap before new RRD starts
└─ Result: One continuous graph with all historical data
```

### Key Points for Plugin Authors

1. **Translation bridges the gap**: Old RRD (`temp.rrd`) provides historical data; new RRD (`device_temperature.rrd`) provides current data
2. **Merge happens automatically**: When users graph `device_temperature`, the system queries both RRD files and merges them
3. **No user intervention needed**: Users upgrading from v1.0 to v2.0 see uninterrupted graphs
4. **New installations are clean**: Fresh installs only create `device_temperature.rrd` (never see old names)

### Without Translation (What Goes Wrong)

```
Old Plugin v1.0 outputs: Metric("temp", 45.0)
RRD: service_temp.rrd [Day 1 ... Day 100]

New Plugin v2.0 outputs: Metric("device_temperature", 45.0)
No translation added!

Result:
├─ service_temp.rrd exists but is orphaned (no longer queried)
├─ service_device_temperature.rrd starts fresh from Day 101
└─ User sees: Graph starting at Day 101 only (100 days of data LOST from view!)
```

### Best Practice: Always Add Translation When Renaming

```python
# In your plugin v2.0 graphing/translations.py
translation_my_device = translations.Translation(
    name="my_device",
    check_commands=[translations.PassiveCheck("my_device")],
    translations={
        # Map OLD names to NEW names
        "temp": translations.RenameTo("device_temperature"),
        "load": translations.RenameToAndScaleBy("device_load", 0.01),  # Also fix units!
        "rpm": translations.RenameTo("device_fan_rpm"),
    },
)
```

This ensures users upgrading from v1.0 see their historical data merged with new data under the new metric names.

---

## Important Notes

- **No data migration needed** - old RRD files stay in place
- **Both names work** during transition period
- **Update check plugin eventually** to output new names (but not urgent)
- **Deprecation**: After ~1 year, can mark translation deprecated; data remains but won't be auto-queried
- **Regex support**: Use `"~pattern"` for pattern matching (e.g., `"~.*_temp"`)

---

## File Locations Reference

```
cmk/plugins/<plugin>/
├── agent_based/
│   └── <plugin>.py              # Check plugin (yields Metrics)
└── graphing/
    ├── metrics.py               # Metric metadata (title, color, unit)
    ├── graphs.py                # Graph definitions
    └── translations.py          # ← CREATE THIS for renaming
```

---

## API Reference (packages/cmk-plugin-apis/cmk/graphing/v1/translations.py)

```python
@dataclass(frozen=True)
class RenameTo:
    metric_name: str

@dataclass(frozen=True)
class ScaleBy:
    factor: int | float

@dataclass(frozen=True)
class RenameToAndScaleBy:
    metric_name: str
    factor: int | float

@dataclass(frozen=True, kw_only=True)
class Translation:
    name: str
    check_commands: Sequence[PassiveCheck | ActiveCheck | HostCheckCommand | NagiosPlugin]
    translations: Mapping[str, RenameTo | ScaleBy | RenameToAndScaleBy]
```

---

## Batch Processing Template (for LLM)

```python
# Template for processing multiple plugins at once
from cmk.graphing.v1 import translations

# Plugin 1
translation_plugin1 = translations.Translation(
    name="plugin1",
    check_commands=[translations.PassiveCheck("plugin1")],
    translations={
        # LLM fills these based on analysis
    },
)

# Plugin 2
translation_plugin2 = translations.Translation(
    name="plugin2",
    check_commands=[translations.PassiveCheck("plugin2")],
    translations={
        # LLM fills these based on analysis
    },
)

# ... repeat for each plugin
```

---

## Common Pitfalls

❌ **Wrong**: Manually renaming RRD files
✅ **Right**: Create Translation entry

❌ **Wrong**: Modifying check plugin first without translation
✅ **Right**: Add translation first, then update check plugin later

❌ **Wrong**: Scale factor inverted (1000 instead of 0.001)
✅ **Right**: Test: `old_value * scale_factor = new_value`

❌ **Wrong**: Object name without `translation_` prefix
✅ **Right**: `translation_my_check = translations.Translation(...)`

---

## End of Guide

**Total concept**: ~100 lines when condensed
**Key files to examine**: `cmk/plugins/collection/graphing/translations.py:1-100`
**API definition**: `packages/cmk-plugin-apis/cmk/graphing/v1/translations.py`
