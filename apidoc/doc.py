from collections import defaultdict

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Blueprint, jsonify, render_template


class Doc(object):
    exclude = {'HEAD', 'OPTIONS'}

    def __init__(self, app=None, config=None):
        self.app = app
        self.config = config or dict()
        self._spec = None
        self._views = defaultdict(dict)
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self._spec = self._init_spec()
        self._register_routes()

    def _init_spec(self):
        config = dict(title='ApiDoc',
                      version='1.0.0',
                      openapi_version='3.0.2')
        config.update(self.app.config.get('apidoc', {}))
        config.update(self.config)
        return APISpec(plugins=[MarshmallowPlugin()], **config)

    def _register_routes(self):
        blueprint = Blueprint('apidoc', __name__,
                              static_folder='./static',
                              static_url_path='/docs/static',
                              template_folder='./templates')

        blueprint.add_url_rule('/docs/', 'apidocs',
                               lambda: render_template('index.html'))
        blueprint.add_url_rule('/docs/spec.json', 'json_spec',
                               self._get_spec)

        self.app.register_blueprint(blueprint)

    def _get_spec(self):
        for rule in self.app.url_map.iter_rules():
            view = self._views.get(rule.endpoint)
            if view:
                self._spec.path(
                    path=rule.rule,
                    parameters=self._make_parameters(rule.arguments),
                    operations=self._make_operations(rule.methods, view)
                )
        return jsonify(self._spec.to_dict())

    def body(self, schema):
        def decorator(func):
            summary, description = self._split_docstring(func)
            self._views[func.__name__].update(
                summary=summary,
                description=description,
                requestBody={
                    'content': {
                        'application/json': {
                            'schema': schema.__name__
                        }
                    }
                }
            )
            return func
        return decorator

    def parameters(self, path=None, query=None, header=None):
        path = path if isinstance(path, list) else [path]
        query = query if isinstance(query, list) else [query]
        header = header if isinstance(header, list) else [header]
        params = []
        params.extend(['path', i] for i in path)
        params.extend(['query', i] for i in query)
        params.extend(['header', i] for i in header)

        def decorator(func):
            summary, description = self._split_docstring(func)
            self._views[func.__name__].update(
                summary=summary,
                description=description,
                parameters=[{'in': location, 'schema': schema}
                            for location, schema in params
                            if schema]
            )
            return func
        return decorator

    def response(self, success=None, **responses):
        if success:
            responses = dict({'200': success}, **responses)

        def decorator(func):
            summary, description = self._split_docstring(func)
            self._views[func.__name__].update(
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
            )
            return func
        return decorator

    @staticmethod
    def _make_parameters(arguments):
        return [
            {'in': 'path', 'name': arg, 'required': True}
            for arg in arguments
        ]

    def _make_operations(self, methods, view):
        return {
            method.lower(): view
            for method in methods
            if method not in self.exclude
        }

    @staticmethod
    def _split_docstring(func):
        docstring = func.__doc__
        first_new_line = docstring.find('\n')
        if first_new_line != -1:
            summary = docstring[:first_new_line].strip()
            description = docstring[first_new_line:].strip()
            return summary, description
        return docstring, ''
