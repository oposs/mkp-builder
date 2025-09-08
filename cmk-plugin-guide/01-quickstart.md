# CheckMK Plugin Development - Quick Start
## Minimal Viable Plugin in 5 Minutes

### Directory Structure (Critical!)

```
./local/lib/python3/cmk_addons/plugins/my_plugin/
├── agent_based/           # Check plugins
├── graphing/             # Graphs (optional)
└── rulesets/             # GUI config (optional)

./local/share/check_mk/agents/plugins/
└── my_plugin             # Agent script
```

**⚠️ Critical Setup**:
```bash
mkdir -p ./local/lib/python3/cmk
ln -s python3/cmk ./local/lib/check_mk  # Symlink prevents production issues
```

### Minimal Working Example

#### 1. Agent Plugin (`./local/share/check_mk/agents/plugins/my_service`)
```bash
#!/bin/bash
echo "<<<my_service>>>"
echo "status OK"
echo "value 42"
```

Make executable: `chmod +x ./local/share/check_mk/agents/plugins/my_service`

#### 2. Check Plugin (`./local/lib/python3/cmk_addons/plugins/my_plugin/agent_based/my_service.py`)
```python
#!/usr/bin/env python3
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

def parse_my_service(string_table):
    """Parse agent output into dict"""
    parsed = {}
    for line in string_table:
        if len(line) == 2:
            parsed[line[0]] = line[1]
    return parsed

# CRITICAL: Name must start with agent_section_
agent_section_my_service = AgentSection(
    name="my_service",
    parse_function=parse_my_service,
)

def discover_my_service(section):
    """Create service if data exists"""
    if section:
        yield Service()

def check_my_service(section):
    """Check logic"""
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data")
        return
    
    status = section.get("status", "UNKNOWN")
    value = int(section.get("value", 0))
    
    if status == "OK":
        state = State.OK
    else:
        state = State.WARN
    
    yield Result(state=state, summary=f"Status: {status}")
    yield Metric("value", value)

# CRITICAL: Name must start with check_plugin_
check_plugin_my_service = CheckPlugin(
    name="my_service",
    service_name="My Service",
    sections=["my_service"],
    discovery_function=discover_my_service,
    check_function=check_my_service,
)
```

#### 3. Deploy & Test
```bash
# Copy agent plugin to target host
scp ./local/share/check_mk/agents/plugins/my_service root@target:/usr/lib/check_mk_agent/plugins/

# Restart CheckMK
cmk -R

# Discover services
cmk -II target_hostname

# Test check
cmk -v --debug target_hostname
```

### Entry Point Prefixes (MANDATORY!)

Variables MUST start with these prefixes to be discovered:
- `agent_section_` - Agent data parsers
- `snmp_section_` - SNMP data parsers  
- `check_plugin_` - Check logic
- `inventory_plugin_` - Inventory

**Wrong**: `my_section = AgentSection(...)`  ❌
**Right**: `agent_section_my_service = AgentSection(...)`  ✅

### Common Pitfalls

1. **Wrong directory** → Use exact paths shown above
2. **Missing prefix** → Variables must have correct prefix
3. **Not executable** → Agent plugins need `chmod +x`
4. **Import errors** → Use `cmk.agent_based.v2` for CheckMK 2.3.0
5. **No section header** → Agent must output `<<<section_name>>>`

### Next Steps

- **SNMP monitoring?** → [02-snmp-plugins.md](02-snmp-plugins.md)
- **Complex agent?** → [03-agent-plugins.md](03-agent-plugins.md)
- **Add graphs?** → [05-metrics-graphing.md](05-metrics-graphing.md)
- **GUI config?** → [06-rulesets.md](06-rulesets.md)
- **Problems?** → [08-testing-debugging.md](08-testing-debugging.md)

### Debug Commands
```bash
# Test agent output
check_mk_agent | grep -A5 "<<<my_service>>>"

# Force discovery
cmk -II --debug hostname

# Test specific check
cmk -v --debug --checks=my_service hostname

# View parsed data
cmk -d hostname | grep -A10 my_service
```