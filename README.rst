*************
aiohttp_utils
*************

.. image:: https://badge.fury.io/py/aiohttp_utils.png
    :target: http://badge.fury.io/py/aiohttp_utils
    :alt: Latest version

.. image:: https://travis-ci.org/sloria/aiohttp_utils.png
    :target: https://travis-ci.org/sloria/aiohttp_utils
    :alt: Travis-CI

**aiohttp_utils** provides handy utilities for building `aiohttp.web <https://aiohttp.readthedocs.io/>`_ applications.


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


    app.router.add_resource_object('/', HelloResource())

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
=======
::

    $ pip install aiohttp_utils

Documentation
=============

Full documentation is available at https://aiohttp-utils.readthedocs.io/.

Project Links
=============

- Docs: https://aiohttp-utils.readthedocs.io/
- Changelog: https://aiohttp-utils.readthedocs.io/en/latest/changelog.html
- PyPI: https://pypi.python.org/pypi/aiohttp_utils
- Issues: https://github.com/sloria/aiohttp_utils/issues

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/aiohttp_utils/blob/master/LICENSE>`_ file for more details.
