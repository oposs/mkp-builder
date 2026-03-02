---
name: checkmk-plugin
description: Build, upgrade, and package Checkmk monitoring plugins (MKP format) for Checkmk 2.3.x. Use this skill whenever the user mentions Checkmk plugins, check_mk, monitoring plugins, MKP packages, SNMP monitoring with Checkmk, Checkmk agent plugins, bakery plugins, special agents, Checkmk notification plugins, metric migration, or needs to work with Checkmk's plugin APIs (cmk.agent_based, cmk.graphing, cmk.rulesets). Also trigger when you see files in paths like cmk_addons/plugins/, local/lib/python3/cmk/, or local/share/check_mk/. Even if the user just says "create a check" or "monitor X" in the context of a Checkmk project, use this skill.
---

# Checkmk Plugin Development

This skill guides you through building, upgrading, and packaging Checkmk 2.3.x monitoring plugins. It covers agent-based checks, SNMP monitoring, special agents, notification plugins, metrics/graphing, rulesets, bakery integration, and MKP packaging via the `oposs/mkp-builder` GitHub Action.

**Not officially affiliated with Checkmk GmbH** — this is community-developed documentation.

## Task Router

Before diving in, identify the task type and read the appropriate reference(s). The references live alongside this file in `references/`.

| Task | Read these references (in order) |
|------|----------------------------------|
| Create first plugin | (this file has everything you need) |
| SNMP device monitoring | `02-snmp-plugins.md` then `04-check-plugins.md` |
| Agent-based monitoring (Linux/Windows) | `03-agent-plugins.md` then `04-check-plugins.md` |
| REST API / cloud / special protocol | `12-special-agents.md` then `04-check-plugins.md` |
| Add graphs and visualizations | `05-metrics-graphing.md` |
| GUI configuration (thresholds) | `06-rulesets.md` |
| Agent bakery (auto-deploy) | `07-bakery.md` and `06-rulesets.md` |
| Custom alerts (Slack, Discord, etc.) | `14-notifications.md` |
| Rename metrics preserving history | `13-metric-migration.md` |
| Cluster/inventory/host labels | `09-advanced-patterns.md` |
| Debug a non-working plugin | `08-testing-debugging.md` |
| See complete real-world examples | `10-examples.md` |
| API imports and quick reference | `11-reference.md` |
| Package as MKP / CI setup | `mkp-builder.md` |

**Decision tree:**
```
What type of monitoring?
+-- SNMP device         --> 02-snmp-plugins.md --> 04-check-plugins.md
+-- Agent (Linux/Win)   --> 03-agent-plugins.md --> 04-check-plugins.md
+-- API/Cloud/Custom    --> 12-special-agents.md --> 04-check-plugins.md
+-- Already have data   --> 04-check-plugins.md
    \-- Then optionally --> 05-metrics-graphing.md, 06-rulesets.md, 07-bakery.md
```

## Critical Conventions

These rules apply to ALL plugin types. Violations cause silent failures that are hard to debug.

### Directory Structure

```
your-plugin-repo/
+-- local/
|   +-- lib/python3/
|   |   +-- cmk_addons/plugins/<plugin_name>/
|   |   |   +-- agent_based/        # Check plugins (.py)
|   |   |   +-- graphing/           # Metric/graph definitions (.py)
|   |   |   +-- rulesets/           # GUI config forms (.py)
|   |   |   +-- server_side_calls/  # Special agent connectors (.py)
|   |   |   +-- libexec/            # Special agent scripts
|   |   |   \-- checkman/           # Documentation
|   |   \-- cmk/base/cee/plugins/bakery/  # Bakery plugins (.py)
|   \-- share/check_mk/
|       +-- agents/plugins/         # Agent scripts (bash/python, executable)
|       \-- notifications/          # Notification scripts (executable)
+-- .mkp-builder.ini                # MKP packaging config
\-- .github/workflows/build.yml     # CI/CD
```

**Required symlink** (prevents production path issues):
```bash
mkdir -p ./local/lib/python3/cmk
ln -s python3/cmk ./local/lib/check_mk
```

### Entry-Point Variable Prefixes (MANDATORY)

Checkmk discovers plugins by scanning for module-level variables with specific prefixes. Without the correct prefix, your plugin is invisible.

| Prefix | Purpose | Example |
|--------|---------|---------|
| `agent_section_` | Agent data parser | `agent_section_myservice = AgentSection(...)` |
| `snmp_section_` | SNMP data parser | `snmp_section_mydevice = SimpleSNMPSection(...)` |
| `check_plugin_` | Check logic | `check_plugin_myservice = CheckPlugin(...)` |
| `inventory_plugin_` | HW/SW inventory | `inventory_plugin_myservice = InventoryPlugin(...)` |
| `special_agent_` | Special agent config | `special_agent_myapi = SpecialAgentConfig(...)` |
| `rule_spec_` | Ruleset definition | `rule_spec_myservice = CheckParameters(...)` |
| `metric_` | Metric definition | `metric_acme_widget_cpu = Metric(...)` |
| `graph_` | Graph definition | `graph_acme_widget_perf = Graph(...)` |
| `perfometer_` | Perfometer | `perfometer_acme_widget_cpu = Perfometer(...)` |
| `translation_` | Metric translation | `translation_acme_widget = Translation(...)` |

**Wrong:** `my_section = AgentSection(...)` — Checkmk ignores it.
**Right:** `agent_section_my_service = AgentSection(...)` — discovered automatically.

### Metric Naming

Checkmk has ~1,000 built-in metrics. Unprefixed names silently conflict and break graphing.

**Format:** `{company}_{plugin}_{metric_name}`

```python
# WRONG - will conflict with built-in metrics
yield Metric("cpu_usage", 45.0)
yield Metric("temperature", 65.0)

# RIGHT - prefixed and safe
yield Metric("acme_widget_cpu_usage", 45.0)
yield Metric("acme_widget_temperature", 65.0)
```

Ask the user for their organization/company name to determine the prefix (e.g., `acme_`, `myorg_`).

### Base SI Units

Always store metrics in base SI units. Checkmk's graphing layer handles display scaling.

- **Time:** seconds (not ms, us, ns)
- **Data:** bytes (not KB, MB, GB)
- **Frequency:** hertz (not kHz, MHz)

```python
# Convert before yielding
latency_s = latency_ms / 1000.0
size_bytes = size_kb * 1024
yield Metric("acme_widget_latency", latency_s)
yield Metric("acme_widget_size", size_bytes)
```

### SimpleLevels Format

Rulesets deliver levels as `("fixed", (warn, crit))` or `None`. Pass them directly to `check_levels()` — never unwrap or restructure them.

```python
# RIGHT - pass directly
yield from check_levels(
    value,
    levels_upper=params.get("cpu_levels"),  # passes ("fixed", (80, 90)) as-is
    metric_name="acme_widget_cpu",
    render_func=render.percent,
)

# WRONG - don't do this
warn, crit = params["cpu_levels"][1]  # breaks when None, fragile
```

### Condition Type in Rulesets

Match the condition to your discovery function:
- `yield Service()` (no item) --> use `HostCondition()`
- `yield Service(item="something")` --> use `HostAndItemCondition(item_title=Title("..."))`

Getting this wrong causes the ruleset to silently not apply.

## Minimal Working Plugin

This is a complete agent-based plugin in 2 files.

### 1. Agent Script
`./local/share/check_mk/agents/plugins/acme_widget` (make executable with `chmod +x`):
```bash
#!/bin/bash
echo "<<<acme_widget>>>"
echo "status OK"
echo "cpu_usage 45.2"
echo "temperature 62"
```

### 2. Check Plugin
`./local/lib/python3/cmk_addons/plugins/acme_widget/agent_based/acme_widget.py`:
```python
from cmk.agent_based.v2 import (
    AgentSection, CheckPlugin, CheckResult, DiscoveryResult,
    Result, Service, State, Metric, check_levels, render,
)

def parse_acme_widget(string_table):
    parsed = {}
    for line in string_table:
        if len(line) >= 2:
            try:
                parsed[line[0]] = float(line[1])
            except ValueError:
                parsed[line[0]] = line[1]
    return parsed

agent_section_acme_widget = AgentSection(
    name="acme_widget",
    parse_function=parse_acme_widget,
)

def discover_acme_widget(section):
    if section:
        yield Service()

def check_acme_widget(params, section):
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data from agent")
        return

    status = section.get("status", "UNKNOWN")
    yield Result(
        state=State.OK if status == "OK" else State.WARN,
        summary=f"Status: {status}",
    )

    yield from check_levels(
        section.get("cpu_usage", 0),
        levels_upper=params.get("cpu_levels"),
        metric_name="acme_widget_cpu_usage",
        label="CPU",
        render_func=render.percent,
    )

    yield from check_levels(
        section.get("temperature", 0),
        levels_upper=params.get("temp_levels"),
        metric_name="acme_widget_temperature",
        label="Temperature",
        render_func=lambda v: f"{v:.1f} C",
    )

check_plugin_acme_widget = CheckPlugin(
    name="acme_widget",
    service_name="ACME Widget",
    sections=["acme_widget"],
    discovery_function=discover_acme_widget,
    check_function=check_acme_widget,
    check_ruleset_name="acme_widget_params",
    check_default_parameters={
        "cpu_levels": ("fixed", (80.0, 90.0)),
        "temp_levels": ("fixed", (70.0, 85.0)),
    },
)
```

### Deploy and Test
```bash
scp ./local/share/check_mk/agents/plugins/acme_widget root@target:/usr/lib/check_mk_agent/plugins/
cmk -R
cmk -II target_hostname
cmk -v --debug target_hostname
```

## Core API Imports

```python
# Agent-based API (Checkmk 2.3.x)
from cmk.agent_based.v2 import (
    AgentSection, SimpleSNMPSection, SNMPSection,
    CheckPlugin, InventoryPlugin,
    Result, Service, State, Metric, HostLabel,
    CheckResult, DiscoveryResult, InventoryResult,
    check_levels, get_rate, get_value_store, render,
    SNMPTree, SNMPDetectSpecification,
    OIDEnd, OIDBytes, OIDCached,
    exists, equals, contains, startswith, endswith, matches,
    all_of, any_of, not_exists, not_contains,
)

# Graphing API
from cmk.graphing.v1 import Title
from cmk.graphing.v1.metrics import Color, DecimalNotation, IECNotation, TimeNotation, Metric, Unit
from cmk.graphing.v1.graphs import Graph, MinimalRange, Bidirectional
from cmk.graphing.v1.perfometers import Perfometer, FocusRange, Closed, Stacked

# Rulesets API
from cmk.rulesets.v1 import Title, Help, Label
from cmk.rulesets.v1.form_specs import (
    Dictionary, DictElement, Integer, Float, String, BooleanChoice,
    SimpleLevels, LevelDirection, DefaultValue,
    CascadingSingleChoice, CascadingSingleChoiceElement,
    List, MultipleChoice, MultipleChoiceElement,
    RegularExpression, TimeSpan, TimeMagnitude, DataSize, validators,
)
from cmk.rulesets.v1.rule_specs import (
    CheckParameters, AgentConfig, Topic,
    HostCondition, HostAndItemCondition,
)

# Bakery API
from cmk.base.plugins.bakery.bakery_api.v1 import (
    register, Plugin, PluginConfig, OS,
    WindowsConfigEntry, FileGenerator, ScriptletGenerator,
)
```

## MKP Packaging

Use the `oposs/mkp-builder` GitHub Action to build MKP packages from the standard directory layout.

### Config file `.mkp-builder.ini`
```ini
[package]
name = acme_widget
title = ACME Widget Monitor
author = Your Name <you@example.com>
description = Monitors ACME Widget devices
version.min_required = 2.3.0p1
version.packaged = 2.3.0p34
download_url = https://github.com/yourorg/acme-widget-check
validate_python = true
```

### GitHub Actions workflow
```yaml
name: Build MKP
on:
  push:
    tags: ['v*']
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Extract version
        id: version
        run: echo "version=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
      - name: Build MKP
        id: build
        uses: oposs/mkp-builder@v2
        with:
          version: ${{ steps.version.outputs.version }}
      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: ${{ steps.build.outputs.package-file }}
```

Read `references/mkp-builder.md` for the full MKP builder reference including advanced workflows, outputs, troubleshooting, and MKP format details.

## Upgrading Existing Plugins

When upgrading a plugin from the old Checkmk API (pre-2.3) or fixing convention issues:

1. **Check entry-point prefixes** — ensure all module-level variables use the correct prefix
2. **Add metric prefixes** — rename bare metrics like `cpu` to `acme_widget_cpu`; use translations to preserve history (see `references/13-metric-migration.md`)
3. **Convert to base SI units** — if metrics were stored in ms/KB, add `ScaleBy` translations
4. **Update imports** — change `cmk.agent_based.v1` to `cmk.agent_based.v2`
5. **Fix SimpleLevels handling** — ensure parameters are passed directly to `check_levels()`
6. **Update directory structure** — move files to `cmk_addons/plugins/<name>/` layout
7. **Add `.mkp-builder.ini`** — for automated MKP packaging

## Debug Commands

```bash
check_mk_agent | grep -A5 "<<<section_name>>>"   # Test agent output
cmk -R                                             # Reload config
cmk -II hostname                                   # Rediscover services
cmk -v --debug hostname                            # Debug check execution
cmk -d hostname                                    # Dump raw agent data
cmk --detect-plugins=name hostname                 # Test SNMP detection
snmpwalk -v2c -c public host .1.3.6.1.2.1.1       # SNMP exploration
```

## Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| Plugin not discovered | Missing variable prefix | Add `agent_section_`, `check_plugin_`, etc. |
| Metrics conflict | Unprefixed metric names | Use `company_plugin_metric` format |
| Ruleset doesn't apply | Wrong condition type | Match `HostCondition`/`HostAndItemCondition` to discovery |
| SimpleLevels crash | Unwrapping the tuple | Pass directly to `check_levels()` |
| Graphs show wrong scale | Non-base units stored | Convert to seconds/bytes before yielding |
| Agent plugin not running | Not executable | `chmod +x` the agent script |
| Import error | Wrong API version | Use `cmk.agent_based.v2` for Checkmk 2.3.x |
| No section output | Missing `<<<section>>>` header | Agent must print `<<<section_name>>>` |
