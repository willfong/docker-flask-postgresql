from flask import Blueprint, redirect, url_for, render_template, request, session, flash

from flask_dance.contrib.github import github
from . import db
from . import auth

blueprint = Blueprint("app", __name__, url_prefix="/app")


@blueprint.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for("auth.login"))
    users = db.read("SELECT COUNT(*) AS total FROM users", one=True)
    posts = db.read(
        "SELECT u.name AS name, u.avatar AS avatar, p.message AS message, p.created AS created FROM posts AS p INNER JOIN users AS u ON p.users_id = u.id ORDER BY p.created DESC LIMIT 20"
    )

    return render_template(
        "app.html", total_users=users["total"], posts=posts
    )


@blueprint.route("/add", methods=["POST"])
def add_post():
    if 'user_id' not in session:
        return redirect(url_for("auth.login"))
    message = request.form.get("message")
    query = "INSERT INTO posts (users_id, message) VALUES (%s, %s)"
    params = (session["user_id"], message)
    db.write(query, params)
    flash("Successfully posted message", "success")
    return redirect(url_for("app.home"))
