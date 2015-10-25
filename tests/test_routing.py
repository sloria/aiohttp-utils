# -*- coding: utf-8 -*-
import pytest
import asyncio

from aiohttp import web

from aiohttp_utils.routing import ResourceRouter, add_route_context, add_resource_context
from tests import views

@pytest.fixture()
def app(loop):
    return web.Application(loop=loop, router=ResourceRouter())

@pytest.fixture()
def client(create_client, app):
    return create_client(app)

def configure_app(app):

    class MyResource:

        def get(self, request):
            return web.Response(body=b'Got it', content_type='text/plain; charset=utf-8')

        @asyncio.coroutine
        def post(self, request):
            return web.Response(body=b'Posted it', content_type='text/plain; charset=utf-8')

    class MyResource2:

        def get(self, request):
            return web.Response()

        def post(self, request):
            return web.Response()

    class ChildResource(MyResource):
        pass

    app.router.add_resource('/my', MyResource())
    app.router.add_resource('/my2', MyResource2(), names={'get': 'my_resource2_get'})
    app.router.add_resource('/child', ChildResource(), methods=('get', ))


class TestResourceRouter:

    def test_registers_handlers(self, app, client):
        configure_app(app)

        res = client.get('/my')
        assert res.status_code == 200
        assert res.text == 'Got it'

        res = client.post('/my')
        assert res.status_code == 200
        assert res.text == 'Posted it'

    def test_default_names(self, app):
        configure_app(app)

        assert app.router['MyResource:get'].url() == '/my'
        assert app.router['MyResource:post'].url() == '/my'

    def test_name_override(self, app):
        configure_app(app)
        assert app.router['my_resource2_get'].url() == '/my2'
        assert app.router['MyResource2:post'].url() == '/my2'

    def test_methods_param(self, app, client):
        configure_app(app)

        with pytest.raises(KeyError):
            app.router['ChildResource:post']

        res = client.post('/child', expect_errors=True)
        assert res.status_code == 405


class TestAddRouteContext:

    def test_add_route_context_basic(self, app):
        with add_route_context(app, views) as route:
            route('GET', '/', 'index')
            route('GET', '/projects/', 'list_projects')
            route('POST', '/projects', 'create_projects')

        assert app.router['index'].url() == '/'
        assert app.router['list_projects'].url() == '/projects/'
        assert app.router['create_projects'].url() == '/projects'

    def test_add_route_context_passing_handler_functions(self, app):
        with add_route_context(app) as route:
            route('GET', '/', views.index)
            route('GET', '/projects/', views.list_projects)
            route('POST', '/projects', views.create_projects)

        assert app.router['index'].url() == '/'
        assert app.router['list_projects'].url() == '/projects/'
        assert app.router['create_projects'].url() == '/projects'

    def test_add_route_raises_error_if_handler_not_found(self, app):
        with add_route_context(app, views) as route:
            with pytest.raises(AttributeError):
                route('GET', '/', 'notfound')

    def test_add_route_context_with_url_prefix(self, app):
        with add_route_context(app, views, url_prefix='/api/') as route:
            route('GET', '/', 'index')
            route('GET', '/projects/', 'list_projects')

        assert app.router['index'].url() == '/api/'
        assert app.router['list_projects'].url() == '/api/projects/'

    def test_add_route_context_with_name_prefix(self, app):
        with add_route_context(app, views, name_prefix='api') as route:
            route('GET', '/', 'index')
            route('GET', '/projects/', 'list_projects')

        assert app.router['api.index'].url() == '/'
        assert app.router['api.list_projects'].url() == '/projects/'

class TestAddResourceContext:

    def test_add_resource_context_basic(self, app):
        with add_resource_context(app, views) as route:
            route('/articles/', 'ArticleResource')
            route('/articles/{pk}', 'ArticleList')

        assert app.router['ArticleResource:get'].url() == '/articles/'
        assert app.router['ArticleResource:post'].url() == '/articles/'
        assert app.router['ArticleList:post'].url(parts={'pk': 42}) == '/articles/42'

    def test_add_resource_context_passing_classes(self, app):
        with add_resource_context(app) as route:
            route('/articles/', views.ArticleResource())
            route('/articles/{pk}', views.ArticleList())

        assert app.router['ArticleResource:get'].url() == '/articles/'
        assert app.router['ArticleResource:post'].url() == '/articles/'
        assert app.router['ArticleList:post'].url(parts={'pk': 42}) == '/articles/42'

    def test_add_resource_context_passing_classes_with_prefix(self, app):
        with add_resource_context(app, name_prefix='articles') as route:
            route('/articles/', views.ArticleResource())
            route('/articles/{pk}', views.ArticleList())

        assert app.router['articles.ArticleResource:get'].url() == '/articles/'
        assert app.router['articles.ArticleResource:post'].url() == '/articles/'
        assert app.router['articles.ArticleList:post'].url(parts={'pk': 42}) == '/articles/42'

    def test_add_resource_context_with_url_prefix(self, app):
        with add_resource_context(app, views, url_prefix='/api/') as route:
            route('/articles/', 'ArticleResource')

        assert app.router['ArticleResource:get'].url() == '/api/articles/'
        assert app.router['ArticleResource:post'].url() == '/api/articles/'

    def test_add_resource_context_with_name_prefix(self, app):
        with add_resource_context(app, views, name_prefix='api') as route:
            route('/articles/', 'ArticleResource')

        assert app.router['api.ArticleResource:get'].url() == '/articles/'
        assert app.router['api.ArticleResource:post'].url() == '/articles/'

    def test_add_resource_context_with_name_prefix_and_override(self, app):
        with add_resource_context(app, views, name_prefix='api') as route:
            route('/articles/', 'ArticleResource', names={'get': 'list_articles'})

        assert app.router['api.list_articles'].url() == '/articles/'
        assert app.router['api.ArticleResource:post'].url() == '/articles/'
