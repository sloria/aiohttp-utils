"""We use the apps in examples/ for integration tests."""
import pytest

from examples.kitchen_sink import app as kitchen_sink_app
from examples.mako_example import app as mako_app


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


class TestMakoApp:

    @pytest.fixture()
    def client(self, loop, create_client):
        mako_app._loop = loop
        return create_client(mako_app)

    def test_json_request(self, client):
        res = client.get('/', headers={'Accept': 'application/json'})
        assert res.content_type == 'application/json'
        assert res.json == {'message': 'Hello World'}

    def test_json_request_with_query_params(self, client):
        res = client.get('/?name=Ada', headers={'Accept': 'application/json'})
        assert res.content_type == 'application/json'
        assert res.json == {'message': 'Hello Ada'}

    def test_html_request(self, client):
        res = client.get('/', headers={'Accept': 'text/html'})
        assert res.status_code == 200
        assert res.content_type == 'text/html'
        assert res.html.find('h1').text == 'Hello World'
