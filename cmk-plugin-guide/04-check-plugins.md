# CheckMK Check Plugin Development
## Data Processing and Service Logic

### Essential Components

Every check plugin requires:
1. **AgentSection/SNMPSection** - Parse raw data
2. **CheckPlugin** - Discovery and check logic
3. **Entry point prefix** - `agent_section_` or `check_plugin_`

### Basic Check Plugin Structure

```python
from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    Metric,
)
from typing import Any, Dict, Mapping

# 1. Parse Function
def parse_my_service(string_table: list[list[str]]) -> Dict[str, Any]:
    """Convert raw data to structured format"""
    parsed = {}
    for line in string_table:
        if len(line) >= 2:
            key, value = line[0], line[1]
            try:
                parsed[key] = float(value) if '.' in value else int(value)
            except ValueError:
                parsed[key] = value
    return parsed

# 2. Agent Section (MUST start with agent_section_)
agent_section_my_service = AgentSection(
    name="my_service",
    parse_function=parse_my_service,
)

# 3. Discovery Function
def discover_my_service(section: Dict[str, Any]) -> DiscoveryResult:
    """Determine what services to create"""
    if section:
        yield Service()  # Single service
        # Or with item for multiple:
        # yield Service(item="instance1")

# 4. Check Function
def check_my_service(section: Dict[str, Any]) -> CheckResult:
    """Evaluate data and determine state"""
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data")
        return
    
    value = section.get("value", 0)
    
    # Determine state
    if value > 100:
        state = State.CRIT
        summary = f"Critical: {value}"
    elif value > 50:
        state = State.WARN
        summary = f"Warning: {value}"
    else:
        state = State.OK
        summary = f"OK: {value}"
    
    yield Result(state=state, summary=summary)
    yield Metric("value", value)

# 5. Check Plugin (MUST start with check_plugin_)
check_plugin_my_service = CheckPlugin(
    name="my_service",
    service_name="My Service",
    sections=["my_service"],
    discovery_function=discover_my_service,
    check_function=check_my_service,
)
```

### Using check_levels Helper

**CRITICAL**: Always use `check_levels` for threshold checking!

```python
from cmk.agent_based.v2 import check_levels, render

def check_with_levels(params: Mapping[str, Any], section: Dict[str, Any]) -> CheckResult:
    value = section.get("cpu_usage", 0)
    
    # check_levels handles everything!
    yield from check_levels(
        value,
        levels_upper=params.get('cpu_levels'),  # Pass directly!
        metric_name="cpu_usage",
        label="CPU usage",
        render_func=render.percent,
        boundaries=(0, 100),
    )
```

### SimpleLevels Format

**⚠️ CRITICAL**: SimpleLevels from rulesets come as `("fixed", (warn, crit))` or `None`

```python
# ✅ CORRECT - Pass parameters directly
def check_my_service(params: Mapping[str, Any], section: Dict[str, Any]) -> CheckResult:
    temperature = section.get("temperature", 0)
    
    yield from check_levels(
        temperature,
        levels_upper=params.get('temp_levels'),  # Direct pass!
        levels_lower=params.get('temp_levels_lower'),  # Direct pass!
        metric_name="temperature",
        label="Temperature",
        render_func=lambda v: f"{v:.1f}°C",
    )

# ❌ WRONG - Don't wrap or extract
storage_levels = params.get('storage_levels')
if isinstance(storage_levels, dict):  # WRONG! It's a tuple!
    levels = storage_levels.get('levels_upper')  # This will fail!
```

### Multi-Item Services

```python
def discover_multi_item(section: Dict[str, Any]) -> DiscoveryResult:
    """Create one service per item"""
    for item_name, item_data in section.items():
        if item_data.get("enabled", True):
            yield Service(
                item=item_name,
                parameters={"speed": item_data.get("speed", 0)}
            )

def check_multi_item(
    item: str,  # Item parameter added!
    params: Mapping[str, Any],
    section: Dict[str, Any]
) -> CheckResult:
    """Check specific item"""
    if item not in section:
        yield Result(state=State.UNKNOWN, summary=f"Item {item} not found")
        return
    
    item_data = section[item]
    yield Result(state=State.OK, summary=f"{item}: {item_data['status']}")
    yield Metric(f"{item}_value", item_data.get("value", 0))

check_plugin_multi_item = CheckPlugin(
    name="multi_item",
    service_name="Item %s",  # %s replaced with item
    discovery_function=discover_multi_item,
    check_function=check_multi_item,
    sections=["my_section"],
    check_ruleset_name="multi_item_params",
)
```

### Parse Function Best Practices

```python
def parse_robust(string_table: list[list[str]]) -> Dict[str, Any]:
    """Robust parsing with error handling"""
    parsed = {}
    
    # Handle empty input
    if not string_table:
        return {}
    
    # Parse with custom separator
    for line in string_table:
        if len(line) < 2:
            continue  # Skip malformed
        
        if line[1] == "ERROR":
            # Structured error
            parsed[line[0]] = {"error": line[2] if len(line) > 2 else "Unknown"}
            continue
        
        try:
            # JSON data
            import json
            parsed[line[0]] = json.loads(line[1])
        except json.JSONDecodeError:
            # Fallback to string
            parsed[line[0]] = line[1]
        except Exception:
            continue  # Skip bad lines
    
    return parsed
```

### Check Function Patterns

#### Basic State Logic
```python
def check_basic(section: Dict[str, Any]) -> CheckResult:
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data")
        return
    
    # Multiple results
    yield Result(state=State.OK, summary="Main status OK")
    yield Result(state=State.OK, notice="Additional info")  # Long output
    
    # Metrics
    yield Metric("metric1", 42)
    yield Metric("metric2", 100, boundaries=(0, 200))
```

#### With Parameters
```python
def check_with_params(
    params: Mapping[str, Any],
    section: Dict[str, Any]
) -> CheckResult:
    # Get parameters with defaults
    warn = params.get("warn_level", 80)
    crit = params.get("crit_level", 90)
    
    value = section.get("value", 0)
    
    # Manual threshold check (when not using check_levels)
    if value >= crit:
        state = State.CRIT
    elif value >= warn:
        state = State.WARN
    else:
        state = State.OK
    
    yield Result(state=state, summary=f"Value: {value}")
    yield Metric("value", value, levels=(warn, crit))
```

#### Using Render Functions
```python
from cmk.agent_based.v2 import render

def check_with_render(section: Dict[str, Any]) -> CheckResult:
    # Built-in render functions
    yield from check_levels(
        section.get("memory_bytes", 0),
        metric_name="memory",
        label="Memory",
        render_func=render.bytes,  # Auto-formats as KiB, MiB, GiB
    )
    
    yield from check_levels(
        section.get("uptime_seconds", 0),
        metric_name="uptime",
        label="Uptime",
        render_func=render.timespan,  # Formats as "2d 3h 15m"
    )
    
    yield from check_levels(
        section.get("cpu_percent", 0),
        metric_name="cpu",
        label="CPU",
        render_func=render.percent,  # Formats as "45.2%"
    )
```

### Default Parameters

```python
check_plugin_with_defaults = CheckPlugin(
    name="my_service",
    service_name="My Service",
    sections=["my_service"],
    discovery_function=discover_my_service,
    check_function=check_my_service,
    check_ruleset_name="my_service_params",
    check_default_parameters={
        # SimpleLevels format
        'cpu_levels': ('fixed', (80.0, 90.0)),
        'memory_levels': ('fixed', (80.0, 90.0)),
        
        # Lower levels
        'temp_levels_upper': ('fixed', (80.0, 90.0)),
        'temp_levels_lower': ('fixed', (10.0, 5.0)),
        
        # No levels
        'disk_levels': None,
        
        # Other parameters
        'check_interval': 60,
        'enabled': True,
    },
)
```

### Advanced Section Features

```python
# With host labels
def host_label_function(section: Dict[str, Any]):
    from cmk.agent_based.v2 import HostLabel
    if section.get("version"):
        yield HostLabel("my_service_version", section["version"])

agent_section_with_labels = AgentSection(
    name="my_service",
    parse_function=parse_my_service,
    host_label_function=host_label_function,
    supersedes=["old_service"],  # Replaces old section
)

# With cluster support
def cluster_check_function(
    params: Mapping[str, Any],
    section: Mapping[str, Dict[str, Any]]  # Node -> section data
) -> CheckResult:
    total = sum(
        node_section.get("value", 0)
        for node_section in section.values()
    )
    yield Result(state=State.OK, summary=f"Cluster total: {total}")
    yield Metric("cluster_total", total)

check_plugin_cluster = CheckPlugin(
    name="my_cluster",
    service_name="Cluster Service",
    sections=["my_section"],
    discovery_function=discover_my_service,
    check_function=check_my_service,
    cluster_check_function=cluster_check_function,
)
```

### Complete Example with All Features

```python
from cmk.agent_based.v2 import (
    AgentSection, CheckPlugin, CheckResult, DiscoveryResult,
    Result, Service, State, Metric, HostLabel,
    check_levels, render,
)
import json

def parse_advanced(string_table):
    """Parse with JSON support"""
    parsed = {}
    for line in string_table:
        if len(line) == 2 and not line[1].startswith("ERROR"):
            try:
                parsed[line[0]] = json.loads(line[1])
            except json.JSONDecodeError:
                parsed[line[0]] = {"raw": line[1]}
    return parsed

def discover_advanced(section):
    """Discover services"""
    for item in section:
        if section[item].get("enabled", True):
            yield Service(item=item)

def check_advanced(item, params, section):
    """Check with all features"""
    if item not in section:
        yield Result(state=State.UNKNOWN, summary=f"{item} not found")
        return
    
    data = section[item]
    
    # Status check
    status = data.get("status", "unknown")
    if status == "ok":
        yield Result(state=State.OK, summary=f"Status: {status}")
    else:
        yield Result(state=State.WARN, summary=f"Status: {status}")
    
    # Metrics with check_levels
    yield from check_levels(
        data.get("cpu", 0),
        levels_upper=params.get('cpu_levels'),
        metric_name="cpu",
        label="CPU usage",
        render_func=render.percent,
    )
    
    yield from check_levels(
        data.get("memory", 0),
        levels_upper=params.get('memory_levels'),
        metric_name="memory",
        label="Memory",
        render_func=render.bytes,
    )

agent_section_advanced = AgentSection(
    name="advanced",
    parse_function=parse_advanced,
)

check_plugin_advanced = CheckPlugin(
    name="advanced",
    service_name="Advanced %s",
    sections=["advanced"],
    discovery_function=discover_advanced,
    check_function=check_advanced,
    check_ruleset_name="advanced_params",
    check_default_parameters={
        'cpu_levels': ('fixed', (80.0, 90.0)),
        'memory_levels': ('fixed', (8*1024**3, 10*1024**3)),  # 8GB, 10GB
    },
)
```

### See Also
- [05-metrics-graphing.md](05-metrics-graphing.md) - Visualizing metrics
- [06-rulesets.md](06-rulesets.md) - GUI configuration
- [08-testing-debugging.md](08-testing-debugging.md) - Testing check plugins