"""AIPE Magnetics Design: evidence-first magnetic component modelling and design for power electronics.

All magnetic data (materials, cores, measurements, schema v0.2) come from the separate
AIPE-Magnetics-Database package (``aipe_magnetics_database``) through :mod:`aipe_magnetics_design.data_access`.

* ``aipe_magnetics_design.models``        - model contract and families (Steinmetz, iGSE, Bertotti, Jiles-Atherton, ODE, data-driven)
* ``aipe_magnetics_design.engineering``   - practical estimation calculations (core loss, winding loss, saturation, reports)
* ``aipe_magnetics_design.design``        - inductor and transformer design (incl. waveform-informed DAB transformer design)
* ``aipe_magnetics_design.geometry`` / ``simulation`` / ``optimisation`` / ``visualisation`` / ``workflows``
* ``aipe_magnetics_design.verification``  - verification levels and evidence registry
* ``aipe_magnetics_design.integrations``  - AIPE-Core / AIPE-Registry compatibility adapters
* ``aipe_magnetics_design.api`` / ``cli`` / ``mcp`` - typed Python API, command line and local stdio MCP server

All mathematics lives in ``models`` / ``engineering`` / ``design`` and is callable without any language model.
"""

from __future__ import annotations

__version__ = "0.3.0"
TOOL_ID = "aipe.magnetics"
TOOL_NAME = "AIPE Magnetics Design"
SCHEMA_VERSION = "0.2.0"

__all__ = ["__version__", "TOOL_ID", "TOOL_NAME", "SCHEMA_VERSION"]
