from collections import OrderedDict

def create_indices(
    collection,
    indices,
    ):
    for index in indices:
        collection.ensure_index(index.items())

def safe_update(
    coll,
    _id,
    changes=None,
    **kwargs
    ):
    if changes or kwargs:
        if changes:
            kwargs['$set'] = changes
        coll.update(
            OrderedDict([
                ('_id', _id),
            ]),
            kwargs,
            upsert=True,
            safe=True,
        )
