# CheckMK Ruleset Integration
## GUI Configuration for Plugins

### Basic Ruleset Structure

```python
# File: ./local/lib/python3/cmk_addons/plugins/my_plugin/rulesets/my_service.py

from cmk.rulesets.v1 import Title, Help, Label
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    Integer,
    Float,
    String,
    BooleanChoice,
    SimpleLevels,
    LevelDirection,
    DefaultValue,
)
from cmk.rulesets.v1.rule_specs import (
    CheckParameters,
    Topic,
    HostAndServiceCondition,  # For single service
    HostAndItemCondition,      # For multi-item services
)

def _form_spec_my_service():
    return Dictionary(
        title=Title("My Service Configuration"),
        elements={
            "levels": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Warning and Critical Levels"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Float(unit_symbol="%"),
                    prefill_fixed_levels=DefaultValue((80.0, 90.0)),
                ),
                required=True,
            ),
        },
    )

rule_spec_my_service = CheckParameters(
    title=Title("My Service"),
    topic=Topic.APPLICATIONS,
    name="my_service",  # Must match check_ruleset_name
    parameter_form=_form_spec_my_service,
    condition=HostAndServiceCondition(),  # See below!
)
```

### ⚠️ CRITICAL: Condition Type Selection

#### For Single Service per Host
```python
# ✅ Use HostAndServiceCondition
condition=HostAndServiceCondition()
```

#### For Multi-Item Services
```python
# ✅ Use HostAndItemCondition
condition=HostAndItemCondition(
    item_title=Title("Device name")  # Describes the item
)
```

#### Common Mistake
```python
# ❌ WRONG - Type mismatch causes errors!
condition=HostAndServiceCondition(service_name="My Service")  # NO!
```

### SimpleLevels Configuration

```python
from cmk.rulesets.v1.form_specs import SimpleLevels, LevelDirection

# Upper thresholds (warn if above)
"cpu_levels": DictElement(
    parameter_form=SimpleLevels(
        title=Title("CPU Usage Levels"),
        level_direction=LevelDirection.UPPER,
        form_spec_template=Float(
            unit_symbol="%",
            custom_validate=[validators.NumberInRange(0, 100)]
        ),
        prefill_fixed_levels=DefaultValue((80.0, 90.0)),
    ),
),

# Lower thresholds (warn if below)
"battery_levels": DictElement(
    parameter_form=SimpleLevels(
        title=Title("Battery Charge Levels"),
        level_direction=LevelDirection.LOWER,
        form_spec_template=Float(unit_symbol="%"),
        prefill_fixed_levels=DefaultValue((20.0, 10.0)),
    ),
),

# No default levels
"optional_levels": DictElement(
    parameter_form=SimpleLevels(
        title=Title("Optional Levels"),
        level_direction=LevelDirection.UPPER,
        form_spec_template=Integer(),
        prefill_fixed_levels=None,  # User must configure
    ),
    required=False,
),
```

### Complete UPS Ruleset Example

```python
from cmk.rulesets.v1 import Title, Help
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    SimpleLevels,
    LevelDirection,
    DefaultValue,
    Float,
    TimeSpan,
    TimeMagnitude,
)
from cmk.rulesets.v1.rule_specs import (
    CheckParameters,
    Topic,
    HostAndServiceCondition,
)

def _form_spec_ups():
    return Dictionary(
        title=Title("UPS Monitoring Configuration"),
        help_text=Help("Configure thresholds for UPS monitoring"),
        elements={
            "battery_charge_lower": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Battery charge levels"),
                    help_text=Help("Warn if battery charge drops below these levels"),
                    level_direction=LevelDirection.LOWER,
                    form_spec_template=Float(
                        unit_symbol="%",
                        custom_validate=[validators.NumberInRange(0, 100)]
                    ),
                    prefill_fixed_levels=DefaultValue((20.0, 10.0)),
                ),
                required=True,
            ),
            "battery_runtime_lower": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Battery runtime levels"),
                    help_text=Help("Warn if runtime drops below these levels"),
                    level_direction=LevelDirection.LOWER,
                    form_spec_template=TimeSpan(
                        displayed_magnitudes=[
                            TimeMagnitude.MINUTE,
                            TimeMagnitude.SECOND,
                        ]
                    ),
                    prefill_fixed_levels=DefaultValue((600.0, 300.0)),  # seconds
                ),
                required=True,
            ),
            "voltage_upper": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Input voltage upper levels"),
                    level_direction=LevelDirection.UPPER,
                    form_spec_template=Float(unit_symbol="V"),
                    prefill_fixed_levels=DefaultValue((250.0, 260.0)),
                ),
            ),
            "voltage_lower": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Input voltage lower levels"),
                    level_direction=LevelDirection.LOWER,
                    form_spec_template=Float(unit_symbol="V"),
                    prefill_fixed_levels=DefaultValue((210.0, 200.0)),
                ),
            ),
        },
    )

rule_spec_ups = CheckParameters(
    title=Title("UPS Status Monitoring"),
    topic=Topic.POWER,
    name="ups_status",  # Matches check_ruleset_name in plugin
    parameter_form=_form_spec_ups,
    condition=HostAndServiceCondition(),  # Single service
)
```

### Advanced Form Elements

```python
from cmk.rulesets.v1.form_specs import (
    CascadingSingleChoice,
    CascadingSingleChoiceElement,
    List,
    MultipleChoice,
    MultipleChoiceElement,
    RegularExpression,
    DataSize,
    TimeSpan,
    validators,
)

def _advanced_form():
    return Dictionary(
        elements={
            # Choice between modes
            "mode": DictElement(
                parameter_form=CascadingSingleChoice(
                    title=Title("Monitoring Mode"),
                    elements=[
                        CascadingSingleChoiceElement(
                            name="simple",
                            title=Title("Simple"),
                            parameter_form=Dictionary(
                                elements={
                                    "threshold": DictElement(
                                        parameter_form=Integer(
                                            title=Title("Threshold"),
                                            prefill=DefaultValue(100),
                                        ),
                                    ),
                                },
                            ),
                        ),
                        CascadingSingleChoiceElement(
                            name="advanced",
                            title=Title("Advanced"),
                            parameter_form=Dictionary(
                                elements={
                                    "thresholds": DictElement(
                                        parameter_form=List(
                                            title=Title("Multiple thresholds"),
                                            element_template=Integer(),
                                        ),
                                    ),
                                },
                            ),
                        ),
                    ],
                    prefill=DefaultValue("simple"),
                ),
                required=True,
            ),
            
            # Multiple selections
            "features": DictElement(
                parameter_form=MultipleChoice(
                    title=Title("Enable features"),
                    elements=[
                        MultipleChoiceElement(
                            name="cpu",
                            title=Title("Monitor CPU"),
                        ),
                        MultipleChoiceElement(
                            name="memory",
                            title=Title("Monitor Memory"),
                        ),
                    ],
                    prefill=DefaultValue(["cpu"]),
                ),
            ),
            
            # Data size
            "max_size": DictElement(
                parameter_form=DataSize(
                    title=Title("Maximum size"),
                    prefill=DefaultValue(1024 * 1024 * 1024),  # 1GB in bytes
                ),
            ),
            
            # Time configuration
            "check_interval": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Check interval"),
                    displayed_magnitudes=[
                        TimeMagnitude.MINUTE,
                        TimeMagnitude.SECOND,
                    ],
                    prefill=DefaultValue(60.0),  # seconds
                ),
            ),
            
            # Regex pattern
            "pattern": DictElement(
                parameter_form=RegularExpression(
                    title=Title("Name pattern"),
                    prefill=DefaultValue(r".*"),
                    custom_validate=[
                        validators.LengthInRange(min_value=1),
                    ],
                ),
            ),
        },
    )
```

### Bakery Ruleset (Agent Deployment)

```python
# File: ./local/lib/python3/cmk_addons/plugins/my_plugin/rulesets/bakery.py

from cmk.rulesets.v1 import Title, Help, Label
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    TimeSpan,
    TimeMagnitude,
)
from cmk.rulesets.v1.rule_specs import AgentConfig, Topic

def _parameter_form_my_agent():
    return Dictionary(
        title=Title("My Service Agent Plugin"),
        help_text=Help("Deploy and configure the agent plugin"),
        elements={
            "enabled": DictElement(
                parameter_form=BooleanChoice(
                    title=Title("Enable plugin"),
                    label=Label("Deploy agent plugin"),
                    prefill=DefaultValue(True),
                )
            ),
            "interval": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Collection interval"),
                    help_text=Help("0 means every agent run"),
                    displayed_magnitudes=[
                        TimeMagnitude.SECOND,
                        TimeMagnitude.MINUTE,
                    ],
                    prefill=DefaultValue(60.0),
                )
            ),
            "timeout": DictElement(
                parameter_form=TimeSpan(
                    title=Title("Command timeout"),
                    displayed_magnitudes=[TimeMagnitude.SECOND],
                    prefill=DefaultValue(30.0),
                )
            ),
        }
    )

rule_spec_my_agent_bakery = AgentConfig(
    name="my_service",  # Matches bakery plugin name
    title=Title("My Service Agent Deployment"),
    topic=Topic.GENERAL,
    parameter_form=_parameter_form_my_agent,
)
```

### Parameter Usage in Check Plugin

```python
# In check plugin
def check_my_service(params: Mapping[str, Any], section: Dict) -> CheckResult:
    # SimpleLevels come as ("fixed", (warn, crit)) or None
    cpu_levels = params.get('cpu_levels')  # Don't unwrap!
    
    yield from check_levels(
        section.get("cpu", 0),
        levels_upper=cpu_levels,  # Pass directly!
        metric_name="cpu",
        label="CPU",
        render_func=render.percent,
    )
    
    # Other parameters
    if params.get('enabled', True):
        # Feature enabled
        pass
    
    interval = params.get('check_interval', 60)
    pattern = params.get('pattern', r'.*')
```

### Topics Reference

```python
from cmk.rulesets.v1.rule_specs import Topic

Topic.GENERAL           # General settings
Topic.APPLICATIONS      # Application monitoring
Topic.DATABASES         # Database systems
Topic.STORAGE           # Storage and filesystems
Topic.NETWORKING        # Network monitoring
Topic.POWER            # Power and UPS
Topic.ENVIRONMENT      # Environmental monitoring
Topic.OPERATING_SYSTEM # OS monitoring
Topic.HARDWARE         # Hardware monitoring
```

### Validation

```python
from cmk.rulesets.v1.form_specs import validators

# Common validators
validators.NumberInRange(min_value=0, max_value=100)
validators.LengthInRange(min_value=1, max_value=255)
validators.NetworkPort()  # 1-65535
validators.Url(schemes=["http", "https"])
validators.EmailAddress()
```

### Testing Rulesets

```python
# Test parameter structure
def test_ruleset_params():
    params = {
        'cpu_levels': ('fixed', (80.0, 90.0)),
        'memory_levels': None,
        'enabled': True,
        'interval': 60,
    }
    
    # Simulate check function
    cpu_levels = params.get('cpu_levels')
    assert cpu_levels == ('fixed', (80.0, 90.0))
    
    # Test with check_levels
    from cmk.agent_based.v2 import check_levels
    results = list(check_levels(
        85.0,
        levels_upper=cpu_levels,
        metric_name="cpu",
    ))
    assert any(r.state == State.WARN for r in results)
```

### Common Pitfalls

| Problem | Solution |
|---------|----------|
| Wrong condition type | Use HostAndItemCondition for multi-item |
| SimpleLevels wrapping | Pass directly to check_levels |
| Missing ruleset name | Must match check_ruleset_name |
| Wrong topic | Check available Topic constants |

### See Also
- [04-check-plugins.md](04-check-plugins.md) - Using parameters
- [07-bakery.md](07-bakery.md) - Agent deployment rules
- [05-metrics-graphing.md](05-metrics-graphing.md) - Threshold visualization