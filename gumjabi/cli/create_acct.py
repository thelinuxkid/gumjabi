import argparse
import random
import time
import logging
import pymongo

from gumjabi import create
from gumjabi.util.config import (
    collections,
    )
from gumjabi.util import mongo

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
        '--db-config',
        help=('Path to the file with information on how to '
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
        {'requested_on': pymongo.ASCENDING},
        ]
    mongo.create_indices(
        collection=colls['kajabi_queue'],
        indices=indices,
        )
    if not create.create_all(colls):
        delay = random.randint(5, 10)
        log.info('No work, sleeping %d seconds...', delay)
        time.sleep(delay)
