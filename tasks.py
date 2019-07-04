# -*- coding: utf-8 -*-
import os
import sys
import webbrowser

from invoke import task

docs_dir = 'docs'
build_dir = os.path.join(docs_dir, '_build')


@task
def test(ctx, watch=False, last_failing=False):
    """Run the tests.

    Note: --watch requires pytest-xdist to be installed.
    """
    import pytest
    flake(ctx)
    args = []
    if watch:
        args.append('-f')
    if last_failing:
        args.append('--lf')
    retcode = pytest.main(args)
    sys.exit(retcode)


@task
def flake(ctx):
    """Run flake8 on codebase."""
    ctx.run('flake8 .', echo=True)


@task
def clean(ctx):
    ctx.run("rm -rf build")
    ctx.run("rm -rf dist")
    ctx.run("rm -rf aiohttp_utils.egg-info")
    clean_docs(ctx)
    print("Cleaned up.")


@task
def clean_docs(ctx):
    ctx.run("rm -rf %s" % build_dir)


@task
def browse_docs(ctx):
    path = os.path.join(build_dir, 'index.html')
    webbrowser.open_new_tab(path)


def build_docs(ctx, browse):
    ctx.run("sphinx-build %s %s" % (docs_dir, build_dir), echo=True)
    if browse:
        browse_docs(ctx)


@task
def docs(ctx, clean=False, browse=False, watch=False):
    """Build the docs."""
    if clean:
        clean_docs(ctx)
    if watch:
        watch_docs(ctx, browse=browse)
    else:
        build_docs(ctx, browse=browse)


@task
def watch_docs(ctx, browse=False):
    """Run build the docs when a file changes."""
    try:
        import sphinx_autobuild  # noqa
    except ImportError:
        print('ERROR: watch task requires the sphinx_autobuild package.')
        print('Install it with:')
        print('    pip install sphinx-autobuild')
        sys.exit(1)
    ctx.run('sphinx-autobuild {0} {1} {2} -z aiohttp_utils'.format(
        '--open-browser' if browse else '', docs_dir, build_dir), echo=True, pty=True)


@task
def readme(ctx, browse=False):
    ctx.run('rst2html.py README.rst > README.html')
    if browse:
        webbrowser.open_new_tab('README.html')


@task
def publish(ctx, test=False):
    """Publish to the cheeseshop."""
    clean(ctx)
    if test:
        ctx.run('python setup.py register -r test sdist bdist_wheel', echo=True)
        ctx.run('twine upload dist/* -r test', echo=True)
    else:
        ctx.run('python setup.py register sdist bdist_wheel', echo=True)
        ctx.run('twine upload dist/*', echo=True)
