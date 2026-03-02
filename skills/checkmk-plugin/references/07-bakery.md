# CheckMK Agent Bakery Integration
## Automatic Agent Plugin Deployment

### Overview

**Two separate files required:**
1. **Bakery Plugin** - Technical logic (`./local/lib/python3/cmk/base/cee/plugins/bakery/`)
2. **Bakery Ruleset** - GUI configuration (`./local/lib/python3/cmk_addons/plugins/*/rulesets/`)

### Basic Bakery Plugin

```python
# File: ./local/lib/python3/cmk/base/cee/plugins/bakery/my_service.py

import json
from cmk.base.plugins.bakery.bakery_api.v1 import (
    register,
    Plugin,
    PluginConfig,
    OS,
)
from pathlib import Path
from typing import Any, Dict

def get_my_service_files(conf: Dict[str, Any]):
    """Generate plugin files based on configuration"""
    if conf is None or not conf.get("enabled", True):
        return  # Don't deploy if disabled
    
    # Get configuration
    interval = conf.get("interval", 60)
    timeout = conf.get("timeout", 30)
    
    # Generate configuration file
    config_content = json.dumps({
        "timeout": int(timeout),
        "interval": int(interval),
    })
    
    yield PluginConfig(
        base_os=OS.LINUX,
        target=Path("my_service.json"),
        lines=config_content.splitlines(),
    )
    
    # Deploy agent plugin
    yield Plugin(
        base_os=OS.LINUX,
        source=Path('my_service'),  # From local/share/check_mk/agents/plugins/
        target=Path('my_service'),  # To /usr/lib/check_mk_agent/plugins/
        interval=interval,
    )

# Register bakery plugin
register.bakery_plugin(
    name="my_service",
    files_function=get_my_service_files,
)
```

### Agent Plugin Source Location

Place agent plugins in:
```
./local/share/check_mk/agents/plugins/my_service
```

The bakery automatically finds them when using `source=Path('my_service')`

### Multi-Platform Support

```python
from cmk.base.plugins.bakery.bakery_api.v1 import (
    register,
    Plugin,
    PluginConfig,
    OS,
    WindowsConfigEntry,
)

def get_multiplatform_files(conf: Dict[str, Any]):
    if not conf.get("enabled", True):
        return
    
    interval = conf.get("interval", 60)
    
    # Linux plugin
    if conf.get("deploy_linux", True):
        yield Plugin(
            base_os=OS.LINUX,
            source=Path('my_service'),
            target=Path('my_service'),
            interval=interval,
        )
    
    # Windows plugin
    if conf.get("deploy_windows", False):
        yield Plugin(
            base_os=OS.WINDOWS,
            source=Path('my_service.ps1'),
            target=Path('my_service.ps1'),
            interval=interval,
        )
        
        # Windows-specific config
        yield WindowsConfigEntry(
            path="my_service",
            content={
                "interval": interval,
                "timeout": conf.get("timeout", 30),
            },
        )
    
    # Solaris support
    if conf.get("deploy_solaris", False):
        yield Plugin(
            base_os=OS.SOLARIS,
            source=Path('my_service'),
            target=Path('my_service'),
            interval=interval,
        )
```

### Configuration Files

```python
def get_config_files(conf: Dict[str, Any]):
    """Generate various configuration files"""
    
    # JSON configuration
    json_config = {
        "enabled": conf.get("enabled", True),
        "items": conf.get("items", []),
        "timeout": conf.get("timeout", 30),
    }
    
    yield PluginConfig(
        base_os=OS.LINUX,
        target=Path("my_service.json"),
        lines=json.dumps(json_config, indent=2).splitlines(),
    )
    
    # INI-style configuration
    ini_lines = [
        "[general]",
        f"enabled = {conf.get('enabled', True)}",
        f"timeout = {conf.get('timeout', 30)}",
        "",
        "[items]",
    ]
    for item in conf.get("items", []):
        ini_lines.append(f"item = {item}")
    
    yield PluginConfig(
        base_os=OS.LINUX,
        target=Path("my_service.ini"),
        lines=ini_lines,
    )
    
    # Shell script configuration
    shell_lines = [
        "#!/bin/bash",
        f"ENABLED={int(conf.get('enabled', True))}",
        f"TIMEOUT={conf.get('timeout', 30)}",
        f"ITEMS=({' '.join(conf.get('items', []))})",
    ]
    
    yield PluginConfig(
        base_os=OS.LINUX,
        target=Path("my_service.conf"),
        lines=shell_lines,
    )
```

### Advanced Features

```python
from cmk.base.plugins.bakery.bakery_api.v1 import (
    ScriptletGenerator,
    FileGenerator,
)

def get_advanced_files(conf: Dict[str, Any]):
    """Advanced bakery features"""
    
    # Conditional deployment
    if conf.get("mode") == "advanced":
        yield Plugin(
            base_os=OS.LINUX,
            source=Path('my_service_advanced'),
            target=Path('my_service_advanced'),
            interval=conf.get("interval", 60),
        )
    
    # Generate file from template
    yield FileGenerator(
        base_os=OS.LINUX,
        target=Path("my_service_generated.py"),
        content=generate_python_script(conf),
        mode=0o755,  # Executable
    )

def generate_python_script(conf: Dict[str, Any]) -> str:
    """Generate Python script based on config"""
    return f'''#!/usr/bin/env python3
import json

CONFIG = {json.dumps(conf)}

def main():
    print("<<<my_service>>>")
    # Generated code based on config
    for item in CONFIG.get("items", []):
        print(f"item {{item}} OK")

if __name__ == "__main__":
    main()
'''

def get_scriptlets(conf: Dict[str, Any]):
    """Installation/uninstallation scripts"""
    if not conf.get("enabled", True):
        return
    
    # Installation script
    install_script = '''#!/bin/bash
# Create required directories
mkdir -p /var/lib/my_service
mkdir -p /etc/my_service

# Set permissions
chmod 755 /usr/lib/check_mk_agent/plugins/my_service

# Initialize service
echo "My Service installed" > /var/lib/my_service/status
'''
    
    # Uninstall script
    uninstall_script = '''#!/bin/bash
# Clean up
rm -rf /var/lib/my_service
rm -rf /etc/my_service
'''
    
    yield ScriptletGenerator(
        install=install_script,
        uninstall=uninstall_script,
    )

# Register with all functions
register.bakery_plugin(
    name="my_service_advanced",
    files_function=get_advanced_files,
    scriptlets_function=get_scriptlets,
)
```

### Complete UPS Bakery Example

```python
# File: ./local/lib/python3/cmk/base/cee/plugins/bakery/ups_monitor.py

import json
from cmk.base.plugins.bakery.bakery_api.v1 import (
    register,
    Plugin,
    PluginConfig,
    OS,
)
from pathlib import Path
from typing import Any, Dict

def get_ups_monitor_files(conf: Dict[str, Any]):
    """Deploy UPS monitoring plugin"""
    if not conf.get("enabled", True):
        return
    
    # Configuration
    interval = conf.get("interval", 300)  # 5 minutes default
    snmp_community = conf.get("community", "public")
    ups_oids = conf.get("oids", [])
    
    # Generate config file
    config = {
        "community": snmp_community,
        "oids": ups_oids,
        "timeout": conf.get("timeout", 30),
    }
    
    yield PluginConfig(
        base_os=OS.LINUX,
        target=Path("ups_monitor.json"),
        lines=json.dumps(config, indent=2).splitlines(),
    )
    
    # Deploy plugin with interval
    yield Plugin(
        base_os=OS.LINUX,
        source=Path('ups_monitor'),
        target=Path('ups_monitor'),
        interval=interval,
    )

register.bakery_plugin(
    name="ups_monitor",
    files_function=get_ups_monitor_files,
)
```

### Bakery Ruleset (GUI)

```python
# File: ./local/lib/python3/cmk_addons/plugins/ups/rulesets/bakery.py

from cmk.rulesets.v1 import Title, Help, Label
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    TimeSpan,
    TimeMagnitude,
    String,
    List,
)
from cmk.rulesets.v1.rule_specs import AgentConfig, Topic

def _parameter_form_ups_monitor():
    return Dictionary(
        title=Title("UPS Monitor Agent Plugin"),
        help_text=Help("Deploy and configure UPS monitoring"),
        elements={
            "enabled": DictElement(
                parameter_form=BooleanChoice(
                    title=Title("Enable UPS monitoring"),
                    label=Label("Deploy plugin"),
                    prefill=DefaultValue(True),
                )
            ),
            "interval": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Check interval"),
                    help_text=Help("How often to check UPS status"),
                    displayed_magnitudes=[
                        TimeMagnitude.MINUTE,
                        TimeMagnitude.SECOND,
                    ],
                    prefill=DefaultValue(300.0),  # 5 minutes
                )
            ),
            "community": DictElement(
                parameter_form=String(
                    title=Title("SNMP Community"),
                    prefill=DefaultValue("public"),
                )
            ),
            "timeout": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Query timeout"),
                    displayed_magnitudes=[TimeMagnitude.SECOND],
                    prefill=DefaultValue(30.0),
                )
            ),
        }
    )

rule_spec_ups_monitor_bakery = AgentConfig(
    name="ups_monitor",  # Must match bakery plugin name
    title=Title("UPS Monitor Agent Deployment"),
    topic=Topic.POWER,
    parameter_form=_parameter_form_ups_monitor,
)
```

### Testing Bakery Deployment

```bash
# Check bakery plugin registration
cmk -D | grep my_service

# Bake agents
cmk -P bake --force

# Test specific host
cmk -P bake --host myhost

# Check generated files
ls -la /omd/sites/mysite/var/check_mk/agents/

# Deploy to host
cmk -P deploy --host myhost
```

### Directory Structure Summary

```
./local/
├── lib/
│   └── python3/
│       ├── cmk/
│       │   └── base/
│       │       └── cee/
│       │           └── plugins/
│       │               └── bakery/
│       │                   └── my_service.py  # Bakery logic
│       └── cmk_addons/
│           └── plugins/
│               └── my_plugin/
│                   └── rulesets/
│                       └── bakery.py  # GUI configuration
└── share/
    └── check_mk/
        └── agents/
            └── plugins/
                └── my_service  # Agent plugin source
```

### Common Patterns

#### Selective Deployment
```python
def get_selective_files(conf):
    # Deploy based on configuration
    if conf.get("monitor_cpu", True):
        yield Plugin(
            base_os=OS.LINUX,
            source=Path('cpu_monitor'),
            target=Path('cpu_monitor'),
            interval=60,
        )
    
    if conf.get("monitor_disk", True):
        yield Plugin(
            base_os=OS.LINUX,
            source=Path('disk_monitor'),
            target=Path('disk_monitor'),
            interval=300,
        )
```

#### Platform Detection
```python
def get_platform_files(conf):
    # Different plugins for different OS versions
    if conf.get("os_type") == "ubuntu":
        source_file = Path('my_service_ubuntu')
    elif conf.get("os_type") == "rhel":
        source_file = Path('my_service_rhel')
    else:
        source_file = Path('my_service')
    
    yield Plugin(
        base_os=OS.LINUX,
        source=source_file,
        target=Path('my_service'),
        interval=conf.get("interval", 60),
    )
```

### See Also
- [03-agent-plugins.md](03-agent-plugins.md) - Writing agent plugins
- [06-rulesets.md](06-rulesets.md) - Bakery GUI configuration
- [08-testing-debugging.md](08-testing-debugging.md) - Testing deployment