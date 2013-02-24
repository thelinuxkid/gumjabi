import logging
import json
import pymongo

from datetime import datetime

MAX_RETRIES = 10

from gumjabi.util import mongo

log = logging.getLogger(__name__)

def _mark_failed(colls, item, msg):
    log.error(
        '{msg}. Marking as failed.'.format(
            msg=msg,
        )
    )
    queue_coll = colls['kajabi-queue']
    kwargs = dict([
        ('$set', dict([
            ('meta.gave_up_msg', msg),
            ('meta.gave_up_on', datetime.utcnow()),
        ]),
     ),
    ])
    mongo.safe_upsert(
        queue_coll,
        item['_id'],
        **kwargs
    )

def _mark_successful(colls, item):
    queue_coll = colls['kajabi-queue']
    kwargs = dict([
        ('$set', dict([
            ('meta.succeeded_on', datetime.utcnow()),
        ]),
     ),
    ])
    mongo.safe_upsert(
        queue_coll,
        item['_id'],
        **kwargs
    )

def _mark_for_retry(colls, item, msg):
    retries = item.get('meta')
    if retries:
        retries = retries.get('times_failed')
    if retries and retries >= MAX_RETRIES:
        msg = (
            'Queue item {_id} has been tried {max_retries} '
            'times'.format(
                _id=item['_id'],
                max_retries=MAX_RETRIES,
            )
        )
        _mark_failed(colls, item, msg)
        return

    log.error(
        '{msg}. Marking for retry.'.format(
            msg=msg,
        )
    )
    queue_coll = colls['kajabi-queue']
    kwargs = dict([
        ('$inc', dict([
            ('meta.times_failed', 1),
        ]),
     ),
        ('$set', dict([
            ('meta.last_failed_on', datetime.utcnow()),
            ('meta.last_failed_msg', msg),
        ]),
     ),
    ])
    mongo.safe_upsert(
        queue_coll,
        item['_id'],
        **kwargs
    )

def create_one(colls, item, session):
    keys_coll = colls['gumjabi-keys']
    email = item.get('email')
    first_name = item.get('first_name')
    last_name = item.get('last_name')
    gumroad_link = item.get('gumroad_link')
    gumjabi_key = item.get('gumjabi_key')

    if not (email and first_name and last_name and gumroad_link):
        missing = dict([
            ('email', email),
            ('first_name', first_name),
            ('last_name', last_name),
            ('gumroad_link', gumroad_link),
        ])
        msg = 'Found incomplete request in queue {missing}'.format(
            missing=json.dumps(missing)
        )
        _mark_failed(colls, item, msg)
        return False
    if not gumjabi_key:
        msg = (
            'Could not find a valid Gumjabi API key in queue item '
            '{_id}'.format(
                _id=item['_id']
            )
        )
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
        _mark_for_retry(colls, item, msg)
        return False
    dblink = dbkey['gumroad_links'].get(gumroad_link)
    if not dblink:
        msg = (
            'Could not find Gumroad link {gumroad_link}'.format(
                gumroad_link=gumroad_link,
            )
        )
        _mark_for_retry(colls, item, msg)
        return False
    funnel = dblink.get('kajabi_funnel')
    if not funnel:
        msg = (
            'Could not find a Kajabi funnel for Gumroad link '
            '{gumroad_link}'.format(
                gumroad_link=gumroad_link,
            )
        )
        _mark_for_retry(colls, item, msg)
        return False
    offer = dblink.get('kajabi_offer')
    if not offer:
        msg = (
            'Could not find a Kajabi offer for Gumroad link '
            '{gumroad_link}'.format(
                gumroad_link=gumroad_link,
            )
        )
        _mark_for_retry(colls, item, msg)
        return False

    # id can be omitted
    params = dict([
        ('api_key', kajabi_key),
        ('kjbf', funnel),
        ('kjbo', offer),
        ('email', email),
        ('first_name', first_name),
        ('last_name', last_name),
    ])
    log.info(
        'Creating Kajabi account for email {email} and Gumroad link '
        '{gumroad_link}'.format(
            email=email,
            gumroad_link=gumroad_link,
        )
    )
    res = session.post(url, params=params)
    if res.text != '1' or res.status_code != 200:
        # res.text can contain a lot more than just a number
        msg = (
            'Kajabi account creation for email {email} '
            'and Gumroad link {gumroad_link} failed with status code '
            '{code}'.format(
                email=email,
                gumroad_link=gumroad_link,
                code=res.status_code,
                )
            )
        _mark_for_retry(colls, item, msg)
        return False
    log.debug(
        'Received an OK response from Kajabi while creating an '
        'account for email {email} and Gumroad link '
        '{gumroad_link}'.format(
            email=email,
            gumroad_link=gumroad_link,
        )
    )
    _mark_successful(colls, item)
    return True

def create_accts(colls, session):
    queue_coll = colls['kajabi-queue']
    gave_up_query = dict([
        ('meta.gave_up_on', dict([('$exists', False)])),
    ])
    requested_query = dict([
        ('meta.succeeded_on', dict([('$exists', False)])),
    ])
    and_query = dict([
        ('$and', [gave_up_query, requested_query]),
    ])
    cursor = queue_coll.find(
        and_query,
        sort=[
            ('meta.requested_on', pymongo.ASCENDING),
        ],
    )
    work = False
    for item in cursor:
        work = create_one(colls, item, session)
    return work
