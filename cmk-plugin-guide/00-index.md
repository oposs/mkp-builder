# CheckMK Plugin Development - Document Index
## CheckMK 2.3.0

> **⚠️ Disclaimer**: This documentation is an independent, community-developed resource and is **not officially affiliated with or endorsed by CheckMK GmbH**.

## Quick Task Mapping

### "I need to..."

| Task | Primary Document | Additional Docs |
|------|-----------------|-----------------|
| **Create my first plugin** | [01-quickstart.md](01-quickstart.md) | - |
| **Monitor a network device via SNMP** | [02-snmp-plugins.md](02-snmp-plugins.md) | [04-check-plugins.md](04-check-plugins.md) |
| **Collect data from a Linux/Windows host** | [03-agent-plugins.md](03-agent-plugins.md) | [04-check-plugins.md](04-check-plugins.md) |
| **Process and check collected data** | [04-check-plugins.md](04-check-plugins.md) | [05-metrics-graphing.md](05-metrics-graphing.md) |
| **Add graphs and visualizations** | [05-metrics-graphing.md](05-metrics-graphing.md) | - |
| **Configure thresholds in the GUI** | [06-rulesets.md](06-rulesets.md) | - |
| **Deploy plugins automatically** | [07-bakery.md](07-bakery.md) | [06-rulesets.md](06-rulesets.md) |
| **Debug a non-working plugin** | [08-testing-debugging.md](08-testing-debugging.md) | - |
| **Handle cluster environments** | [09-advanced-patterns.md](09-advanced-patterns.md) | - |
| **See a complete example** | [10-examples.md](10-examples.md) | - |
| **Look up API details** | [11-reference.md](11-reference.md) | - |

## Decision Tree

```
START: What type of monitoring?
├── SNMP Device → 02-snmp-plugins.md
│   └── Then → 04-check-plugins.md → 05-metrics-graphing.md
├── Agent-based (Linux/Windows) → 03-agent-plugins.md
│   └── Then → 04-check-plugins.md → 05-metrics-graphing.md
└── Already have data → 04-check-plugins.md
    └── Then → 05-metrics-graphing.md

Need GUI configuration? → 06-rulesets.md
Need automatic deployment? → 07-bakery.md
Having problems? → 08-testing-debugging.md
```

## Document Descriptions

### Core Documents (Start Here)
- **[01-quickstart.md](01-quickstart.md)** - Minimal working example, directory structure, common pitfalls
- **[11-reference.md](11-reference.md)** - API imports, constants, quick reference

### Development Phase Documents

#### Data Collection
- **[02-snmp-plugins.md](02-snmp-plugins.md)** - SNMP monitoring via network
- **[03-agent-plugins.md](03-agent-plugins.md)** - Host-based data collection

#### Data Processing
- **[04-check-plugins.md](04-check-plugins.md)** - Parse data, determine states, generate metrics
- **[05-metrics-graphing.md](05-metrics-graphing.md)** - Visualizations and performance data

#### Configuration & Deployment
- **[06-rulesets.md](06-rulesets.md)** - GUI configuration forms
- **[07-bakery.md](07-bakery.md)** - Automatic agent deployment

#### Advanced Topics
- **[08-testing-debugging.md](08-testing-debugging.md)** - Troubleshooting and validation
- **[09-advanced-patterns.md](09-advanced-patterns.md)** - Clusters, inventory, host labels
- **[10-examples.md](10-examples.md)** - Complete real-world examples

## Prerequisites

Before starting:
- CheckMK 2.3.0 installation
- Python 3 knowledge
- Access to CheckMK site
- Understanding of what you want to monitor

## Critical Warnings

⚠️ **Directory Structure**: Always use `./local/lib/python3/cmk` as the actual directory
⚠️ **Entry Points**: Variables must start with `agent_section_`, `snmp_section_`, `check_plugin_`
⚠️ **Units**: Always store metrics in base SI units (seconds, bytes)
⚠️ **SimpleLevels**: Never wrap parameters - pass directly to check_levels()

## Token Efficiency

This modular structure reduces token usage by ~80%:
- Full guide: 4,220 lines
- Typical task: 200-600 lines loaded
- Maximum efficiency: Load only what you need