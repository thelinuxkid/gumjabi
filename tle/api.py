import json
import logging
import bottle
import functools

from paste import httpserver
from paste.translogger import TransLogger

from collections import OrderedDict

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

class EventAPI01(object):
    def __init__(self):
        pass

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
