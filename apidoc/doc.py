from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from collections import defaultdict

spec = APISpec(
    title="Gisty",
    version="1.0.0",
    openapi_version="3.0.2",
    info=dict(description="A minimal gist API"),
    plugins=[MarshmallowPlugin()],
)


views = defaultdict(dict)


def body(schema):
    def decorator(func):
        summary, description = _split_docstring(func)
        views[func.__name__].update(dict(
            summary=summary,
            description=description,
            requestBody={
                'content': {
                    'application/json': {
                        'schema': schema.__name__
                    }
                }
            }
        ))
        # @wraps(func)
        # def wrapper(*args, **kwargs):
        #     return func(*args, **kwargs)
        # return wrapper
        return func
    return decorator


def parameters(path=None, query=None, header=None):
    path = path if isinstance(path, list) else [path]
    query = query if isinstance(query, list) else [query]
    header = header if isinstance(header, list) else [header]
    params = []
    params.extend(['path', i] for i in path)
    params.extend(['query', i] for i in query)
    params.extend(['header', i] for i in header)
    def decorator(func):
        summary, description = _split_docstring(func)
        views[func.__name__].update(dict(
            summary=summary,
            description=description,
            parameters=[{'in': location, 'schema': schema}
                        for location, schema in params
                        if schema]
        ))
        return func
    return decorator


def response(success=None, **responses):
    if success:
        responses = dict({'200': success}, **responses)
    def decorator(func):
        summary, description = _split_docstring(func)
        views[func.__name__].update(dict(
            summary=summary,
            description=description,
            responses={
                code: {
                    'content': {
                        'application/json': {
                            'schema': schema.__name__
                        }
                    }
                }
                for code, schema in responses.items()
            }
        ))
        return func
    return decorator


def get_spec(app):
    for rule in app.url_map.iter_rules():
        view = views.get(rule.endpoint)
        if view:
            spec.path(path=rule.rule,
                      parameters=_make_parameters(rule.arguments),
                      operations=_make_operations(rule.methods, view))
    return spec.to_dict()


def _make_parameters(arguments):
    return [
        {'in': 'path', 'name': arg, 'required': True}
        for arg in arguments
    ]

EXCLUDE = {'HEAD', 'OPTIONS'}

def _make_operations(methods, view):
    return {
        method.lower(): view
        for method in methods
        if method not in EXCLUDE
    }


def _split_docstring(func):
    docstring = func.__doc__
    first_new_line = docstring.find('\n')
    if first_new_line != -1:
        summary = docstring[:first_new_line].strip()
        description = docstring[first_new_line:].strip()
        return summary, description
    return docstring, ''
