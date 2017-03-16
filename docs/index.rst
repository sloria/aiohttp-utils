aiohttp_utils
=============

Release v\ |version|. (:ref:`Changelog <changelog>`)

**aiohttp_utils** provides handy utilities for building `aiohttp.web <https://aiohttp.readthedocs.io/>`_ applications.


* Method-based handlers ("resources")
* Routing utilities
* Content negotiation with JSON rendering by default

**Everything is optional**. You can use as much (or as little) of this toolkit as you need.

.. code-block:: python

    from aiohttp import web
    from aiohttp_utils import Response, routing, negotiation

    app = web.Application(router=routing.ResourceRouter())

    # Method-based handlers
    class HelloResource:

        async def get(self, request):
            name = request.GET.get('name', 'World')
            return Response({
                'message': 'Hello ' + name
            })


    app.router.add_resource_object('/', HelloResource())

    # Content negotiation
    negotiation.setup(
        app, renderers={
            'application/json': negotiation.render_json
        }
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
    modules/routing

Project info
------------

.. toctree::
   :maxdepth: 1

   changelog
   versioning
   license
