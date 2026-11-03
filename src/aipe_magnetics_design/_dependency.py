"""Explicit, guided check of the AIPE-Magnetics-Database dependency."""

from __future__ import annotations

MINIMUM_DATABASE_VERSION = (0, 3, 0)
INSTALL_HINT = ('pip install "aipe-magnetics-database @ git+https://github.com/FulongLi/AIPE-Magnetics-Database.git" '
                "(AIPE-Magnetics-Design reads all magnetic data from the AIPE-Magnetics-Database package)")


def require_database() -> str:
    """Return the installed Database version; raise ImportError with the installation command otherwise."""
    try:
        import aipe_magnetics_database
    except ImportError as error:  # pragma: no cover - exercised only in a broken environment
        raise ImportError(f"aipe-magnetics-database is not installed: {INSTALL_HINT}") from error
    version = tuple(int(part) for part in aipe_magnetics_database.__version__.split(".")[:3] if part.isdigit())
    if version < MINIMUM_DATABASE_VERSION:  # pragma: no cover
        raise ImportError(f"aipe-magnetics-database {aipe_magnetics_database.__version__} is too old "
                          f"(>= {'.'.join(map(str, MINIMUM_DATABASE_VERSION))} required): {INSTALL_HINT}")
    return aipe_magnetics_database.__version__
