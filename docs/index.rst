aiohttp_utils
=============

Release v\ |version|. (:ref:`Changelog <changelog>`)

**aiohttp_utils** provides handy utilities for building `aiohttp.web <http://aiohttp.readthedocs.org/>`_ applications.


* Method-based handlers ("resources")
* Content negotiation with JSON rendering by default
* Local development server with auto-reloading
* And more

**Everything is optional**. You can use as much (or as little) of this toolkit as you need.

.. code-block:: python

    from aiohttp import web
    from aiohttp_utils import Response, routing, negotiation, run

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
    negotiation.setup(
        app, renderers={
            'application/json': negotiation.render_json
        }
    )

    if __name__ == '__main__':
        # Development server
        run(
            app,
            app_uri='hello.app:app',
            reload=True,
            port=8000
        )

Install
-------
::

    $ pip install aiohttp_utils


**Ready to get started?** Go on to one of the the usage guides below  or check out some `examples <https://github.com/sloria/aiohttp_utils/tree/master/examples>`_.

Guides
------

Below are usage guides for each of the modules.

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
   versioning
   license
