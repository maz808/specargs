from typing import List

from flask import Blueprint

from .examples import examples_blueprint
from .spec import spec


api_blueprints: List[Blueprint] = []
api_blueprints.append(examples_blueprint)
