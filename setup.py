# -*- coding: utf-8 -*-

import sys, os
from setuptools import setup

DESC = "YML 2 compiler"
SDISTVER = '2.6.2.3'

with open('README.rst', 'r', encoding='utf-8') as fh:
    long_desc = fh.read().strip()
    long_description_content_type = 'text/markdown'

setup(
    name='YML2',
    version=SDISTVER,
    description=DESC,
    long_description=long_desc,
    long_description_content_type=long_description_content_type,
    author="Volker Birk",
    author_email="vb@pep.foundation",
    license="GPL-2.0",
    url="https://pep.foundation/dev/repos/yml2",
    download_url="https://software.pep.foundation/r/pypi/yml2/YML2-%s.tar.gz" % SDISTVER,
    zip_safe=False,
    packages=["yml2"],
    install_requires=['lxml'],
    package_data = {
        '': ['COPYING.txt', '*.css', '*.yhtml2'],
        'yml2': ['*.yml2', '*.ysl2'],
    },
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

