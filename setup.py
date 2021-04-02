# File: setup.py
# Date: 6-Oct-2018
#
# Update:
#
import re
import glob

from setuptools import find_packages
from setuptools import setup

packages = []
thisPackage = 'wwpdb.apps.workmanager'

with open('wwpdb/apps/workmanager/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

setup(
    name=thisPackage,
    version=version,
    description='wwPDB workflow manager app',
    long_description="See:  README.md",
    author='Ezra Peisach',
    author_email='ezra.peisach@rcsb.org',
    url='https://github.com/rcsb/py-wwpdb_apps_workmanager',
    #
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    #
    install_requires=['wwpdb.utils.config',
                      'wwpdb.utils.wf',
                      'wwpdb.io ~= 0.6.dev1',
                      'rcsb.utils.multiproc',
                      'wwpdb.apps.wf_engine >= 0.5',
                      'wwpdb.utils.db >= 0.4',
                      'wwpdb.utils.session >= 0.3',
                      'mmcif.utils',
                      'wwpdb.utils.detach ~= 0.3.dev1',
                      'mysqlclient'
                      ],
    packages=find_packages(exclude=['wwpdb.apps.tests-workmanager']),
    # Enables Manifest to be used
    # include_package_data = True,
    package_data={
        # If any package contains *.md or *.rst ...  files, include them:
        '': ['*.md', '*.rst', "*.txt", "*.cfg"],
        # 'wwpdb': ['apps/deposit/private/countries.pkl'],
    },
    #
    # These basic tests require no database services -
    test_suite="wwpdb.apps.tests-workmanager",
    tests_require=['tox'],
    #
    # Not configured ...
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    # Added for
    command_options={
        'build_sphinx': {
            'project': ('setup.py', thisPackage),
            'version': ('setup.py', version),
            'release': ('setup.py', version)
        }
    },
    # This setting for namespace package support -
    zip_safe=False,
)
