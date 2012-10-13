import json
import logging
import bottle
import functools

from datetime import datetime
from collections import OrderedDict

from paste import httpserver
from paste.translogger import TransLogger

log = logging.getLogger(__name__)

class APILogger(TransLogger):
    def write_log(
        self,
        environ,
        method,
        req_uri,
        start,
        status,
        bytes_,
        ):
        remote_addr = environ['REMOTE_ADDR']
        protocol = environ['SERVER_PROTOCOL']
        referer = environ.get('HTTP_REFERER', '-')
        user_agent = environ.get('HTTP_USER_AGENT', '-')
        msg = ('{remote_addr} {method} {req_uri} {protocol} {status} '
               '{bytes_} {referer} {user_agent}'
               ).format(
            remote_addr=remote_addr,
            method=method,
            req_uri=req_uri,
            protocol=protocol,
            status=status,
            bytes_=bytes_,
            referer=referer,
            user_agent=user_agent,
            )
        log.info(msg)

class APIServer(bottle.ServerAdapter):
    def run(self, handler):
        handler = APILogger(handler)
        httpserver.serve(
            handler,
            host=self.host,
            port=str(self.port),
            **self.options
            )

def set_content(type_, charset='charset=UTF-8'):
    bottle.response.content_type = '{type_}; {charset}'.format(
        type_=type_,
        charset=charset,
        )

def json_content(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        set_content('application/json')
        return fn(*args, **kwargs)
    return wrapper

@bottle.error(404)
@bottle.error(403)
@bottle.error(500)
@json_content
def api_error(error):
    status = OrderedDict([
            ('code', error.status),
            ('message', error.body)
            ])
    status = OrderedDict([
            ('status', status),
            ])

    return json.dumps(status)

def update_key(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        key = bottle.request.query.key
        # request.query returns empty if attr doesn't exist
        if not key:
            raise bottle.HTTPError(
                status=403,
                body='You must specify an API key',
            )
        host = bottle.request.environ.get('REMOTE_ADDR')
        db_key = kwargs['self']._keys_coll.find_one(
            OrderedDict([
                ('hosts', host),
                ]),
        )
        if db_key is None or db_key['disabled'] or key != db_key['key']:
            raise bottle.HTTPError(
                status=403,
                body='Invalid API key',
                )
        res = fn(*args, **kwargs)
        try:
            now = datetime.utcnow()
            kwargs['self']._keys_coll.update(
                OrderedDict([
                        ('hosts', host),
                        ]),
                OrderedDict([
                        ('$set', OrderedDict([
                                    ('last_used', now),
                                    ])
                         ),
                        ('$inc', OrderedDict([
                                    ('times_used', 1),
                                    ])
                         ),
                        ]),
                )
        except Exception, e:
            log.error(
                'Could not update key for {host}: {e}'.format(
                    host=host,
                    e=str(e),
                )
            )
        finally:
            return res
    return wrapper

class EventAPI01(object):
    def __init__(self, colls):
        self._keys_coll = colls['keys']

    def apply(self, callback, context):
        """
        Similar to a bottle.JSONPlugin's apply
        method. This one also ensures that self
        is available to methods with bottle
        decorators.
        """
        @functools.wraps(callback)
        @json_content
        def wrapper(*args, **kwargs):
            kwargs['self'] = self
            return callback(*args, **kwargs)
        return wrapper

    @bottle.post('/webhook')
    @bottle.post('/webhook/')
    @update_key
    def gumroad_webhook(self):
        pass
