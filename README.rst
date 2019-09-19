*************
aiohttp-utils
*************

.. image:: https://badgen.net/pypi/v/aiohttp-utils
    :target: https://pypi.org/project/aiohttp-utils/
    :alt: Latest version

.. image:: https://badgen.net/travis/sloria/aiohttp-utils
    :target: https://travis-ci.org/sloria/aiohttp-utils
    :alt: Travis-CI

**aiohttp-utils** provides handy utilities for building `aiohttp.web <https://aiohttp.readthedocs.io/>`_ applications.


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
=======
::

    $ pip install aiohttp-utils

Documentation
=============

Full documentation is available at https://aiohttp-utils.readthedocs.io/.

Project Links
=============

- Docs: https://aiohttp-utils.readthedocs.io/
- Changelog: https://aiohttp-utils.readthedocs.io/en/latest/changelog.html
- PyPI: https://pypi.python.org/pypi/aiohttp-utils
- Issues: https://github.com/sloria/aiohttp-utils/issues

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/aiohttp-utils/blob/master/LICENSE>`_ file for more details.
