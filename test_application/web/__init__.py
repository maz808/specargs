from typing import List

from flask import Blueprint

from .example import example_blueprint


api_blueprints: List[Blueprint] = []
api_blueprints.append(example_blueprint)
