"""Deprecated v0.2 import name ``aipe_magnetics`` (compatibility shim, removed in 0.5).

AIPE Magnetics 0.2.0 shipped one package. In 0.3.0 it is split into ``aipe_magnetics_database``
(AIPE-Magnetics-Database: data, schema, catalogue, importers) and ``aipe_magnetics_design``
(AIPE-Magnetics-Design: models, engineering, design, verification, API/CLI/MCP). Importing
``aipe_magnetics.<module>`` resolves to the *same module object* in the new packages, so classes and
functions are identical; a :class:`DeprecationWarning` names the new path. See docs/migration-v0.3.md.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys
import types
import warnings

from aipe_magnetics_design import SCHEMA_VERSION, TOOL_ID, TOOL_NAME, __version__

# v0.2 module prefix -> 0.3 module (longest prefix wins)
ALIASES: dict[str, str] = {
    "aipe_magnetics.common": "aipe_magnetics_database.common",
    "aipe_magnetics.data": "aipe_magnetics_database.data",
    "aipe_magnetics.database.loss": "aipe_magnetics_design.engineering.loss_evaluator",
    "aipe_magnetics.database.accessors": "aipe_magnetics_database.database.accessors",
    "aipe_magnetics.database.properties": "aipe_magnetics_database.database.properties",
    "aipe_magnetics.database.query": "aipe_magnetics_database.database.query",
    "aipe_magnetics.database": "aipe_magnetics_design.data_access",
    "aipe_magnetics": "aipe_magnetics_design",
}


def resolve(name: str) -> str:
    """0.3 module name for a v0.2 module name (``aipe_magnetics.models.empirical`` -> ``aipe_magnetics_design.models.empirical``)."""
    for old in sorted(ALIASES, key=len, reverse=True):
        if name == old or name.startswith(old + "."):
            return ALIASES[old] + name[len(old):]
    raise ModuleNotFoundError(name)


class _AliasLoader(importlib.abc.Loader):
    def __init__(self, target: str):
        self.target = target

    def create_module(self, spec):  # noqa: D102 - importlib protocol
        module = importlib.import_module(self.target)
        if spec.submodule_search_locations is not None and not hasattr(module, "__path__"):
            # a v0.2 package that became a plain module (aipe_magnetics.database -> data_access): expose its names in a
            # package object so that v0.2 submodules (aipe_magnetics.database.loss ...) can still be aliased
            package = types.ModuleType(spec.name, module.__doc__)
            package.__dict__.update({k: v for k, v in vars(module).items() if not k.startswith("__")})
            package.__path__ = []
            return package
        return module

    def exec_module(self, module):  # noqa: D102 - the target module is already executed
        return None


class _AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):  # noqa: D102 - importlib protocol
        if not fullname.startswith("aipe_magnetics."):
            return None
        new = resolve(fullname)
        if importlib.util.find_spec(new) is None:
            return None
        warnings.warn(f"'{fullname}' is deprecated since 0.3.0; import '{new}' instead", DeprecationWarning, stacklevel=2)
        module = importlib.import_module(new)
        has_children = any(old.startswith(fullname + ".") for old in ALIASES)
        return importlib.util.spec_from_loader(fullname, _AliasLoader(new), is_package=hasattr(module, "__path__") or has_children)


if not any(isinstance(f, _AliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _AliasFinder())

__all__ = ["ALIASES", "SCHEMA_VERSION", "TOOL_ID", "TOOL_NAME", "__version__", "resolve"]
