from flask import Blueprint, redirect, url_for, render_template, request, session, flash, jsonify
from . import db
from . import auth

blueprint = Blueprint("api", __name__, url_prefix="/api")

@blueprint.route("/")
@auth.token_required
def root(id):
    print("User ID: {}".format(id))
    return jsonify({'status': 'ok'})