"""Example using

- `routing.ResourceRouter`,
- routing helpers,
- content negotiation,
- path normalization, and
- local development server with reloading.

Start the app with the `adev runserver` command from aiohttp-devtools
::
    $ pip install aiohttp-devtools
    $ adev runserver examples/kitchen_sink.py

Try it out:
::

    $ pip install httpie
    $ http :8000/
    $ http :8000/api/
"""
from aiohttp import web
from aiohttp_utils import Response, routing, negotiation

app = web.Application(router=routing.ResourceRouter())


async def index(request):
    return Response('Welcome!')


class HelloResource:

    async def get(self, request):
        return Response({
            'message': 'Welcome to the API!'
        })


with routing.add_route_context(app) as route:
    route('GET', '/', index)

with routing.add_resource_context(app, url_prefix='/api/') as route:
    route('/', HelloResource())

negotiation.setup(app)
