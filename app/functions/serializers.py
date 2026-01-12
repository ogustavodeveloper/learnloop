from sqlalchemy.inspection import inspect


def model_to_dict(obj):
    if obj is None:
        return None
    mapper = inspect(obj)
    attrs = {}
    for column in mapper.mapper.column_attrs:
        key = column.key
        attrs[key] = getattr(obj, key)
    return attrs


def models_to_list(objs):
    return [model_to_dict(o) for o in objs]
