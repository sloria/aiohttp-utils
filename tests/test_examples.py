"""We use the apps in examples/ for integration tests."""
import pytest

from examples.kitchen_sink import app as kitchen_sink_app

class TestKitchenSinkApp:

    @pytest.fixture()
    def client(self, loop, create_client):
        kitchen_sink_app._loop = loop
        return create_client(kitchen_sink_app)

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

