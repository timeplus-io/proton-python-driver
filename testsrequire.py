import os
import sys

USE_NUMPY = bool(int(os.getenv('USE_NUMPY', '0')))

tests_require = [
    'pytest',
    'parameterized',
    'freezegun',
    'zstd',
    'clickhouse-cityhash>=1.0.2.1'
]

if sys.implementation.name == 'pypy':
    tests_require.append('lz4<=3.0.1')
else:
    tests_require.append('lz4')

if USE_NUMPY:
    # pandas 3 changed default dtypes (str columns, datetime64[us]) and
    # nullable comparison semantics; the driver's dataframe support
    # targets pandas 2 — pandas 3 support is tracked separately.
    tests_require.extend(['numpy', 'pandas<3'])

try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain

pipmain(['install'] + tests_require)
