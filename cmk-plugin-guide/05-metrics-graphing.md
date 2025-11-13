# CheckMK Metrics and Graphing
## Visualizations and Performance Data

### ⚠️ CRITICAL: Always Use Base SI Units!

**Store all metrics in base SI units:**
- **Time**: seconds (NOT milliseconds, microseconds, nanoseconds)
- **Data**: bytes (NOT KB, MB, GB)
- **Frequency**: hertz (NOT kHz, MHz)

```python
# ✅ CORRECT - Base units
latency_seconds = latency_ns / 1_000_000_000.0
yield Metric("latency", latency_seconds)

# ❌ WRONG - Non-base units
yield Metric("latency", latency_ns)  # Storing nanoseconds
```

### Metric Naming: Always Use Prefixes!

**⚠️ IMPORTANT**: Always prefix metric names with `mycompany_myplugin_` format!

See **[01-quickstart.md](01-quickstart.md#metric-names-critical)** for complete naming conventions.

**Quick reminder:**
```python
# ❌ WRONG - Generic names
yield Metric("cpu_usage", 45.0)

# ✅ CORRECT - Prefixed
yield Metric("acme_widget_cpu_usage", 45.0)
```

**Why?** CheckMK has ~1,000 built-in metrics. Unprefixed names cause conflicts and can be overridden by CheckMK updates. See [01-quickstart.md](01-quickstart.md) and [13-metric-migration.md](13-metric-migration.md) for details.

### Basic Metric Definition

```python
from cmk.graphing.v1 import Title
from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
    IECNotation,
    TimeNotation,
    Metric,
    Unit,
)

# Define units
unit_percentage = Unit(DecimalNotation("%"))
unit_bytes = Unit(IECNotation("B"))  # Auto-scales: B, KiB, MiB, GiB
unit_seconds = Unit(TimeNotation())  # Auto-scales: ns, µs, ms, s
unit_celsius = Unit(DecimalNotation("°C"))

# Define metrics with mycompany_myplugin prefix
metric_mycompany_myplugin_cpu = Metric(
    name="mycompany_myplugin_cpu",  # Prefixed!
    title=Title("CPU Usage"),
    unit=unit_percentage,
    color=Color.BLUE,
)

metric_mycompany_myplugin_memory = Metric(
    name="mycompany_myplugin_memory",  # Prefixed!
    title=Title("Memory Usage"),
    unit=unit_bytes,
    color=Color.GREEN,
)

metric_mycompany_myplugin_latency = Metric(
    name="mycompany_myplugin_latency",  # Prefixed!
    title=Title("Latency"),
    unit=unit_seconds,  # Expects seconds!
    color=Color.ORANGE,
)
```

### Graph Definitions

```python
from cmk.graphing.v1.graphs import (
    Graph,
    MinimalRange,
    Bidirectional,
)

# Simple graph - use prefixed metric names
graph_performance = Graph(
    name="mycompany_myplugin_performance",
    title=Title("System Performance"),
    simple_lines=[
        "mycompany_myplugin_cpu",
        "mycompany_myplugin_memory",
    ],
    minimal_range=MinimalRange(
        lower=0,
        upper=100,
    ),
)

# Graph with optional metrics
graph_with_optional = Graph(
    name="mycompany_myplugin_operations",
    title=Title("Operations"),
    simple_lines=[
        "mycompany_myplugin_read_ops",
        "mycompany_myplugin_write_ops",
        "mycompany_myplugin_scrub_ops",
    ],
    optional=["mycompany_myplugin_scrub_ops"],  # Only present during scrub
)

# Bidirectional graph (network, I/O)
graph_network = Bidirectional(
    name="mycompany_myplugin_network_traffic",
    title=Title("Network Traffic"),
    lower=Graph(
        name="mycompany_myplugin_network_in",
        title=Title("Inbound"),
        compound_lines=["mycompany_myplugin_bytes_in"],
    ),
    upper=Graph(
        name="mycompany_myplugin_network_out",
        title=Title("Outbound"),
        compound_lines=["mycompany_myplugin_bytes_out"],
    ),
)
```

### Handling Missing Metrics

#### Using float('nan') for Unknown Data
```python
def check_with_nan(section):
    cpu = section.get('cpu_usage')
    if cpu is None:
        # Explicitly mark as unknown
        yield Metric("mycompany_myplugin_cpu", float('nan'))
        yield Result(state=State.UNKNOWN, summary="CPU data not available")
    else:
        yield Metric("mycompany_myplugin_cpu", cpu)
```

#### Optional Metrics in Graphs
```python
# Graph displays even when some metrics missing
graph_adaptive = Graph(
    name="mycompany_myplugin_adaptive",
    title=Title("Adaptive Metrics"),
    simple_lines=[
        "mycompany_myplugin_always_present",
        "mycompany_myplugin_sometimes_present",
    ],
    optional=["mycompany_myplugin_sometimes_present"],  # Won't break graph if missing
)
```

### Unit Conversions

```python
# Conversion helpers
def nanoseconds_to_seconds(ns):
    return ns / 1_000_000_000.0

def milliseconds_to_seconds(ms):
    return ms / 1_000.0

def kilobytes_to_bytes(kb):
    return kb * 1024

def megabits_to_bytes(mb):
    return mb * 125_000  # 1 Mbit = 125,000 bytes

# In check function
def check_my_service(section):
    # External tool gives nanoseconds
    latency_ns = section.get('latency_ns', 0)
    latency_s = nanoseconds_to_seconds(latency_ns)

    yield from check_levels(
        latency_s,  # Pass seconds!
        levels_upper=("fixed", (0.05, 0.1)),  # 50ms, 100ms in seconds
        metric_name="mycompany_myplugin_latency",  # Prefixed!
        render_func=render.timespan,  # Formats appropriately
    )
```

### Perfometer Definitions

```python
from cmk.graphing.v1.perfometers import (
    Perfometer,
    FocusRange,
    Closed,
    Stacked,
)

# Simple perfometer
perfometer_cpu = Perfometer(
    name="mycompany_myplugin_cpu_perf",
    focus_range=FocusRange(
        lower=Closed(0),
        upper=Closed(100),
    ),
    segments=["mycompany_myplugin_cpu"],
)

# Stacked perfometer
perfometer_stacked = Stacked(
    name="mycompany_myplugin_cpu_memory",
    lower=Perfometer(
        name="mycompany_myplugin_cpu_perf",
        focus_range=FocusRange(
            lower=Closed(0),
            upper=Closed(100),
        ),
        segments=["mycompany_myplugin_cpu"],
    ),
    upper=Perfometer(
        name="mycompany_myplugin_mem_perf",
        focus_range=FocusRange(
            lower=Closed(0),
            upper=Closed(100),
        ),
        segments=["mycompany_myplugin_memory_percent"],
    ),
)
```

### Complete UPS Graphing Example

```python
# File: ./local/lib/python3/cmk_addons/plugins/ups/graphing/ups.py

from cmk.graphing.v1 import Title
from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
    Metric,
    Unit,
    TimeNotation,
)
from cmk.graphing.v1.graphs import Graph, MinimalRange

# Units
unit_percentage = Unit(DecimalNotation("%"))
unit_volts = Unit(DecimalNotation("V"))
unit_seconds = Unit(TimeNotation())

# Metrics with mycompany_ups prefix
metric_mycompany_ups_battery_charge = Metric(
    name="mycompany_ups_battery_charge",
    title=Title("Battery Charge"),
    unit=unit_percentage,
    color=Color.GREEN,
)

metric_mycompany_ups_battery_runtime = Metric(
    name="mycompany_ups_battery_runtime",
    title=Title("Battery Runtime"),
    unit=unit_seconds,  # Stored in seconds!
    color=Color.BLUE,
)

metric_mycompany_ups_input_voltage = Metric(
    name="mycompany_ups_input_voltage",
    title=Title("Input Voltage"),
    unit=unit_volts,
    color=Color.ORANGE,
)

metric_mycompany_ups_battery_voltage = Metric(
    name="mycompany_ups_battery_voltage",
    title=Title("Battery Voltage"),
    unit=unit_volts,
    color=Color.PURPLE,
)

# Graphs
graph_mycompany_ups_battery = Graph(
    name="mycompany_ups_battery",
    title=Title("UPS Battery Status"),
    simple_lines=[
        "mycompany_ups_battery_charge",
        "mycompany_ups_battery_runtime",
    ],
    minimal_range=MinimalRange(
        lower=0,
        upper=100,
    ),
)

graph_mycompany_ups_voltage = Graph(
    name="mycompany_ups_voltage",
    title=Title("UPS Voltages"),
    simple_lines=[
        "mycompany_ups_input_voltage",
        "mycompany_ups_battery_voltage",
    ],
    minimal_range=MinimalRange(
        lower=0,
        upper=300,
    ),
)
```

### Color Constants Reference

```python
from cmk.graphing.v1 import Color

# Available colors
Color.BLUE, Color.LIGHT_BLUE, Color.DARK_BLUE
Color.GREEN, Color.LIGHT_GREEN, Color.DARK_GREEN
Color.RED, Color.LIGHT_RED, Color.DARK_RED
Color.ORANGE, Color.LIGHT_ORANGE, Color.DARK_ORANGE
Color.YELLOW, Color.LIGHT_YELLOW, Color.DARK_YELLOW
Color.PURPLE, Color.LIGHT_PURPLE, Color.DARK_PURPLE
Color.CYAN, Color.LIGHT_CYAN, Color.DARK_CYAN
Color.PINK, Color.LIGHT_PINK, Color.DARK_PINK
Color.BROWN, Color.LIGHT_BROWN, Color.DARK_BROWN
Color.GRAY, Color.LIGHT_GRAY, Color.DARK_GRAY
Color.BLACK, Color.WHITE
```

### Custom Render Functions

```python
# In check plugin
def _render_operations_per_second(value: float) -> str:
    return f"{value:.1f}/s"

def _render_milliseconds(value: float) -> str:
    # Value is in seconds, display as ms
    return f"{value * 1000:.2f}ms"

def check_with_custom_render(section):
    yield from check_levels(
        section.get("ops_per_sec", 0),
        levels_upper=("fixed", (1000, 2000)),
        metric_name="mycompany_myplugin_operations",  # Prefixed!
        render_func=_render_operations_per_second,
        label="Operations",
    )
```

### Renaming Existing Metrics

If you need to rename metrics (to add prefixes or fix units), see **[13-metric-migration.md](13-metric-migration.md)** for the complete guide on using CheckMK's Translation system to preserve historical data.

### Best Practices

#### DO ✅
- **Always prefix metric names** with `mycompany_myplugin_` format
- Store metrics in base SI units (seconds, bytes)
- Convert at check plugin level
- Use CheckMK's render functions
- Handle missing metrics with NaN or optional
- Use meaningful, descriptive metric names

#### DON'T ❌
- Use generic unprefixed metric names (e.g., `cpu`, `latency`, `temp`)
- Store non-base units (ms, KB, ns)
- Convert in graphing definitions
- Assume metrics always present
- Mix unit types in same graph

### Common Unit Patterns

```python
# Time metrics
def check_time_metrics(section):
    # From milliseconds
    response_ms = section.get("response_ms", 0)
    response_s = response_ms / 1000.0
    yield Metric("mycompany_myplugin_response_time", response_s)

    # From nanoseconds
    latency_ns = section.get("latency_ns", 0)
    latency_s = latency_ns / 1e9
    yield Metric("mycompany_myplugin_latency", latency_s)

    # Already in seconds
    uptime_s = section.get("uptime", 0)
    yield Metric("mycompany_myplugin_uptime", uptime_s)

# Data size metrics
def check_data_metrics(section):
    # From kilobytes
    size_kb = section.get("size_kb", 0)
    size_bytes = size_kb * 1024
    yield Metric("mycompany_myplugin_size", size_bytes)

    # From megabits
    bandwidth_mbit = section.get("bandwidth_mbit", 0)
    bandwidth_bytes = bandwidth_mbit * 125_000
    yield Metric("mycompany_myplugin_bandwidth", bandwidth_bytes)
```

### Testing Graphs

```python
# Test metric output
def test_metrics():
    from check_plugin import check_my_service

    section = {"latency_ns": 50_000_000}  # 50ms
    results = list(check_my_service(section))

    metrics = [r for r in results if isinstance(r, Metric)]
    assert len(metrics) > 0

    # Check correct unit conversion and prefixed name
    latency_metric = next(
        (m for m in metrics if m.name == "mycompany_myplugin_latency"), None
    )
    assert latency_metric is not None
    assert latency_metric.value == 0.05  # 50ms = 0.05s
```

### See Also
- [04-check-plugins.md](04-check-plugins.md) - Generating metrics
- [06-rulesets.md](06-rulesets.md) - Configuring thresholds
- [09-advanced-patterns.md](09-advanced-patterns.md) - Complex graphing