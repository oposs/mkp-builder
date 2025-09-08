# CheckMK Complete Examples
## Real-World Production Patterns

### Complete Temperature Monitor Plugin

#### Agent Plugin
```bash
#!/bin/bash
# File: ./local/share/check_mk/agents/plugins/temperature_monitor

echo "<<<temperature_monitor>>>"

# Get temperature data
for sensor in /sys/class/thermal/thermal_zone*/temp; do
    if [ -r "$sensor" ]; then
        zone=$(basename $(dirname "$sensor"))
        temp=$(cat "$sensor")
        # Convert millidegrees to degrees
        temp_c=$((temp / 1000))
        echo "${zone} ${temp_c} OK"
    fi
done

# System info
echo "system_info Temperature_Monitor_v1.0"
```

#### Check Plugin
```python
# File: ./local/lib/python3/cmk_addons/plugins/temperature/agent_based/temperature_monitor.py

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    Metric,
    HostLabel,
    check_levels,
    render,
)
from typing import Any, Dict, Mapping

def parse_temperature_monitor(string_table):
    """Parse temperature data"""
    sensors = {}
    system_info = {}
    
    for line in string_table:
        if not line:
            continue
            
        if line[0] == "system_info":
            system_info["version"] = " ".join(line[1:])
        elif len(line) >= 3:
            sensor_name = line[0]
            try:
                temperature = float(line[1])
                status = line[2]
                sensors[sensor_name] = {
                    "temperature": temperature,
                    "status": status,
                }
            except (ValueError, IndexError):
                continue
    
    return {"sensors": sensors, "system_info": system_info}

def host_label_temperature(section):
    """Add host labels"""
    if section.get("system_info", {}).get("version"):
        yield HostLabel("has_temperature_monitor", "yes")

agent_section_temperature_monitor = AgentSection(
    name="temperature_monitor",
    parse_function=parse_temperature_monitor,
    host_label_function=host_label_temperature,
)

def discover_temperature_monitor(section):
    """Discover temperature sensors"""
    for sensor_name in section.get("sensors", {}):
        yield Service(item=sensor_name)

def check_temperature_monitor(item, params, section):
    """Check temperature sensor"""
    sensors = section.get("sensors", {})
    
    if item not in sensors:
        yield Result(state=State.UNKNOWN, summary=f"Sensor {item} not found")
        return
    
    sensor_data = sensors[item]
    temperature = sensor_data["temperature"]
    
    # Check temperature levels
    yield from check_levels(
        temperature,
        levels_upper=params.get("levels_upper"),
        levels_lower=params.get("levels_lower"),
        metric_name="temperature",
        label="Temperature",
        render_func=lambda v: f"{v:.1f}°C",
    )
    
    # Check sensor status
    status = sensor_data.get("status", "UNKNOWN")
    if status != "OK":
        yield Result(
            state=State.WARN,
            notice=f"Sensor status: {status}"
        )

check_plugin_temperature_monitor = CheckPlugin(
    name="temperature_monitor",
    service_name="Temperature %s",
    sections=["temperature_monitor"],
    discovery_function=discover_temperature_monitor,
    check_function=check_temperature_monitor,
    check_ruleset_name="temperature_monitor",
    check_default_parameters={
        "levels_upper": ("fixed", (70.0, 80.0)),
        "levels_lower": ("fixed", (10.0, 5.0)),
    },
)
```

#### Graphing
```python
# File: ./local/lib/python3/cmk_addons/plugins/temperature/graphing/temperature.py

from cmk.graphing.v1 import Title
from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
    Metric,
    Unit,
)
from cmk.graphing.v1.graphs import Graph, MinimalRange
from cmk.graphing.v1.perfometers import Perfometer, FocusRange, Closed

unit_celsius = Unit(DecimalNotation("°C"))

metric_temperature = Metric(
    name="temperature",
    title=Title("Temperature"),
    unit=unit_celsius,
    color=Color.ORANGE,
)

graph_temperature = Graph(
    name="temperature",
    title=Title("Temperature"),
    simple_lines=["temperature"],
    minimal_range=MinimalRange(
        lower=0,
        upper=100,
    ),
)

perfometer_temperature = Perfometer(
    name="temperature",
    focus_range=FocusRange(
        lower=Closed(0),
        upper=Closed(100),
    ),
    segments=["temperature"],
)
```

#### Ruleset
```python
# File: ./local/lib/python3/cmk_addons/plugins/temperature/rulesets/temperature.py

from cmk.rulesets.v1 import Title, Help
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    SimpleLevels,
    LevelDirection,
    DefaultValue,
    Float,
)
from cmk.rulesets.v1.rule_specs import (
    CheckParameters,
    Topic,
    HostAndItemCondition,
)

def _form_spec_temperature():
    return Dictionary(
        title=Title("Temperature Monitoring"),
        elements={
            "levels_upper": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Upper temperature levels"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Float(unit_symbol="°C"),
                    prefill_fixed_levels=DefaultValue((70.0, 80.0)),
                ),
            ),
            "levels_lower": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Lower temperature levels"),
                    level_direction=LevelDirection.LOWER,
                    form_spec_template=Float(unit_symbol="°C"),
                    prefill_fixed_levels=DefaultValue((10.0, 5.0)),
                ),
            ),
        },
    )

rule_spec_temperature_monitor = CheckParameters(
    title=Title("Temperature Monitoring"),
    topic=Topic.ENVIRONMENT,
    name="temperature_monitor",
    parameter_form=_form_spec_temperature,
    condition=HostAndItemCondition(
        item_title=Title("Sensor name")
    ),
)
```

### Complete SMART Error Monitor

```python
#!/usr/bin/env python3
# Agent plugin for SMART errors

import json
import subprocess
from typing import Dict, List, Optional

def get_smart_devices() -> List[str]:
    """Get list of devices"""
    try:
        result = subprocess.run(
            ['lsblk', '-d', '-n', '-o', 'NAME,TYPE'],
            capture_output=True,
            text=True,
            timeout=10
        )
        devices = []
        for line in result.stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 2 and parts[1] == 'disk':
                devices.append(f"/dev/{parts[0]}")
        return devices
    except Exception:
        return []

def get_smart_data(device: str) -> Optional[Dict]:
    """Get SMART data for device"""
    try:
        result = subprocess.run(
            ['smartctl', '--json=c', '-a', device],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode in [0, 1, 2, 4, 64]:
            return json.loads(result.stdout)
        return None
    except Exception:
        return None

def main():
    print("<<<smart_status:sep(124)>>>")
    
    for device in get_smart_devices():
        smart_data = get_smart_data(device)
        
        if smart_data:
            output = {
                'model': smart_data.get('model_name', 'Unknown'),
                'serial': smart_data.get('serial_number', 'Unknown'),
                'temperature': smart_data.get('temperature', {}).get('current', 0),
                'power_on_hours': smart_data.get('power_on_time', {}).get('hours', 0),
                'smart_passed': smart_data.get('smart_status', {}).get('passed', False),
            }
            print(f"{device}|{json.dumps(output, separators=(',', ':'))}")
        else:
            print(f"{device}|ERROR|Failed to get SMART data")

if __name__ == "__main__":
    main()
```

### Production Patterns

#### Pattern: Resilient Data Collection
```python
def collect_with_fallback(primary_cmd, fallback_cmd, timeout=30):
    """Try primary command, fall back if needed"""
    for cmd in [primary_cmd, fallback_cmd]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            continue
    return None
```

#### Pattern: Rate Calculation
```python
from cmk.agent_based.v2 import get_rate, get_value_store

def check_with_rates(section):
    """Calculate rates between checks"""
    value_store = get_value_store()
    
    # Get current counter
    counter = section.get("bytes_total", 0)
    
    # Calculate rate
    rate = get_rate(
        value_store,
        "bytes",
        time.time(),
        counter,
        raise_overflow=True
    )
    
    yield Metric("bytes_per_sec", rate)
    yield Result(
        state=State.OK,
        summary=f"Rate: {render.bytes(rate)}/s"
    )
```

#### Pattern: Service Dependencies
```python
def check_with_dependencies(section):
    """Check with service dependencies"""
    # Check primary service first
    primary_status = section.get("primary_status")
    
    if primary_status != "running":
        yield Result(
            state=State.CRIT,
            summary="Primary service not running - skipping other checks"
        )
        return
    
    # Only check dependent services if primary is OK
    for service in section.get("dependent_services", []):
        if service["status"] != "running":
            yield Result(
                state=State.WARN,
                summary=f"Dependent service {service['name']} not running"
            )
```

#### Pattern: Automatic Threshold Adjustment
```python
def check_with_auto_thresholds(section):
    """Adjust thresholds based on context"""
    value = section.get("metric", 0)
    
    # Adjust thresholds based on time of day
    hour = datetime.now().hour
    
    if 9 <= hour < 17:  # Business hours
        levels = ("fixed", (80.0, 90.0))
    else:  # Off hours
        levels = ("fixed", (95.0, 99.0))
    
    yield from check_levels(
        value,
        levels_upper=levels,
        metric_name="metric",
        label="Adaptive metric",
    )
```

### Testing Helpers

```python
# test_helpers.py
import json
from typing import List, Dict, Any

def create_string_table(data: Dict[str, Any]) -> List[List[str]]:
    """Create string table from dict"""
    string_table = []
    for key, value in data.items():
        if isinstance(value, dict):
            string_table.append([key, json.dumps(value)])
        else:
            string_table.append([key, str(value)])
    return string_table

def run_check_test(check_function, section, params=None):
    """Run check and return results"""
    if params:
        results = list(check_function(params, section))
    else:
        results = list(check_function(section))
    
    states = [r for r in results if isinstance(r, Result)]
    metrics = [r for r in results if isinstance(r, Metric)]
    
    return {
        'states': states,
        'metrics': metrics,
        'worst_state': max((r.state for r in states), default=State.OK)
    }

# Usage
test_section = {"cpu": 85, "memory": 1024}
result = run_check_test(check_my_service, test_section)
assert result['worst_state'] == State.WARN
```

### See Also
- [01-quickstart.md](01-quickstart.md) - Getting started
- [09-advanced-patterns.md](09-advanced-patterns.md) - Advanced techniques
- [11-reference.md](11-reference.md) - API reference