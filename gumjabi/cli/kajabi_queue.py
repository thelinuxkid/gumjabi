import argparse
import random
import time
import logging
import pymongo
import requests

from gumjabi import queue
from gumjabi.util.config import (
    collections,
    )
from gumjabi.util import mongo

log = logging.getLogger(__name__)

# Disable annoying "HTTP connection" log lines from the requests module
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

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
    colls = collections(
        config=args.db_config,
        )
    indices = [
        {'meta.requested_on': pymongo.ASCENDING},
        ]
    mongo.create_indices(
        collection=colls['kajabi-queue'],
        indices=indices,
        )
    session = requests.session()
    if not queue.create_accts(colls, session):
        delay = random.randint(5, 10)
        log.debug('No work, sleeping %d seconds...', delay)
        time.sleep(delay)
