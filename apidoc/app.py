from flask import Flask
from marshmallow import Schema, fields

from . import doc


# Optional Flask support
app = Flask(__name__)
app.config["DEBUG"] = True
doc.init_app(app)


class GistParameter(Schema):
    gist_id = fields.Int()


class GistSchema(Schema):
    id = fields.Int()
    content = fields.Str()


@app.route("/gists/<string:gist_id>")
@doc.response(GistSchema)
@doc.parameters(GistParameter)
def get_gist(gist_id):
    """This is a summary.

    This is a description.
    """
    return '', 200


@app.route("/gists", methods=['POST'])
@doc.body(GistSchema)
def post_gist():
    """Post a gist."""
    return '', 200


app.run()
