"""Routing utilities."""
from collections.abc import Mapping, Iterable
from contextlib import contextmanager

from aiohttp import web

class ResourceRouter(web.UrlDispatcher):
    """Router with an :meth:`add_resource` method for registering method-based handlers,
    a.k.a "resources". Includes all the methods `aiohttp.web.UrlDispatcher` with the addition
    of `add_resource`.

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

def make_path(path, url_prefix=None):
    return ('/'.join((url_prefix.rstrip('/'), path.lstrip('/')))
            if url_prefix
            else path)

@contextmanager
def add_route_context(app, module=None, url_prefix=None, name_prefix=None):
    """Context manager which yields a function for adding multiple routes from a given module.

    Example:
    ::
        # myapp/articles/views.py
        async def list_articles(request):
            return web.Response(b'article list...')

        async def create_article(request):
            return web.Response(b'created article...')

    ::

        # myapp/app.py
        from myapp.articles import views

        with add_route_context(app, url_prefix='/api/', name_prefix='articles') as route:
            route('GET', '/articles/', views.list_articles)
            route('POST', '/articles/', views.create_article)

        app.router['articles.list_articles'].url()  # /api/articles/
    """
    def add_route(method, path, handler, name=None):
        """
        :param str method: HTTP method.
        :param str path: Path for the route.
        :param handler: A handler function or a name of a handler function contained
            in `module`.
        :param str name: Name for the route. If `None`, defaults to the handler's
            function name.
        """
        if isinstance(handler, (str, bytes)):
            if not module:
                raise ValueError(
                    'Must pass module to add_route_context if passing handler name strings.'
                )
            name = name or handler
            handler = getattr(module, handler)
        else:
            name = name or handler.__name__
        path = make_path(path, url_prefix)
        name = '.'.join((name_prefix, name)) if name_prefix else name
        return app.router.add_route(method, path, handler, name=name)
    yield add_route


def get_supported_method_names(resource):
    return [
        method_name for method_name in ResourceRouter.HTTP_METHOD_NAMES
        if hasattr(resource, method_name)
    ]

@contextmanager
def add_resource_context(app, module=None, url_prefix=None, name_prefix=None):
    """Context manager which yields a function for adding multiple resources from a given module
    to an app using `ResourceRouter <aiohttp_utils.routing.ResourceRouter>`.

    Example:
    ::

        # myapp/articles/views.py
        class ArticleList:
            async def get(self, request):
                return web.Response(b'article list...')

        class ArticleDetail:
            async def get(self, request):
                return web.Response(b'article detail...')

    ::

        # myapp/app.py
        from myapp.articles import views

        with add_resource_context(app, url_prefix='/api/') as route:
            route('/articles/', views.ArticleList())
            route('/articles/{pk}', views.ArticleDetail())

        app.router['ArticleList:get'].url()  # /api/articles/
        app.router['ArticleDetail:get'].url(parts={'pk': 42})  # /api/articles/42
    """

    def get_base_name(resource, method_name, names):
        return names.get(method_name,
                         app.router.get_default_handler_name(resource, method_name))

    def add_route(
        path: str,
        resource,
        names: Mapping=None,
        make_resource=lambda cls: cls()
    ):
        names = names or {}
        if isinstance(resource, (str, bytes)):
            if not module:
                raise ValueError(
                    'Must pass module to add_route_context if passing resource name strings.'
                )
            resource_cls = getattr(module, resource)
            resource = make_resource(resource_cls)
        path = make_path(path, url_prefix)
        if name_prefix:
            supported_method_names = get_supported_method_names(resource)
            names = {
                method_name: '.'.join(
                    (name_prefix, get_base_name(resource, method_name, names=names))
                )
                for method_name in supported_method_names
            }
        return app.router.add_resource(path, resource, names=names)
    yield add_route
