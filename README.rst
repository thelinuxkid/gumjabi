=======
Gumjabi
=======

Gumjabi is a set of services which connect the `Gumroad Ping API`_
with `Kajabi's custom cart integration`_. This allows Gumroad users to
seamlessly share content on Kajabi with their purchasers.

Description
===========

A Gumroad permalink represents a product for a purchaser to buy. A
Gumroad user wanting to give purchasers access to extra content on
Kajabi can use Gumjabi to automatically create an account for each
purchaser and give them access to a Kajabi funnel/offer.

Gumjabi is made up of two services. The `REST API`_ listens for POST
requests from Gumroad and puts the information provided in a
queue. The `Account creation service`_ processes the requests in the
queue creating a Kajabi account with access to a funnel/offer for
each. You must be familiar with the `Gumroad Ping API`_ and `Kajabi's
custom cart integration`_ in order to use Gumjabi.

Some parts of this documentation apply only to Unix-like operating
systems.

Usage
=====

To use Gumjabi you must setup the `Gumroad Ping API`_ with a Gumjabi
API URL that has the endpoint /gumroad/ping. This endpoint expects a
Gumjabi API key in the query string and any fields provided by Gumroad
as POST form parameters.

End points
----------

/gumroad/ping
+++++++++++++

Required query parameters:

    key
       The Gumjabi API key

Required POST form parameters:

    email
       The purchaser's email. The Kajabi account will be created using
       this email address.

    permalink
       The permalink the user followed to make the purchase on
       Gumroad. This permalink is tied to a Kajabi funnel/offer.

Optional POST form parameters:

    First Name
        The purchaser's first name. If it's not provided then
        'Friendly' will be used a default. The Kajabi account will be
        created using this first name.

    Last Name
        The purchaser's last name. If it's not provided then 'Human'
        will be used a default. The Kajabi account will be created
        using this last name.

Example::

    curl -w '\n' \
    -d "First%20Name=Andres" \
    -d "Last%20Name=Buritica" \
    -d "email=andres@thelinuxkid.com" \
    -d "price=100" \
    -d "permalink=andres_link" \
    "http://localhost:8080/gumroad/ping?key=1234"

The ``First Name`` and ``Last Name`` optional parameters come from
custom fields set in the permalink's user purchase form.

Installation
============

System dependencies
-------------------

    - Python 2.7
    - MongoDB 2.2.0

Python external dependencies
----------------------------

    - build-essential
    - python-dev
    - python-setuptools
    - python-virtualenv

Setup
-----

To install Gumjabi run the following commands from the project's base
directory. You can download the source code from github_::

    virtualenv .virtual
    .virtual/bin/python setup.py install
    # At this point, gumjabi will already be in easy-install.pth.
    # So, pip will not attempt to download it
    .virtual/bin/pip install gumjabi[test]

    # The test requirement installs all the dependencies. But,
    # depending on the service you wish to run you might want to install
    # only the appropriate dependencies as listed in setup.py. For
    # example to run kajabi-queue you only need the mongo and web
    # requirements which install the pymongo and requests dependencies
    .virtual/bin/pip install gumjabi[web,mongo]

Running
=======

It is recommended that you use an init daemon such as upstart_ or
runit_ to run the Gumjabi services.

REST API
--------

To start the API call the ``gumjabi-api`` cli with the ``--config``
and ``--db-config`` arguments::

    .virtual/bin/gumjabi-api --config=gumjabi-api.conf --db-config=mongodb.conf

``gumjabi-api.conf`` looks like::

      [connection]
      host = <host>
      port = <port>
      ssl-pem = <path_to_certificate>

      [api]
      restrict-hosts = <true|false>

Use ``ssl-pem`` if you want to enable SSL for the API. If you
want to restrict the hosts which can make requests to the API set
``restrict-hosts`` to true (see `Database structures`_
section). Neither option is required.

``mongodb.conf`` looks like::

    [connection]
    host = <host>:<port>
    replica-set = <replicaset-name>
    database = <database-name>

    [collection]
    gumjabi-keys = <collection-name>
    kajabi-queue = <collection-name>

The ``replica-set`` option is not necessary. If you are not using a
replica set in your MongoDB setup then omit this line. The collections
used here are described in the `Database structures`_ section.

Account creation service
------------------------

To process the requests in the queue creating the Kajabi accounts and
giving each account access to a funnel/offer call the ``kajabi-queue``
cli with the ``--db-config`` argument::

    .virtual/bin/kajabi-queue --db-config=mongodb.conf

``mongodb.conf`` looks the same as above.

``kajabi-queue`` will retry failed account creation requests a few
times before giving up. It will also restart every 5 to 10 seconds to
look for new items in the queue (as long as it's setup as a service).

.. _dbstructures:

Database structures
-------------------

Gumjabi uses two MongoDB collections. The code uses the names
``kajabi-queue`` and ``gumjabi-keys`` which are defined in
``gumjabi-api.conf`` but you can name the actual collections anything
you want. ``kajabi-queue`` is used as a queue for the Kajabi accounts
that are to be created. ``gumjabi-keys`` holds the Gumroad and Kajabi
information for each Gumjabi user and must be pre-populated. A Gumjabi
user is identified by their Gumjabi API key. For example::

    {
      "_id": "1234",
      "kajabi_key": "1357",
      "kajabi_url": "http://foo.kajabi.com/order_notifications",
      "meta": {
        "hosts": [
          "23.20.142.110",
          "23.22.199.140",
        ],
        "disabled": "true",
      },
      "links": {
        "ZUqn": {
          "kajabi_funnel": "11223",
          "kajabi_offer": "44556",
          }
        },
      }
    }

Fields:

    _id
      The Gumjabi API key

    kajabi_key:
      The Kajabi API key tied to this Gumjabi API key

    kajabi_url
      The Kajabi notification URL tied to this Gumjabi API key

    hosts:
      A list of hosts. If the ``restrict-hosts`` option is set in
      ``gumjabi-api`` then any request using this Gumjabi API key and
      coming from hosts outside this list will be denied

    disabled:
      true of false. If set to false any request using this Gumjabi
      API key will be denied

    links:
      A dictionary with Gumroad permalinks as keys

    kajabi_funnel:
     The Kajabi funnel tied to this Gumroad permalink

    kajabi_offer:
     The Kajabi offer tied to this Gumroad permalink

A SHA-256 function or greater is recommended when creating the Gumjabi
API keys.

Developing
==========

To start developing follow the instructions in the Installation_
section but replace::

    .virtual/bin/python setup.py install

with::

    .virtual/bin/python setup.py develop

If you like to use ipython you can install it with the dev
requirement::

    .virtual/bin/pip install gumjabi[dev]

.. _runit: http://smarden.org/runit/
.. _upstart: http://upstart.ubuntu.com/
.. _github: https://github.com/thelinuxkid/gumjabi
.. _`Gumroad Ping API`: https://gumroad.com/ping
.. _`Kajabi's custom cart integration`: http://help.kajabi.com/customer/portal/articles/735181-how-do-i-setup-a-custom-shopping-cart-
