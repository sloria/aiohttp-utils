#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import pytest

from webtest_aiohttp import TestApp

@pytest.fixture(scope='session')
def loop():
    """Create and provide asyncio loop."""
    loop_ = asyncio.get_event_loop()
    asyncio.set_event_loop(loop_)
    return loop_

@pytest.fixture()
def create_client(app):
    def maker(*args, **kwargs):
        return TestApp(app, *args, **kwargs)
    return maker
