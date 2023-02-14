"""Example of using content negotiation to simultaneously support HTML and JSON representations,
using Mako for templating. Also demonstrates app configuration.

Start the app with the `adev runserver` command from aiohttp-devtools
::
    $ pip install aiohttp-devtools
    $ adev runserver examples/mako_example.py

Try it out:
::

    $ pip install httpie
    $ http :8000/ Accept:application/json
    $ http :8000/ Accept:text/html
"""
from collections import OrderedDict
from collections.abc import Mapping

from aiohttp import web
from aiohttp_utils import Response, negotiation

from mako.lookup import TemplateLookup


# ##### Templates #####

lookup = TemplateLookup()
# Note: In a real app, this would be in a separate file.
template = """
<html>
    <body>
        <h1>${message}</h1>
    </body>
</html>
"""
lookup.put_string('index.html', template)


# ##### Handlers #####

async def index(request):
    return Response({
        'message': 'Hello ' + request.query.get('name', 'World')
    })


# ##### Custom router #####

class RouterWithTemplating(web.UrlDispatcher):
    """Optionally save a template name on a handler function's __dict__."""

    def add_route(self, method, path, handler, template: str = None, **kwargs):
        if template:
            handler.__dict__['template'] = template
        super().add_route(method, path, handler, **kwargs)


# ##### Renderer #####

def render_mako(request, data):
    handler = request.match_info.handler
    template_name = handler.__dict__.get('template', None)
    if not template_name:
        raise web.HTTPNotAcceptable(text='text/html not supported.')
    if not isinstance(data, Mapping):
        raise web.HTTPInternalServerError(
            text="context should be mapping, not {}".format(type(data)))
    template = request.app['mako_lookup'].get_template(template_name)
    text = template.render_unicode(**data)
    return web.Response(text=text, content_type=request['selected_media_type'])


# ##### Configuration #####

CONFIG = {
    'AIOHTTP_UTILS': {
        'RENDERERS': OrderedDict([
            ('application/json', negotiation.render_json),
            ('text/html', render_mako),
        ])
    }
}


# ##### Application #####

app = web.Application(router=RouterWithTemplating(), debug=True)
app['mako_lookup'] = lookup
app.update(CONFIG)
negotiation.setup(app)
app.router.add_route('GET', '/', index, template='index.html')
