"""Content negotiation API. Includes
`ContentNegotation <aiohttp_utils.negotiation.BaseContentNegotiation>` classes,
which are responsible for selecting an appropriate
`Renderer <aiohttp_utils.negotiation.BaseRenderer>` for a given request.
::

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


Most of the implementation for the ContentNegotation and Renderer classes are
attributed to Django Rest Framework. See NOTICE for license information.
"""
import asyncio
import json as pyjson

from aiohttp import web

from .constants import APP_KEY
from .mediatypes import media_type_matches, _MediaType, HTTP_HEADER_ENCODING


class Response(web.Response):
    """Same as `aiohttp.web.Response`, except that the constructor takes a `data` argument,
    which is the data to be negotiated by the
    `negotiation_middleware <aiohttp_utils.negotiation.negotiation_middleware`.
    """

    def __init__(self, data=None, *args, **kwargs):
        if data is not None and kwargs.get('body', None):
            raise ValueError('data and body are not allowed together.')
        if data is not None and kwargs.get('text', None):
            raise ValueError('data and text are not allowed together.')
        self.data = data
        super().__init__(*args, **kwargs)


##### ContentNegotiation classes #####

class BaseContentNegotiation(object):
    """Base content negotiation class. Must implement `select_renderer`."""

    def select_renderer(self, request, renderers):
        raise NotImplementedError('.select_renderer() must be implemented')

class DefaultContentNegotiation(BaseContentNegotiation):
    """Default content negotation class."""

    force = True

    def select_renderer(self, request, renderers):
        """
        Given a request and a list of renderers, return a two-tuple of:
        (renderer, media type).
        """
        accepts = get_accept_list(request)

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is we're looping over len(accept_list) * len(self.renderers)
        for media_type_set in accepts:
            for renderer in renderers:
                for media_type in media_type_set:
                    if media_type_matches(renderer.media_type, media_type):
                        # Return the most specific media type as accepted.
                        media_type_wrapper = _MediaType(media_type)
                        if (
                            _MediaType(renderer.media_type).precedence >
                            media_type_wrapper.precedence
                        ):
                            # Eg client requests '*/*'
                            # Accepted media type is 'application/json'
                            full_media_type = ';'.join(
                                (renderer.media_type,) +
                                tuple('{0}={1}'.format(
                                    key, value.decode(HTTP_HEADER_ENCODING))
                                    for key, value in media_type_wrapper.params.items()))
                            return renderer, full_media_type
                        else:
                            # Eg client requests 'application/json; indent=8'
                            # Accepted media type is 'application/json; indent=8'
                            return renderer, media_type
        if self.force:
            return (renderers[0], renderers[0].media_type)
        else:
            raise web.HTTPNotAcceptable()

def get_accept_list(request):
    """
    Given the incoming request, return a tokenised list of media
    type strings.

    Allows URL style accept override.  eg. "?accept=application/json"
    """
    header = request.headers.get('HTTP_ACCEPT', '*/*')
    header = request.GET.get('accept', header)
    return [token.strip() for token in header.split(',')]

###### Renderers ######

class BaseRenderer(object):
    """Base renderer class. Must implement `render`."""
    media_type = None

    def render(self, data):
        raise NotImplementedError('Renderer class requires .render() to be implemented')


class JSONRenderer(BaseRenderer):
    """Renders to JSON."""

    media_type = 'application/json'

    json_module = pyjson

    def render(self, data):
        return self.json_module.dumps(data).encode('utf-8')


##### Main API #####

#: Default configuration
DEFAULTS = {
    'NEGOTIATION_CLASS': DefaultContentNegotiation,
    'RENDERER_CLASSES': [
        JSONRenderer,
    ]
}


def get_config(app, key):
    return app[APP_KEY].get(key, DEFAULTS[key])

@asyncio.coroutine
def negotiation_middleware(app, handler):
    """Middleware which selects a renderer for a given request then renders
    a handler's data to a `aiohttp.web.Response`.
    """
    negotiator = get_config(app, 'NEGOTIATION_CLASS')()
    renderers = get_config(app, 'RENDERER_CLASSES')

    @asyncio.coroutine
    def middleware(request):
        renderer_cls, content_type = negotiator.select_renderer(
            request=request,
            renderers=renderers
        )
        renderer = renderer_cls()

        response = yield from handler(request)
        if response.data:
            # Render data with the selected renderer
            if asyncio.iscoroutinefunction(renderer.render):
                response.body = yield from renderer.render(response.data)
            else:
                response.body = renderer.render(response.data)
            response.content_type = content_type

        return response
    return middleware


def setup(app: web.Application, overrides: dict=None):
    """Set up the negotiation middleware.

    :param aiohttp.web.Application: Application to set up.
    :param dict overrides: Configuration overrides.
    """
    overrides = overrides or {}
    config = app.get(APP_KEY, {})
    config.update(DEFAULTS)
    config.update(overrides)
    app[APP_KEY] = config
    app.middlewares.append(negotiation_middleware)
    return app
