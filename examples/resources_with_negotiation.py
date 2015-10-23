"""Example using `routing.ResourceRouter` and `negotiation` (content negotation).

Start the app with
::
    $ pip install gunicorn http
    $ gunicorn -k aiohttp.worker.GunicornWebWorker examples.resources_with_negotiation:app --reload

Try it out:
::

    $ pip install httpie
    $ http :8000/ message==Hello
    $ http POST :8000/ message=Greetings
"""
from aiohttp import web

from aiohttp_utils import Response, routing, negotiation


class EchoResource:

    async def get(self, request):
        return Response({
            'GET': dict(request.GET)
        })

    async def post(self, request):
        data = await request.json()
        return Response({
            'POST': dict(data)
        })


def create_app():
    app = web.Application(router=routing.ResourceRouter())
    app.router.add_resource('/', EchoResource())

    negotiation.setup(app)
    return app

app = create_app()
