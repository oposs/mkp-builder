# CheckMK Agent Plugin Development
## Host-Based Data Collection

### Quick Start - Basic Agent Plugin

```bash
#!/bin/bash
# Location: /usr/lib/check_mk_agent/plugins/my_service
echo "<<<my_service>>>"
echo "status OK"
echo "cpu_usage 45.2"
echo "memory_mb 1024"
```

**Make executable**: `chmod +x /usr/lib/check_mk_agent/plugins/my_service`

### Output Format Requirements

```
<<<section_name>>>           # MANDATORY section header
key value                    # Space-separated key-value
key value1 value2           # Multiple values allowed
<<<section_name:sep(124)>>> # Custom separator (|)
item|{"json": "data"}      # JSON with separator
```

### Python Agent Plugin Template

```python
#!/usr/bin/env python3
import json
import os
import subprocess
import sys

# Config file path using MK_CONFDIR
CONFIG_FILE = os.path.join(
    os.environ.get("MK_CONFDIR", "/etc/check_mk"),
    "my_service.json"
)

def get_config():
    """Read configuration"""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def collect_data(timeout=30):
    """Collect monitoring data"""
    try:
        result = subprocess.run(
            ['your_command'],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout"
    except Exception as e:
        return f"ERROR: {e}"

def main():
    config = get_config()
    timeout = config.get("timeout", 30)
    
    # Always output section header
    print("<<<my_service>>>")
    
    data = collect_data(timeout)
    if data.startswith("ERROR:"):
        print(data, file=sys.stderr)
        sys.exit(1)
    
    print(data)

if __name__ == "__main__":
    main()
```

### JSON Encoding Pattern

```python
#!/usr/bin/env python3
import json
import subprocess

def main():
    # Use custom separator for JSON data
    print("<<<my_devices:sep(124)>>>")  # Pipe separator
    
    devices = ["/dev/sda", "/dev/sdb"]
    
    for device in devices:
        device_data = get_device_data(device)
        if device_data:
            # Compact JSON encoding
            json_str = json.dumps(device_data, separators=(',', ':'))
            print(f"{device}|{json_str}")
        else:
            print(f"{device}|ERROR|Failed to get data")

def get_device_data(device):
    """Get device information"""
    try:
        # Your data collection logic
        return {
            "model": "Samsung SSD",
            "capacity_bytes": 512000000000,
            "temperature": 35,
            "health": "OK"
        }
    except Exception:
        return None

if __name__ == "__main__":
    main()
```

### Multi-Section Output

```python
#!/usr/bin/env python3
import time

def main():
    # Section 1: Simple metrics
    print("<<<system_metrics>>>")
    print(f"cpu_usage 45.2")
    print(f"memory_usage 67.8")
    print(f"load_average 1.2 1.5 1.8")
    print(f"timestamp {int(time.time())}")
    
    # Section 2: JSON data with separator
    print("<<<service_status:sep(124)>>>")
    services = get_services()
    for service in services:
        import json
        data = json.dumps(service, separators=(',', ':'))
        print(f"{service['name']}|{data}")
    
    # Section 3: Simple status
    print("<<<system_info>>>")
    print(f"hostname {get_hostname()}")
    print(f"uptime {get_uptime()}")

def get_services():
    return [
        {"name": "nginx", "status": "running", "pid": 1234},
        {"name": "mysql", "status": "running", "pid": 5678},
    ]

def get_hostname():
    import socket
    return socket.gethostname()

def get_uptime():
    with open('/proc/uptime') as f:
        return int(float(f.read().split()[0]))

if __name__ == "__main__":
    main()
```

### Error Handling Best Practices

```python
#!/usr/bin/env python3
import sys
import json
import subprocess
from typing import Dict, List, Optional

def safe_command(cmd: List[str], timeout: int = 30) -> Optional[str]:
    """Execute command safely"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False  # Don't raise on non-zero exit
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None
    except Exception:
        return None

def validate_data(data: Dict) -> bool:
    """Validate data quality"""
    required = ['status', 'metrics']
    return all(field in data for field in required)

def main():
    print("<<<my_service:sep(124)>>>")
    
    items = get_items()
    for item in items:
        data = collect_item_data(item)
        
        if data and validate_data(data):
            # Valid data
            json_str = json.dumps(data, separators=(',', ':'))
            print(f"{item}|{json_str}")
        else:
            # Structured error
            print(f"{item}|ERROR|Invalid or missing data")

def get_items():
    # Your item discovery logic
    return ["item1", "item2", "item3"]

def collect_item_data(item):
    # Your data collection logic
    output = safe_command(['get_data', item])
    if output:
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return None
    return None

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("<<<my_service_error>>>", file=sys.stderr)
        print(f"error {e}", file=sys.stderr)
        sys.exit(1)
```

### Performance Optimization

```python
#!/usr/bin/env python3
import json
import concurrent.futures
from typing import Dict, List

def collect_all_data() -> Dict:
    """Batch collection - efficient"""
    # Single collection call
    cmd_output = run_command(['get_all_data'])
    return parse_output(cmd_output)

def main():
    # GOOD: Batch processing
    print("<<<my_service:sep(124)>>>")
    
    all_data = collect_all_data()
    for item_name, item_data in all_data.items():
        if item_data:
            output = {
                'name': item_data['name'],
                'metrics': item_data.get('metrics', {}),
                'timestamp': int(time.time())
            }
            print(f"{item_name}|{json.dumps(output, separators=(',', ':'))}")

    # For parallel collection when needed
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(collect_item, item): item 
            for item in get_items()
        }
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            try:
                data = future.result(timeout=10)
                if data:
                    print(f"{item}|{json.dumps(data, separators=(',', ':'))}")
            except Exception:
                print(f"{item}|ERROR|Collection failed")
```

### JSON vs Simple Format

#### Use JSON When:
- Nested data structures
- Multiple metrics per item
- Complex error information
- Mixed data types

```python
# JSON format - complex data
print("<<<devices:sep(124)>>>")
device_data = {
    'model': 'Samsung SSD',
    'metrics': {
        'read_ops': 1234,
        'write_ops': 5678,
        'temperature': 35
    },
    'arrays': [1, 2, 3],
    'status': 'healthy'
}
print(f"sda|{json.dumps(device_data, separators=(',', ':'))}")
```

#### Use Simple Format When:
- Flat data structure
- Single metrics
- Maximum performance
- Backward compatibility

```python
# Simple format - basic metrics
print("<<<cpu_usage>>>")
print("cpu0 85.2")
print("cpu1 67.8")
print("load_avg 1.25")
```

### Special Characters & Unicode

```python
#!/usr/bin/env python3
import json

def main():
    print("<<<my_service:sep(124)>>>")
    
    # Handle special characters in keys
    device_name = "/dev/disk|by-id|special"
    safe_key = device_name.replace('|', '_').replace('\n', '_')
    
    data = {"status": "OK", "value": 42}
    
    # Ensure ASCII output
    json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=True)
    print(f"{safe_key}|{json_str}")
```

### Advanced Patterns

#### Configuration File Support
```python
CONFIG_DEFAULTS = {
    'timeout': 30,
    'interval': 60,
    'enabled': True,
    'items': []
}

def get_config():
    config = CONFIG_DEFAULTS.copy()
    config_file = os.path.join(
        os.environ.get("MK_CONFDIR", "/etc/check_mk"),
        "my_service.json"
    )
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception:
            pass
    return config
```

#### Caching Expensive Operations
```python
import pickle
import time

CACHE_FILE = "/tmp/my_service_cache.pkl"
CACHE_TTL = 300  # 5 minutes

def get_cached_data():
    try:
        if os.path.exists(CACHE_FILE):
            mtime = os.path.getmtime(CACHE_FILE)
            if time.time() - mtime < CACHE_TTL:
                with open(CACHE_FILE, 'rb') as f:
                    return pickle.load(f)
    except Exception:
        pass
    return None

def save_cache(data):
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(data, f)
    except Exception:
        pass
```

### Testing Agent Plugins

```bash
# Test directly
/usr/lib/check_mk_agent/plugins/my_service

# Test with agent
check_mk_agent | grep -A10 "<<<my_service>>>"

# Check JSON parsing
/usr/lib/check_mk_agent/plugins/my_service | python3 -c "
import sys, json
for line in sys.stdin:
    if '|' in line:
        parts = line.strip().split('|', 1)
        print(json.loads(parts[1]))
"
```

### Common Pitfalls

| Problem | Solution |
|---------|----------|
| No output | Check executable bit, test manually |
| Missing header | Always output `<<<section>>>` first |
| JSON parsing fails | Use separators, ensure ASCII |
| Special characters | Escape or replace separators |
| Performance | Batch operations, use caching |

### See Also
- [04-check-plugins.md](04-check-plugins.md) - Parse and check data
- [07-bakery.md](07-bakery.md) - Deploy agents automatically
- [08-testing-debugging.md](08-testing-debugging.md) - Debug techniques