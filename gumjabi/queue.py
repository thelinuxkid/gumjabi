import logging
import json
import pymongo

from datetime import datetime

MAX_RETRIES = 10

from gumjabi.util import mongo

log = logging.getLogger(__name__)

def _mark_failed(colls, item, msg):
    queue_coll = colls['kajabi-queue']
    kwargs = dict([
        ('$set', dict([
            ('gave_up_msg', msg),
            ('gave_up', datetime.utcnow()),
        ]),
     ),
    ])
    mongo.safe_upsert(
        queue_coll,
        item['_id'],
        **kwargs
    )

def _mark_for_retry(colls, item, msg):
    retries = item.get('times_failed')
    if retries and retries >= MAX_RETRIES:
        msg = (
            'Queue item {_id} has been tried {max_retries} '
            'times'.format(
                _id=item['_id'],
                max_retries=MAX_RETRIES,
            )
        )
        _log_failed_error(msg)
        _mark_failed(colls, item, msg)
        return

    queue_coll = colls['kajabi-queue']
    kwargs = dict([
        ('$inc', dict([
            ('times_failed', 1),
        ]),
     ),
        ('$set', dict([
            ('last_failed', datetime.utcnow()),
            ('last_failed_msg', msg),
        ]),
     ),
    ])
    mongo.safe_upsert(
        queue_coll,
        item['_id'],
        **kwargs
    )

def _log_retry_error(msg):
    msg = '{msg}. Marking for retry.'.format(
        msg=msg,
    )
    log.error(msg)

def _log_failed_error(msg):
    msg = '{msg}. Marking as failed.'.format(
        msg=msg,
    )
    log.error(msg)

def create_one(colls, item, session):
    keys_coll = colls['gumjabi-keys']
    email = item.get('email')
    first_name = item.get('first_name')
    last_name = item.get('last_name')
    link = item.get('link')
    gumjabi_key = item.get('gumjabi_key')

    if not (email and first_name and last_name and link):
        missing = dict([
            ('email', email),
            ('first_name', first_name),
            ('last_name', last_name),
            ('link', link),
        ])
        msg = 'Found incomplete request in queue {missing}'.format(
            missing=json.dumps(missing)
        )
        _log_failed_error(msg)
        _mark_failed(colls, item, msg)
        return False
    if not gumjabi_key:
        msg = (
            'Found invalid Gumjabi API key in queue item '
            '{_id}'.format(
                _id=item['_id']
            )
        )
        _log_failed_error(msg)
        _mark_failed(colls, item, msg)
        return False

    dbkey = keys_coll.find_one({'_id': gumjabi_key})
    kajabi_key = dbkey.get('kajabi_key')
    if not kajabi_key:
        msg = (
            'Could not find a Kajabi API key for queue item '
            '{_id}'.format(
                _id=item['_id']
            )
        )
        _log_retry_error(msg)
        _mark_for_retry(colls, item, msg)
        return False
    url = dbkey.get('kajabi_url')
    if not url:
        msg = (
            'Could not find a Kajabi URL for queue item '
            '{_id}'.format(
                _id=item['_id']
            )
        )
        _log_retry_error(msg)
        _mark_for_retry(colls, item, msg)
        return False
    dblink = dbkey['links'].get(link)
    if not dblink:
        msg = 'Could not find Gumroad link {link}'.format(
            link=link,
        )
        _log_retry_error(msg)
        _mark_for_retry(colls, item, msg)
        return False
    kajabi = dblink.get('kajabi')
    if not kajabi:
        msg = 'Could not find kajabi info for link {link}'.format(
            link=link,
        )
        _log_retry_error(msg)
        _mark_for_retry(colls, item, msg)
        return False
    funnel = kajabi.get('funnel')
    if not funnel:
        msg = 'Could not find a funnel for link {link}'.format(
            link=link,
        )
        _log_retry_error(msg)
        _mark_for_retry(colls, item, msg)
        return False
    offer = kajabi.get('offer')
    if not offer:
        msg = 'Could not find an offer for link {link}'.format(
            link=link,
        )
        _log_retry_error(msg)
        _mark_for_retry(colls, item, msg)
        return False

    # id can be omitted
    params = dict([
        ('kajabi_key', kajabi_key),
        ('kjbf', funnel),
        ('kjbo', offer),
        ('email', email),
        ('first_name', first_name),
        ('last_name', last_name),
    ])
    log.info(
        'Creating Kajabi account for email {email} and link '
        '{link}'.format(
            email=email,
            link=link,
        )
    )
    res = session.post(url, params=params)
    if res.text != '1' or res.status_code != 200:
        msg = (
            'Kajabi account creation for email {email}, '
            'and link {link} failed with status code '
            '{code}'.format(
                email=email,
                link=link,
                code=res.status_code,
                )
            )
        _log_retry_error(msg)
        _mark_for_retry(colls, item, msg)
        return False
    log.debug(
        'Received an OK response from Kajabi while creating an '
        'account for {email} and link {link}'.format(
            email=email,
            link=link,
        )
    )
    return True

def create_accts(colls, session):
    queue_coll = colls['kajabi-queue']
    cursor = queue_coll.find(
        dict([
            ('gave_up', dict([('$exists', False)])),
        ]),
        sort=[
            ('requested_on', pymongo.ASCENDING),
        ],
    )
    work = False
    for item in cursor:
        work = create_one(colls, item, session)
    return work
