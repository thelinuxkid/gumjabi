#!/usr/bin/python
from setuptools import setup, find_packages

EXTRAS_REQUIRES = dict(
    web=[
        'bottle>=0.11',
        ],
    test=[
        'pytest>=2.2.4',
        'mock>=0.8.0',
        ],
    dev=[
        'ipython>=0.13',
        ],
    )

# Tests always depend on all other requirements, except dev
for k,v in EXTRAS_REQUIRES.iteritems():
    if k == 'test' or k == 'dev':
        continue
    EXTRAS_REQUIRES['test'] += v

setup(
    name='tle',
    version='0.0.1',
    description=('tle -- Glue code for TheLeanEntrepreneur between the '
                 'Gumroad and Kajabi APIs'
                 ),
    author='Andres Buritica',
    author_email='andres@thelinuxkid.com',
    maintainer='Andres Buritica',
    maintainer_email='andres@thelinuxkid.com',
    packages = find_packages(),
    test_suite='nose.collector',
    install_requires=[
        'setuptools',
        ],
    extras_require=EXTRAS_REQUIRES,
    entry_points={
        'console_scripts': [
            'tle = tle.cli.glue_api:main[web]',
            ],
        },
    )
