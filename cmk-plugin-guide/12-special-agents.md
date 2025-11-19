# CheckMK Special Agent Development
## Server-Side Data Collection

### ⚠️ CRITICAL: Naming Conventions

**Always follow CheckMK naming conventions!**

- **Metric names**: Prefix with `mycompany_myplugin_` format
- **Entry points**: Use correct variable prefixes (`special_agent_`, `check_plugin_`, etc.)
- **Plugin names**: Use descriptive, unique names with your org prefix

See **[01-quickstart.md](01-quickstart.md#naming-conventions-critical)** for complete naming conventions.

**Quick example:**
```python
# ✅ Correct metric naming
yield Metric("acme_weather_temperature", temp)
yield Metric("acme_weather_humidity", humidity)
```

Also see [05-metrics-graphing.md](05-metrics-graphing.md) for units and [13-metric-migration.md](13-metric-migration.md) for renaming.

---

### What are Special Agents?

Special agents are programs that run on the CheckMK server (not on monitored hosts) to collect monitoring data from devices/services that:
- Don't support standard CheckMK agents (Linux/Windows)
- Use proprietary APIs (REST, SOAP, XML-RPC)
- Require special authentication
- Are network devices without agent capability

Examples: Cloud services (AWS, Azure), network devices (routers, firewalls), proprietary systems

### Special Agent Components

A complete special agent plugin consists of four parts:

```
~/local/lib/python3/cmk_addons/plugins/my_plugin/
├── __init__.py                  # Package marker
├── libexec/
│   └── agent_my_plugin          # 1. Executable data collector
├── server_side_calls/
│   └── my_plugin.py             # 2. Command builder
├── rulesets/
│   └── my_plugin.py             # 3. GUI configuration
└── agent_based/
    └── my_plugin.py             # 4. Check plugin (data processor)
```

---

## Part 1: The Special Agent Script (libexec/)

### Basic Structure

```python
#!/usr/bin/env python3
# File: ~/local/lib/python3/cmk_addons/plugins/my_plugin/libexec/agent_my_plugin

import argparse
import sys
import requests
from cmk.utils.password_store import replace_passwords

def parse_arguments(argv):
    parser = argparse.ArgumentParser(description="Special agent for My Service")
    parser.add_argument("-u", "--username", required=True, help="Username")
    parser.add_argument("-p", "--password", required=True, help="Password")
    parser.add_argument("-P", "--port", type=int, default=443, help="Port")
    parser.add_argument("--protocol", choices=["http", "https"], default="https")
    parser.add_argument("hostaddress", help="Host address")
    return parser.parse_args(argv)

def fetch_data(args):
    """Collect data from external source"""
    url = f"{args.protocol}://{args.hostaddress}:{args.port}/api/status"
    response = requests.get(
        url,
        auth=(args.username, args.password),
        verify=False,  # nosec - for self-signed certs
        timeout=30
    )
    response.raise_for_status()
    return response.json()

def main(argv=None):
    # CRITICAL: Call this first to handle password store
    replace_passwords()

    args = parse_arguments(argv or sys.argv[1:])

    # Output agent section
    print("<<<my_service>>>")

    try:
        data = fetch_data(args)
        # Output data in agent format
        for key, value in data.items():
            print(f"{key} {value}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Key Requirements

1. **Executable**: Must be executable without file extension
   ```bash
   chmod 755 agent_my_plugin
   ```

2. **Entry Point**: Must include `if __name__ == "__main__":` block
   ```python
   if __name__ == "__main__":
       sys.exit(main())
   ```
   **Without this, the script will not execute when called from the command line!**

3. **Password Handling**: Always call `replace_passwords()` first
   ```python
   from cmk.utils.password_store import replace_passwords
   replace_passwords()  # Must be FIRST thing in main()
   ```

4. **Output Format**: Standard CheckMK agent output
   ```python
   print("<<<section_name>>>")
   print("key1 value1")
   print("key2 value2")
   ```

5. **Error Handling**: Write errors to stderr, return non-zero on failure

### JSON Output Pattern

```python
import json

def main(argv=None):
    replace_passwords()
    args = parse_arguments(argv or sys.argv[1:])

    # Use separator for JSON data
    print("<<<my_devices:sep(124)>>>")  # Pipe separator

    try:
        devices = fetch_devices(args)
        for device_id, device_data in devices.items():
            # Compact JSON on single line
            json_str = json.dumps(device_data, separators=(',', ':'))
            print(f"{device_id}|{json_str}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
```

---

## Part 2: Server-Side Calls (server_side_calls/)

### Purpose

Converts GUI ruleset parameters into command-line arguments for the special agent.

### Basic Implementation

```python
# File: ~/local/lib/python3/cmk_addons/plugins/my_plugin/server_side_calls/my_plugin.py

from collections.abc import Iterator
from pydantic import BaseModel
from cmk.server_side_calls.v1 import (
    HostConfig,
    Secret,
    SpecialAgentCommand,
    SpecialAgentConfig,
)

class Params(BaseModel):
    """Type-safe parameter model"""
    username: str
    password: Secret
    port: int | None = None
    protocol: str = "https"

def commands_function(
    params: Params,
    host_config: HostConfig,
) -> Iterator[SpecialAgentCommand]:
    """Build command-line arguments"""

    # Build argument list
    args = [
        "-u", params.username,
        "-p", params.password.unsafe(),  # Extract password from Secret
    ]

    # Optional parameters
    if params.port:
        args.extend(["-P", str(params.port)])

    args.extend(["--protocol", params.protocol])

    # Host address (from CheckMK host config)
    args.append(host_config.primary_ip_config.address or host_config.name)

    yield SpecialAgentCommand(command_arguments=args)

# CRITICAL: Must be named special_agent_<name>
special_agent_my_plugin = SpecialAgentConfig(
    name="my_plugin",
    parameter_parser=Params.model_validate,
    commands_function=commands_function,
)
```

### Advanced Pattern: Multiple Commands

```python
def commands_function(
    params: Params,
    host_config: HostConfig,
) -> Iterator[SpecialAgentCommand]:
    """Generate multiple agent calls if needed"""

    # Main data collection
    yield SpecialAgentCommand(command_arguments=[
        "-u", params.username,
        "-p", params.password,
        "--mode", "main",
        host_config.primary_ip_config.address,
    ])

    # Optional extended data
    if params.collect_extended:
        yield SpecialAgentCommand(command_arguments=[
            "-u", params.username,
            "-p", params.password,
            "--mode", "extended",
            host_config.primary_ip_config.address,
        ])
```

### Host Config Properties

```python
# Available in host_config:
host_config.name                           # Hostname
host_config.alias                          # Host alias
host_config.primary_ip_config.address      # IP address (IPv4/IPv6)
host_config.primary_ip_config.family       # "ipv4" or "ipv6"
host_config.macros                         # Custom macros
```

---

## Part 3: Rulesets (rulesets/)

### Basic Ruleset

```python
# File: ~/local/lib/python3/cmk_addons/plugins/my_plugin/rulesets/my_plugin.py

from cmk.rulesets.v1 import Title, Help, Label
from cmk.rulesets.v1.form_specs import (
    DefaultValue,
    DictElement,
    Dictionary,
    Integer,
    Password,
    SingleChoice,
    SingleChoiceElement,
    String,
    validators,
)
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic

def _formspec():
    return Dictionary(
        title=Title("My Service API"),
        help_text=Help("Configure access to My Service"),
        elements={
            "username": DictElement(
                parameter_form=String(
                    title=Title("Username"),
                    help_text=Help("API username"),
                    custom_validate=[validators.LengthInRange(min_value=1)],
                ),
                required=True,
            ),
            "password": DictElement(
                parameter_form=Password(
                    title=Title("Password"),
                    help_text=Help("API password"),
                ),
                required=True,
            ),
            "port": DictElement(
                parameter_form=Integer(
                    title=Title("TCP Port"),
                    prefill=DefaultValue(443),
                    custom_validate=[validators.NetworkPort()],
                ),
                required=False,
            ),
            "protocol": DictElement(
                parameter_form=SingleChoice(
                    title=Title("Protocol"),
                    elements=[
                        SingleChoiceElement(name="http", title=Title("HTTP")),
                        SingleChoiceElement(name="https", title=Title("HTTPS")),
                    ],
                    prefill=DefaultValue("https"),
                ),
                required=True,
            ),
        },
    )

# CRITICAL: Must be named rule_spec_special_agent_<name>
rule_spec_special_agent_my_plugin = SpecialAgent(
    name="my_plugin",  # Must match libexec/agent_my_plugin
    title=Title("My Service"),
    topic=Topic.CLOUD,
    parameter_form=_formspec,
)
```

### Password Migration

If migrating from old API with `MigrateToIndividualOrStoredPassword`:

```python
from cmk.rulesets.v1.form_specs import Password, migrate_to_password

"password": DictElement(
    parameter_form=Password(
        title=Title("Password"),
        migrate=migrate_to_password,  # Handles old format
    ),
    required=True,
),
```

### Advanced Form Elements

```python
from cmk.rulesets.v1.form_specs import (
    CascadingSingleChoice,
    CascadingSingleChoiceElement,
    BooleanChoice,
)

def _formspec():
    return Dictionary(
        elements={
            # Authentication method selection
            "auth_method": DictElement(
                parameter_form=CascadingSingleChoice(
                    title=Title("Authentication Method"),
                    elements=[
                        CascadingSingleChoiceElement(
                            name="basic",
                            title=Title("Basic Auth"),
                            parameter_form=Dictionary(
                                elements={
                                    "username": DictElement(
                                        parameter_form=String(title=Title("Username")),
                                        required=True,
                                    ),
                                    "password": DictElement(
                                        parameter_form=Password(title=Title("Password")),
                                        required=True,
                                    ),
                                },
                            ),
                        ),
                        CascadingSingleChoiceElement(
                            name="token",
                            title=Title("API Token"),
                            parameter_form=Dictionary(
                                elements={
                                    "token": DictElement(
                                        parameter_form=Password(title=Title("Token")),
                                        required=True,
                                    ),
                                },
                            ),
                        ),
                    ],
                    prefill=DefaultValue("basic"),
                ),
                required=True,
            ),

            # Optional features
            "verify_ssl": DictElement(
                parameter_form=BooleanChoice(
                    title=Title("Verify SSL Certificate"),
                    label=Label("Enable SSL verification"),
                    prefill=DefaultValue(True),
                ),
            ),
        },
    )
```

---

## Part 4: Check Plugin (agent_based/)

Standard check plugin that processes special agent output. See [04-check-plugins.md](04-check-plugins.md).

```python
# File: ~/local/lib/python3/cmk_addons/plugins/my_plugin/agent_based/my_plugin.py

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
)

def parse_my_plugin(string_table):
    """Parse special agent output"""
    parsed = {}
    for line in string_table:
        if len(line) == 2:
            parsed[line[0]] = line[1]
    return parsed

agent_section_my_plugin = AgentSection(
    name="my_plugin",
    parse_function=parse_my_plugin,
)

def discover_my_plugin(section):
    if section:
        yield Service()

def check_my_plugin(section):
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data")
        return

    status = section.get("status", "unknown")
    if status == "ok":
        yield Result(state=State.OK, summary=f"Status: {status}")
    else:
        yield Result(state=State.WARN, summary=f"Status: {status}")

check_plugin_my_plugin = CheckPlugin(
    name="my_plugin",
    service_name="My Service",
    discovery_function=discover_my_plugin,
    check_function=check_my_plugin,
    sections=["my_plugin"],
)
```

---

## Complete Example: REST API Monitoring

This example uses the `acme_weather` naming convention consistently throughout all components.

### 1. Special Agent (libexec/agent_acme_weather)

```python
#!/usr/bin/env python3
import argparse
import json
import sys
import requests
from cmk.utils.password_store import replace_passwords

def parse_arguments(argv):
    parser = argparse.ArgumentParser(description="ACME Weather API Special Agent")
    parser.add_argument("-k", "--api-key", required=True, help="API key")
    parser.add_argument("-l", "--location", required=True, help="Location")
    parser.add_argument("--units", choices=["metric", "imperial"], default="metric")
    parser.add_argument("hostaddress", help="API endpoint")
    return parser.parse_args(argv)

def fetch_weather(args):
    url = f"https://{args.hostaddress}/weather"
    params = {
        "location": args.location,
        "units": args.units,
        "apikey": args.api_key,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def main(argv=None):
    replace_passwords()
    args = parse_arguments(argv or sys.argv[1:])

    # ✅ Section name matches plugin name
    print("<<<acme_weather:sep(124)>>>")

    try:
        data = fetch_weather(args)
        json_str = json.dumps({
            "temperature": data["temp"],
            "humidity": data["humidity"],
            "condition": data["condition"],
        }, separators=(',', ':'))
        print(f"{args.location}|{json_str}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 2. Server-Side Calls (server_side_calls/my_plugin.py)

```python
from collections.abc import Iterator
from pydantic import BaseModel
from cmk.server_side_calls.v1 import (
    HostConfig,
    Secret,
    SpecialAgentCommand,
    SpecialAgentConfig,
)

class Params(BaseModel):
    api_key: Secret
    location: str
    units: str = "metric"

def commands_function(
    params: Params,
    host_config: HostConfig,
) -> Iterator[SpecialAgentCommand]:
    yield SpecialAgentCommand(command_arguments=[
        "-k", params.api_key.unsafe(),
        "-l", params.location,
        "--units", params.units,
        host_config.primary_ip_config.address or "api.weather.com",
    ])

# ✅ Variable name must be: special_agent_{name}
# Name must match: libexec/agent_{name}
special_agent_acme_weather = SpecialAgentConfig(
    name="acme_weather",
    parameter_parser=Params.model_validate,
    commands_function=commands_function,
)
```

### 3. Ruleset (rulesets/my_plugin.py)

```python
from cmk.rulesets.v1 import Title, Help
from cmk.rulesets.v1.form_specs import (
    DefaultValue,
    DictElement,
    Dictionary,
    Password,
    SingleChoice,
    SingleChoiceElement,
    String,
)
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic

def _formspec():
    return Dictionary(
        title=Title("ACME Weather API Configuration"),
        elements={
            "api_key": DictElement(
                parameter_form=Password(title=Title("API Key")),
                required=True,
            ),
            "location": DictElement(
                parameter_form=String(
                    title=Title("Location"),
                    help_text=Help("City name or coordinates"),
                ),
                required=True,
            ),
            "units": DictElement(
                parameter_form=SingleChoice(
                    title=Title("Units"),
                    elements=[
                        SingleChoiceElement(name="metric", title=Title("Metric (°C)")),
                        SingleChoiceElement(name="imperial", title=Title("Imperial (°F)")),
                    ],
                    prefill=DefaultValue("metric"),
                ),
            ),
        },
    )

# ✅ Variable name must be: rule_spec_special_agent_{name}
# Name must match special_agent_{name} in server_side_calls
rule_spec_special_agent_acme_weather = SpecialAgent(
    name="acme_weather",
    title=Title("ACME Weather API"),
    topic=Topic.GENERAL,
    parameter_form=_formspec,
)
```

### 4. Check Plugin (agent_based/acme_weather.py)

```python
import json
from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Metric,
    Result,
    Service,
    State,
)

def parse_acme_weather(string_table):
    parsed = {}
    for line in string_table:
        if len(line) == 2:
            location, json_data = line[0], line[1]
            try:
                parsed[location] = json.loads(json_data)
            except json.JSONDecodeError:
                pass
    return parsed

# ✅ Variable name must be: agent_section_{name}
# Name must match section output: <<<name>>>
agent_section_acme_weather = AgentSection(
    name="acme_weather",
    parse_function=parse_acme_weather,
)

def discover_acme_weather(section):
    for location in section:
        yield Service(item=location)

def check_acme_weather(item, section):
    if item not in section:
        yield Result(state=State.UNKNOWN, summary=f"Location {item} not found")
        return

    data = section[item]
    temp = data.get("temperature", 0)
    humidity = data.get("humidity", 0)
    condition = data.get("condition", "unknown")

    yield Result(state=State.OK, summary=f"Condition: {condition}")
    yield Result(state=State.OK, notice=f"Temperature: {temp}°C")
    yield Result(state=State.OK, notice=f"Humidity: {humidity}%")

    # ✅ CRITICAL: Always use prefixed metric names!
    # Format: mycompany_myplugin_metricname
    yield Metric("acme_weather_temperature", temp)
    yield Metric("acme_weather_humidity", humidity)

# ✅ Variable name must be: check_plugin_{name}
check_plugin_acme_weather = CheckPlugin(
    name="acme_weather",
    service_name="ACME Weather %s",
    discovery_function=discover_acme_weather,
    check_function=check_acme_weather,
    sections=["acme_weather"],
)
```

---

## Testing Special Agents

### Manual Testing

```bash
# 1. Test agent directly
~/local/lib/python3/cmk_addons/plugins/my_plugin/libexec/agent_my_plugin \
    -u admin -p 'secret' api.example.com

# 2. Test via CheckMK
cmk --debug -v hostname

# 3. Check agent output
cmk -d hostname | grep -A10 "<<<my_plugin>>>"

# 4. Test service discovery
cmk -II hostname --debug

# 5. Test specific check
cmk --debug --checks=my_plugin hostname
```

### Test Data Pattern

```python
# In special agent
def main(argv=None):
    replace_passwords()
    args = parse_arguments(argv or sys.argv[1:])

    # Test mode
    if args.hostaddress == "test":
        import os
        test_file = "/tmp/my_plugin_test_data.json"
        if os.path.exists(test_file):
            with open(test_file) as f:
                data = json.load(f)
                print("<<<my_plugin:sep(124)>>>")
                print(f"test|{json.dumps(data, separators=(',', ':'))}")
                return 0

    # Normal operation
    # ...
```

---

## Common Patterns

### Multiple API Endpoints

```python
def commands_function(params, host_config):
    base_args = ["-u", params.username, "-p", params.password]

    # Main endpoint
    yield SpecialAgentCommand(command_arguments=[
        *base_args,
        "--endpoint", "status",
        host_config.primary_ip_config.address,
    ])

    # Metrics endpoint
    if params.collect_metrics:
        yield SpecialAgentCommand(command_arguments=[
            *base_args,
            "--endpoint", "metrics",
            host_config.primary_ip_config.address,
        ])
```

### Multi-Section Output

```python
def main(argv=None):
    replace_passwords()
    args = parse_arguments(argv or sys.argv[1:])

    try:
        data = fetch_data(args)

        # Section 1: Status
        print("<<<my_plugin_status>>>")
        print(f"status {data['status']}")

        # Section 2: Metrics
        print("<<<my_plugin_metrics:sep(124)>>>")
        for metric_id, metric_data in data['metrics'].items():
            json_str = json.dumps(metric_data, separators=(',', ':'))
            print(f"{metric_id}|{json_str}")

        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
```

### Error Recovery

```python
def fetch_data_with_retry(args, max_retries=3):
    import time
    for attempt in range(max_retries):
        try:
            return fetch_data(args)
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                continue
            raise
```

---

## Common Pitfalls

| Problem | Solution |
|---------|----------|
| Agent not found | Check naming: `libexec/agent_<name>` matches ruleset `name="<name>"` |
| Password not working | Must call `replace_passwords()` FIRST |
| Arguments not passed | Check server_side_calls parameter types match |
| No data in check | Verify agent outputs correct section name `<<<name>>>` |
| Import errors | Special agent must be standalone or use cmk modules |

---

## Migration from Old API

### Old Structure (CheckMK <2.3)
```
local/lib/python3/cmk/special_agents/agent_my_plugin.py
local/share/check_mk/agents/special/agent_my_plugin  # Wrapper
local/share/check_mk/checks/agent_my_plugin          # special_agent_info
local/share/check_mk/web/plugins/wato/my_plugin.py  # GUI
```

### New Structure (CheckMK 2.3+)
```
local/lib/python3/cmk_addons/plugins/my_plugin/
├── __init__.py
├── libexec/agent_my_plugin
├── server_side_calls/my_plugin.py
├── rulesets/my_plugin.py
└── agent_based/my_plugin.py
```

### Migration Steps
1. Create `__init__.py` package marker
2. Move agent to `libexec/agent_<name>`
3. Create `server_side_calls/<name>.py` from old `special_agent_info`
4. Convert WATO ruleset to `rulesets/<name>.py`
5. Update check plugin imports (v1 → v2)
6. Test thoroughly

---

## See Also
- [04-check-plugins.md](04-check-plugins.md) - Processing agent data
- [06-rulesets.md](06-rulesets.md) - Ruleset details
- [08-testing-debugging.md](08-testing-debugging.md) - Debug techniques
- [Official Docs](https://docs.checkmk.com/latest/en/devel_special_agents.html)
