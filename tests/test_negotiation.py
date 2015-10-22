import pytest
import asyncio

from aiohttp import web

from aiohttp_utils import negotiation
from aiohttp_utils.negotiation import Response


@pytest.fixture()
def app(loop):
    return web.Application(loop=loop)

@pytest.fixture()
def client(create_client, app):
    return create_client(app, lint=False)

def configure_app(app, overrides=None):

    def handler(request):
        return Response({'message': 'Hello world'})

    @asyncio.coroutine
    def coro_handler(request):
        return Response({'message': 'Hello coro'})

    @asyncio.coroutine
    def post_coro_handler(request):
        return Response({'message': 'Post coro'}, status=201)

    app.router.add_route('GET', '/hello', handler)
    app.router.add_route('GET', '/hellocoro', coro_handler)
    app.router.add_route('POST', '/postcoro', post_coro_handler)
    negotiation.setup(app, overrides=overrides)

def test_renders_to_json_by_default(app, client):
    configure_app(app, overrides=None)
    res = client.get('/hello')
    assert res.content_type == 'application/json'
    assert res.json == {'message': 'Hello world'}

    res = client.get('/hellocoro')
    assert res.content_type == 'application/json'
    assert res.json == {'message': 'Hello coro'}

    res = client.post('/postcoro')
    assert res.content_type == 'application/json'
    assert res.status_code == 201
    assert res.json == {'message': 'Post coro'}
