"""Run an `aiohttp.web.Application` on a local development server. If
:attr:`debug` is set on the application, the server will automatically
reload when code changes.
::

    from aiohttp import web
    from aiohttp_utils import runner

    app = web.Application()
    # ...
    runner.run(app, port=5000)
"""
from aiohttp import web
from gunicorn.app.wsgiapp import WSGIApplication as BaseApplication
from aiohttp.worker import GunicornWebWorker as BaseWorker


class GunicornWorker(BaseWorker):
    # Override to set the app's loop to the worker's loop
    def make_handler(self, app, host, port):
        # self.loop.set_debug(app.debug)
        app._loop = self.loop
        return super().make_handler(app, host, port)

class GunicornApp(BaseApplication):

    def __init__(self, app: web.Application, *args, **kwargs):
        self._app = app
        super().__init__(*args, **kwargs)

    # Override BaseApplication so that we don't try to parse command-line args
    def load_config(self):
        pass

    # Override BaseApplication to return aiohttp app
    def load(self):
        self.chdir()
        return self._app

class Runner:
    worker_class = 'aiohttp_utils.runner.GunicornWorker'

    def __init__(
        self,
        app: web.Application=None,
        host='127.0.0.1',
        port=5000,
        reload: bool=None,
        **options
    ):
        self.app = app
        self.host = host
        self.port = port
        self.reload = reload or app.debug
        self.options = options

    @property
    def bind(self):
        return '{self.host}:{self.port}'.format(self=self)

    def make_gunicorn_app(self):
        gapp = GunicornApp(self.app)
        gapp.cfg.set('bind', self.bind)
        gapp.cfg.set('reload', self.reload)
        gapp.cfg.settings['worker_class'].default = self.worker_class
        gapp.cfg.set('worker_class', self.worker_class)
        for key, value in self.options.items():
            gapp.cfg.set(key, value)
        return gapp

    def run(self):
        gapp = self.make_gunicorn_app()
        gapp.run()


def run(app, **kwargs):
    """Run an `aiohttp.web.Application` using gunicorn.

    :param web.Application app: The app to run.
    :param str host: Hostname to listen on.
    :param int port: Port of the server.
    :param bool reload: Whether to reload the server on a code change.
        If not set, will take the same value as ``app.debug``.
    :param \*\*kwargs: Extra configuration options to set on the
        ``GunicornApp's`` config object.
    """
    runner = Runner(app, **kwargs)
    runner.run()
