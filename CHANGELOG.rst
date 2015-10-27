*********
Changelog
*********

1.0.0 (unreleased)
==================

- [negotiation,path_norm] *Backwards-incompatible*: Changed signatures of ``negotiation.setup`` and ``path_norm.setup`` to be more explicit. Both now take keyword-only arguments which are the same as the module's configuration keys, except lowercased, e.g. ``setup(app, append_slash=True, merge_slashes=True)``.
- [runner] Make ``run`` importable from top-level ``aiohttp_utils`` module.
- [runner] Fix behavior when passing ``reload=False`` when ``app.debug=True``

0.1.0 (2015-10-25)
==================

- First PyPI release. Includes ``negotiation``, ``path_norm``, ``routing``, and ``runner`` modules.
