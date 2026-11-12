"""The syntax check must use the Python of the oldest Checkmk a package
supports (version.min_required), not the Python that runs mkp-builder.

Run with: python3 -m unittest discover -s tests
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / 'mkp-builder.py'

# Real plugin code, one 3.12-only construct each.
PEP695_TYPE = '''\
from cmk.agent_based.v2 import StringTable

type Section = list[list[str]]


def parse_demo(string_table: StringTable) -> Section:
    return string_table
'''

PEP695_GENERIC = '''\
def first[T](items: list[T]) -> T:
    return items[0]
'''

PEP701_SAME_QUOTES = '''\
def summary(section: dict[str, str]) -> str:
    return f"Model: {section["model"]}"
'''

PEP701_BACKSLASH = '''\
def summary(lines: list[str]) -> str:
    return f"{'\\n'.join(lines)}"
'''

PEP701_MULTILINE = '''\
def summary(section: dict[str, int]) -> str:
    return f"Errors: {
        section['errors']
    }"
'''

PEP701_COMMENT = '''\
def summary(errors: int) -> str:
    return f"""Errors: {
        errors  # uncorrected only
    }"""
'''

# Fine on 3.11: different quotes inside, triple quotes outside, a format spec.
PY311_FSTRINGS = '''\
def summary(section: dict[str, int]) -> str:
    one = f"Errors: {section['errors']}"
    two = f"""Model: {section["model"]!r:>10}"""
    three = f"{section['rate']:.2f}"
    return one + two + three
'''

# 3.11 syntax a 2.2 package may use.
PY311_EXCEPT_STAR = '''\
def check() -> None:
    try:
        pass
    except* ValueError:
        pass
'''

PY310_MATCH = '''\
def state(code: int) -> str:
    match code:
        case 0:
            return "OK"
        case _:
            return "CRIT"
'''


def build(source: str, min_required: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        plugin = Path(tmp, 'local/lib/python3/cmk_addons/plugins/demo/agent_based/demo.py')
        plugin.parent.mkdir(parents=True)
        plugin.write_text(source, encoding='utf-8')
        return subprocess.run(
            [sys.executable, str(SCRIPT), '--version', '1.0.0', '--name', 'demo',
             '--version-min-required', min_required],
            cwd=tmp, capture_output=True, text=True, check=False)


@unittest.skipIf(sys.version_info < (3, 12), 'needs Python 3.12, the Python of Checkmk 2.3')
class SyntaxFollowsMinRequired(unittest.TestCase):

    def assertRejected(self, source: str, min_required: str, message: str) -> None:
        result = build(source, min_required)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('demo.py', result.stderr)
        self.assertIn(message, result.stderr)

    def assertAccepted(self, source: str, min_required: str) -> None:
        result = build(source, min_required)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('All Python files validated successfully', result.stdout)

    def test_type_statement_rejected_for_2_2(self):
        self.assertRejected(PEP695_TYPE, '2.2.0p1', 'Python 3.11')

    def test_type_parameters_rejected_for_2_2(self):
        self.assertRejected(PEP695_GENERIC, '2.2.0', 'Python 3.11')

    def test_nested_same_quotes_rejected_for_2_2(self):
        self.assertRejected(PEP701_SAME_QUOTES, '2.2.0p1', 'Python 3.11')

    def test_backslash_in_fstring_expression_rejected_for_2_2(self):
        self.assertRejected(PEP701_BACKSLASH, '2.2.0p1', 'Python 3.11')

    def test_multiline_fstring_expression_rejected_for_2_2(self):
        self.assertRejected(PEP701_MULTILINE, '2.2.0p1', 'Python 3.11')

    def test_comment_in_fstring_expression_rejected_for_2_2(self):
        self.assertRejected(PEP701_COMMENT, '2.2.0p1', 'Python 3.11')

    def test_match_rejected_for_2_1(self):
        self.assertRejected(PY310_MATCH, '2.1.0p1', 'Python 3.9')

    def test_311_syntax_accepted_for_2_2(self):
        for source in (PY311_FSTRINGS, PY311_EXCEPT_STAR, PY310_MATCH):
            with self.subTest(source=source.splitlines()[0]):
                self.assertAccepted(source, '2.2.0p1')

    def test_312_syntax_accepted_for_2_3_and_2_4(self):
        for min_required in ('2.3.0p1', '2.4.0'):
            for source in (PEP695_TYPE, PEP695_GENERIC, PEP701_SAME_QUOTES,
                           PEP701_BACKSLASH, PEP701_MULTILINE, PEP701_COMMENT):
                with self.subTest(min_required=min_required, source=source.splitlines()[0]):
                    self.assertAccepted(source, min_required)


if __name__ == '__main__':
    unittest.main()
