=======
Gumjabi
=======

Gumjabi is a set of services which connect the `Gumroad Ping API`_
with `Kajabi's custom cart integration`_. This allows Gumroad users
to seamlessly create Kajabi accounts for their purchasers. You must be
familiar with the `Gumroad Ping API`_ and `Kajabi's custom cart
integration`_ in order to follow these instructions. The Installation_
and Developing_ sections are written for Linux systems.

Design
======

Gumjabi is made up of two services. The Gumjabi API listens for POST
requests from the Gumroad Ping API and puts the information provided
in a queue. The Kajabi account creation service then gets the queue
items and creates the accounts, retrying if necessary. The queue is
stored in a MongoDB collection.

API
---

To start the API call the ``gumjabi-api`` command with the
``--config`` and ``--db-config`` arguments::

    gumjabi-api --config=gumjabi-api.conf --db-config=mongodb.conf

``gumjabi-api.conf`` looks like::

      [connection]
      host = <hostname>
      port = <port>
      ssl-pem = <path_to_certificate>

      [api]
      restrict-hosts = <true|false>

Use ``ssl-pem`` if you want to run the API with SSL enabled. If you
want to restrict the hosts which can make requests to the API set
``restrict-hosts`` to true (see `Database structures`_ below). Neither
option is required.

``mongodb.conf`` looks like::

    [connection]
    host = <hostname>:<port>
    replica-set = <replicaset-name>
    database = <database-name>

    [collection]
    gumjabi-keys = <collection-name>
    kajabi-queue = <collection-name>

The ``replica-set`` option is not necessary. If you are not using a
replica set in your MongoDB setup omit this line. The collections used
here are described in the `Database structures`_ section below.

Account creation service
------------------------

To monitor the queue which contains the Kajabi accounts to create call
the ``kajabi-queue`` command with the ``--db-config`` argument::

    kajabi-queue --db-config=mongodb.conf

``mongodb.conf`` looks the same as above.


.. _dbstructures:

Database structures
-------------------

Gumjabi uses two MongoDB collections. The system uses the names
kajabi-queue and gumjabi-keys which are defined in
``gumjabi-api.conf`` but you can name the actual collections anything
you want. kajabi-queue is used as a queue for the Kajabi accounts that
are to be created. gumjabi-keys holds Gumroad and Kajabi information
for each user and must be pre-populated.::

    {
      "_id": <Gumroad-API-key>,
      "kajabi_key": <Kajabi-API-key>,
      "kajabi_url": <Kajabi-API-URL>,
      "meta": {
        "hosts": [
          <Gumroad-host>,
          ...
        ],
        "disabled": <true|false>,
      },
      "links": {
        <Gumroad-link>: {
          "kajabi": {
            "funnel": <Kajabi-funnel>,
            "offer": <Kajabi-offer>
          }
        },
        ...
      }
    }

Usage
=====

Installation
============

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
directory. You can download the source from github_::

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
    # example to run kajabi-queue you need the mongo and web
    # requirements which install the pymongo and requests dependencies
    .virtual/bin/pip install gumjabi[web,mongo]

If you like to use ipython you can install it with the dev
requirement::

    .virtual/bin/pip install gumjabi[dev]

.. _github: https://github.com/thelinuxkid/gumjabi
.. _`Gumroad Ping API`: https://gumroad.com/ping
.. _`Kajabi's custom cart integration`: http://help.kajabi.com/customer/portal/articles/735181-how-do-i-setup-a-custom-shopping-cart-
