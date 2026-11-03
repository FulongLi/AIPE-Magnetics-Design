# Release verification record - AIPE Magnetics Design 0.3.0

Branch `feature/design-migration-from-database`, run on 2026-11-02/03. Host: macOS (Apple silicon), Python 3.12.13
(uv 0.11.21 virtualenv), numpy 2.5.4, scipy 1.18.1, pydantic 2.14.2, jsonschema 4.26.0, h5py 3.16.0, mcp 2.x.
Database dependency: `aipe-magnetics-database` 0.3.0 from branch `feature/database-separation-and-open-data`
(editable install). This record lists what was **actually executed**; anything marked *not executed* is not claimed.

## Executed

| Command | Result |
| --- | --- |
| `python -m pytest -q` | **755 passed, 8 skipped**. Skips have explicit reasons: executed DAB waveform file of the ecosystem run not present (2), `AIPE_ECOSYSTEM_CHECKOUTS` not set (4), `magnethub` not installed (1), Claude Code CLI not installed (1). |
| `aipe-magnetics-design verify --output reports/verification --update-bundled` | **58 checks, 58 passed**, stable after re-run; bundled evidence `src/aipe_magnetics_design/verification/evidence/v0.3.0.json`, Markdown twin `docs/verification-report-v0.3.0.md` |
| `aipe-magnetics-design verify --check-bundled` | `bundled evidence matches this run` |
| `aipe-magnetics-design demo dab-10kw --output <dir>` | 10 kW / 100 kHz DAB transformer in N87, E 65/32/27, **21 : 10 turns, core 21.54 W + copper 17.68 W = 39.22 W** (identical to the 0.2.0 demo) |
| `python examples/database_to_design.py` | reads `measurement.princeton-magnet-n87-core-loss` (MIT) from the Database, 367 sinusoidal zero-bias rows at 90 degC, 50-500 kHz; the refitted Steinmetz set reproduces the catalogue estimate (77,304.6 W/m^3 at 100 kHz / 100 mT, relative difference < 1e-6) |
| `python -m aipe_magnetics_design.mcp.server --self-test` | 13 tools listed |
| `python tools/sync_plugin_skills.py --check` | skills in sync |
| `import aipe_magnetics.*` (v0.2 shim) | covered by `tests/test_compat_shim.py`; resolves to the same module objects with a `DeprecationWarning` |

## Not executed

- `claude plugin validate` / Codex plugin installation (neither CLI is installed on this host); structural plugin
  checks in `tests/plugins` passed.
- External tests needing ecosystem checkouts (`AIPE_ECOSYSTEM_CHECKOUTS`) and the optional `magnethub` package.
- Windows / Linux runs: delegated to the CI matrix (`.github/workflows/ci.yml`).
