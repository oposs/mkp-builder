"""Make the Checkmk API importable so this plugin's tests can run at all.

A Checkmk plugin imports `cmk.agent_based`, `cmk.graphing`, `cmk.rulesets` and
`cmk.server_side_calls`. None of them exist outside a Checkmk installation, so
without this file there is nothing to run pytest against.

The API comes from Checkmk itself, pinned to the version this plugin targets,
rather than from hand-written stubs. A stub only ever catches the API calls
somebody remembered to model. The real thing catches every one -- and raising
CMK_VERSION below is how you find out what a Checkmk upgrade breaks, before a
user does.

The four API packages are namespace packages, so putting their directories on
sys.path is enough; nothing is installed. The one exception is the enterprise
agent bakery API, which imports `cmk.utils` from the Checkmk monolith and so
cannot be used standalone. `cmk_stubs/` covers exactly that one module -- and
it must stay a namespace package (no `cmk/__init__.py` anywhere in it), or it
would shadow the real `cmk` instead of merging with it.
"""

import pathlib
import shutil
import subprocess
import sys

# The Checkmk version this plugin targets. Raise it to find out what breaks.
CMK_VERSION = "2.3.0"

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CACHE = ROOT / ".cmk-api" / CMK_VERSION
API_PACKAGES = ("cmk-agent-based", "cmk-graphing", "cmk-rulesets", "cmk-server-side-calls")


def _fetch_cmk_api(target):
    """A blobless sparse clone of just the API packages: ~7 MB, a second or two.

    Deliberately not `pip install "... @ git+https://...#subdirectory=..."`.
    That clones the whole Checkmk repository including a submodule the public
    cannot read, takes over a minute, and then fails.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_name(target.name + ".partial")
    shutil.rmtree(staging, ignore_errors=True)
    try:
        subprocess.run(
            ["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none", "--sparse",
             "-b", CMK_VERSION, "https://github.com/Checkmk/checkmk.git", str(staging)],
            check=True)
        subprocess.run(
            ["git", "-C", str(staging), "sparse-checkout", "set",
             *(f"packages/{p}" for p in API_PACKAGES)],
            check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        shutil.rmtree(staging, ignore_errors=True)
        raise RuntimeError(
            f"could not fetch the Checkmk {CMK_VERSION} API from GitHub: {exc}\n"
            "The tests import cmk.* and cannot run without it. Check network access, "
            "or that CMK_VERSION in tests/conftest.py names a real Checkmk tag."
        ) from exc
    # Rename last, so an interrupted clone never leaves a half-populated cache
    # that later runs would treat as good.
    staging.rename(target)


if not CACHE.is_dir():
    _fetch_cmk_api(CACHE)

for package in API_PACKAGES:
    sys.path.insert(0, str(CACHE / "packages" / package))

# Helper modules under a plugin's libexec/ import each other by bare name --
# that is how Checkmk ships and runs them -- so every libexec directory goes on
# the path too. Without this, a plugin that splits its agent across several
# files cannot be imported at all.
for libexec in sorted(ROOT.glob("local/lib/python3/**/libexec")):
    if libexec.is_dir():
        sys.path.insert(0, str(libexec))

# Last insert wins position 0. The bakery stub must precede the real packages
# so `cmk.base` resolves, and it merges with them because neither side defines
# `cmk/__init__.py`.
sys.path.insert(0, str(HERE / "cmk_stubs"))
