"""Middleware for normalizing paths.

- Appends slashes missing trailing slashes (/path -> /path/)
- Removes double-slashes (/path// -> /path/)

.. code-block:: python

    from aiohttp_utils import path_norm

    path_norm.setup(app, {
        'APPEND_SLASHES': True,
        'MERGE_SLASHES': True
    })
"""
import asyncio

from aiohttp import web, hdrs
from aiohttp.web_urldispatcher import (
    SystemRoute, UrlMappingMatchInfo, _MethodNotAllowedMatchInfo, _NotFoundMatchInfo
)

from .constants import APP_KEY

DEFAULTS = {
    # Whether to append trailing slashes to URLs.
    'APPEND_SLASH': True,
    'MERGE_SLASHES': True,
}

@asyncio.coroutine
def resolve2(router, method, path):
    allowed_methods = set()

    for route in router._urls:
        match_dict = route.match(path)
        if match_dict is None:
            continue

        route_method = route.method
        if route_method == method or route_method == hdrs.METH_ANY:
            return UrlMappingMatchInfo(match_dict, route)

        allowed_methods.add(route_method)
    else:
        if allowed_methods:
            return _MethodNotAllowedMatchInfo(method, allowed_methods)
        else:
            return _NotFoundMatchInfo()

class NormalizePathMiddleware:
    """Middleware for path normalization

    :param bool append_slash: Whether to append trailing slashes to URLs.
    :param bool merge_slashes: Whether to normalize double-slashes to single-slashes,
        e.g. path//to -> path/to
    """
    redirect_class = web.HTTPMovedPermanently

    def __init__(
        self,
        append_slash=DEFAULTS['APPEND_SLASH'],
        merge_slashes=DEFAULTS['MERGE_SLASHES']
    ):
        self.append_slash = append_slash
        self.merge_slashes = merge_slashes

    @asyncio.coroutine
    def __call__(self, app, handler):
        @asyncio.coroutine
        def middleware(request):
            try:
                return (yield from handler(request))
            except web.HTTPNotFound as exc:
                if request.method in ('POST', 'PUT', 'PATCH'):
                    # should check for empty request.content
                    # actually even GET may have a BODY
                    raise exc

                router = request.app.router
                new_path = None
                if self.merge_slashes:
                    if '//' in request.path:
                        path = request.path
                        while True:
                            path = path.replace('//', '/')
                            if '//' not in path:
                                break

                        match_info = yield from resolve2(router, request.method, path)
                        if not isinstance(match_info.route, SystemRoute):
                            new_path = path
                if self.append_slash:
                    if not request.path.endswith('/'):
                        path = request.path + '/'
                        match_info = yield from resolve2(router, request.method, path)
                        if not isinstance(match_info.route, SystemRoute):
                            new_path = path

                if new_path is not None:
                    if request.query_string:
                        new_path += '?' + request.query_string
                    return self.redirect_class(new_path)
                else:
                    raise exc
        return middleware

normalize_path_middleware = NormalizePathMiddleware

def setup(app: web.Application, overrides: dict=None):
    """Set up the path normalization middleware. Saves configuration to
    app['aiohttp_utils'].

    :param aiohttp.web.Application: Application to set up.
    :param dict overrides: Configuration overrides.
    """
    overrides = overrides or {}
    config = app.get(APP_KEY, {})
    config.update(DEFAULTS)
    config.update(overrides)
    app[APP_KEY] = config

    middleware = normalize_path_middleware(
        append_slash=config['APPEND_SLASH'],
        merge_slashes=config['MERGE_SLASHES'],
    )
    app.middlewares.append(middleware)
    return app
