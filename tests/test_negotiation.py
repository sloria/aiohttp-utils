import pytest
import asyncio
from collections import OrderedDict

from aiohttp import web

from aiohttp_utils import negotiation, CONFIG_KEY
from aiohttp_utils.negotiation import Response


@pytest.fixture()
def app(loop):
    return web.Application(loop=loop)


@pytest.fixture()
def client(create_client, app):
    return create_client(app)


def add_routes(app):
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


def configure_app(app, overrides=None, setup=False):
    overrides = overrides or {}
    add_routes(app)

    if setup:
        negotiation.setup(app, **overrides)
    else:
        middleware = negotiation.negotiation_middleware(**overrides)
        app.middlewares.append(middleware)


@pytest.mark.parametrize('setup', [True, False])
def test_renders_to_json_by_default(app, client, setup):
    configure_app(app, overrides=None, setup=setup)
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


def dummy_renderer(request, data):
    return web.Response(
        body='<p>{}</p>'.format(data['message']).encode('utf-8'),
        content_type='text/html'
    )


def test_renderer_override(app, client):
    configure_app(app, overrides={
        'renderers': OrderedDict([
            ('text/html', dummy_renderer),
        ])
    }, setup=True)

    res = client.get('/hello')
    assert res.content_type == 'text/html'
    assert res.body == b'<p>Hello world</p>'


def test_renderer_override_multiple_classes(app, client):
    configure_app(app, overrides={
        'renderers': OrderedDict([
            ('text/html', dummy_renderer),
            ('application/json', negotiation.render_json),
            ('application/vnd.api+json', negotiation.render_json),
        ])
    }, setup=True)

    res = client.get('/hello', headers={'Accept': 'application/json'})
    assert res.content_type == 'application/json'
    assert res.json == {'message': 'Hello world'}

    res = client.get('/hello', headers={'Accept': 'application/vnd.api+json'})
    assert res.content_type == 'application/vnd.api+json'
    assert res.json == {'message': 'Hello world'}

    res = client.get('/hello', headers={'Accept': 'text/html'})
    assert res.content_type == 'text/html'
    assert res.body == b'<p>Hello world</p>'


def test_renderer_override_force(app, client):
    configure_app(app, overrides={
        'force_negotiation': False,
    }, setup=True)

    res = client.get('/hello', headers={'Accept': 'text/notsupported'}, expect_errors=True)
    assert res.status_code == 406


def test_nonordered_dict_of_renderers(app, client):
    configure_app(app, overrides={
        'renderers': {
            'application/json': negotiation.render_json
        }
    }, setup=True)

    res = client.get('/hello', headers={'Accept': 'text/notsupported'})
    assert res.content_type == 'application/json'


def test_configuration_through_app_key(app, client):
    add_routes(app)
    app[CONFIG_KEY] = {
        'RENDERERS': OrderedDict([
            ('text/html', dummy_renderer),
        ])
    }
    negotiation.setup(app)
    res = client.get('/hello')
    assert res.content_type == 'text/html'
    assert res.body == b'<p>Hello world</p>'
