# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    setup_requires = ["setuptools >= 30.3.0"],  # release 2016-12-06
    long_description=long_description,
    entry_points = {
        'console_scripts': [
            'yml2c=yml2.yml2c:main',
            'yml2proc=yml2.yml2proc:main'
        ],
    },
    classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Intended Audience :: Developers',
      'Environment :: Console',
      'Topic :: Software Development :: Build Tools',
      'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
    ],
)

