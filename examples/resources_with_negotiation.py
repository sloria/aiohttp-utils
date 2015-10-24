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

from aiohttp_utils import Response, routing, negotiation, runner

app = web.Application(router=routing.ResourceRouter())

class HelloResource:

    async def get(self, request):
        name = request.GET.get('name', 'World')
        return Response({
            'message': 'Hello ' + name
        })


app.router.add_resource('/', HelloResource())
negotiation.setup(app)

if __name__ == "__main__":
    runner.run(
        app,
        app_uri="examples.resources_with_negotiation:app",
        reload=True,
        port=8000
    )
