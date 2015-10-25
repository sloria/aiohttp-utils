from aiohttp import web
import pytest

from aiohttp_utils import path_norm
from aiohttp_utils.path_norm import normalize_path_middleware

from .conftest import make_dummy_handler

@pytest.fixture()
def app(loop):
    return web.Application(loop=loop)

@pytest.fixture()
def client(create_client, app):
    return create_client(app)

def configure_app(app, overrides=None, setup=True):
    overrides = overrides or {}

    app.router.add_route('GET', '/', make_dummy_handler())
    app.router.add_route('GET', '/articles/', make_dummy_handler())

    # https://github.com/KeepSafe/aiohttp/pull/362/files#r30354438
    def handler1(req):
        raise web.HTTPNotFound()

    def handler2(req):
        pass

    app.router.add_route("GET", '/root/resource/', handler1)
    app.router.add_route("GET", "/root/resource/{tail:.*}", handler2)

    if setup:
        overrides = {key.upper(): value for key, value in overrides.items()}
        path_norm.setup(app, overrides)
    else:
        kwargs = {key.lower(): value for key, value in overrides.items()}
        middleware = normalize_path_middleware(**kwargs)
        app.middlewares.append(middleware)


class TestNormalizePathMiddleware:

    @pytest.mark.parametrize('setup', [True, False])
    def test_appends_slash_by_default(self, app, client, setup):
        configure_app(app, overrides=None, setup=setup)
        res = client.get('/articles/')
        assert res.status_code == 200

        res = client.get('/articles')
        assert res.status_code == 301
        res = res.follow()
        assert res.request.path_qs == '/articles/'

    @pytest.mark.parametrize('setup', [True, False])
    def test_merges_slash_by_default(self, app, client, setup):
        configure_app(app, overrides=None, setup=setup)
        res = client.get('/articles/')
        assert res.status_code == 200

        res = client.get('/articles//')
        assert res.status_code == 301
        res = res.follow()
        assert res.request.path_qs == '/articles/'

    def test_append_slash_false_not_found(self, app, client):
        configure_app(app, {
            'append_slash': False
        })
        res = client.get('/articles', expect_errors=True)
        assert res.status_code == 404

    def test_append_slash(self, app, client):
        configure_app(app, {
            'append_slash': True
        })

        res = client.get('/articles/')
        assert res.status_code == 200

        res = client.get('/articles')
        assert res.status_code == 301
        res = res.follow()
        assert res.request.path_qs == '/articles/'

    def test_append_slash_with_query_string(self, app, client):
        configure_app(app, {
            'append_slash': True
        })

        res = client.get('/articles?foo=bar')
        assert res.status_code == 301

        res = res.follow()
        assert res.status_code == 200
        assert res.request.path_qs == '/articles/?foo=bar'

    @pytest.mark.parametrize('url', ['/articles//', '/articles///'])
    def test_merge_slashes(self, app, client, url):
        configure_app(app, {
            'append_slash': True
        })

        res = client.get(url)
        assert res.status_code == 301
        res = res.follow()
        assert res.request.path_qs == '/articles/'

    def test_404_if_request_has_body(self, app, client):
        configure_app(app, {'append_slash': True, 'merge_slashes': True})
        res = client.post('/articles', {'foo': 42}, expect_errors=True)
        assert res.status_code == 404

    def test_404_raised_by_handler(self, app, client):
        configure_app(app, {'append_slash': True})
        res = client.get('/root/resource')
        assert res.status_code == 301
        res = res.follow(expect_errors=True)
        assert res.status_code == 404
