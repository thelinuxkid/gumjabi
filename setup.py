#!/usr/bin/python
from setuptools import setup, find_packages

EXTRAS_REQUIRES = dict(
    web=[
        'bottle>=0.11',
        'paste>=1.7.5.1',
        'requests>=0.14.1',
    ],
    mongo=[
        'pymongo>=2.3',
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
    name='gumjabi',
    version='0.0.1',
    description='Gumjabi -- Glue API between Gumroad and Kajabi APIs',
    long_description=(
        'Gumjabi -- Glue API which connects Gumroad webhooks with '
        'Kajabi\'s custom cart integration. This allows a Gumroad '
        'user to seamlessly create Kajabi accounts for a customer.'
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
            'glue-api = gumjabi.cli.glue_api:main[web]',
            ],
        },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ],
)
