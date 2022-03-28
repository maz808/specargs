from enum import Enum
import os
import sys

import webargs

class Framework(Enum):
    FLASK = "flask"
    DJANGO = "django"
    TORNADO = "tornado"
    BOTTLE = "bottle"


class MissingFrameworkError(Exception):
    '''Raised when the project environment has not installed a supported framework'''
    pass


class MultipleFrameworkError(Exception):
    '''Raised when the project environment has installed multiple supported frameworks'''
    pass


def _determine_framework():
    active_framework = None
    for framework in Framework:
        if framework.value in sys.modules:
            if active_framework:
                raise MultipleFrameworkError("Multiple frameworks in the environment is not supported!")
            active_framework = framework

    if not active_framework:
        raise MissingFrameworkError("A supported web framework (e.g. Flask, Django, etc.) must be installed!")

    return active_framework


FRAMEWORK = _determine_framework() if not os.environ.get("ASWA_DOCS", False) else None

if not FRAMEWORK:
    parser = webargs.core.Parser()
    get_request_body = create_paths = lambda: None
    from ..plugin import WebargsPlugin
elif FRAMEWORK == Framework.FLASK:
    from webargs.flaskparser import parser
    from .flask import get_request_body, create_paths, FlaskWebargsPlugin as WebargsPlugin
elif FRAMEWORK == Framework.DJANGO:
    from webargs.djangoparser import parser
    from .django import get_request_body, create_paths, DjangoWebargsPlugin as WebargsPlugin
elif FRAMEWORK == Framework.TORNADO:
    from webargs.tornadoparser import parser
    from .tornado import TornadoWebargsPlugin as WebargsPlugin
elif FRAMEWORK == Framework.BOTTLE:
    from webargs.bottleparser import parser
    from .bottle import BottleWebargsPlugin as WebargsPlugin
