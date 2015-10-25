"""Handlers for testing routing"""
from asyncio import coroutine

from aiohttp import web

@coroutine
def index(request):
    return web.Response()

@coroutine
def list_projects(request):
    return web.Response()

@coroutine
def create_projects(request):
    return web.Response()

class ArticleResource:

    @coroutine
    def get(self, request):
        return web.Response()

    @coroutine
    def post(self, request):
        return web.Response()

class ArticleList:

    @coroutine
    def get(self, request):
        return web.Response()

    @coroutine
    def post(self, request):
        return web.Response()
