def create_indices(
    collection,
    indices,
    ):
    for index in indices:
        collection.ensure_index(index.items())
