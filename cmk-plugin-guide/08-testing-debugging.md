# CheckMK Plugin Testing and Debugging
## Troubleshooting Guide

### Essential Debug Commands

```bash
# Test agent plugin directly
/usr/lib/check_mk_agent/plugins/my_service

# View agent output
check_mk_agent | grep -A10 "<<<my_service>>>"

# Force discovery
cmk -II --debug hostname

# Test specific check
cmk -v --debug --checks=my_service hostname

# View parsed data
cmk -d hostname | grep -A10 my_service

# SNMP testing
snmpwalk -v2c -c public 192.168.1.100 .1.3.6.1.2.1.1.1.0

# Detect SNMP plugins
cmk --debug -vvI --detect-plugins=my_snmp_device hostname
```

### Common Issues and Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| Plugin not discovered | Wrong prefix | Use `agent_section_`, `check_plugin_` |
| No data | Not executable | `chmod +x` agent plugin |
| Parse errors | Malformed data | Add error handling |
| Import errors | Wrong API | Use `cmk.agent_based.v2` |
| SNMP no data | Wrong OIDs | Test with snmpwalk |
| Wrong state | Threshold logic | Check SimpleLevels format |

### Unit Testing Patterns

```python
# test_my_plugin.py
import pytest
from cmk.agent_based.v2 import Result, State, Metric, Service

# Import your plugin
from cmk_addons.plugins.my_plugin.agent_based.my_service import (
    parse_my_service,
    discover_my_service,
    check_my_service,
)

class TestMyService:
    def test_parse_normal_data(self):
        """Test parsing with normal data"""
        string_table = [
            ["status", "OK"],
            ["cpu", "45.2"],
            ["memory", "1024"],
        ]
        
        result = parse_my_service(string_table)
        
        assert result["status"] == "OK"
        assert result["cpu"] == 45.2
        assert result["memory"] == 1024
    
    def test_parse_empty_data(self):
        """Test with empty input"""
        result = parse_my_service([])
        assert result == {}
    
    def test_parse_malformed_data(self):
        """Test with malformed lines"""
        string_table = [
            ["incomplete"],  # Missing value
            ["valid", "data"],
            [],  # Empty line
        ]
        
        result = parse_my_service(string_table)
        assert "valid" in result
        assert "incomplete" not in result
    
    def test_discovery(self):
        """Test service discovery"""
        section = {"status": "OK", "cpu": 45.2}
        services = list(discover_my_service(section))
        
        assert len(services) == 1
        assert isinstance(services[0], Service)
    
    def test_check_ok_state(self):
        """Test OK state"""
        section = {"status": "OK", "cpu": 45.2}
        results = list(check_my_service(section))
        
        # Find Result objects
        states = [r for r in results if isinstance(r, Result)]
        assert any(r.state == State.OK for r in states)
    
    def test_check_warning_state(self):
        """Test warning threshold"""
        section = {"status": "OK", "cpu": 85.0}
        params = {"cpu_levels": ("fixed", (80.0, 90.0))}
        
        results = list(check_my_service(params, section))
        states = [r for r in results if isinstance(r, Result)]
        assert any(r.state == State.WARN for r in states)
    
    def test_metrics(self):
        """Test metric generation"""
        section = {"cpu": 45.2, "memory": 1024}
        results = list(check_my_service(section))
        
        metrics = [r for r in results if isinstance(r, Metric)]
        assert len(metrics) >= 1
        
        cpu_metric = next((m for m in metrics if m.name == "cpu"), None)
        assert cpu_metric is not None
        assert cpu_metric.value == 45.2

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### SNMP Plugin Testing

```python
def test_parse_snmp():
    """Test SNMP parsing"""
    # Simulate SNMP response
    string_table = [
        ["2", "1320", "95", "2301"],  # Status, voltage, charge, input
    ]
    
    from my_snmp_plugin import parse_ups_status
    result = parse_ups_status(string_table)
    
    assert result["status"] == "onLine"
    assert result["battery_voltage"] == 132.0  # Decivolts to volts
    assert result["battery_charge"] == 95

def test_snmp_detection():
    """Test SNMP detection"""
    from cmk.agent_based.v2 import contains, exists
    
    # Simulate OID responses
    oid_responses = {
        ".1.3.6.1.2.1.1.1.0": "APC UPS Model X",
        ".1.3.6.1.4.1.318.1.1.1.1.1.1.0": "1",
    }
    
    # Test detection logic
    assert "APC" in oid_responses[".1.3.6.1.2.1.1.1.0"]
    assert oid_responses.get(".1.3.6.1.4.1.318.1.1.1.1.1.1.0") is not None
```

### Debugging with Logging

```python
import logging

# Set up logging
logger = logging.getLogger("cmk.base.plugins.agent_based.my_service")

def parse_my_service_debug(string_table):
    """Parse with debug logging"""
    logger.debug(f"Parsing {len(string_table)} lines")
    
    parsed = {}
    for i, line in enumerate(string_table):
        logger.debug(f"Line {i}: {line}")
        
        if len(line) >= 2:
            try:
                key, value = line[0], line[1]
                parsed[key] = value
                logger.debug(f"Parsed: {key} = {value}")
            except Exception as e:
                logger.error(f"Parse error on line {i}: {e}")
    
    logger.debug(f"Final parsed data: {parsed}")
    return parsed

def check_my_service_debug(section):
    """Check with debug logging"""
    logger.debug(f"Checking section: {section}")
    
    if not section:
        logger.warning("Empty section data")
        yield Result(state=State.UNKNOWN, summary="No data")
        return
    
    for key, value in section.items():
        logger.debug(f"Processing {key}: {value}")
        # Check logic here
    
    logger.debug("Check completed")
```

### Plugin Validation Script

```python
#!/usr/bin/env python3
# validate_plugin.py

import sys
import importlib.util
from pathlib import Path

def validate_plugin(plugin_path):
    """Validate plugin structure"""
    print(f"Validating: {plugin_path}")
    
    # Check file exists
    if not Path(plugin_path).exists():
        print("❌ File not found")
        return False
    
    # Try to import
    try:
        spec = importlib.util.spec_from_file_location("plugin", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Check required components
    required = {
        "agent_section_": "Agent section",
        "check_plugin_": "Check plugin",
    }
    
    found = []
    for attr in dir(module):
        for prefix in required:
            if attr.startswith(prefix):
                print(f"✅ Found: {attr}")
                found.append(prefix)
    
    missing = set(required) - set(found)
    if missing:
        print(f"❌ Missing: {[required[m] for m in missing]}")
        return False
    
    print("✅ Validation passed!")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_plugin.py <plugin_path>")
        sys.exit(1)
    
    sys.exit(0 if validate_plugin(sys.argv[1]) else 1)
```

### Performance Profiling

```python
import time
import cProfile
import pstats
from io import StringIO

def profile_check_function():
    """Profile check performance"""
    # Setup test data
    section = generate_large_section()  # Your test data
    
    # Profile the check
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run check multiple times
    for _ in range(100):
        list(check_my_service(section))
    
    profiler.disable()
    
    # Print stats
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
    
    print(stream.getvalue())

def benchmark_parse_function():
    """Benchmark parsing speed"""
    # Large test data
    string_table = [
        [f"item_{i}", str(i * 1.5)]
        for i in range(10000)
    ]
    
    start = time.time()
    result = parse_my_service(string_table)
    elapsed = time.time() - start
    
    print(f"Parsed {len(string_table)} lines in {elapsed:.3f}s")
    print(f"Rate: {len(string_table)/elapsed:.0f} lines/sec")
```

### Interactive Debugging

```python
# debug_helper.py
def debug_section(hostname, check_name):
    """Interactive debugging helper"""
    import subprocess
    import json
    
    # Get raw agent output
    result = subprocess.run(
        ['cmk', '-d', hostname],
        capture_output=True,
        text=True
    )
    
    # Parse section
    lines = result.stdout.split('\n')
    in_section = False
    section_data = []
    
    for line in lines:
        if f"<<<{check_name}>>>" in line:
            in_section = True
            continue
        elif line.startswith("<<<") and in_section:
            break
        elif in_section:
            section_data.append(line)
    
    print(f"Section data for {check_name}:")
    for line in section_data:
        print(f"  {line}")
    
    # Try parsing
    string_table = [line.split() for line in section_data if line]
    
    from my_plugin import parse_my_service
    parsed = parse_my_service(string_table)
    
    print(f"\nParsed data:")
    print(json.dumps(parsed, indent=2))
    
    return parsed

# Usage
if __name__ == "__main__":
    section = debug_section("myhost", "my_service")
    
    # Test check function
    from my_plugin import check_my_service
    results = list(check_my_service(section))
    
    for r in results:
        print(r)
```

### Common Error Messages

```python
# TypeError: HostAndServiceCondition got unexpected argument
# Solution: Use HostAndItemCondition for multi-item services

# ModuleNotFoundError: No module named 'cmk.base.pyugins'
# Solution: Fix typo - should be 'plugins'

# No section header in agent output
# Solution: Ensure agent outputs <<<section_name>>>

# ValueError: invalid literal for int()
# Solution: Add error handling in parse function

# SNMP TimeoutError
# Solution: Check network, community string, firewall
```

### Debugging Checklist

- [ ] Agent plugin executable? (`chmod +x`)
- [ ] Section header present? (`<<<name>>>`)
- [ ] Correct entry point prefix? (`agent_section_`, `check_plugin_`)
- [ ] Parse function handles empty data?
- [ ] Check function handles missing section?
- [ ] SimpleLevels passed directly to check_levels?
- [ ] Metrics in base SI units? (seconds, bytes)
- [ ] SNMP OIDs exist on device? (test with snmpwalk)
- [ ] Bakery plugin registered? (`cmk -D | grep plugin`)
- [ ] Imports correct? (`cmk.agent_based.v2`)

### See Also
- [01-quickstart.md](01-quickstart.md) - Basic setup
- [04-check-plugins.md](04-check-plugins.md) - Check logic
- [09-advanced-patterns.md](09-advanced-patterns.md) - Complex debugging