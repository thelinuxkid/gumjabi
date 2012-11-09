import argparse
import logging
import pymongo

from paste.gzipper import middleware
from bottle import install, run, default_app
from gumjabi.util.config import (
    config_parser,
    collections,
    )
from gumjabi.api import EventAPI01, APIServer
from gumjabi.util import mongo
from gumjabi.util.config import abs_path, config_option

log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Start the Glue API',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False,
        help='output DEBUG logging statements (default: %(default)s)',
        )
    parser.add_argument(
        '--config',
        help=('path to the file with information on how to '
              'configure the Glue API'
              ),
        required=True,
        metavar='PATH',
        type=str,
        )
    parser.add_argument(
        '--db-config',
        help=('path to the file with information on how to '
              'retrieve and store data in the database'
              ),
        required=True,
        metavar='PATH',
        type=str,
        )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s.%(msecs)03d %(name)s: %(levelname)s: %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
        )
    config = config_parser(args.config)
    host = config.get('connection', 'host')
    port = config.get('connection', 'port')
    pem = config_option(config.get, 'connection', 'ssl_pem')
    colls = collections(
        config=args.db_config,
        )
    indices = [
        {'meta.hosts': pymongo.ASCENDING},
        ]
    mongo.create_indices(
        collection=colls['gumroad_keys'],
        indices=indices,
        )

    restrict = config_option(
        config.getboolean,
        'api',
        'restrict_host',
    )
    if restrict is None:
        restrict = False
    glue_api = EventAPI01(
        colls,
        restrict_host=restrict,
    )
    install(glue_api)
    log.info(
        'Starting server http://{host}:{port}'.format(
            host=host,
            port=port,
            )
        )
    app = middleware(default_app())
    server_opts = dict([
        ('quiet', True),
        ])
    if pem:
        pem = abs_path(pem)
        server_opts['ssl_pem'] = pem
    run(app=app,
        host=host,
        port=port,
        server=APIServer,
        **server_opts
        )
