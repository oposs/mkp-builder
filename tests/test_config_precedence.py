"""A flag given on the command line beats .mkp-builder.ini, and the ini
beats the built-in defaults.

Run with: python3 -m unittest discover -s tests
"""

import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / 'mkp-builder.py'

INI = '''\
[package]
name = oposs_demo
title = OPOSS Demo From Ini
author = Ini Author <ini@example.com>
description = Description from the ini.
version.min_required = 2.3.0p1
version.packaged = 2.3.0p52
download_url = https://example.com/ini
version.usable_until =
validate_python = true
'''

CHECK = '''\
from cmk.agent_based.v2 import StringTable


def parse_demo(string_table: StringTable) -> StringTable:
    return string_table
'''

BROKEN = 'def parse_demo(:\n'


class Build:
    """A plugin directory with an optional ini, built with the given flags."""

    def __init__(self, ini, flags, source=CHECK):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        for name in ('oposs_demo', 'cli_name'):
            plugin = root / 'local/lib/python3/cmk_addons/plugins' / name / 'agent_based' / f'{name}.py'
            plugin.parent.mkdir(parents=True)
            plugin.write_text(source, encoding='utf-8')
        if ini is not None:
            (root / '.mkp-builder.ini').write_text(ini, encoding='utf-8')
        self.result = subprocess.run(
            [sys.executable, str(SCRIPT), '--version', '1.0.0', *flags],
            cwd=root, capture_output=True, text=True, check=False)
        self.packages = sorted(p.name for p in root.glob('*.mkp'))
        self.info = None
        if len(self.packages) == 1:
            with tarfile.open(root / self.packages[0], 'r:gz') as tar:
                self.info = json.load(tar.extractfile('info.json'))
        self.tmp.cleanup()


class FlagBeatsIni(unittest.TestCase):

    def built(self, ini, flags, source=CHECK):
        build = Build(ini, flags, source)
        self.assertEqual(build.result.returncode, 0, build.result.stdout + build.result.stderr)
        return build

    def test_ini_values_reach_the_package(self):
        info = self.built(INI, []).info
        self.assertEqual(info['name'], 'oposs_demo')
        self.assertEqual(info['title'], 'OPOSS Demo From Ini')
        self.assertEqual(info['author'], 'Ini Author <ini@example.com>')
        self.assertEqual(info['version.packaged'], '2.3.0p52')
        self.assertIsNone(info['version.usable_until'])

    def test_flags_beat_the_ini(self):
        build = self.built(INI, [
            '--name', 'cli_name',
            '--title', 'Title From Flag',
            '--author', 'Flag Author <flag@example.com>',
            '--description', 'Description from the flag.',
            '--version-min-required', '2.4.0p1',
            '--version-packaged', '2.4.0p39',
            '--download-url', 'https://example.com/flag',
            '--version-usable-until', '2.5.0',
        ])
        self.assertEqual(build.packages, ['cli_name-1.0.0.mkp'])
        info = build.info
        self.assertEqual(info['name'], 'cli_name')
        self.assertEqual(info['title'], 'Title From Flag')
        self.assertEqual(info['author'], 'Flag Author <flag@example.com>')
        self.assertEqual(info['description'], 'Description from the flag.')
        self.assertEqual(info['version.min_required'], '2.4.0p1')
        self.assertEqual(info['version.packaged'], '2.4.0p39')
        self.assertEqual(info['download_url'], 'https://example.com/flag')
        self.assertEqual(info['version.usable_until'], '2.5.0')

    def test_ini_beats_the_defaults(self):
        ini = INI.replace('2.3.0p52', '2.3.0p40').replace('2.3.0p1', '2.3.0p9')
        info = self.built(ini, []).info
        self.assertEqual(info['version.min_required'], '2.3.0p9')
        self.assertEqual(info['version.packaged'], '2.3.0p40')

    def test_defaults_without_ini(self):
        info = self.built(None, ['--name', 'oposs_demo']).info
        self.assertEqual(info['title'], 'oposs_demo')
        self.assertEqual(info['version.min_required'], '2.3.0p1')
        self.assertEqual(info['version.packaged'], '2.3.0p34')

    def test_no_validate_flag_beats_ini(self):
        build = self.built(INI, ['--no-validate'], source=BROKEN)
        self.assertIn('Skipping Python validation', build.result.stdout)

    def test_validate_flag_beats_ini(self):
        ini = INI.replace('validate_python = true', 'validate_python = false')
        build = Build(ini, ['--validate'], source=BROKEN)
        self.assertEqual(build.result.returncode, 1, build.result.stdout)
        self.assertIn('Python syntax error', build.result.stderr)

    def test_ini_turns_validation_off_without_a_flag(self):
        ini = INI.replace('validate_python = true', 'validate_python = false')
        build = self.built(ini, [], source=BROKEN)
        self.assertIn('Skipping Python validation', build.result.stdout)


if __name__ == '__main__':
    unittest.main()
