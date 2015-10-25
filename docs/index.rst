aiohttp_utils
=============

Release v\ |version|. (:ref:`Changelog <changelog>`)

**aiohttp_utils** provides handy utilities for building `aiohttp.web <http://aiohttp.readthedocs.org/>`_ applications.


* Method-based handlers ("resources")
* Content negotiation with JSON rendering by default
* Local development server with auto-reloading
* And more

**Everything is optional**. You can use as much (or as little) of the toolkit as you need.

.. code-block:: python

    from aiohttp import web
    from aiohttp_utils import Response, routing, negotiation, runner

    app = web.Application(router=routing.ResourceRouter())

    # Method-based handlers
    class HelloResource:

        async def get(self, request):
            name = request.GET.get('name', 'World')
            return Response({
                'message': 'Hello ' + name
            })


    app.router.add_resource('/', HelloResource())

    # Content negotiation
    negotiation.setup(app, {
        'RENDERERS': {
            'application/json': negotiation.render_json
        }
    })

    if __name__ == '__main__':
        # Development server
        runner.run(
            app,
            app_uri='hello.app:app',
            reload=True,
            port=8000
        )

Utilities
---------

.. toctree::
    :maxdepth: 1

    modules/negotiation
    modules/path_norm
    modules/routing
    modules/runner

Project info
------------

.. toctree::
   :maxdepth: 1

   changelog
   license
