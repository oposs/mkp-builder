#!/usr/bin/env python3
"""
CheckMK MKP Package Builder (mkp-builder)
Builds MKP packages from local directory structure using Python standard library only.
"""

import argparse
import ast
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

# Version info
__version__ = "2.0.0"
__author__ = "OETIKER+PARTNER AG"

# Default configuration
DEFAULT_CONFIG = {
    'cmk_min_version': '2.3.0p1',
    'cmk_packaged_version': '2.3.0p34',
    'validate_python': True,
    'output_dir': '.',
    'verbose': False,
}

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

class Logger:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def info(self, message: str) -> None:
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")
    
    def success(self, message: str) -> None:
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")
    
    def warning(self, message: str) -> None:
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")
    
    def error(self, message: str) -> None:
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}", file=sys.stderr)
    
    def debug(self, message: str) -> None:
        if self.verbose:
            print(f"{Colors.BLUE}[VERBOSE]{Colors.NC} {message}")

class MKPBuilder:
    """CheckMK MKP Package Builder"""
    
    def __init__(self):
        self.logger = Logger()
        self.work_dir = Path.cwd()
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        
    def load_config(self, config_file: Optional[Path] = None) -> None:
        """Load configuration from .mkp-builderrc file"""
        if config_file is None:
            # Look for config file in work directory first, then script directory
            candidates = [
                self.work_dir / '.mkp-builderrc',
                Path(__file__).parent / '.mkp-builderrc'
            ]
            config_file = next((f for f in candidates if f.exists()), None)
        
        if config_file is None or not config_file.exists():
            self.logger.warning(f"No configuration file found")
            return
            
        self.logger.info(f"Loading configuration from {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' not in line:
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Map config keys to internal keys
                    key_map = {
                        'PACKAGE_NAME': 'name',
                        'PACKAGE_TITLE': 'title',
                        'PACKAGE_AUTHOR': 'author',
                        'PACKAGE_DESCRIPTION': 'description',
                        'CMK_MIN_VERSION': 'cmk_min_version',
                        'CMK_PACKAGED_VERSION': 'cmk_packaged_version',
                        'DOWNLOAD_URL': 'download_url',
                        'VERSION_USABLE_UNTIL': 'version_usable_until',
                        'VALIDATE_PYTHON': 'validate_python',
                    }
                    
                    if key in key_map:
                        config_key = key_map[key]
                        if config_key == 'validate_python':
                            self.config[config_key] = value.lower() in ('yes', 'true', '1')
                        else:
                            self.config[config_key] = value
                            
        except Exception as e:
            self.logger.warning(f"Error reading config file: {e}")
    
    def auto_detect_package_name(self) -> str:
        """Auto-detect package name from directory structure"""
        agents_dir = self.work_dir / 'local' / 'share' / 'check_mk' / 'agents' / 'plugins'
        
        if agents_dir.exists():
            plugins = [f for f in agents_dir.iterdir() 
                      if f.is_file() and os.access(f, os.X_OK)]
            
            if len(plugins) == 1:
                return plugins[0].name
        
        # Fallback to directory name
        return self.work_dir.name or 'unknown_package'
    
    def set_defaults(self) -> None:
        """Set default values for missing configuration"""
        if 'name' not in self.config:
            self.config['name'] = self.auto_detect_package_name()
        
        if 'title' not in self.config:
            self.config['title'] = self.config['name']
        
        # Ensure all defaults are set
        for key, value in DEFAULT_CONFIG.items():
            if key not in self.config:
                self.config[key] = value
    
    def validate_parameters(self) -> None:
        """Validate required parameters and constraints"""
        self.logger.info("Validating parameters...")
        
        # Required parameters
        if not self.config.get('version'):
            raise ValueError("Package version is required. Use --version argument.")
        
        if not self.config.get('name'):
            raise ValueError("Package name could not be determined. Use --name argument.")
        
        # Validate version format
        version_pattern = r'^\d+\.\d+\.\d+'
        if not re.match(version_pattern, self.config['version']):
            raise ValueError(f"Invalid version format: {self.config['version']}\n"
                           "Expected format: MAJOR.MINOR.PATCH (e.g., 1.2.3)")
        
        # Check local directory exists
        local_dir = self.work_dir / 'local'
        if not local_dir.exists():
            raise ValueError(f"Local directory not found: {local_dir}\n"
                           "This script must be run from a CheckMK plugin project directory.")
        
        self.logger.debug(f"Package name: {self.config['name']}")
        self.logger.debug(f"Package version: {self.config['version']}")
        self.logger.debug(f"Package title: {self.config['title']}")
        self.logger.debug(f"Package author: {self.config.get('author', '(not set)')}")
    
    def validate_python_files(self) -> None:
        """Validate Python files using AST parsing"""
        if not self.config.get('validate_python'):
            self.logger.info("Skipping Python validation")
            return
        
        self.logger.info("Validating Python files...")
        
        local_dir = self.work_dir / 'local'
        python_files = list(local_dir.rglob('*.py'))
        
        if not python_files:
            self.logger.warning("No Python files found to validate")
            return
        
        errors = 0
        for py_file in python_files:
            self.logger.debug(f"Validating: {py_file}")
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                # Parse with AST to check syntax
                ast.parse(source, filename=str(py_file))
                
            except SyntaxError as e:
                self.logger.error(f"Python syntax error in {py_file}:{e.lineno}: {e.msg}")
                errors += 1
            except Exception as e:
                self.logger.error(f"Error validating {py_file}: {e}")
                errors += 1
        
        if errors > 0:
            raise RuntimeError(f"Found {errors} Python syntax errors")
        
        self.logger.success("All Python files validated successfully")
    
    def collect_files(self) -> Dict[str, List[str]]:
        """Collect files for each MKP section"""
        files = {
            'agents': [],
            'cmk_addons_plugins': [],
            'lib': [],
        }
        
        package_name = self.config['name']
        
        # Collect agent files
        agents_dir = self.work_dir / 'local' / 'share' / 'check_mk' / 'agents'
        if agents_dir.exists():
            for file_path in agents_dir.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(agents_dir)
                    files['agents'].append(str(rel_path))
        
        # Collect CMK addon files
        addons_dir = self.work_dir / 'local' / 'lib' / 'python3' / 'cmk_addons' / 'plugins'
        if addons_dir.exists():
            # Look for package-specific directory
            pkg_dir = addons_dir / package_name
            if pkg_dir.exists():
                for file_path in pkg_dir.rglob('*'):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(addons_dir)
                        files['cmk_addons_plugins'].append(str(rel_path))
            
            # Look for flat structure files
            for subdir in ['agent_based', 'checkman', 'graphing', 'rulesets']:
                sub_path = addons_dir / subdir
                if sub_path.exists():
                    for file_path in sub_path.rglob('*'):
                        if file_path.is_file() and package_name in file_path.name:
                            rel_path = file_path.relative_to(addons_dir)
                            files['cmk_addons_plugins'].append(str(rel_path))
        
        # Collect lib files
        lib_dir = self.work_dir / 'local' / 'lib' / 'python3'
        bakery_dir = lib_dir / 'cmk' / 'base' / 'cee' / 'plugins' / 'bakery'
        if bakery_dir.exists():
            for file_path in bakery_dir.rglob('*'):
                if file_path.is_file() and package_name in file_path.name:
                    rel_path = file_path.relative_to(lib_dir)
                    files['lib'].append(str(rel_path))
        
        return files
    
    def create_tar_file(self, base_dir: Path, tar_path: Path, files: List[str]) -> None:
        """Create a tar file with the specified files"""
        with tarfile.open(tar_path, 'w') as tar:
            for file_rel_path in files:
                file_path = base_dir / file_rel_path
                if file_path.exists():
                    tar.add(file_path, arcname=file_rel_path)
    
    def create_package_tars(self, build_dir: Path, files: Dict[str, List[str]]) -> None:
        """Create the tar files for each MKP section"""
        # Create agents.tar
        self.logger.info("Creating agents.tar...")
        agents_base = self.work_dir / 'local' / 'share' / 'check_mk' / 'agents'
        self.create_tar_file(agents_base, build_dir / 'agents.tar', files['agents'])
        
        # Create cmk_addons_plugins.tar
        self.logger.info("Creating cmk_addons_plugins.tar...")
        addons_base = self.work_dir / 'local' / 'lib' / 'python3' / 'cmk_addons' / 'plugins'
        self.create_tar_file(addons_base, build_dir / 'cmk_addons_plugins.tar', files['cmk_addons_plugins'])
        
        # Create lib.tar
        self.logger.info("Creating lib.tar...")
        lib_base = self.work_dir / 'local' / 'lib' / 'python3'
        self.create_tar_file(lib_base, build_dir / 'lib.tar', files['lib'])
    
    def generate_metadata(self, build_dir: Path, files: Dict[str, List[str]]) -> None:
        """Generate metadata files (info and info.json)"""
        self.logger.info("Creating metadata files...")
        
        # Create info file (Python dict format)
        info_data = {
            'author': self.config.get('author', ''),
            'description': self.config.get('description', ''),
            'download_url': self.config.get('download_url', ''),
            'files': files,
            'name': self.config['name'],
            'title': self.config['title'],
            'version': self.config['version'],
            'version.min_required': self.config['cmk_min_version'],
            'version.packaged': self.config['cmk_packaged_version'],
            'version.usable_until': self.config.get('version_usable_until') or None,
        }
        
        # Write info file in Python dict format
        with open(build_dir / 'info', 'w', encoding='utf-8') as f:
            f.write("{\n")
            for key, value in info_data.items():
                if value is None:
                    f.write(f" '{key}': None,\n")
                elif isinstance(value, str):
                    f.write(f" '{key}': '{value}',\n")
                elif isinstance(value, dict):
                    # Format files dict
                    f.write(f" '{key}': {{\n")
                    for section, file_list in value.items():
                        formatted_files = [f"'{file}'" for file in file_list]
                        f.write(f"  '{section}': [{', '.join(formatted_files)}],\n")
                    f.write(" },\n")
                else:
                    f.write(f" '{key}': {repr(value)},\n")
            f.write("}\n")
        
        # Write info.json file
        with open(build_dir / 'info.json', 'w', encoding='utf-8') as f:
            # Convert to JSON-compatible format
            json_data = info_data.copy()
            json_data['version.usable_until'] = json_data['version.usable_until']
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    def create_mkp_package(self, build_dir: Path) -> Path:
        """Create the final MKP package"""
        output_dir = Path(self.config['output_dir'])
        output_file = output_dir / f"{self.config['name']}-{self.config['version']}.mkp"
        
        self.logger.info(f"Creating MKP package: {output_file}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the final MKP package
        with tarfile.open(output_file, 'w:gz') as tar:
            for file_name in ['info', 'info.json', 'agents.tar', 'cmk_addons_plugins.tar', 'lib.tar']:
                file_path = build_dir / file_name
                if file_path.exists():
                    tar.add(file_path, arcname=file_name)
        
        self.logger.success(f"MKP package created: {output_file}")
        
        # Show package info
        size = output_file.stat().st_size
        size_str = self._format_size(size)
        self.logger.info(f"Package size: {size_str}")
        
        if self.config.get('verbose'):
            self.logger.info("Package contents:")
            with tarfile.open(output_file, 'r:gz') as tar:
                for member in tar.getmembers():
                    self.logger.debug(f"  {member.name}")
        
        return output_file
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'K', 'M', 'G']:
            if size_bytes < 1024:
                return f"{size_bytes}{unit}"
            size_bytes //= 1024
        return f"{size_bytes}T"
    
    def build(self) -> Path:
        """Main build process"""
        self.logger.info("CheckMK MKP Package Builder starting...")
        
        # Load configuration
        self.load_config()
        self.logger.info("Config loaded successfully")
        
        # Set defaults
        self.set_defaults()
        self.logger.info("Defaults set successfully")
        
        # Validate parameters
        self.validate_parameters()
        
        # Validate Python files
        self.validate_python_files()
        
        # Create temporary build directory
        with tempfile.TemporaryDirectory() as build_dir_str:
            build_dir = Path(build_dir_str)
            self.logger.info(f"Using build directory: {build_dir}")
            
            # Collect files
            files = self.collect_files()
            
            # Create package tar files
            self.create_package_tars(build_dir, files)
            
            # Generate metadata files
            self.generate_metadata(build_dir, files)
            
            # Create final MKP package
            output_file = self.create_mkp_package(build_dir)
        
        self.logger.success("MKP package build completed successfully!")
        return output_file

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='CheckMK MKP Package Builder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mkp-builder.py --version 1.2.3
  mkp-builder.py --version 1.2.3 --author "John Doe <john@example.com>"
  mkp-builder.py --version 1.2.3 --output-dir dist/ --verbose

Configuration:
  Default values are loaded from .mkp-builderrc file if it exists.
  Command line arguments override config file values.
        """
    )
    
    # Required arguments
    parser.add_argument('--version', required=True,
                       help='Package version (e.g., 1.2.3)')
    
    # Optional arguments
    parser.add_argument('--name',
                       help='Package name (default: from config or auto-detect)')
    parser.add_argument('--title',
                       help='Package title (default: from config)')
    parser.add_argument('--author',
                       help='Author name and email (default: from config)')
    parser.add_argument('--description',
                       help='Package description (default: from config)')
    parser.add_argument('--cmk-min',
                       help='Minimum CheckMK version (default: from config)')
    parser.add_argument('--cmk-packaged',
                       help='CheckMK version used for packaging (default: from config)')
    parser.add_argument('--download-url',
                       help='Download URL (default: from config)')
    parser.add_argument('--version-usable-until',
                       help='The last CheckMK version this plugin is compatible with (default: from config)')
    parser.add_argument('--output-dir', default='.',
                       help='Output directory (default: current directory)')
    
    # Boolean flags
    validation_group = parser.add_mutually_exclusive_group()
    validation_group.add_argument('--validate', action='store_true',
                                 help='Validate Python files before packaging')
    validation_group.add_argument('--no-validate', action='store_true',
                                 help='Skip Python validation')
    
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    
    return parser

def main() -> int:
    """Main entry point"""
    try:
        parser = create_parser()
        args = parser.parse_args()
        
        # Create builder instance
        builder = MKPBuilder()
        builder.logger.verbose = args.verbose
        
        # Set configuration from command line arguments
        if args.version:
            builder.config['version'] = args.version
        if args.name:
            builder.config['name'] = args.name
        if args.title:
            builder.config['title'] = args.title
        if args.author:
            builder.config['author'] = args.author
        if args.description:
            builder.config['description'] = args.description
        if getattr(args, 'cmk_min'):
            builder.config['cmk_min_version'] = getattr(args, 'cmk_min')
        if getattr(args, 'cmk_packaged'):
            builder.config['cmk_packaged_version'] = getattr(args, 'cmk_packaged')
        if getattr(args, 'download_url'):
            builder.config['download_url'] = getattr(args, 'download_url')
        if getattr(args, 'version_usable_until'):
            builder.config['version_usable_until'] = getattr(args, 'version_usable_until')
        if args.output_dir:
            builder.config['output_dir'] = args.output_dir
        
        # Handle validation flags
        if args.validate:
            builder.config['validate_python'] = True
        elif args.no_validate:
            builder.config['validate_python'] = False
        
        if args.verbose:
            builder.config['verbose'] = True
        
        # Build the package
        output_file = builder.build()
        
        # Output for GitHub Actions
        print(f"::set-output name=package-file::{output_file}")
        print(f"::set-output name=package-name::{builder.config['name']}")
        print(f"::set-output name=package-size::{builder._format_size(output_file.stat().st_size)}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nBuild interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        Logger().error(str(e))
        return 1

if __name__ == '__main__':
    sys.exit(main())
