# -*- coding: utf-8 -*-

import sys
from setuptools import setup

sys.path.insert(0, '.')
from yml2 import yml2c
caption = yml2c.__doc__.split('\n')[0]
short_desc, version = map(lambda s: s.strip(), caption.split('version', 1))

with open('README.md', 'r') as fh:
    long_desc = fh.read().strip()

setup(
        name='YML2',
        version=version,
        description=short_desc,
        long_description=long_desc,
        author="Volker Birk",
        author_email="vb@pep.foundation",
        url="https://pep.foundation/dev/repos/yml2",
        zip_safe=False,
        packages=["yml2"],
        install_requires=['lxml'],
        package_data = {
            '': ['gpl-2.0.txt', '*.css', '*.yhtml2'],
            'yml2': ['*.yml2', '*.ysl2'],
        },
        entry_points = {
            'console_scripts': [
                'yml2c=yml2.yml2c:main',
                'yml2proc=yml2.yml2proc:main'
            ],
        }
    )

