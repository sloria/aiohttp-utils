import pytest
from aiohttp import web
from aiohttp_utils.runner import Runner


class TestRunner:

    def test_bind(self):
        app = web.Application()
        runner = Runner(app, host='1.2.3.4', port=5678,
                        app_uri='http://1.2.3.4:5678')
        assert runner.bind == '1.2.3.4:5678'

    def test_app_uri_is_required_for_reload(self):
        app = web.Application()
        with pytest.raises(RuntimeError):
            Runner(app, reload=True)  # no api_uri

    def test_reload_takes_value_of_app_debug_by_default(self):
        app = web.Application(debug=True)
        assert Runner(app, app_uri='foo').reload is True
        app = web.Application(debug=False)
        assert Runner(app, app_uri='foo').reload is False

    def test_reload_override(self):
        app = web.Application(debug=True)
        assert Runner(app, reload=False).reload is False

        app = web.Application(debug=False)
        assert Runner(app, reload=True, app_uri='foo').reload is True
