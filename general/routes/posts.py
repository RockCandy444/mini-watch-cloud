from flask import Blueprint, redirect, render_template, request, url_for

from post_rules import validate_post
from repositories import posts

posts_bp = Blueprint("posts", __name__)


def missing_post():
    return render_template("error.html", message="게시글을 찾을 수 없습니다."), 404


@posts_bp.get("/")
def index():
    return render_template("index.html", posts=posts.list_posts())


@posts_bp.get("/board/<int:post_id>")
def detail(post_id):
    post = posts.find_post(post_id)
    if post is None:
        return missing_post()
    return render_template("detail.html", post=post)


@posts_bp.route("/board/new", methods=["GET", "POST"])
def new():
    title = body = ""
    errors = []
    if request.method == "POST":
        title, body, errors = validate_post(
            request.form.get("title", ""), request.form.get("body", "")
        )
        if not errors:
            post_id = posts.create_post(title, body)
            return redirect(url_for("posts.detail", post_id=post_id), code=303)
    return render_template("new.html", title=title, body=body, errors=errors), 400 if errors else 200


@posts_bp.route("/board/<int:post_id>/edit", methods=["GET", "POST"])
def edit(post_id):
    post = posts.find_post(post_id)
    if post is None:
        return missing_post()
    title, body = post["title"], post["body"]
    errors = []
    if request.method == "POST":
        title, body, errors = validate_post(
            request.form.get("title", ""), request.form.get("body", "")
        )
        if not errors:
            updated = posts.update_post(post_id, title, body)
            if updated is None:
                return missing_post()
            return redirect(url_for("posts.detail", post_id=post_id), code=303)
    return render_template("edit.html", post=post, title=title, body=body, errors=errors), 400 if errors else 200


@posts_bp.route("/board/<int:post_id>/delete", methods=["GET", "POST"])
def delete(post_id):
    if request.method == "POST":
        deleted = posts.delete_post(post_id)
        if deleted is None:
            return missing_post()
        return redirect(url_for("posts.index"), code=303)
    post = posts.find_post(post_id)
    if post is None:
        return missing_post()
    return render_template("delete.html", post=post)


@posts_bp.get("/posts/<int:post_id>")
def get_post(post_id):
    """수업에서 사용하던 JSON 조회 주소도 계속 제공한다."""
    post = posts.find_post(post_id)
    if post is None:
        return {"error": "게시글을 찾을 수 없습니다."}, 404
    return post
