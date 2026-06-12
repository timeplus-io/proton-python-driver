"""Verify proton_driver imports cleanly on interpreters that lack stdlib
compression modules (zlib / bz2 / compression.zstd / lzma).

This guards the invariant from PR #69 review: the Cython 3.2 output
default-imports those modules at module init to decompress its string
table. We defeat that by compiling with -DCYTHON_COMPRESS_STRINGS=0 (see
setup.py), which selects the #else /* compression: none */ branch.
Running this on a stock runner where those modules happen to be present
would trivially pass, so we explicitly install an import blocker for
them before loading proton_driver.

Used by:
  - cibuildwheel test-command in pyproject.toml (on every built wheel)
  - smoke-ft job in .github/workflows/test.yml (free-threaded 3.14t)
"""
import sys

# Pre-import runtime deps now, while the blocker is NOT yet in place. These
# ship as proton_driver install_requires and don't use any blocked module.
import pytz  # noqa: F401
import tzlocal  # noqa: F401

BLOCKED = frozenset({
    'zlib',
    'bz2', '_bz2',
    'compression', 'compression.zstd', '_zstd',
    'lzma', '_lzma',
})


class _BlockCompressionImports:
    def find_spec(self, name, path, target=None):
        if name in BLOCKED:
            raise ImportError(
                f'{name!r} import blocked: Cython string-table compression '
                f'would silently pull this back in'
            )
        return None


sys.meta_path.insert(0, _BlockCompressionImports())
# Evict any already-cached copies so a re-import also hits the blocker.
for _mod in list(sys.modules):
    if _mod in BLOCKED:
        del sys.modules[_mod]

import proton_driver  # noqa: E402
import proton_driver.bufferedreader  # noqa: E402, F401
import proton_driver.bufferedwriter  # noqa: E402, F401
import proton_driver.varint  # noqa: E402, F401
import proton_driver.columns.largeint  # noqa: E402, F401

leaked = sorted(m for m in sys.modules if m in BLOCKED)
if leaked:
    raise SystemExit(f'FAIL: leaked blocked modules: {leaked}')

# On a free-threaded build, importing the driver must not re-enable the
# GIL. Any extension still compiled without `freethreading_compatible =
# True` declares Py_MOD_GIL_USED, CPython flips the GIL back on at import
# time, and the cp314t wheel silently degrades into a GIL build.
import sysconfig  # noqa: E402

if sysconfig.get_config_var('Py_GIL_DISABLED') and sys._is_gil_enabled():
    raise SystemExit(
        'FAIL: free-threaded interpreter, but an extension import '
        're-enabled the GIL (missing freethreading_compatible directive)'
    )

print(
    f'proton_driver {proton_driver.VERSION} imports cleanly on '
    f'Python {sys.version_info.major}.{sys.version_info.minor}'
    f'{"t" if not getattr(sys, "_is_gil_enabled", lambda: True)() else ""} '
    f'with {{zlib, bz2, compression.zstd, lzma}} blocked'
)
