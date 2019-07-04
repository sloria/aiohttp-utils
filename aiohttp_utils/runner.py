"""Run an `aiohttp.web.Application` on a local development server. If
:attr:`debug` is set to `True` on the application, the server will automatically
reload when code changes.
::

    from aiohttp import web
    from aiohttp_utils import run

    app = web.Application()
    # ...
    run(app, app_uri='path.to.module:app', reload=True, port=5000)


.. warning::
    Auto-reloading functionality is currently **experimental**.
"""
import warnings

from aiohttp import web
from aiohttp.worker import GunicornWebWorker as BaseWorker
from gunicorn.app.wsgiapp import WSGIApplication as BaseApplication
from gunicorn.util import import_app

__all__ = (
    'run',
    'Runner',
    'GunicornApp',
    'GunicornWorker',
)


class GunicornWorker(BaseWorker):
    # Override to set the app's loop to the worker's loop
    def make_handler(self, app, **kwargs):
        app._loop = self.loop
        return super().make_handler(app, **kwargs)


class GunicornApp(BaseApplication):

    def __init__(self, app: web.Application,
                 app_uri: str = None, *args, **kwargs):
        self._app = app
        self.app_uri = app_uri
        super().__init__(*args, **kwargs)

    # Override BaseApplication so that we don't try to parse command-line args
    def load_config(self):
        pass

    # Override BaseApplication to return aiohttp app
    def load(self):
        self.chdir()
        if self.app_uri:
            return import_app(self.app_uri)
        return self._app


class Runner:
    worker_class = 'aiohttp_utils.runner.GunicornWorker'

    def __init__(
        self,
        app: web.Application = None,
        app_uri: str = None,
        host='127.0.0.1',
        port=5000,
        reload: bool = None,
        **options
    ):
        warnings.warn('aiohttp_utils.runner is deprecated. '
                      'Install aiohttp-devtools and use '
                      'the "adev runserver" command instead.', DeprecationWarning)
        self.app = app
        self.app_uri = app_uri
        self.host = host
        self.port = port
        self.reload = reload if reload is not None else app.debug
        if self.reload and not self.app_uri:
            raise RuntimeError('"reload" option requires "app_uri"')
        self.options = options

    @property
    def bind(self):
        return '{self.host}:{self.port}'.format(self=self)

    def make_gunicorn_app(self):
        gapp = GunicornApp(self.app, app_uri=self.app_uri)
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


def run(app: web.Application, **kwargs):
    """Run an `aiohttp.web.Application` using gunicorn.

    :param app: The app to run.
    :param str app_uri: Import path to `app`. Takes the form
        ``$(MODULE_NAME):$(VARIABLE_NAME)``.
        The module name can be a full dotted path.
        The variable name refers to the `aiohttp.web.Application` instance.
        This argument is required if ``reload=True``.
    :param str host: Hostname to listen on.
    :param int port: Port of the server.
    :param bool reload: Whether to reload the server on a code change.
        If not set, will take the same value as ``app.debug``.
        **EXPERIMENTAL**.
    :param kwargs: Extra configuration options to set on the
        ``GunicornApp's`` config object.
    """
    runner = Runner(app, **kwargs)
    runner.run()
