# Checkmk MKP Builder Action

[![GitHub release](https://img.shields.io/github/release/oposs/mkp-builder.svg)](https://github.com/oposs/mkp-builder/releases)
[![GitHub marketplace](https://img.shields.io/badge/marketplace-mkp--builder-blue?logo=github)](https://github.com/marketplace/actions/build-checkmk-mkp-package)

> **⚠️ Disclaimer**: This is an independent, community-developed tool and is **not officially affiliated with or endorsed by Checkmk GmbH**. This project was developed by reverse-engineering existing MKP package formats and studying Checkmk documentation. Any issues, bugs, or incompatibilities are our responsibility and should be reported to this project's issue tracker, not to Checkmk support.

> **📚 Plugin Development Guide**: Since many users of mkp-builder are developing Checkmk plugins, we maintain comprehensive modular documentation for Checkmk 2.3.x plugin development in [`cmk-plugin-guide/`](cmk-plugin-guide/). The guide covers agent plugins, SNMP plugins, special agents, check plugins, rulesets, graphing, bakery integration, and metric migration with practical examples and best practices. Start with the [guide index](cmk-plugin-guide/00-index.md) or read the [guide overview](cmk-plugin-guide/README.md).

> **🚨 Breaking Changes in v2.0.0**: If you're upgrading from v1.x, please note that v2.0.0 introduces breaking changes. The configuration file format has changed from `.mkp-builderrc` to `.mkp-builder.ini` with INI format syntax. GitHub Action input names have also been updated. See the [changelog](CHANGES.md) for full migration details.

A reusable GitHub Action for building Checkmk MKP (Monitoring Konfiguration Package) files from local directory structures.

## Features

- 🏗️ **Automated MKP Building**: Converts Checkmk plugin directory structures into installable MKP packages
- 🔧 **Configurable**: Supports all build options via inputs or configuration files
- 🐍 **Python Validation**: Optional syntax checking of Python files before packaging
- 📦 **Artifact Ready**: Outputs package information for easy artifact upload
- 🧹 **Clean**: No permanent changes to your repository
- ⚡ **Fast**: Downloads build tools on-demand, no bloated containers

## Quick Start

```yaml
- name: Build MKP Package
  uses: oposs/mkp-builder@v2
  with:
    version: '1.2.3'
```

## Version Pinning

For production use, choose the appropriate versioning strategy:

```yaml
# Pin to exact version (recommended for production)
- uses: oposs/mkp-builder@v2.0.0

# Pin to major version (gets latest features and fixes)  
- uses: oposs/mkp-builder@v2

# Use latest from main branch (not recommended for production)
- uses: oposs/mkp-builder@main
```

## Usage

### Basic Usage

```yaml
name: Build MKP Package

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
        uses: oposs/mkp-builder@v2
        with:
          version: ${{ steps.version.outputs.version }}
```

### Advanced Usage

```yaml
- name: Build MKP Package
  id: build-mkp
  uses: oposs/mkp-builder@v2
  with:
    version: ${{ github.ref_name }}
    package-name: 'my_plugin'
    title: 'My Awesome Plugin'
    author: 'John Doe <john@example.com>'
    description: 'A plugin that does amazing things'
    version-min-required: '2.3.0p1'
    version-packaged: '2.3.0p34'
    validate-python: 'true'
    verbose: 'true'

- name: Upload MKP Package
  uses: actions/upload-artifact@v4
  with:
    name: mkp-package
    path: ${{ steps.build-mkp.outputs.package-file }}
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `version` | Package version (e.g., 1.2.3) | ✅ | - |
| `package-name` | Package name | ❌ | Auto-detected |
| `title` | Package title | ❌ | From config file |
| `author` | Author name and email | ❌ | From config file |
| `description` | Package description | ❌ | From config file |
| `version-min-required` | Minimum Checkmk version | ❌ | From config file |
| `version-packaged` | Checkmk packaging version | ❌ | From config file |
| `download-url` | Download URL | ❌ | From config file |
| `version-usable-until` | The last Checkmk version this plugin is compatible with | ❌ | From config file |
| `output-dir` | Output directory | ❌ | `.` |
| `validate-python` | Validate Python files | ❌ | `true` |
| `verbose` | Enable verbose output | ❌ | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `package-file` | Path to the created MKP package file |
| `package-name` | Name of the package that was built |
| `package-size` | Size of the created package |

## Configuration File

Create a `.mkp-builder.ini` file in your repository root for default values:

```ini
[package]
# Package Information
name = my_plugin
title = My Awesome Plugin
author = John Doe <john@example.com>
description = A plugin that does amazing things.
    This description can span multiple lines
    and provides better formatting options.

# Checkmk Compatibility
version.min_required = 2.3.0p1
version.packaged = 2.3.0p34
version.usable_until = 3.0.0

# Optional
download_url = https://github.com/user/repo
validate_python = true
```

## Required Directory Structure

Your repository must follow the Checkmk local directory structure:

```
repository/
├── local/
│   ├── lib/python3/
│   │   ├── cmk_addons/plugins/
│   │   │   └── your_plugin/
│   │   │       ├── agent_based/
│   │   │       │   └── your_plugin.py
│   │   │       ├── checkman/
│   │   │       │   └── your_plugin
│   │   │       ├── graphing/
│   │   │       │   └── your_plugin.py
│   │   │       └── rulesets/
│   │   │           ├── your_plugin.py
│   │   │           └── your_plugin_bakery.py
│   │   └── cmk/base/cee/plugins/bakery/
│   │       └── your_plugin.py
│   └── share/check_mk/
│       ├── agents/plugins/
│       │   └── your_plugin
│       └── notifications/
│           └── your_notification.py
├── .mkp-builder.ini          # Optional config file
└── .github/workflows/
    └── build.yml
```

## Complete Workflow Examples

### Simple Release Workflow

```yaml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  release:
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
          verbose: 'true'
      
      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: ${{ steps.build.outputs.package-file }}
          generate_release_notes: true
```

### Advanced Workflow with Validation

```yaml
name: Build and Test

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Validate structure
        run: |
          if [[ ! -d "local" ]]; then
            echo "::error::Missing local/ directory"
            exit 1
          fi
      
      - name: Test build
        uses: oposs/mkp-builder@v2
        with:
          version: '0.0.0-test'
          validate-python: 'true'
          verbose: 'true'

  release:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: validate
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

## MKP Package Structure

The action creates MKP packages with the following structure:

```
package.mkp (tar file, gzip compressed)
├── info                    # Python dict with package metadata
├── info.json              # JSON version of metadata
├── agents.tar             # Agent plugins and scripts
├── cmk_addons_plugins.tar # CheckMK addon plugins
├── lib.tar                # Library files (bakery plugins)
└── notifications.tar      # Notification scripts
```

## Supported Checkmk Versions

- **Checkmk 2.3.x** (default)

## File Mapping

The action automatically maps files from your local directory structure:

### Agent Files
- Source: `local/share/check_mk/agents/plugins/*`
- Target: `plugins/*` in agents.tar

### CMK Addons
- Source: `local/lib/python3/cmk_addons/plugins/PACKAGE_NAME/*`
- Target: `PACKAGE_NAME/*` in cmk_addons_plugins.tar

### Library Files
- Source: `local/lib/python3/cmk/base/cee/plugins/bakery/PACKAGE_NAME.py`
- Target: `cmk/base/cee/plugins/bakery/PACKAGE_NAME.py` in lib.tar

### Notification Scripts
- Source: `local/share/check_mk/notifications/*`
- Target: notification files in notifications.tar

## Troubleshooting

### Common Issues

**"No MKP file found after build"**
- Ensure your `local/` directory structure is correct
- Check that your `.mkp-builder.ini` file has valid syntax
- Verify Python files pass validation

**"Package name could not be determined"**
- Add `package-name` input or set `name` in the `[package]` section of `.mkp-builder.ini`
- Ensure your agent plugin files exist in the correct location

**"Python syntax error"**
- Fix Python syntax errors in your plugin files
- Or set `validate-python: 'false'` to skip validation

### Debug Mode

Enable verbose output for detailed logging:

```yaml
- uses: oposs/mkp-builder@v2
  with:
    version: '1.0.0'
    verbose: 'true'
```

### Manual Testing

You can test the build script locally:

```bash
# Download the script
curl -sSL https://raw.githubusercontent.com/oposs/mkp-builder/main/mkp-builder.sh -o mkp-builder.sh
chmod +x mkp-builder.sh

# Run locally
./mkp-builder.sh --version 1.0.0 --verbose
```

## Version Pinning

For production use, pin to a specific version:

```yaml
# Pin to a specific version
- uses: oposs/mkp-builder@v2.0.0

# Pin to a major version (recommended)
- uses: oposs/mkp-builder@v2

# Use latest (not recommended for production)
- uses: oposs/mkp-builder@main
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development

1. Fork this repository
2. Make your changes
3. Test with a sample Checkmk plugin repository
4. Submit a pull request

### Reporting Issues

Please use the [issue tracker](https://github.com/oposs/mkp-builder/issues) to report bugs or request features.

## License

This project is licensed under the same terms as Checkmk - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [Checkmk Official Documentation](https://docs.checkmk.com/)
- [Checkmk Plugin Development Guide](https://docs.checkmk.com/latest/en/devel_intro.html)
- [MKP Package Format Specification](https://docs.checkmk.com/latest/en/mkps.html)

## Acknowledgments

- Built for the Checkmk community
- Inspired by the need for automated MKP package building
- Thanks to all contributors and testers

---

Made with ❤️  for the Checkmk community
