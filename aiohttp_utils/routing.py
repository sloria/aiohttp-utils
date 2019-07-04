"""Routing utilities."""
from collections.abc import Mapping
from contextlib import contextmanager
import importlib

from aiohttp import web

__all__ = (
    'ResourceRouter',
    'add_route_context',
    'add_resource_context',
)


class ResourceRouter(web.UrlDispatcher):
    """Router with an :meth:`add_resource` method for registering method-based handlers,
    a.k.a "resources". Includes all the methods `aiohttp.web.UrlDispatcher` with the addition
    of `add_resource`.

    Example:

    .. code-block:: python

        from aiohttp import web
        from aiohttp_utils.routing import ResourceRouter

        app = web.Application(router=ResourceRouter())

        class IndexResource:

            async def get(self, request):
                return web.Response(body=b'Got it', content_type='text/plain')

            async def post(self, request):
                return web.Response(body=b'Posted it', content_type='text/plain')


        app.router.add_resource_object('/', IndexResource())

        # Normal function-based handlers still work
        async def handler(request):
            return web.Response()

        app.router.add_route('GET', '/simple', handler)

    By default, handler names will be registered with the name ``<ClassName>:<method>``. ::

        app.router['IndexResource:post'].url() == '/'

    You can override the default names by passing a ``names`` dict to `add_resource`. ::

        app.router.add_resource_object('/', IndexResource(), names={'get': 'index_get'})
        app.router['index_get'].url() == '/'
    """

    HTTP_METHOD_NAMES = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def get_default_handler_name(self, resource, method_name: str):
        return '{resource.__class__.__name__}:{method_name}'.format(**locals())

    def add_resource_object(self, path: str, resource,
                            methods: tuple = tuple(), names: Mapping = None):
        """Add routes by an resource instance's methods.

        :param path: route path. Should be started with slash (``'/'``).
        :param resource: A "resource" instance. May be an instance of a plain object.
        :param methods: Methods (strings) to register.
        :param names: Dictionary of ``name`` overrides.
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
def add_route_context(
    app: web.Application, module=None,
        url_prefix: str = None, name_prefix: str = None):
    """Context manager which yields a function for adding multiple routes from a given module.

    Example:

    .. code-block:: python

        # myapp/articles/views.py
        async def list_articles(request):
            return web.Response(b'article list...')

        async def create_article(request):
            return web.Response(b'created article...')

    .. code-block:: python

        # myapp/app.py
        from myapp.articles import views

        with add_route_context(app, url_prefix='/api/', name_prefix='articles') as route:
            route('GET', '/articles/', views.list_articles)
            route('POST', '/articles/', views.create_article)

        app.router['articles.list_articles'].url()  # /api/articles/

    If you prefer, you can also pass module and handler names as strings.

    .. code-block:: python

        with add_route_context(app, module='myapp.articles.views',
                               url_prefix='/api/', name_prefix='articles') as route:
            route('GET', '/articles/', 'list_articles')
            route('POST', '/articles/', 'create_article')

    :param app: Application to add routes to.
    :param module: Import path to module (str) or module object which contains the handlers.
    :param url_prefix: Prefix to prepend to all route paths.
    :param name_prefix: Prefix to prepend to all route names.
    """
    if isinstance(module, (str, bytes)):
        module = importlib.import_module(module)

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
def add_resource_context(
        app: web.Application, module=None,
        url_prefix: str = None, name_prefix: str = None,
        make_resource=lambda cls: cls()):
    """Context manager which yields a function for adding multiple resources from a given module
    to an app using `ResourceRouter <aiohttp_utils.routing.ResourceRouter>`.

    Example:

    .. code-block:: python

        # myapp/articles/views.py
        class ArticleList:
            async def get(self, request):
                return web.Response(b'article list...')

        class ArticleDetail:
            async def get(self, request):
                return web.Response(b'article detail...')

    .. code-block:: python

        # myapp/app.py
        from myapp.articles import views

        with add_resource_context(app, url_prefix='/api/') as route:
            route('/articles/', views.ArticleList())
            route('/articles/{pk}', views.ArticleDetail())

        app.router['ArticleList:get'].url()  # /api/articles/
        app.router['ArticleDetail:get'].url(pk='42')  # /api/articles/42

    If you prefer, you can also pass module and class names as strings. ::

        with add_resource_context(app, module='myapp.articles.views',
                                  url_prefix='/api/') as route:
            route('/articles/', 'ArticleList')
            route('/articles/{pk}', 'ArticleDetail')

    .. note::
        If passing class names, the resource classes will be instantiated with no
        arguments. You can change this behavior by overriding ``make_resource``.

        .. code-block:: python

            # myapp/authors/views.py
            class AuthorList:
                def __init__(self, db):
                    self.db = db

                async def get(self, request):
                    # Fetch authors from self.db...

        .. code-block:: python

            # myapp/app.py
            from myapp.database import db

            with add_resource_context(app, module='myapp.authors.views',
                                    url_prefix='/api/',
                                    make_resource=lambda cls: cls(db=db)) as route:
                route('/authors/', 'AuthorList')

    :param app: Application to add routes to.
    :param resource: Import path to module (str) or module object
        which contains the resource classes.
    :param url_prefix: Prefix to prepend to all route paths.
    :param name_prefix: Prefix to prepend to all route names.
    :param make_resource: Function which receives a resource class and returns
        a resource instance.
    """
    assert isinstance(app.router, ResourceRouter), 'app must be using ResourceRouter'

    if isinstance(module, (str, bytes)):
        module = importlib.import_module(module)

    def get_base_name(resource, method_name, names):
        return names.get(method_name,
                         app.router.get_default_handler_name(resource, method_name))

    default_make_resource = make_resource

    def add_route(path: str, resource,
                  names: Mapping = None, make_resource=None):
        make_resource = make_resource or default_make_resource
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
        return app.router.add_resource_object(path, resource, names=names)
    yield add_route
