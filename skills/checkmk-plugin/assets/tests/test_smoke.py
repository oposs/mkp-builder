# repo-infra: checkmk-harness v1
"""Every plugin module imports and registers.

This is the floor, not the ceiling. It catches the failure that actually
happens: a check that references a Checkmk API which moved, discovered by a
user on upgrade rather than by CI.
"""

import importlib.util
import pathlib
import sys

import pytest

# Anchored to this file, not to the working directory: `pytest tests/` and
# `pytest` from a subdirectory must collect the same modules, or the suite
# silently shrinks to nothing and still reports success.
ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULES = sorted((ROOT / "local/lib/python3").rglob("*.py"))


def _module_name(path):
    """A name unique per file.

    Several plugins name the agent_based, graphing and rulesets modules
    identically, so the file stem is not unique. Registering two different
    files under one name would let the second silently reuse the first.
    """
    return "cmk_smoke_" + path.relative_to(ROOT).as_posix().replace("/", "_")[:-3]


@pytest.mark.parametrize("path", MODULES, ids=lambda p: str(p.relative_to(ROOT)))
def test_the_module_imports(path):
    name = _module_name(path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # A dataclass with `from __future__ import annotations` resolves its
    # deferred annotations by looking itself up in sys.modules, so a module
    # that is not registered there fails to import for a reason that has
    # nothing to do with the plugin.
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)


def test_there_is_something_to_import():
    assert MODULES, "no plugin modules under local/lib/python3 -- is this a Checkmk plugin?"
