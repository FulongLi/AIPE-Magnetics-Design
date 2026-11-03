# AIPE Magnetics Design

AIPE Magnetics Design models and designs magnetic components for power electronics. It covers core-loss and
hysteresis models (Steinmetz, iGSE, Bertotti, Jiles-Atherton, ODE and data-driven) and inductor and transformer
design, including waveform-informed DAB transformer design. It also computes winding loss (Dowell and harmonic),
saturation screening, geometry, thermal and FEM helpers, optimisation, verification evidence and reports. Each
result is an envelope with values and units, assumptions, model identity, sources, verification level, warnings
and limitations. Inputs outside a model's domain are rejected, never clipped.

All magnetic data come from **[AIPE-Magnetics-Database](https://github.com/FulongLi/AIPE-Magnetics-Database)**,
the `aipe-magnetics-database` package. Design is consumed through `aipe_magnetics_design.data_access`. No dataset
is stored in this repository.

```
AIPE-Magnetics-Design (models, design, verification, API/CLI/MCP)  -->  AIPE-Magnetics-Database (schema, records, queries)
```

## Installation

Python 3.10 or newer. Install the Database first; it is not on PyPI yet. Then install Design:

```sh
pip install "aipe-magnetics-database @ git+https://github.com/FulongLi/AIPE-Magnetics-Database.git"
pip install "aipe-magnetics-design[mcp] @ git+https://github.com/FulongLi/AIPE-Magnetics-Design.git"
# or, from a checkout: pip install -r requirements.txt
```

Extras: `[mcp]` MCP server, `[hdf5]` waveform files, `[torch]` data-driven backend, `[viz]` plots, `[mesh]` /
`[cad]` geometry export. If the Database is missing, the package fails with an `ImportError` that gives the
install command.

## Usage

```sh
aipe-magnetics-design materials compare N87 3C94 N49 -f "100 kHz" -b "100 mT" -t "90 degC"
aipe-magnetics-design loss estimate N87 -f "100 kHz" -b "150 mT" -t "100 degC" --waveform triangular --core core.tdk-e65-32-27
aipe-magnetics-design demo dab-10kw --output reports/demo
python examples/database_to_design.py
```

```python
import aipe_magnetics_design.api as design
r = design.estimate_core_loss(material="N87", frequency={"value": 100, "unit": "kHz"},
                              flux_density_peak={"value": 150, "unit": "mT"}, temperature={"value": 100, "unit": "degC"},
                              waveform={"kind": "triangular"})
print(r.values["loss_density"].quantity, r.model.id, r.verification.state)
```

The DAB demo sizes a 10 kW, 800 V : 400 V, 100 kHz dual-active-bridge transformer in N87: E 65/32/27 core,
21 : 10 turns, 39.2 W estimated loss. These are analytical estimates with stated assumptions; nothing was built
or measured ([docs/demo-dab-10kw.md](docs/demo-dab-10kw.md)).

`examples/database_to_design.py` reads the Princeton MagNet N87 measurements (90 °C, sinusoidal) from the
Database and fits a Steinmetz set to them. The fit is labelled as derived data. It reproduces the catalogue set
used by `estimate_core_loss`.

## Agent integration

The Claude Code and Codex plugins `aipe-magnetics-design` are in `plugins/`, with marketplaces in
`.claude-plugin/` and `.agents/plugins/`. They start the local stdio MCP server `aipe-magnetics-design-mcp` for
design and loss tools. For data-only work, install the separate `aipe-magnetics-database` plugin from the
Database repository. See [docs/plugins.md](docs/plugins.md) and [docs/mcp.md](docs/mcp.md).

## Migrating from aipe-magnetics 0.2

`import aipe_magnetics.<module>` still works through a deprecation shim that maps v0.2 paths to the new
packages. The CLI name `aipe-magnetics` is kept as an alias. See [docs/migration-v0.3.md](docs/migration-v0.3.md).

## Project Information

- Version 0.3.0 (`aipe-magnetics-design`). Requires `aipe-magnetics-database>=0.3,<0.4`. Status: prototype.
  Verification levels are recorded per capability ([docs/verification.md](docs/verification.md)).
- Developer: Fulong Li, Spirit Connect / AIPE Labs.
- Licence: `NOASSERTION` (not yet declared; [LICENSING.md](LICENSING.md)).
- Docs: [architecture](docs/architecture.md), [models](docs/models.md), [API](docs/api.md),
  [waveform-informed design](docs/waveform-informed-design.md), [limitations](docs/limitations.md),
  [CHANGELOG.md](CHANGELOG.md).
