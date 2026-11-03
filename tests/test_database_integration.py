"""AIPE-Magnetics-Design consumes AIPE-Magnetics-Database: data come from the Database package, never from a copy."""

from __future__ import annotations

import importlib.util
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_database_is_an_installed_dependency_not_a_copy():
    import aipe_magnetics_database
    from aipe_magnetics_design._dependency import MINIMUM_DATABASE_VERSION, require_database

    assert tuple(int(x) for x in require_database().split(".")[:3]) >= MINIMUM_DATABASE_VERSION
    assert ROOT / "src" not in Path(aipe_magnetics_database.__file__).resolve().parents
    assert not list((ROOT / "src").rglob("*.jsonl")), "no magnetic datasets may be stored in the Design repository"
    assert importlib.util.find_spec("aipe_magnetics_design.data") is None


def test_design_reads_materials_through_the_data_access_seam():
    from aipe_magnetics_design.data_access import LossEvaluator, material_data

    n87 = material_data("N87")
    assert n87.id == "material.tdk-n87" and n87.steinmetz_sets
    assert LossEvaluator(n87.id, n87.steinmetz_sets).sets


def test_example_retrieves_measured_data_and_fits_a_derived_steinmetz_set():
    pytest.importorskip("aipe_magnetics_database.store")
    result = runpy.run_path(str(ROOT / "examples" / "database_to_design.py"))["run"]()
    assert result["database_record"] == "measurement.princeton-magnet-n87-core-loss" and result["license"] == "MIT"
    assert result["rows_used"] > 100
    fit = result["derived_steinmetz_fit"]
    assert 1.0 < fit["alpha"] < 2.0 and 2.0 < fit["beta"] < 3.2
    assert result["design_api_status"] == "ok"
    # cross-check: the curated N87 90 degC set is the bundled MagNet-derived fit (benchmarks/fit_steinmetz_from_magnet.py,
    # 50-500 kHz, 0.01-0.3 T, sinusoidal, zero bias); refitting the Database rows reproduces it
    ratio = result["fit_at_100kHz_100mT_W_per_m3"] / result["design_api_estimate_W_per_m3"]
    assert abs(ratio - 1.0) < 1e-6
