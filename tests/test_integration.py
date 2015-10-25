"""Tests for a kitchen-sink app."""
from asyncio import coroutine
import pytest

from aiohttp import web
from aiohttp_utils import Response, routing, negotiation, path_norm


@pytest.fixture()
def app(loop):
    app_ = web.Application(loop=loop, router=routing.ResourceRouter())
    configure_app(app_)
    return app_

@pytest.fixture()
def client(create_client, app):
    return create_client(app)

def configure_app(app):
    @coroutine
    def index(request):
        return Response('Welcome!')

    class HelloResource:

        @coroutine
        def get(self, request):
            return Response({
                'message': 'Welcome to the API!'
            })

    with routing.add_route_context(app) as route:
        route('GET', '/', index)

    with routing.add_resource_context(app, url_prefix='/api/') as route:
        route('/', HelloResource())

    negotiation.setup(app)
    path_norm.setup(app)


class TestIntegration:

    def test_index(self, client):
        res = client.get('/')
        assert res.status_code == 200
        assert res.json == 'Welcome!'

    def test_api_index(self, client):
        res = client.get('/api/')
        assert res.status_code == 200
        assert res.json == {'message': 'Welcome to the API!'}

    def test_api_index_append_slash(self, client):
        res = client.get('/api')
        assert res.status_code == 301
        res = res.follow()
        assert res.status_code == 200
        assert res.request.path == '/api/'

    def test_api_index_merge_slashes(self, client):
        res = client.get('/api//')
        assert res.status_code == 301
        res = res.follow()
        assert res.status_code == 200
        assert res.request.path == '/api/'

