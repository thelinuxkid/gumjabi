=======
Gumjabi
=======

Gumjabi is an API which connects Gumroad webhooks with Kajabi's custom
cart integration. This allows a Gumroad user to seamlessly create
Kajabi accounts for a customer.

Developing
==========

External dependencies
---------------------

    - build-essential
    - python-dev
    - python-setuptools
    - python-virtualenv

Setup
-----

To start developing run the following commands from the project's base
directory. You can download the source from
https://github.com/thelinuxkid/gumjabi::

    # I like to install the virtual environment in a hidden repo.
    virtualenv .virtual
    # I leave the magic to Ruby developers (.virtual/bin/activate)
    .virtual/bin/python setup.py develop
    # At this point, gumjabi will already be in easy-install.pth.
    # So, pip will not attempt to download it
    .virtual/bin/pip install gumjabi[test]

    # The test requirement installs all the dependencies. But,
    # depending on the cli you wish to run you might want to install
    # only the appropriate dependencies as listed in setup.py. For
    # example to run create-acct you only need the mongo
    # requirement which installs the pymongo dependency
    .virtual/bin/pip install gumjabi[mongo]

If you like to use ipython you can install it with the dev
requirement::

    .virtual/bin/pip install gumjabi[dev]
