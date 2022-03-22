import os

from ..common import FRAMEWORK, Framework


if os.environ.get("ASWA_DOCS", False):
    from .webargs_plugin import WebargsPlugin
elif FRAMEWORK == Framework.FLASK:
    from .flask_plugin import FlaskWebargsPlugin as WebargsPlugin
elif FRAMEWORK == Framework.DJANGO:
    from .django_plugin import DjangoWebargsPlugin as WebargsPlugin
elif FRAMEWORK == Framework.TORNADO:
    from .tornado_plugin import TornadoWebargsPlugin as WebargsPlugin
elif FRAMEWORK == Framework.BOTTLE:
    from .bottle_plugin import BottleWebargsPlugin as WebargsPlugin
