import json
import logging
import bottle
import functools
import requests

from datetime import datetime
from collections import OrderedDict

from paste import httpserver
from paste.translogger import TransLogger

from gumjabi.util import mongo

log = logging.getLogger(__name__)

DEFAULT_FIRST_NAME = 'Friendly'
DEFAULT_LAST_NAME = 'Human'

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

def plain_content(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        set_content('text/plain')
        return fn(*args, **kwargs)
    return wrapper

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
        self._cli_coll = colls['clients']
        self._gmrd_coll = colls['gumroad']
        self._kjb_coll = colls['kajabi']

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

    def _create_kajabi_customer(
            self,
            email,
            first_name,
            last_name,
            link,
            kajabi,
            ):
        # TODO make this asynchronous
        # TODO Allow for multiple users with different keys and urls
        meta = self._kjb_coll.find_one('meta')
        api_key = meta.get('api_key')
        # None and empty are both bad
        if not api_key:
            log.error('Could not find a kajabi api key')
            return False
        url = meta.get('url')
        # None and empty are both bad
        if not url:
            log.error('Could not find a kajabi url')
            return False
        # None and empty are both bad
        if not kajabi:
            log.error(
                'Could not find kajabi info for link {link}'.format(
                    link=link,
                )
            )
            return False
        funnel = kajabi.get('funnel')
        # None and empty are both bad
        if not funnel:
            log.error(
                'Could not find a funnel for link {link}'.format(
                    link=link,
                )
            )
            return False
        offer = kajabi.get('offer')
        # None and empty are both bad
        if not offer:
            log.error(
                'Could not find an offer for link {link}'.format(
                    link=link,
                )
            )
            return False
        # id can be omitted
        params = OrderedDict([
            ('api_key', api_key),
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
        res = requests.post(url, params=params)
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
            log.error(msg)
            return False
        log.debug(
            'Received an OK response from Kajabi while creating an '
            'account for {email} and link {link}'.format(
                email=email,
                link=link,
            )
        )
        return True

    def _inc_downloads(self, email, link):
        key = 'redirections.{link}'.format(link=link)
        kwargs = OrderedDict([
            ('$inc', OrderedDict([
                (key, 1),
            ]),
         )
        ])
        mongo.safe_upsert(
            self._cli_coll,
            email,
            **kwargs
        )

    def _log_gumroad_param_error(self, param, form):
        tmpl = (
            'Gumroad did not provide {param} but it did '
            'provide: {form}. Returning error URL for redirection.'
        )
        msg = tmpl.format(
            param=param,
            form=json.dumps(dict(form)),
        )
        log.error(msg)

    @bottle.post('/gumroad/webhook')
    @bottle.post('/gunroad/webhook/')
    @update_key
    @plain_content
    def gumroad_webhook(self):
        form = bottle.request.forms
        email = form.get('email')
        price = form.get('price')
        first_name = form.get('first_name')
        last_name = form.get('last_name')
        test = form.get('test')
        link = bottle.request.query.link
        # TODO Allow for multiple users with multiple links
        links = self._gmrd_coll.find_one({'_id': 'links'})
        test_redir = links['test']['redirect']
        error_redir = links['error']['redirect']

        # Simpler than loading JSON for just this variable
        if test == 'true':
            log.info('Returning test URL for redirection')
            return test_redir
        if not email:
            self._log_gumroad_param_error(
                param='an email',
                form=form,
            )
            return error_redir
        if not price:
            self._log_gumroad_param_error(
                param='a price',
                form=form,
            )
            return error_redir
        if not link:
            self._log_gumroad_param_error(
                param='a link',
                form=form,
            )
            return error_redir
        if not first_name:
            first_name = DEFAULT_FIRST_NAME
        if not last_name:
            last_name = DEFAULT_LAST_NAME

        dblink = links.get(link)
        # None and empty are both bad
        if not dblink:
            msg = 'Could not find Gumroad link {link}'.format(
                    link=link,
            )
            log.error(msg)
            return error_redir
        redir = dblink.get('redirect')
        # None and empty are both bad
        if not redir:
            msg = 'Could not find a redirect for link {link}'.format(
                    link=link,
            )
            log.error(msg)
            return error_redir
        kajabi = dblink.get('kajabi')
        self._create_kajabi_customer(
            email,
            first_name,
            last_name,
            link,
            kajabi,
        )
        self._inc_downloads(email, link)
        log.debug(
            'Returning URL "{redir}" for redirection'.format(
                redir=redir,
            )
        )
        return redir