"""Custom router classes."""
from collections.abc import Mapping, Iterable

from aiohttp import web

class ResourceRouter(web.UrlDispatcher):
    """Router with an :meth:`add_resource` method for registering "resource classes". A resource
    class is simply a class with methods that are HTTP method names.

    Includes all the same methods as `aiohttp.web.UrlDispatcher`.

    Example: ::

        from aiohttp import web
        from aiohttp_utils.routing import ResourceRouter

        app = web.Application(router=ResourceRouter())

        class IndexResource:

            async def get(self, request):
                return web.Response(body=b'Got it', content_type='text/plain')

            async def post(self, request):
                return web.Response(body=b'Posted it', content_type='text/plain')


        app.router.add_resource('/', IndexResource())

        # Normal function-based handlers still work
        async def handler(request):
            return web.Response()

        app.router.add_route('GET', '/simple', handler)

    By default, handler names will be registered with the name ``<ClassName>:<method>``. ::

        app.router['IndexResource:post'].url() == '/'

    You can override the default names by passing a ``names`` dict to `add_resource`. ::

        app.router.add_resource('/', IndexResource(), names={'get': 'index_get'})
        app.router['index_get'].url() == '/'
    """

    HTTP_METHOD_NAMES = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def get_default_handler_name(self, resource, method_name: str):
        return '{resource.__class__.__name__}:{method_name}'.format(**locals())

    def add_resource(self, path: str, resource, methods: Iterable=tuple(), names: Mapping=None):
        """Add routes by an resource instance's methods.

        :param str path: route path. Should be started with slash (``'/'``).
        :param resource: A "resource" instance. May be an instance of a plain object.
        :param iterable methods: Methods (strings) to register.
        :param dict names: Dictionary of ``name`` overrides.
        """
        names = names or {}
        if methods:
            method_names = methods
        else:
            method_names = self.HTTP_METHOD_NAMES
        for method_name in method_names:
            handler = getattr(resource, method_name, None)
            if handler:
                name = names.get(method_name, self.get_default_handler_name(resource, method_name))
                self.add_route(method_name.upper(), path, handler, name=name)
