#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

from aiohttp import web
import pytest

from webtest_aiohttp import TestApp


@pytest.fixture(scope='session')
def loop():
    """Create and provide asyncio loop."""
    loop_ = asyncio.get_event_loop()
    asyncio.set_event_loop(loop_)
    return loop_


@pytest.fixture()
def create_client():
    def maker(app, *args, **kwargs):
        # Set to False because we set app['aiohttp_utils'], which
        # is invalid in wsgi environs
        kwargs.setdefault('lint', False)
        return TestApp(app, *args, **kwargs)
    return maker


def make_dummy_handler(**kwargs):
    async def dummy(request):
        return web.Response(**kwargs)
    return dummy
