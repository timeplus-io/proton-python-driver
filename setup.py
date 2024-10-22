import os
import re
from codecs import open

from setuptools import setup, find_packages
from distutils.extension import Extension

try:
    from Cython.Build import cythonize
except ImportError:
    USE_CYTHON = False
else:
    USE_CYTHON = True

CYTHON_TRACE = bool(os.getenv('CYTHON_TRACE', False))

here = os.path.abspath(os.path.dirname(__file__))


def read_version():
    regexp = re.compile(r'^VERSION\W*=\W*\(([^\(\)]*)\)')
    init_py = os.path.join(here, 'proton_driver', '__init__.py')
    with open(init_py, encoding='utf-8') as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1).replace(', ', '.')
        else:
            raise RuntimeError(
                'Cannot find version in proton_driver/__init__.py'
            )


with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Prepare extensions.
ext = '.pyx' if USE_CYTHON else '.c'
extensions = [
    Extension(
        'proton_driver.bufferedreader',
        ['proton_driver/bufferedreader' + ext]
    ),
    Extension(
        'proton_driver.bufferedwriter',
        ['proton_driver/bufferedwriter' + ext]
    ),
    Extension(
        'proton_driver.columns.largeint',
        ['proton_driver/columns/largeint' + ext]
    ),
    Extension(
        'proton_driver.varint',
        ['proton_driver/varint' + ext]
    )
]

if USE_CYTHON:
    compiler_directives = {'language_level': '3'}
    if CYTHON_TRACE:
        compiler_directives['linetrace'] = True

    extensions = cythonize(extensions, compiler_directives=compiler_directives)

setup(
    name='proton-driver',
    version=read_version(),

    description='Python driver with native interface for Proton',
    long_description=long_description,

    url='https://github.com/timeplus-io/proton-python-driver',

    author='Gang Tao',
    author_email='gang@timeplus.com',

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',


        'Environment :: Console',


        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',


        'License :: OSI Approved :: MIT License',


        'Operating System :: OS Independent',


        'Programming Language :: SQL',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: PyPy',

        'Topic :: Database',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Information Analysis'
    ],

    keywords='Proton db database cloud analytics',

    packages=find_packages('.', exclude=['tests*']),
    python_requires='>=3.8, <4',
    install_requires=[
        'pytz',
        'tzlocal',
        'tzlocal<2.1; python_version=="3.5"'
    ],
    ext_modules=extensions,
    extras_require={
        'lz4': [
            'lz4<=3.0.1; implementation_name=="pypy"',
            'lz4; implementation_name!="pypy"',
            'clickhouse-cityhash>=1.0.2.1'
        ],
        'zstd': ['zstd', 'clickhouse-cityhash>=1.0.2.1'],
        'numpy': ['numpy>=1.12.0', 'pandas>=0.24.0']
    },
    test_suite='pytest'
)
