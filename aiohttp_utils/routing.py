"""Routing utilities."""
from collections.abc import Mapping, Iterable
from contextlib import contextmanager

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

def make_url(url, url_prefix=None):
    return ('/'.join((url_prefix.rstrip('/'), url.lstrip('/')))
            if url_prefix
            else url)

@contextmanager
def add_route_context(app, module, url_prefix=None, name_prefix=None):
    """Context manager which yields a function for adding multiple routes from a given module.

    Example: ::

        from myapp.articles import views

        with add_route_context(app, views,
                               url_prefix='/api/', name_prefix='articles') as route:
            route('GET', '/articles/', 'list')
            route('POST', '/articles/', 'create')

        app.router['articles.list'].url()  # /api/articles/
    """
    def add_route(method, url, name):
        view = getattr(module, name)
        url = make_url(url, url_prefix)
        name = '.'.join((name_prefix, name)) if name_prefix else name
        return app.router.add_route(method, url, view, name=name)
    yield add_route


def get_supported_method_names(resource):
    return [
        method_name for method_name in ResourceRouter.HTTP_METHOD_NAMES
        if hasattr(resource, method_name)
    ]

@contextmanager
def add_resource_context(app, module, url_prefix=None, name_prefix=None):
    """Context manager which yields a function for adding multiple resources from a given module
    to an app using `ResourceRouter <aiohttp_utils.routing.ResourceRouter>`.

    Example: ::

        from myapp.articles import views

        with add_resource_context(app, views, url_prefix='/api/') as route:
            route('/articles/', 'ArticleList')
            route('/articles/{pk}', 'ArticleDetail')

        app.router['ArticleList:get'].url()  # /api/articles/
        app.router['ArticleDetail:get'].url(parts={'pk': 42})  # /api/articles/42
    """

    def get_base_name(resource, method_name, names):
        return names.get(method_name,
                         app.router.get_default_handler_name(resource, method_name))

    def add_route(
        url: str,
        resource_name: str,
        names: Mapping=None,
        make_resource=lambda cls: cls()
    ):
        names = names or {}
        resource_cls = getattr(module, resource_name)
        resource = make_resource(resource_cls)
        url = make_url(url, url_prefix)
        if name_prefix:
            supported_method_names = get_supported_method_names(resource)
            names = {
                method_name: '.'.join(
                    (name_prefix, get_base_name(resource, method_name, names=names))
                )
                for method_name in supported_method_names
            }
        return app.router.add_resource(url, resource, names=names)
    yield add_route
