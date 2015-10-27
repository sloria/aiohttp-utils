"""Example using

- `routing.ResourceRouter`,
- routing helpers,
- content negotiation,
- path normalization, and
- local development server with reloading.

Start the app with
::
    $ python examples/resources_with_negotiation.py

Try it out:
::

    $ pip install httpie
    $ http :8000/
    $ http :8000/api/
"""
from asyncio import coroutine

from aiohttp import web
from aiohttp_utils import Response, routing, negotiation, run, path_norm

app = web.Application(router=routing.ResourceRouter())

@coroutine
def index(request):
    return Response('Welcome!')

class HelloResource:

    @coroutine
    def get(self, request):
        return Response({
            'message': 'Welcome to the API!'
        })


with routing.add_route_context(app) as route:
    route('GET', '/', index)

with routing.add_resource_context(app, url_prefix='/api/') as route:
    route('/', HelloResource())

negotiation.setup(app)
path_norm.setup(app)

if __name__ == "__main__":
    run(
        app,
        app_uri="examples.kitchen_sink:app",
        reload=True,
        port=8000
    )
