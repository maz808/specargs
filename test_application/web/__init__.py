from typing import List

from flask import Blueprint

from .examples import examples_blueprint
from .about import bp
from .spec import spec


api_blueprints: List[Blueprint] = []
api_blueprints.append(examples_blueprint)
api_blueprints.append(bp)
