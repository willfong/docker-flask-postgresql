import os
from . import db
from flask import Flask, redirect, url_for, render_template
#from flask_talisman import Talisman


def start_app():
    # create and configure the app
    a = Flask(__name__, instance_relative_config=True)
    #Talisman(a, content_security_policy=None)

    a.config.from_mapping(SECRET_KEY=os.environ.get("SESSION_SECRET_KEY"))

    from . import api
    a.register_blueprint(api.blueprint)

    from . import auth
    a.register_blueprint(auth.blueprint)
    #a.register_blueprint(auth.login_github)
    #a.register_blueprint(auth.login_google)
    #a.register_blueprint(auth.login_facebook)

    return a
