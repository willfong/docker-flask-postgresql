from flask import Blueprint, redirect, url_for, render_template, request, session, flash, jsonify
from . import db

blueprint = Blueprint("api", __name__, url_prefix="/api")

@blueprint.route("/")
def root():
    return jsonify({'status': 'ok'})