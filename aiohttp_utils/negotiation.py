"""Content negotiation is the process of selecting an appropriate
representation (e.g. JSON, HTML, etc.) to return to a client based on the client's and/or server's
preferences.

If no custom renderers are supplied, this plugin will render responses to JSON.

.. code-block:: python

    import asyncio

    from aiohttp import web
    from aiohttp_utils import negotiation, Response

    async def handler(request):
        return Response({'message': "Let's negotiate"})

    app = web.Application()
    app.router.add_route('GET', '/', handler)

    # No configuration: renders to JSON by default
    negotiation.setup(app)

We can consume the app with httpie.
::

    $ pip install httpie
    $ http :5000/
    HTTP/1.1 200 OK
    CONNECTION: keep-alive
    CONTENT-LENGTH: 30
    CONTENT-TYPE: application/json
    DATE: Thu, 22 Oct 2015 06:03:39 GMT
    SERVER: Python/3.5 aiohttp/0.17.4

    {
        "message": "Let's negotiate"
    }

.. note::

    Handlers **MUST** return an `aiohttp_utils.negotiation.Response` (which can be imported from
    the top-level `aiohttp_utils` module) for data
    to be properly negotiated. `aiohttp_utils.negotiation.Response` is the
    same as `aiohttp.web.Response`, except that its first
    argument is `data`, the data to be negotiated.

Customizing negotiation
=======================

Renderers are just callables that receive a `request <aiohttp.web.Request>` and the
data to render.

Renderers can return either the rendered representation of the data
or a `Response <aiohttp.web.Response>`.

Example:

.. code-block:: python

    # A simple text renderer
    def render_text(request, data):
        return data.encode(request.charset)

    # OR, if you need to parametrize your renderer, you can use a class

    class TextRenderer:
        def __init__(self, charset):
            self.charset = charset

        def __call__(self, request, data):
            return data.encode(self.charset)

    render_text_utf8 = TextRenderer('utf-8')
    render_text_utf16 = TextRenderer('utf-16')

You can then pass your renderers to `setup <aiohttp_utils.negotiation.setup>`
with a corresponding media type.

.. code-block:: python

    from collections import OrderedDict
    from aiohttp_utils import negotiation

    negotiation.setup(app, renderers=OrderedDict([
        ('text/plain', render_text),
        ('application/json', negotiation.render_json),
    ]))

.. note::

    We use an `OrderedDict <collections.OrderedDict>` of renderers because priority is given to
    the first specified renderer when the client passes an unsupported media type.

By default, rendering the value returned by a handler according to content
negotiation will only occur if this value is considered True. If you want to
enforce the rendering whatever the boolean interpretation of the returned
value you can set the `force_rendering` flag:

.. code-block:: python

    from collections import OrderedDict
    from aiohttp_utils import negotiation

    negotiation.setup(app, force_rendering=True,
                      renderers=OrderedDict([
        ('application/json', negotiation.render_json),
    ]))

"""
from collections import OrderedDict
import asyncio
import json as pyjson

from aiohttp import web
import mimeparse

from .constants import CONFIG_KEY


__all__ = (
    'setup',
    'negotiation_middleware',
    'Response',
    'select_renderer',
    'JSONRenderer',
    'render_json'
)


class Response(web.Response):
    """Same as `aiohttp.web.Response`, except that the constructor takes a `data` argument,
    which is the data to be negotiated by the
    `negotiation_middleware <aiohttp_utils.negotiation.negotiation_middleware>`.
    """

    def __init__(self, data=None, *args, **kwargs):
        if data is not None and kwargs.get('body', None):
            raise ValueError('data and body are not allowed together.')
        if data is not None and kwargs.get('text', None):
            raise ValueError('data and text are not allowed together.')
        self.data = data
        super().__init__(*args, **kwargs)


# ##### Negotiation strategies #####

def select_renderer(request: web.Request, renderers: OrderedDict, force=True):
    """
    Given a request, a list of renderers, and the ``force`` configuration
    option, return a two-tuple of:
    (media type, render callable). Uses mimeparse to find the best media
    type match from the ACCEPT header.
    """
    header = request.headers.get('ACCEPT', '*/*')
    best_match = mimeparse.best_match(renderers.keys(), header)
    if not best_match or best_match not in renderers:
        if force:
            return tuple(renderers.items())[0]
        else:
            raise web.HTTPNotAcceptable
    return best_match, renderers[best_match]


# ###### Renderers ######

# Use a class so that json module is easily override-able
class JSONRenderer:
    """Callable object which renders to JSON."""
    json_module = pyjson

    def __repr__(self):
        return '<JSONRenderer()>'

    def __call__(self, request, data):
        return self.json_module.dumps(data).encode('utf-8')


#: Render data to JSON. Singleton `JSONRenderer`. This can be passed to the
#: ``RENDERERS`` configuration option, e.g. ``('application/json', render_json)``.
render_json = JSONRenderer()


# ##### Main API #####

#: Default configuration
DEFAULTS = {
    'NEGOTIATOR': select_renderer,
    'RENDERERS': OrderedDict([
        ('application/json', render_json),
    ]),
    'FORCE_NEGOTIATION': True,
    'FORCE_RENDERING': False,
}


def negotiation_middleware(
    renderers=DEFAULTS['RENDERERS'],
    negotiator=DEFAULTS['NEGOTIATOR'],
    force_negotiation=DEFAULTS['FORCE_NEGOTIATION'],
    force_rendering=DEFAULTS['FORCE_RENDERING']
):
    """Middleware which selects a renderer for a given request then renders
    a handler's data to a `aiohttp.web.Response`.
    """
    async def factory(app, handler):
        async def middleware(request):
            content_type, renderer = negotiator(
                request,
                renderers,
                force_negotiation,
            )
            request['selected_media_type'] = content_type
            response = await handler(request)

            data = getattr(response, 'data', None)
            if isinstance(response, Response) and (force_rendering or data):
                # Render data with the selected renderer
                if asyncio.iscoroutinefunction(renderer):
                    render_result = await renderer(request, data)
                else:
                    render_result = renderer(request, data)
            else:
                render_result = response
            if isinstance(render_result, web.Response):
                return render_result

            if force_rendering or data is not None:
                response.body = render_result
                response.content_type = content_type

            return response
        return middleware
    return factory


def setup(
        app: web.Application, *, negotiator: callable = DEFAULTS['NEGOTIATOR'],
        renderers: OrderedDict = DEFAULTS['RENDERERS'],
        force_negotiation: bool = DEFAULTS['FORCE_NEGOTIATION'],
        force_rendering: bool = DEFAULTS['FORCE_RENDERING']):
    """Set up the negotiation middleware. Reads configuration from
    ``app['AIOHTTP_UTILS']``.

    :param app: Application to set up.
    :param negotiator: Function that selects a renderer given a
        request, a dict of renderers, and a ``force`` parameter (whether to return
        a renderer even if the client passes an unsupported media type).
    :param renderers: Mapping of mediatypes to callable renderers.
    :param force_negotiation: Whether to return a renderer even if the
        client passes an unsupported media type).
    :param force_rendering: Whether to enforce rendering the result even if it
        considered False.
    """
    config = app.get(CONFIG_KEY, {})
    middleware = negotiation_middleware(
        renderers=config.get('RENDERERS', renderers),
        negotiator=config.get('NEGOTIATOR', negotiator),
        force_negotiation=config.get('FORCE_NEGOTIATION', force_negotiation),
        force_rendering=config.get('FORCE_RENDERING', force_rendering)
    )
    app.middlewares.append(middleware)
    return app
