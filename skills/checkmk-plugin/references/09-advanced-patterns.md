# CheckMK Advanced Patterns
## Complex Scenarios and Solutions

### Cluster Support

```python
from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    Result,
    State,
    Metric,
)
from typing import Mapping

def cluster_check_my_service(
    params: Mapping[str, Any],
    section: Mapping[str, Dict[str, Any]]  # node_name -> section_data
) -> CheckResult:
    """Aggregate data from cluster nodes"""
    if not section:
        yield Result(state=State.UNKNOWN, summary="No cluster data")
        return
    
    # Aggregate metrics
    total_cpu = 0
    total_memory = 0
    node_count = 0
    failed_nodes = []
    
    for node_name, node_data in section.items():
        if not node_data:
            failed_nodes.append(node_name)
            continue
        
        total_cpu += node_data.get("cpu", 0)
        total_memory += node_data.get("memory", 0)
        node_count += 1
    
    # Determine cluster state
    if node_count == 0:
        yield Result(state=State.CRIT, summary="All nodes failed")
        return
    elif failed_nodes:
        yield Result(
            state=State.WARN,
            summary=f"Failed nodes: {', '.join(failed_nodes)}"
        )
    
    # Average metrics
    avg_cpu = total_cpu / node_count
    avg_memory = total_memory / node_count
    
    yield Result(
        state=State.OK,
        summary=f"Cluster OK ({node_count} nodes)"
    )
    yield Metric("cluster_cpu_avg", avg_cpu)
    yield Metric("cluster_memory_total", total_memory)

check_plugin_cluster = CheckPlugin(
    name="my_cluster",
    service_name="Cluster Service",
    sections=["my_section"],
    discovery_function=discover_my_service,
    check_function=check_my_service,
    cluster_check_function=cluster_check_my_service,
)
```

### Inventory Integration

```python
from cmk.agent_based.v2 import (
    InventoryPlugin,
    InventoryResult,
    TableRow,
    Attributes,
)

def inventory_my_service(section: Dict[str, Any]) -> InventoryResult:
    """Add to HW/SW inventory"""
    if not section:
        return
    
    # Add attributes
    yield Attributes(
        path=["software", "applications", "my_service"],
        inventory_attributes={
            "version": section.get("version", "unknown"),
            "status": section.get("status", "unknown"),
            "install_date": section.get("install_date"),
        },
    )
    
    # Add table rows for components
    if "components" in section:
        for comp in section["components"]:
            yield TableRow(
                path=["software", "applications", "my_service", "components"],
                key_columns={"name": comp["name"]},
                inventory_columns={
                    "version": comp.get("version"),
                    "status": comp.get("status"),
                    "size": comp.get("size", 0),
                },
            )

inventory_plugin_my_service = InventoryPlugin(
    name="my_service",
    inventory_function=inventory_my_service,
    sections=["my_service"],
)
```

### Host Labels

```python
from cmk.agent_based.v2 import HostLabel

def host_label_my_service(section: Dict[str, Any]):
    """Generate host labels for filtering"""
    if not section:
        return
    
    # Version label
    if "version" in section:
        yield HostLabel("my_service_version", section["version"])
    
    # Type label
    service_type = section.get("type", "standard")
    yield HostLabel("my_service_type", service_type)
    
    # Conditional labels
    if section.get("cluster_enabled"):
        yield HostLabel("my_service_cluster", "yes")
    
    if section.get("cpu", 0) > 80:
        yield HostLabel("high_load", "yes")

agent_section_with_labels = AgentSection(
    name="my_service",
    parse_function=parse_my_service,
    host_label_function=host_label_my_service,
)
```

### Time Unit Handling

```python
# CRITICAL: Always store in base SI units!

# Conversion constants
NANOSECONDS_PER_SECOND = 1_000_000_000
MICROSECONDS_PER_SECOND = 1_000_000
MILLISECONDS_PER_SECOND = 1_000

# Conversion functions
def ns_to_s(ns: float) -> float:
    """Convert nanoseconds to seconds"""
    return ns / NANOSECONDS_PER_SECOND

def ms_to_s(ms: float) -> float:
    """Convert milliseconds to seconds"""
    return ms / MILLISECONDS_PER_SECOND

def check_with_conversions(section):
    # External tool gives nanoseconds
    latency_ns = section.get('latency_ns', 0)
    latency_s = ns_to_s(latency_ns) if latency_ns else 0
    
    # Store in seconds!
    yield Metric("latency", latency_s)
    
    # Display nicely
    yield from check_levels(
        latency_s,
        levels_upper=("fixed", (0.05, 0.1)),  # 50ms, 100ms
        metric_name="latency",
        render_func=render.timespan,
    )
```

### Custom Render Functions

```python
def _render_iops(value: float) -> str:
    """Format I/O operations per second"""
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M ops/s"
    elif value >= 1_000:
        return f"{value/1_000:.1f}K ops/s"
    else:
        return f"{value:.0f} ops/s"

def _render_temperature_c(value: float) -> str:
    """Format temperature with color hints"""
    if value > 80:
        return f"{value:.1f}°C (high!)"
    elif value < 10:
        return f"{value:.1f}°C (low!)"
    else:
        return f"{value:.1f}°C"

# Usage
yield from check_levels(
    iops,
    levels_upper=("fixed", (10000, 20000)),
    metric_name="iops",
    render_func=_render_iops,
    label="I/O Operations",
)
```

### Dynamic Service Discovery

```python
def discover_dynamic(section: Dict[str, Any]) -> DiscoveryResult:
    """Discover services based on data"""
    # Discover based on type
    for item_name, item_data in section.items():
        item_type = item_data.get("type")
        
        if item_type == "database":
            # Database service
            yield Service(
                item=item_name,
                parameters={
                    "check_type": "database",
                    "connection_limit": 100,
                }
            )
        elif item_type == "webserver":
            # Web service
            yield Service(
                item=item_name,
                parameters={
                    "check_type": "webserver",
                    "response_time_limit": 1.0,
                }
            )
        else:
            # Generic service
            yield Service(item=item_name)
```

### Predictive Monitoring

```python
from cmk.agent_based.v2 import get_value_store

def check_with_prediction(section):
    """Track trends over time"""
    value_store = get_value_store()
    current_value = section.get("metric", 0)
    
    # Store history
    history = value_store.get("history", [])
    history.append(current_value)
    history = history[-100:]  # Keep last 100
    value_store["history"] = history
    
    # Calculate trend
    if len(history) >= 10:
        recent_avg = sum(history[-10:]) / 10
        older_avg = sum(history[-20:-10]) / 10 if len(history) >= 20 else recent_avg
        
        trend = recent_avg - older_avg
        if trend > 10:
            yield Result(
                state=State.WARN,
                summary=f"Increasing trend: +{trend:.1f}/check"
            )
    
    yield Metric("metric", current_value)
```

### Multi-Protocol Support

```python
# Support both agent and SNMP
from cmk.agent_based.v2 import (
    AgentSection,
    SimpleSNMPSection,
    SNMPTree,
)

# Agent section
agent_section_my_device = AgentSection(
    name="my_device",
    parse_function=parse_agent_data,
)

# SNMP section (same name!)
snmp_section_my_device = SimpleSNMPSection(
    name="my_device",
    parse_function=parse_snmp_data,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.12345",
        oids=["1.0", "2.0"],
    ),
    detect=SNMPDetectSpecification(
        exists(".1.3.6.1.4.1.12345.1.0")
    ),
)

# Single check plugin works with both
check_plugin_my_device = CheckPlugin(
    name="my_device",
    service_name="My Device",
    sections=["my_device"],  # Works with both sources
    discovery_function=discover_my_device,
    check_function=check_my_device,
)
```

### Performance Optimization

```python
import functools
import time

# Cache expensive operations
@functools.lru_cache(maxsize=128)
def expensive_calculation(value):
    # Simulate expensive operation
    time.sleep(0.1)
    return value ** 2

def parse_optimized(string_table):
    """Optimized parsing"""
    # Pre-allocate
    result = {}
    
    # Use generator for memory efficiency
    valid_lines = (
        line for line in string_table
        if len(line) >= 2 and not line[1].startswith("ERROR")
    )
    
    # Batch process
    for line in valid_lines:
        try:
            # Avoid repeated lookups
            key = line[0]
            value = line[1]
            
            # Parse once
            if value.isdigit():
                result[key] = int(value)
            elif '.' in value:
                result[key] = float(value)
            else:
                result[key] = value
        except (ValueError, IndexError):
            continue
    
    return result
```

### Error Recovery

```python
def check_with_recovery(section):
    """Graceful error recovery"""
    # Track errors
    errors = []
    results = []
    
    # Check each metric independently
    metrics_to_check = [
        ("cpu", "CPU Usage", render.percent),
        ("memory", "Memory", render.bytes),
        ("disk", "Disk Usage", render.percent),
    ]
    
    for metric_name, label, render_func in metrics_to_check:
        try:
            value = section.get(metric_name)
            if value is not None:
                results.extend(check_levels(
                    value,
                    metric_name=metric_name,
                    label=label,
                    render_func=render_func,
                ))
            else:
                errors.append(f"{label} missing")
        except Exception as e:
            errors.append(f"{label}: {e}")
    
    # Report errors if any
    if errors:
        yield Result(
            state=State.WARN,
            summary=f"Errors: {'; '.join(errors)}"
        )
    
    # Still yield successful results
    yield from results
```

### See Also
- [04-check-plugins.md](04-check-plugins.md) - Basic patterns
- [05-metrics-graphing.md](05-metrics-graphing.md) - Visualization
- [10-examples.md](10-examples.md) - Complete examples