#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'requests',
    'splinter',
    'voluptuous'
    # TODO: put package requirements here
]

setup_requirements = [
    'pytest-runner',
    # TODO(eddienko): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    'pytest',
    # TODO: put package test requirements here
]

setup(
    name='esoarchive',
    version='0.9.1',
    description="Automatic ESO archive requests and download",
    long_description=readme + '\n\n' + history,
    author="Eduardo Gonzalez Solares",
    author_email='eglez@gilgalad.co.uk',
    url='https://github.com/eddienko/esoarchive',
    packages=find_packages(include=['esoarchive']),
    entry_points={
        'console_scripts': [
            'esoarchive=esoarchive.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='esoarchive',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
