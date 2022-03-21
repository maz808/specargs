from flask import Blueprint
from apispec_webargs import use_kwargs, use_response, use_empty_response
from webargs import fields


bp = Blueprint("about-api", __name__, url_prefix="/about")


@bp.get("")
@use_kwargs({"details": fields.Bool()})
# @use_response({"about": fields.String()})
@use_response(fields.List(fields.String()))
def get_about():
    # return {"about": "THIS IS THE ABOUT"}
    # return "THIS IS THE ABOUT"
    return "THIS IS THE ABOUT".encode("utf-8")


@bp.post("")
@use_kwargs({"details": fields.Str()})
@use_empty_response()
def post_about():
    return "ABOUT POSTED"


@bp.get("/<int:id>")
@use_kwargs({"details": fields.Bool()})
@use_response({"about": fields.String()})
def get_single_about():
    return {"about": "THIS IS THE ABOUT"}


@bp.delete("/<int:id>")
@use_kwargs({"details": fields.Str()})
@use_empty_response()
def delete_single_about():
    return "ABOUT DELETED"
