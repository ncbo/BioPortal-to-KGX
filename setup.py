import os
import re
from codecs import open as copen  # to use a consistent encoding
from setuptools import find_packages, setup

from post_setup.post_setup import robot_setup

here = os.path.abspath(os.path.dirname(__file__))

# get the long description from the relevant file
with copen(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

def read(*parts):
    with copen(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

__version__ = '0.0.1'

test_deps = [
    'pytest',
    'pytest-cov',
    'coveralls',
    'validate_version_code',
    'codacy-coverage',
    'parameterized'
]

extras = {
    'test': test_deps
}

setup(
    name='bioportal_to_kgx',
    version=__version__,
    url='https://github.com/ncbo/BioPortal-to-KGX',
    license='BSD-3',
    author='Harry Caufield',
    author_email='jhc@lbl.gov',
    description='Utility to assemble a BioPortal Knowledge Graph',
    long_description=long_description,
    python_requires='>=3.7',

    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3'
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    tests_require=test_deps,
    # add package dependencies
    install_requires=[
        'kgx',
        'requests',
        'setuptools',
        'click',
        'sh',
        'sssom'
    ],
    extras_require=extras,
)

robot_setup()
