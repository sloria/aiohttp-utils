# -*- coding: utf-8 -*-
import pytest

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
            return web.Response(body=b'Got it', content_type='text/plain')

        async def post(self, request):
            return web.Response(body=b'Posted it', content_type='text/plain')

    class MyResource2:

        def get(self, request):
            return web.Response()

        def post(self, request):
            return web.Response()

    class ChildResource(MyResource):
        pass

    app.router.add_resource_object('/my', MyResource())
    app.router.add_resource_object('/my2', MyResource2(), names={'get': 'my_resource2_get'})
    app.router.add_resource_object('/child', ChildResource(), methods=('get', ))


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

        assert str(app.router['MyResource:get'].url_for()) == '/my'
        assert str(app.router['MyResource:post'].url_for()) == '/my'

    def test_name_override(self, app):
        configure_app(app)
        assert str(app.router['my_resource2_get'].url_for()) == '/my2'
        assert str(app.router['MyResource2:post'].url_for()) == '/my2'

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

        assert str(app.router['index'].url_for()) == '/'
        assert str(app.router['list_projects'].url_for()) == '/projects/'
        assert str(app.router['create_projects'].url_for()) == '/projects'

    def test_add_route_context_passing_handler_functions(self, app):
        with add_route_context(app) as route:
            route('GET', '/', views.index)
            route('GET', '/projects/', views.list_projects)
            route('POST', '/projects', views.create_projects)

        assert str(app.router['index'].url_for()) == '/'
        assert str(app.router['list_projects'].url_for()) == '/projects/'
        assert str(app.router['create_projects'].url_for()) == '/projects'

    def test_passing_module_and_handlers_as_strings(self, app):
        with add_route_context(app, module='tests.views') as route:
            route('GET', '/', 'index')
            route('GET', '/projects/', 'list_projects')
            route('POST', '/projects', 'create_projects')

        assert str(app.router['index'].url_for()) == '/'
        assert str(app.router['list_projects'].url_for()) == '/projects/'
        assert str(app.router['create_projects'].url_for()) == '/projects'

    def test_route_name_override(self, app):
        with add_route_context(app) as route:
            route('GET', '/', views.index, name='home')

        assert str(app.router['home'].url_for()) == '/'

    def test_add_route_raises_error_if_handler_not_found(self, app):
        with add_route_context(app, views) as route:
            with pytest.raises(AttributeError):
                route('GET', '/', 'notfound')

    def test_add_route_context_with_url_prefix(self, app):
        with add_route_context(app, views, url_prefix='/api/') as route:
            route('GET', '/', 'index')
            route('GET', '/projects/', 'list_projects')

        assert str(app.router['index'].url_for()) == '/api/'
        assert str(app.router['list_projects'].url_for()) == '/api/projects/'

    def test_add_route_context_with_name_prefix(self, app):
        with add_route_context(app, views, name_prefix='api') as route:
            route('GET', '/', 'index')
            route('GET', '/projects/', 'list_projects')

        assert str(app.router['api.index'].url_for()) == '/'
        assert str(app.router['api.list_projects'].url_for()) == '/projects/'


class TestAddResourceContext:

    def test_add_resource_context_basic(self, app):
        with add_resource_context(app, views) as route:
            route('/articles/', 'ArticleResource')
            route('/articles/{pk}', 'ArticleList')

        assert str(app.router['ArticleResource:get'].url_for()) == '/articles/'
        assert str(app.router['ArticleResource:post'].url_for()) == '/articles/'
        assert str(app.router['ArticleList:post'].url_for(
            pk='42')) == '/articles/42'

    def test_add_resource_context_passing_classes(self, app):
        with add_resource_context(app) as route:
            route('/articles/', views.ArticleResource())
            route('/articles/{pk}', views.ArticleList())

        assert str(app.router['ArticleResource:get'].url_for()) == '/articles/'
        assert str(app.router['ArticleResource:post'].url_for()) == '/articles/'

    def test_passing_module_and_resources_as_strings(self, app):
        with add_resource_context(app, module='tests.views') as route:
            route('/articles/', 'ArticleResource')
            route('/articles/{pk}', 'ArticleList')

        assert str(app.router['ArticleResource:get'].url_for()) == '/articles/'
        assert str(app.router['ArticleResource:post'].url_for()) == '/articles/'
        assert str(app.router['ArticleList:post'].url_for(
            pk='42')) == '/articles/42'

    def test_make_resource_override(self, app):
        db = {}
        with add_resource_context(app, module='tests.views') as route:
            route('/authors/', 'AuthorList', make_resource=lambda cls: cls(db=db))

    def test_make_resource_override_on_context_manager(self, app):
        db = {}
        with add_resource_context(app, module='tests.views',
                                  make_resource=lambda cls: cls(db=db)) as route:
            route('/authors/', 'AuthorList')

    def test_add_resource_context_passing_classes_with_prefix(self, app):
        with add_resource_context(app, name_prefix='articles') as route:
            route('/articles/', views.ArticleResource())
            route('/articles/{pk}', views.ArticleList())

        assert str(app.router['articles.ArticleResource:get'].url_for()) == '/articles/'
        assert str(app.router['articles.ArticleResource:post'].url_for()) == '/articles/'
        assert str(app.router['articles.ArticleList:post'].url_for(
            pk='42')) == '/articles/42'  # noqa

    def test_add_resource_context_with_url_prefix(self, app):
        with add_resource_context(app, views, url_prefix='/api/') as route:
            route('/articles/', 'ArticleResource')

        assert str(app.router['ArticleResource:get'].url_for()) == '/api/articles/'
        assert str(app.router['ArticleResource:post'].url_for()) == '/api/articles/'

    def test_add_resource_context_with_name_prefix(self, app):
        with add_resource_context(app, views, name_prefix='api') as route:
            route('/articles/', 'ArticleResource')

        assert str(app.router['api.ArticleResource:get'].url_for()) == '/articles/'
        assert str(app.router['api.ArticleResource:post'].url_for()) == '/articles/'

    def test_add_resource_context_with_name_prefix_and_override(self, app):
        with add_resource_context(app, views, name_prefix='api') as route:
            route('/articles/', 'ArticleResource', names={'get': 'list_articles'})

        assert str(app.router['api.list_articles'].url_for()) == '/articles/'
        assert str(app.router['api.ArticleResource:post'].url_for()) == '/articles/'
