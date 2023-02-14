*********
Changelog
*********

3.2.1 (2023-02-14)
==================

- Actually bump package version...

3.2.0 (2023-02-14)
==================

- Add support for Python 3.10 and 3.11
- Switch ci to gh actions
- Rename package name as aiohttp-utils


3.1.1 (2019-07-11)
==================

- [negotiation]: Fix handling of aiohttp.web.Response when force_rendering is set.
- Add examples to the MANIFEST.

3.1.0 (2019-07-09)
==================

- Add support for aiohttp>=3.
- Drop support for Python 3.4.
- Test against Python 3.7.
- [negotiation]: Add a new `force_rendering` config option.

3.0.0 (2016-03-16)
==================

- Test against Python 3.6.
- [runner] *Backwards-incompatible*: The `runner` module is deprecated. Install `aiohttp-devtools` and use the `adev runserver` command instead.
- [path_norm] *Backwards-incompatible*: The `path_norm` module is removed, as it is now available in `aiohttp` in `aiohttp.web_middlewares.normalize_path_middleware`.

2.0.1 (2016-04-03)
==================

- [runner] Fix compatibility with aiohttp>=0.21.0 (:issue:`2`). Thanks :user:`charlesfleche` for reporting.

2.0.0 (2016-03-13)
==================

- Fix compatibility with aiohttp>=0.21.0.
- [routing] *Backwards-incompatible*: Renamed ``ResourceRouter.add_resource`` to ``ResourceRouter.add_resource_object`` to prevent clashing with aiohttp's URLDispatcher.

1.0.0 (2015-10-27)
==================

- [negotiation,path_norm] *Backwards-incompatible*: Changed signatures of ``negotiation.setup`` and ``path_norm.setup`` to be more explicit. Both now take keyword-only arguments which are the same as the module's configuration keys, except lowercased, e.g. ``setup(app, append_slash=True, merge_slashes=True)``.
- [runner] Make ``run`` importable from top-level ``aiohttp_utils`` module.
- [runner] Fix behavior when passing ``reload=False`` when ``app.debug=True``
- Improved docs.

0.1.0 (2015-10-25)
==================

- First PyPI release. Includes ``negotiation``, ``path_norm``, ``routing``, and ``runner`` modules.
