# Contributing to CheckMK MKP Builder

Thank you for your interest in contributing to the CheckMK MKP Builder Action! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information**:
   - Operating system and version
   - CheckMK version
   - Action version
   - Complete error messages
   - Minimal reproduction case

### Suggesting Features

1. **Check existing feature requests** to avoid duplicates
2. **Describe the problem** you're trying to solve
3. **Explain your proposed solution** with examples
4. **Consider backwards compatibility**

### Pull Requests

1. **Fork the repository** and create a feature branch
2. **Make your changes** with clear, focused commits
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

## Development Setup

### Testing Changes

You can test the action locally by:

1. **Setting up a test repository** with CheckMK plugin structure
2. **Copying your modified files** to the test repository
3. **Running the build script directly**:
   ```bash
   ./mkp-builder.sh --version 1.0.0-test --verbose
   ```

### Testing in GitHub Actions

1. **Push to a fork** of this repository
2. **Reference your fork** in a test workflow:
   ```yaml
   - uses: yourusername/mkp-builder@your-branch
   ```
3. **Test with various inputs** and directory structures

## Code Style

### Shell Scripts

- Use `#!/bin/bash` shebang
- Set `set -euo pipefail` for error handling
- Use meaningful variable names
- Add comments for complex logic
- Quote variables to prevent word splitting
- Use `[[ ]]` instead of `[ ]` for tests

### YAML Files

- Use 2-space indentation
- Quote strings when needed
- Use meaningful step names
- Group related inputs/outputs logically

### Documentation

- Use clear, concise language
- Provide working examples
- Update README.md for new features
- Include troubleshooting for common issues

## Testing Guidelines

### Manual Testing

Test the action with:

1. **Minimal plugin structure** (agent plugin only)
2. **Complete plugin structure** (all components)
3. **Various CheckMK versions**
4. **Different input combinations**
5. **Edge cases** (missing files, invalid syntax)

### Validation Checklist

- [ ] Action works with minimal inputs
- [ ] Action works with all inputs provided
- [ ] Configuration file is respected
- [ ] Python validation works correctly
- [ ] Verbose output is helpful
- [ ] Error messages are clear
- [ ] Generated MKP installs correctly in CheckMK
- [ ] Documentation is updated

## Release Process

1. **Update version** in relevant files
2. **Update CHANGELOG** with new features/fixes
3. **Tag the release** following semantic versioning
4. **Test the tagged version** before announcing
5. **Update marketplace** if needed

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and improve
- Keep discussions relevant and professional

## Getting Help

- **Create an issue** for bugs or feature requests
- **Start a discussion** for questions or ideas
- **Check existing documentation** first

## Recognition

Contributors will be recognized in:
- Release notes
- README acknowledgments
- GitHub contributors list

Thank you for helping make the CheckMK MKP Builder better for everyone!
