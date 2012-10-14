import os
import pymongo

from ConfigParser import SafeConfigParser

DEFAULT_DB_HOST = 'localhost:27017'

def abs_path(path):
    path = os.path.expanduser(path)
    path = os.path.abspath(path)

    return path

def config_parser(path):
    path = abs_path(path)
    config = SafeConfigParser()
    with open(path) as fp:
        config.readfp(fp)

    return config

def _db_config_parts(path):
    config = config_parser(path)

    conn = dict(config.items('connection'))
    if 'host' not in conn:
        conn['host'] =  DEFAULT_DB_HOST

    colls = dict(config.items('collection'))

    return (conn, colls)

def collections(
    config,
    read_preference=None,
    ):
    (conn, colls) = _db_config_parts(config)
    host = conn['host']
    replica_set = conn.get('replica-set')
    db = conn['database']

    if replica_set:
        conn = pymongo.ReplicaSetConnection(
            host,
            replicaSet=replica_set,
            )
        # ReadPreference.PRIMARY is the default
        if read_preference is not None:
            conn.read_preference = read_preference
    else:
        conn = pymongo.Connection(host)

    db = conn[db]
    colls = dict(
        [(k,db[v])
         for k,v
         in colls.items()
         ]
        )

    return colls
