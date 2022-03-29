from enum import Enum
import os
import pkgutil

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


INSTALLED_MODULES = {module.name for module in pkgutil.iter_modules()}


def _determine_framework():
    active_framework = None
    for framework in Framework:
        if framework.value in INSTALLED_MODULES:
            if active_framework:
                raise MultipleFrameworkError("Multiple frameworks in the environment is not currently supported!")
            active_framework = framework

    if not active_framework:
        raise MissingFrameworkError("A supported web framework (e.g. Flask, Django, etc.) must be installed!")

    return active_framework


FRAMEWORK = _determine_framework() if not os.environ.get("ASWA_DOCS", False) else None
if not FRAMEWORK:
    parser = webargs.core.Parser()
    make_response = lambda: None
    get_request_body = make_response
    create_paths = get_request_body
    from ..plugin import WebargsPlugin
elif FRAMEWORK == Framework.FLASK:
    from .flask import make_response, get_request_body, create_paths, WebargsPlugin, parser
elif FRAMEWORK == Framework.DJANGO:
    from .django import make_response, get_request_body, create_paths, WebargsPlugin, parser
elif FRAMEWORK == Framework.TORNADO:
    from .tornado import make_response, get_request_body, create_paths, WebargsPlugin, parser
elif FRAMEWORK == Framework.BOTTLE:
    from .bottle import make_response, get_request_body, create_paths, WebargsPlugin, parser
