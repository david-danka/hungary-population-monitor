"""Hungary Population Monitor package.

Provides the high-level package for collecting, transforming and loading
Hungarian population and settlement data into a star-schema SQLite
database. Use subpackages for concrete functionality: ``data_collection``,
``transform``, and ``load``.

This module intentionally keeps the top-level API minimal; import the
specific submodules to access collectors, transformers, and loaders.
"""
