aiohttp_utils
=============

Release v\ |version|. (:ref:`Changelog <changelog>`)

**aiohttp_utils** provides handy utilities for building `aiohttp.web <http://aiohttp.readthedocs.org/>`_ applications.


* Class-based handlers ("resources")
* Content negotiation (JSON rendering by default)
* Local development server with auto-reloading

This package is a toolkit; you can use as much (or as little) of it as you need.

.. code-block:: python

    from aiohttp import web
    from aiohttp_utils import Response, routing, negotiation, runner

    app = web.Application(router=routing.ResourceRouter())

    # Class-based handlers
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

Modules
-------

.. toctree::
    :maxdepth: 1

    modules/routing
    modules/negotiation
    modules/runner

Project info
------------

.. toctree::
   :maxdepth: 1

   license
