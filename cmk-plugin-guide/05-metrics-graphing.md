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

# Define metrics
metric_cpu_usage = Metric(
    name="cpu_usage",
    title=Title("CPU Usage"),
    unit=unit_percentage,
    color=Color.BLUE,
)

metric_memory = Metric(
    name="memory",
    title=Title("Memory Usage"),
    unit=unit_bytes,
    color=Color.GREEN,
)

metric_latency = Metric(
    name="latency",
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

# Simple graph
graph_performance = Graph(
    name="performance",
    title=Title("System Performance"),
    simple_lines=[
        "cpu_usage",
        "memory_percent",
    ],
    minimal_range=MinimalRange(
        lower=0,
        upper=100,
    ),
)

# Graph with optional metrics
graph_with_optional = Graph(
    name="operations",
    title=Title("Operations"),
    simple_lines=["read_ops", "write_ops", "scrub_ops"],
    optional=["scrub_ops"],  # Only present during scrub
)

# Bidirectional graph (network, I/O)
graph_network = Bidirectional(
    name="network_traffic",
    title=Title("Network Traffic"),
    lower=Graph(
        name="network_in",
        title=Title("Inbound"),
        compound_lines=["bytes_in"],
    ),
    upper=Graph(
        name="network_out",
        title=Title("Outbound"),
        compound_lines=["bytes_out"],
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
        yield Metric("cpu_usage", float('nan'))
        yield Result(state=State.UNKNOWN, summary="CPU data not available")
    else:
        yield Metric("cpu_usage", cpu)
```

#### Optional Metrics in Graphs
```python
# Graph displays even when some metrics missing
graph_adaptive = Graph(
    name="adaptive_graph",
    title=Title("Adaptive Metrics"),
    simple_lines=["always_present", "sometimes_present"],
    optional=["sometimes_present"],  # Won't break graph if missing
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
        metric_name="latency",
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
    name="cpu_usage",
    focus_range=FocusRange(
        lower=Closed(0),
        upper=Closed(100),
    ),
    segments=["cpu_usage"],
)

# Stacked perfometer
perfometer_stacked = Stacked(
    name="cpu_memory",
    lower=Perfometer(
        name="cpu_perf",
        focus_range=FocusRange(
            lower=Closed(0),
            upper=Closed(100),
        ),
        segments=["cpu_usage"],
    ),
    upper=Perfometer(
        name="mem_perf",
        focus_range=FocusRange(
            lower=Closed(0),
            upper=Closed(100),
        ),
        segments=["memory_percent"],
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
)
from cmk.graphing.v1.graphs import Graph, MinimalRange

# Units
unit_percentage = Unit(DecimalNotation("%"))
unit_volts = Unit(DecimalNotation("V"))
unit_seconds = Unit(TimeNotation())

# Metrics
metric_battery_charge = Metric(
    name="battery_charge",
    title=Title("Battery Charge"),
    unit=unit_percentage,
    color=Color.GREEN,
)

metric_battery_runtime = Metric(
    name="battery_runtime",
    title=Title("Battery Runtime"),
    unit=unit_seconds,  # Stored in seconds!
    color=Color.BLUE,
)

metric_input_voltage = Metric(
    name="input_voltage",
    title=Title("Input Voltage"),
    unit=unit_volts,
    color=Color.ORANGE,
)

metric_battery_voltage = Metric(
    name="battery_voltage",
    title=Title("Battery Voltage"),
    unit=unit_volts,
    color=Color.PURPLE,
)

# Graphs
graph_ups_battery = Graph(
    name="ups_battery",
    title=Title("UPS Battery Status"),
    simple_lines=[
        "battery_charge",
        "battery_runtime",
    ],
    minimal_range=MinimalRange(
        lower=0,
        upper=100,
    ),
)

graph_ups_voltage = Graph(
    name="ups_voltage",
    title=Title("UPS Voltages"),
    simple_lines=[
        "input_voltage",
        "battery_voltage",
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
        metric_name="operations",
        render_func=_render_operations_per_second,
        label="Operations",
    )
```

### Migration: Fixing Wrong Units

If you stored metrics in wrong units (e.g., nanoseconds), use NEW metric names:

```python
# OLD (wrong): Stored nanoseconds
yield Metric("latency", latency_ns)  # ❌

# NEW (correct): Store seconds with new name
latency_s = latency_ns / 1e9
yield Metric("latency_s", latency_s)  # ✅ New metric name!

# In graphing
metric_latency_s = Metric(
    name="latency_s",  # New name
    title=Title("Latency"),
    unit=Unit(TimeNotation()),  # Expects seconds
    color=Color.BLUE,
)
```

### Best Practices

#### DO ✅
- Store metrics in base SI units (seconds, bytes)
- Convert at check plugin level
- Use CheckMK's render functions
- Handle missing metrics with NaN or optional
- Use meaningful metric names

#### DON'T ❌
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
    yield Metric("response_time", response_s)
    
    # From nanoseconds
    latency_ns = section.get("latency_ns", 0)
    latency_s = latency_ns / 1e9
    yield Metric("latency", latency_s)
    
    # Already in seconds
    uptime_s = section.get("uptime", 0)
    yield Metric("uptime", uptime_s)

# Data size metrics
def check_data_metrics(section):
    # From kilobytes
    size_kb = section.get("size_kb", 0)
    size_bytes = size_kb * 1024
    yield Metric("size", size_bytes)
    
    # From megabits
    bandwidth_mbit = section.get("bandwidth_mbit", 0)
    bandwidth_bytes = bandwidth_mbit * 125_000
    yield Metric("bandwidth", bandwidth_bytes)
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
    
    # Check correct unit conversion
    latency_metric = next((m for m in metrics if m.name == "latency"), None)
    assert latency_metric.value == 0.05  # 50ms = 0.05s
```

### See Also
- [04-check-plugins.md](04-check-plugins.md) - Generating metrics
- [06-rulesets.md](06-rulesets.md) - Configuring thresholds
- [09-advanced-patterns.md](09-advanced-patterns.md) - Complex graphing