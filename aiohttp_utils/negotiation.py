"""Content negotiation API.

.. code-block:: python

    import asyncio

    from aiohttp import web
    from aiohttp_utils import negotiation, Response

    app = web.Application()

    async def handler(request):
        return Response({'message': "Let's negotiate"})


    async def init(loop, port=5000):
        app = web.Application(loop=loop)
        app.router.add_route('GET', '/', handler)

        negotiation.setup(app)

        srv = await loop.create_server(
            app.make_handler(), '0.0.0.0', 5000)
        return srv

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

.. note::

    Handlers must return `aiohttp_utils.negotiation.Response` (which can be imported from
    the top-level `aiohttp_utils` module) for data
    to be properly negotiated. `aiohttp_utils.negotiation.Response` is the
    same as `aiohttp.web.Response`, except that its first
    argument is `data`, which is the data to be negotiated.


The middleware will render responses to JSON by default.

Example with httpie:
::

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

Customizing negotiation
=======================

Renderers are just callables that receive a `request <aiohttp.web.Request>`
data and return the rendered representation of that data.

Example:

.. code-block:: python

    def render_text(request, data):
        return data.encode('utf-8')

    # OR, if you need to parametrize your renderer, you can use a class

    class TextRenderer:
        def __init__(self, charset):
            self.charset = charset

        def __call__(self, request, data):
            return data.encode(self.charset)

    render_text_utf8 = TextRenderer('utf-8')
    render_text_utf16 = TextRenderer('utf-16')

You can then pass your renderers to `setup <aiohttp_utils.negotiation.setup>`
with a corresponding mediatype.

.. note::

    We use an `OrderedDict <collections.OrderedDict>` because priority is given to
    the first specified renderer when the client passes an unsupported media type.

.. code-block:: python

    from aiohttp_utils import negotiation

    negotiation.setup(app, {
        'RENDERERS': OrderedDict([
            ('text/plain', render_text),
            ('application/json', negotiation.render_json),
        ])
    })
"""
from collections import OrderedDict
import asyncio
import json as pyjson

from aiohttp import web
import mimeparse

from .constants import APP_KEY


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


##### Negotiation strategies #####

def select_renderer(request: web.Request, renderers: OrderedDict, force=True):
    """
    Given a request and a list of renderers, return a two-tuple of:
    (media type, render callable).
    """
    header = request.headers.get('ACCEPT', '*/*')
    best_match = mimeparse.best_match(renderers.keys(), header)
    if not best_match or best_match not in renderers:
        if force:
            return tuple(renderers.items())[0]
        else:
            raise web.HTTPNotAcceptable
    return best_match, renderers[best_match]

###### Renderers ######

# Use a class so that json module is easily override-able
class JSONRenderer:
    """Callable object which renders to JSON."""
    json_module = pyjson

    def __call__(self, request, data):
        return self.json_module.dumps(data).encode('utf-8')

#: Render data to JSON.
render_json = JSONRenderer()

##### Main API #####

#: Default configuration
DEFAULTS = {
    # Function that selects a renderer
    'NEGOTIATOR': select_renderer,
    'RENDERERS': OrderedDict([
        ('application/json', render_json),
    ]),
    # If True, use the first renderer in RENDERERS if the
    # client sends an unsupported media type
    'FORCE_NEGOTIATION': True,
}


def negotiation_middleware(
    renderers=DEFAULTS['RENDERERS'],
    negotiator=DEFAULTS['NEGOTIATOR'],
    force_negotiation=True
):
    """Middleware which selects a renderer for a given request then renders
    a handler's data to a `aiohttp.web.Response`.
    """
    @asyncio.coroutine
    def factory(app, handler):

        @asyncio.coroutine
        def middleware(request):
            content_type, renderer = negotiator(
                request=request,
                renderers=renderers,
                force=force_negotiation
            )
            response = yield from handler(request)

            if getattr(response, 'data', None):
                # Render data with the selected renderer
                if asyncio.iscoroutinefunction(renderer):
                    render_result = yield from renderer(request, response.data)
                else:
                    render_result = renderer(request, response.data)
            else:
                render_result = response

            if isinstance(render_result, web.Response):
                return render_result

            if getattr(response, 'data', None):
                response.body = render_result
                response.content_type = content_type

            return response
        return middleware
    return factory


def setup(app: web.Application, overrides: dict=None):
    """Set up the negotiation middleware. Saves configuration to
    app['aiohttp_utils'].

    :param aiohttp.web.Application: Application to set up.
    :param dict overrides: Configuration overrides.
    """
    overrides = overrides or {}
    config = app.get(APP_KEY, {})
    config.update(DEFAULTS)
    config.update(overrides)
    app[APP_KEY] = config

    middleware = negotiation_middleware(
        renderers=config['RENDERERS'],
        negotiator=config['NEGOTIATOR'],
        force_negotiation=config['FORCE_NEGOTIATION']
    )
    app.middlewares.append(middleware)
    return app
