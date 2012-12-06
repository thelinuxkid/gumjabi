#!/usr/bin/python
from setuptools import setup, find_packages
import os

EXTRAS_REQUIRES = dict(
    api=[
        'bottle>=0.11',
        'paste>=1.7.5.1',
        'pyOpenSSL>=0.13',
    ],
    web=[
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

# Pypi package documentation
root = os.path.dirname(__file__)
path = os.path.join(root, 'README.rst')
with open(path) as fp:
    long_description = fp.read()

# Tests always depend on all other requirements, except dev
for k,v in EXTRAS_REQUIRES.iteritems():
    if k == 'test' or k == 'dev':
        continue
    EXTRAS_REQUIRES['test'] += v

setup(
    name='gumjabi',
    version='0.0.2',
    description='Gumjabi -- Glue API between Gumroad and Kajabi APIs',
    long_description=long_description,
    author='Andres Buritica',
    author_email='andres@thelinuxkid.com',
    maintainer='Andres Buritica',
    maintainer_email='andres@thelinuxkid.com',
    url='https://github.com/thelinuxkid/gumjabi',
    license='MIT',
    packages = find_packages(),
    test_suite='nose.collector',
    install_requires=[
        'setuptools',
        ],
    extras_require=EXTRAS_REQUIRES,
    entry_points={
        'console_scripts': [
            'gumjabi-api = gumjabi.cli.gumjabi_api:main[api,mongo]',
            'kajabi-queue = gumjabi.cli.kajabi_queue:main[web,mongo]',
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
