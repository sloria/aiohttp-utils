"""Handlers for testing routing"""
from aiohttp import web


async def index(request):
    return web.Response()


async def list_projects(request):
    return web.Response()


async def create_projects(request):
    return web.Response()


class ArticleResource:

    async def get(self, request):
        return web.Response()

    async def post(self, request):
        return web.Response()


class ArticleList:

    async def get(self, request):
        return web.Response()

    async def post(self, request):
        return web.Response()


class AuthorList:

    def __init__(self, db):
        self.db = db

    async def get(self, request):
        return web.Response()
