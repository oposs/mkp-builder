# CheckMK MKP Package Structure and Build Guide

## Overview

MKP (Monitoring Konfiguration Package) files are CheckMK's package format for distributing plugins, checks, and extensions. This document provides a comprehensive guide to understanding and building MKP packages.

## MKP Package Structure

### File Format
- **Container**: Gzip-compressed tar archive (`.tar.gz` with `.mkp` extension)
- **Compression**: Maximum gzip compression
- **Contents**: Multiple tar archives and metadata files

### Package Components

An MKP package contains the following files:

```
package.mkp (gzip compressed)
├── info                    # Python dict with package metadata
├── info.json              # JSON version of metadata
├── agents.tar             # Agent plugins and scripts
├── cmk_addons_plugins.tar # CheckMK addon plugins
└── lib.tar                # Library files (bakery plugins)
```

## Component Details

### 1. Metadata Files

#### `info` (Python Dictionary Format)
```python
{
    'author': 'Author Name <email@domain.com>',
    'description': 'Multi-line description of the package functionality',
    'download_url': '',  # Optional download URL
    'files': {
        'agents': ['plugins/plugin_name'],
        'cmk_addons_plugins': [
            'agent_based/plugin_name.py',
            'checkman/plugin_name',
            'graphing/plugin_name.py',
            'rulesets/plugin_name.py',
            'rulesets/plugin_name_bakery.py'
        ],
        'lib': ['check_mk/base/cee/plugins/bakery/plugin_name.py']
    },
    'name': 'plugin_name',
    'title': 'Human Readable Title',
    'version': '1.0.0',
    'version.min_required': '2.3.0p1',
    'version.packaged': '2.3.0p34',
    'version.usable_until': None
}
```

#### `info.json` (JSON Format)
Same structure as `info` but in JSON format for easier parsing.

### 2. Agent Components (`agents.tar`)

Contains files that will be deployed to monitored hosts:

```
plugins/
├── plugin_name           # Main agent plugin script
├── plugin_name.py        # Python agent plugin
└── special/plugin_name   # Special agent plugin
```

**Installation Path**: `/usr/lib/check_mk_agent/plugins/`

### 3. CheckMK Addons (`cmk_addons_plugins.tar`)

Contains CheckMK server-side components:

```
agent_based/
├── plugin_name.py        # Check plugin (CMK 2.x API)

checkman/
├── plugin_name           # Manual page documentation

graphing/
├── plugin_name.py        # Metrics and graph definitions

rulesets/
├── plugin_name.py        # Check configuration rules
└── plugin_name_bakery.py # Agent bakery rules

plugin_name/              # Plugin-specific directory
├── agent_based/
├── checkman/
├── graphing/
└── rulesets/
```

**Installation Path**: `~SITE/local/lib/python3/cmk_addons/plugins/`

### 4. Library Components (`lib.tar`)

Contains CheckMK core extensions:

```
check_mk/base/cee/plugins/bakery/
├── plugin_name.py        # Agent bakery plugin
```

**Installation Path**: `~SITE/local/lib/python3/`

## Directory Structure Requirements

Your source project should follow this structure:

```
project_root/
├── local/                # CheckMK local directory structure
│   ├── lib/
│   │   └── python3/
│   │       ├── cmk/      # note three is local/check_mk -> python3/cmk
│   │       │   └── base/cee/plugins/bakery/
│   │       │       └── plugin_name.py
│   │       └── cmk_addons/plugins/
│   │           └── plugin_name/
│   │               ├── agent_based/
│   │               ├── checkman/
│   │               ├── graphing/
│   │               └── rulesets/
│   └── share/check_mk/agents/plugins/
│       └── plugin_name
├── .mkp-builder.ini      # Package configuration
```

Note: a common source of confusion is the path
`check_mk/base/cee/plugins/bakery/` actually the path is
`python3/cmk/base/cee/plugins/bakery/` since `check_mk` is actually
a symlink to `python3/cmk`.


## Build Process

### 1. Manual Build Steps

1. **Create metadata**:
   ```bash
   # Generate info and info.json files
   ```

2. **Create component archives**:
   ```bash
   # Create agents.tar
   tar -cf agents.tar -C local/share/check_mk/agents plugins/

   # Create cmk_addons_plugins.tar  
   tar -cf cmk_addons_plugins.tar -C local/lib/python3/cmk_addons/plugins .

   # Create lib.tar
   tar -cf lib.tar -C local/lib/python3 check_mk/
   ```

3. **Package final MKP**:
   ```bash
   tar -czf package_name-version.mkp info info.json agents.tar cmk_addons_plugins.tar lib.tar
   ```

### 2. Automated Build Script

Use the provided `build-mkp.sh` script:

```bash
./build-mkp.sh [options]
```

## Package Configuration

### `.build-mkprc` Format

```bash
# Package Information (no version - comes from command line)
PACKAGE_NAME="plugin_name"
PACKAGE_TITLE="Human Readable Title" 
PACKAGE_AUTHOR="Author Name <email@domain.com>"
PACKAGE_DESCRIPTION="Multi-line package description"

# CheckMK Compatibility
CMK_MIN_VERSION="2.3.0p1"
CMK_PACKAGED_VERSION="2.3.0p34"

# Optional
DOWNLOAD_URL=""
VERSION_USABLE_UNTIL=""

# Build Options
VALIDATE_PYTHON="yes"
```

## File Mapping Logic

The build process automatically maps files from your local directory structure:

### Agents Mapping
- Source: `local/share/check_mk/agents/plugins/*`
- Target: `plugins/*` in agents.tar
- Pattern: All executable files in plugins directory

### CMK Addons Mapping
- Source: `local/lib/python3/cmk_addons/plugins/PACKAGE_NAME/*`
- Target: `PACKAGE_NAME/*` and flat structure in cmk_addons_plugins.tar
- Pattern: Recursive inclusion of all Python files and documentation

### Library Mapping  
- Source: `local/lib/python3/cmk/base/cee/plugins/bakery/PACKAGE_NAME.py`
- Target: `check_mk/base/cee/plugins/bakery/PACKAGE_NAME.py` in lib.tar
- Pattern: Bakery plugin files only

## Version Management

### Semantic Versioning
- Format: `MAJOR.MINOR.PATCH`
- Example: `1.0.0`, `1.2.3`, `2.0.0-beta1`

### CheckMK Version Compatibility
- `version.min_required`: Minimum CheckMK version
- `version.packaged`: CheckMK version used for packaging
- `version.usable_until`: Maximum compatible version (optional)

## Validation and Testing

### Pre-build Validation
1. **File Structure**: Verify all required files exist
2. **Python Syntax**: Check all Python files compile
3. **Naming Consistency**: Ensure consistent naming throughout
4. **Dependencies**: Verify all imports are available

### Post-build Validation
1. **Archive Integrity**: Verify tar files are valid
2. **Metadata Consistency**: Check info and info.json match
3. **File Permissions**: Ensure executable bits are preserved
4. **Size Limits**: Check package size is reasonable

### Installation Testing
1. **Extract Package**: Test MKP extraction
2. **File Placement**: Verify files go to correct locations
3. **Import Check**: Test Python module imports
4. **Service Discovery**: Verify check discovery works

## Common Issues and Solutions

### Build Issues

**Issue**: Missing files in package
- **Cause**: Incorrect directory structure
- **Solution**: Follow exact directory layout requirements

**Issue**: Python import errors
- **Cause**: Inconsistent naming or missing dependencies  
- **Solution**: Use consistent naming throughout all components

**Issue**: Permission denied errors
- **Cause**: Agent plugins not executable
- **Solution**: Set executable permissions before packaging

### Installation Issues

**Issue**: Package not recognized by CheckMK
- **Cause**: Invalid metadata format
- **Solution**: Validate info/info.json structure

**Issue**: Services not discovered
- **Cause**: Agent plugin deployment failed
- **Solution**: Check agent plugin permissions and paths

**Issue**: Import errors after installation
- **Cause**: Missing dependencies or API mismatches
- **Solution**: Verify CheckMK version compatibility

## Best Practices

### Development
1. **Consistent Naming**: Use same name throughout all components
2. **API Compatibility**: Use appropriate CheckMK API versions
3. **Error Handling**: Implement robust error handling
4. **Documentation**: Include comprehensive checkman documentation
5. **Testing**: Test on clean CheckMK instance

### Packaging
1. **Version Control**: Tag releases in version control
2. **Changelog**: Maintain detailed change documentation
3. **Dependencies**: Document all requirements clearly
4. **Backwards Compatibility**: Consider upgrade paths

### Distribution
1. **Package Signing**: Consider digital signatures for security
2. **Repository**: Use proper package repositories
3. **Documentation**: Provide installation and configuration guides
4. **Support**: Establish support channels

## Advanced Topics

### Custom File Layouts
For non-standard layouts, modify the build script's file mapping logic.

### Multiple Packages
For projects with multiple related packages, consider:
- Shared components
- Dependency management  
- Coordinated versioning

### Enterprise Features
Some features require CheckMK Enterprise Edition:
- Agent Bakery integration
- Certain API features
- Advanced configuration options

## Appendix

### Example Package Metadata
See the extracted `temp_mkp/info` and `temp_mkp/info.json` files for real-world examples.

### File Permissions
- Agent plugins: 755 (executable)
- Python modules: 644 (readable)
- Documentation: 644 (readable)

### Useful Commands
```bash
# Extract MKP for inspection
mkdir temp && cd temp && tar -xzf ../package.mkp

# List MKP contents
tar -tzf package.mkp

# Validate tar files
tar -tf agents.tar
tar -tf cmk_addons_plugins.tar  
tar -tf lib.tar

# Check Python syntax
python3 -m py_compile file.py

# Test agent plugin
./local/share/check_mk/agents/plugins/plugin_name
```

This documentation provides everything needed to understand and build CheckMK MKP packages from scratch.
