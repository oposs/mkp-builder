# CheckMK Plugin Development Guide

**Comprehensive modular documentation for CheckMK 2.3.x plugin development**

## 📖 How to Use This Documentation

**For ALL tasks:**
1. **Start with** `00-index.md` - Find the right documents for your task
2. **Always load** `01-quickstart.md` - Contains naming conventions used everywhere
3. **Then load** task-specific documents as needed

**Why?** The quickstart contains foundational concepts (naming conventions, directory structure, entry points) that all other documents reference. Loading it first prevents confusion and redundancy.

---

## ✅ Completed Files

### 00-index.md (96 lines)
- Task-to-document mapping
- Quick decision tree
- Document descriptions
- Prerequisites
- Critical warnings

### 01-quickstart.md (159 lines) ⭐ **ALWAYS LOAD THIS FIRST**
- **CRITICAL: Naming conventions** (entry points, metrics, plugins)
- Minimal working plugin example
- Directory structure setup
- Entry point prefixes (agent_section_, check_plugin_, etc.)
- Metric naming (`mycompany_myplugin_` format)
- Common pitfalls
- Debug commands

**Why load first:** Contains foundational naming conventions referenced by ALL other documents

### 02-snmp-plugins.md (334 lines)
- SimpleSNMPSection vs SNMPSection
- Detection specifications
- Special OID types (OIDEnd, OIDBytes, OIDCached)
- Multi-item discovery
- Complete UPS example
- Testing & troubleshooting

### 03-agent-plugins.md (329 lines)
- Output format requirements
- Python agent template
- JSON encoding patterns
- Error handling
- Performance optimization
- Testing methods

### 04-check-plugins.md (450 lines)
- AgentSection and CheckPlugin classes
- Parse functions with error handling
- Discovery and check functions
- check_levels usage and SimpleLevels
- Multi-item services
- Parameters and defaults

### 05-metrics-graphing.md (462 lines)
- Metric definitions
- Graph configurations
- Perfometer setup
- **CRITICAL: Base SI units (seconds, bytes)**
- Unit conversion patterns
- Optional metrics and NaN handling
- Color constants reference

### 06-rulesets.md (300 lines)
- Form specifications
- HostAndItemCondition vs HostAndServiceCondition
- SimpleLevels configuration
- Dictionary elements
- CascadingSingleChoice patterns
- Parameter validation

### 07-bakery.md (250 lines)
- Bakery plugin structure
- Files function
- Agent deployment configuration
- Bakery rulesets (separate from technical logic)
- Platform-specific deployment
- Scriptlets

### 08-testing-debugging.md (300 lines)
- Unit testing patterns
- Debug commands
- Common errors and solutions
- Validation scripts
- Logging strategies
- Performance profiling

### 09-advanced-patterns.md (350 lines)
- Cluster support
- Inventory integration
- Host labels
- Multi-site considerations
- Custom render functions
- Time unit handling

### 10-examples.md (400 lines)
- Complete temperature monitoring example
- Real-world patterns from production
- Integration patterns
- Best practices demonstration

### 11-reference.md (250 lines)
- API import reference
- Color constants
- Common SNMP OIDs
- Checkman documentation format
- Useful commands cheatsheet

### 12-special-agents.md (834 lines)
- Special agent architecture (4 parts: libexec, server_side_calls, rulesets, agent_based)
- Server-side data collection
- REST API and cloud service monitoring
- Password handling and authentication
- Complete ACME Weather API example
- Testing special agents

### 13-metric-migration.md (375 lines)
- Translation system for metric renaming
- Preserving historical data during metric changes
- RenameTo, ScaleBy, RenameToAndScaleBy operations
- Unit conversions and scaling
- Real-world migration examples
- Plugin author workflow for metric updates

---

## 📊 Documentation Status

**All 14 core documentation files are complete!** (00-13 plus README)

Total: ~5,000 lines covering all aspects of CheckMK 2.3.x plugin development.

## Benefits Achieved

### Token Efficiency
- **Original guide**: 4,595 lines (all loaded every time)
- **Modular approach**:
  - Core foundation: 255 lines (00-index.md + 01-quickstart.md) ⭐
  - Task-specific: ~250-450 lines per document
  - **Typical task**: 500-1,200 lines (foundation + 1-3 task docs)
  - **Average reduction**: 67-89% fewer tokens loaded

**Example comparisons:**
- Simple agent plugin: 255 + 329 = 584 lines (87% reduction)
- SNMP with checks: 255 + 334 + 450 = 1,039 lines (77% reduction)
- Full special agent with metrics: 255 + 834 + 450 + 462 = 2,001 lines (56% reduction)

### Task Focus
- Each document addresses specific development phase
- Clear separation of concerns
- Easy to find relevant information

### Maintainability
- Update individual topics without affecting others
- Version control friendly
- Easier to review changes

### Usage Pattern

**Standard workflow for any task:**
```bash
# Step 1: ALWAYS load foundational documents
docs/00-index.md        # Find what you need (96 lines)
docs/01-quickstart.md   # Naming conventions + basics (159 lines) ⭐ REQUIRED

# Step 2: Load task-specific documents
# Example: SNMP UPS plugin development
docs/02-snmp-plugins.md  # SNMP specifics (334 lines)
docs/04-check-plugins.md # Check logic (450 lines)
docs/05-metrics-graphing.md # If you need graphs (462 lines)

# Total: ~1,500 lines vs 4,595 lines (67% reduction)
# Without metrics/graphing: ~1,039 lines (77% reduction)
```

**Key principle:** 01-quickstart.md establishes naming conventions that ALL other guides reference, preventing redundancy while ensuring consistency.

## Implementation Notes

The modular structure allows for:
1. **Foundation-first approach** - 00-index.md + 01-quickstart.md establish core concepts
2. **Selective loading** - Load only needed task-specific documents
3. **Single source of truth** - Naming conventions centralized in 01-quickstart.md
4. **Cross-references** - All documents reference the foundation instead of duplicating
5. **Progressive disclosure** - Start with basics, add complexity as needed
6. **Efficient updates** - Change one topic without touching others

**Key Architecture Decision:** Naming conventions are in the quickstart (not scattered) because:
- They apply to ALL plugin types (agent, SNMP, special agents)
- They're needed from day one (not advanced topics)
- Centralizing them prevents conflicting advice
- Cross-referencing avoids 1,000+ lines of duplication

## Quick Start

**New to CheckMK plugin development?**

1. Read [`00-index.md`](00-index.md) - Find what you need
2. Read [`01-quickstart.md`](01-quickstart.md) - Learn naming conventions and basics
3. Follow the index to your specific task

**Common starting points:**
- Creating your first plugin? → [01-quickstart.md](01-quickstart.md)
- SNMP device monitoring? → [02-snmp-plugins.md](02-snmp-plugins.md)
- Agent-based monitoring? → [03-agent-plugins.md](03-agent-plugins.md)
- REST API/Cloud monitoring? → [12-special-agents.md](12-special-agents.md)
- Need to rename metrics? → [13-metric-migration.md](13-metric-migration.md)