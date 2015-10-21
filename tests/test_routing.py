# -*- coding: utf-8 -*-
import pytest
import asyncio

from aiohttp import web

from aiohttp_utils.routing import ResourceRouter

@pytest.fixture()
def app(loop):
    return web.Application(router=ResourceRouter())

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
