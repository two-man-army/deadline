"""
    Universal helper methods that are useful across apps
"""


def fetch_models_by_pks(ids_by_models) -> ([], bool, str):
    """
    Given a dictionary of Django ORM Model Objects: Primary Keys,
        tries to fetch the object and returns an error message if any fetch fails
    Returning them in correct order obviously relies on Python 3.6's ordered dictionaries

    :returns a list of the fetched objects, a boolean indicating if everything is valid and a potential error string
    """
    fetched_objects = []
    for model, id in ids_by_models.items():
        try:
            fetched_objects.append(model.objects.get(id=id))
        except model.DoesNotExist:
            return None, False, f'{model.__name__} with ID {id} does not exist.'

    return fetched_objects, True, ''
