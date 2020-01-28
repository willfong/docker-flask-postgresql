import os
import requests
import jwt
import pprint
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, redirect, url_for, flash, session, render_template, request, current_app, jsonify

from . import db

blueprint = Blueprint("auth", __name__, url_prefix="/auth")

FACEBOOK_URL_APP_TOKEN = f'https://graph.facebook.com/oauth/access_token?client_id={os.environ.get("FACEBOOK_CLIENT_ID")}&client_secret={os.environ.get("FACEBOOK_CLIENT_SECRET")}&grant_type=client_credentials'



# TODO: Don't know why my decorator doesn't work.
def login_required(func):
    def wrapper():
        if 'user_id' not in session:
            return redirect(url_for("auth.login"))
        return func()

    return wrapper


def facebook_get_app_token():
    return requests.get(FACEBOOK_URL_APP_TOKEN).json()['access_token']

def facebook_verify_access_token(access_token):
    app_token = facebook_get_app_token()
    access_token_url = f'https://graph.facebook.com/debug_token?input_token={access_token}&access_token={app_token}'
    try:
        user_id = requests.get(access_token_url).json()['data']['user_id']
    except (ValueError, KeyError, TypeError) as error:
        print(error)
        return error
    return user_id

def facebook_find_or_create_user(id):
    query = "INSERT INTO users (facebook_id, last_login) VALUES (%s, NOW()) ON CONFLICT (facebook_id) DO UPDATE SET last_login = NOW() RETURNING id"
    params = (id,)
    user_id = db.write(query, params, returning=True)[0]
    return user_id  

def google_verify_access_token(access_token):
    # We're doing it the lazy way here. What we get from the client side is JWT, we can just verify that instead of calling Google
    # Reason for that is to reduce the amount of dependencies for this, a demo app
    # For production, we should do it the right way by using google-auth 

    jwt = requests.get(f'https://oauth2.googleapis.com/tokeninfo?id_token={access_token}').json()
    if jwt.get('error'):
        print(jwt.get('error_description'))
        return jwt.get('error_description')
    return jwt['sub']

def google_find_or_create_user(id):
    query = "INSERT INTO users (google_id, last_login) VALUES (%s, NOW()) ON CONFLICT (google_id) DO UPDATE SET last_login = NOW() RETURNING id"
    params = (id,)
    user_id = db.write(query, params, returning=True)[0]
    return user_id 

def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
    auth_token = request.headers.get('Authorization', '')

        invalid_msg = {
            'message': 'Invalid token. Registeration and / or authentication required',
            'authenticated': False
        }
        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }

        try:
            data = jwt.decode(auth_token, current_app.config['SECRET_KEY'])
            return f(data['user_id'], *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return jsonify(invalid_msg), 401
    return _verify

@blueprint.route("/login/facebook", methods=['POST'])
def facebook_login():
    access_token = request.json.get("accessToken")
    # TODO: Handle bad access token
    facebook_id = facebook_verify_access_token(access_token)
    user_id = facebook_find_or_create_user(facebook_id)
    token = jwt.encode({
        'user_id': user_id,
        'facebook_id': facebook_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=30)},
        current_app.config['SECRET_KEY'])
    return jsonify({ 'token': token.decode('UTF-8') })

@blueprint.route("/login/google", methods=['POST'])
def google_login():
    access_token = request.json.get("accessToken")
    google_id = google_verify_access_token(access_token)
    user_id = google_find_or_create_user(google_id)
    token = jwt.encode({
        'user_id': user_id,
        'google_id': google_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=30)},
        current_app.config['SECRET_KEY'])
    return jsonify({ 'token': token.decode('UTF-8') })


@blueprint.route("/logout")
def logout():
    session.clear()
    flash("Successfully logged out!", "success")
    return redirect(url_for("index.home"))





'''
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook

login_github = make_github_blueprint(
    client_id=os.environ.get("GITHUB_CLIENT_ID"),
    client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
    redirect_to="auth.oauth_github"
)

login_google = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    redirect_to="auth.oauth_google"
)

login_facebook = make_facebook_blueprint(
    client_id=os.environ.get("FACEBOOK_CLIENT_ID"),
    client_secret=os.environ.get("FACEBOOK_CLIENT_SECRET"),
    redirect_to="auth.oauth_facebook"
)

@blueprint.route("/oauth/github")
def oauth_github():
    resp = github.get("/user")
    assert resp.ok
    oauth_resp = resp.json()
    print("GitHub Response:\n{}".format(oauth_resp))
    # TODO: Should be checking for errors from DB
    query = "INSERT INTO users (github_id, name, avatar, last_login) VALUES (%s, %s, %s, NOW()) ON CONFLICT (github_id) DO UPDATE SET last_login = NOW() RETURNING id, name"
    # GitHub/Oauth returns keys with values of None. Can't use .get() defaults, need to use or.
    params = (
        oauth_resp.get("id"),
        oauth_resp.get("name", "") or "",
        oauth_resp.get("avatar_url", "") or "",
    )
    session["user_id"], session["user_name"] = db.write(query, params, returning=True)
    flash("Successfully logged in via GitHub!", "success")
    return redirect(url_for("app.home"))


@blueprint.route("/oauth/google")
def oauth_google():
    resp = google.get("/plus/v1/people/me")
    oauth_resp = resp.json()
    print("Google Response:\n{}".format(oauth_resp))
    # TODO: Should be checking for errors from DB
    query = "INSERT INTO users (google_id, name, avatar, last_login) VALUES (%s, %s, %s, NOW()) ON CONFLICT (google_id) DO UPDATE SET last_login = NOW() RETURNING id, name"
    params = (
        oauth_resp.get("id"),
        oauth_resp.get("displayName", "") or "",
        oauth_resp.get("image", "").get("url").replace('/s50/', '/s500/') or "",
    )
    session["user_id"], session["user_name"] = db.write(query, params, returning=True)
    flash("Successfully logged in via Google!", "success")
    return redirect(url_for("app.home"))


@blueprint.route("/oauth/facebook")
def oauth_facebook():
    resp = facebook.get("/me")
    assert resp.ok
    oauth_resp = resp.json()
    print("Facebook Response:\n{}".format(oauth_resp))
    resp = facebook.get("/me/picture?redirect=0&width=1000")
    fb_photo = resp.json()
    print("Facebook Photo: {}".format(fb_photo.get('data').get('url')))
    # TODO: Should be checking for errors from DB
    query = "INSERT INTO users (facebook_id, name, avatar, last_login) VALUES (%s, %s, NOW()) ON CONFLICT (facebook_id) DO UPDATE SET last_login = NOW() RETURNING id, name"
    params = (
        oauth_resp.get("id"),
        oauth_resp.get("name", "") or "",
        fb_photo.get('data').get('url') or ""
    )
    session["user_id"], session["user_name"] = db.write(query, params, returning=True)
    flash("Successfully logged in via Facebook!", "success")
    return redirect(url_for("app.home"))
'''