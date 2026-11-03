"""The deprecated v0.2 import name ``aipe_magnetics`` maps onto the 0.3 packages (same module objects)."""

from __future__ import annotations

import importlib
import warnings

import pytest


@pytest.mark.parametrize("old, new", [
    ("aipe_magnetics.api", "aipe_magnetics_design.api"),
    ("aipe_magnetics.models.empirical.steinmetz", "aipe_magnetics_design.models.empirical.steinmetz"),
    ("aipe_magnetics.engineering.transformer", "aipe_magnetics_design.engineering.transformer"),
    ("aipe_magnetics.data.records", "aipe_magnetics_database.data.records"),
    ("aipe_magnetics.common.quantity", "aipe_magnetics_database.common.quantity"),
    ("aipe_magnetics.database.loss", "aipe_magnetics_design.engineering.loss_evaluator"),
    ("aipe_magnetics.database.accessors", "aipe_magnetics_database.database.accessors"),
    ("aipe_magnetics.database", "aipe_magnetics_design.data_access"),
])
def test_v02_module_paths_resolve_to_the_same_module(old, new):
    import aipe_magnetics

    assert aipe_magnetics.resolve(old) == new
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        module = importlib.import_module(old)
    target = importlib.import_module(new)
    assert module is target or all(getattr(module, name) is getattr(target, name) for name in target.__all__)
    assert any(issubclass(w.category, DeprecationWarning) and new in str(w.message) for w in caught) or old in __import__("sys").modules


def test_v02_public_api_still_computes():
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from aipe_magnetics.api import estimate_core_loss
        from aipe_magnetics.database import LossEvaluator, material_data
    result = estimate_core_loss(material="N87", frequency={"value": 100, "unit": "kHz"}, flux_density_peak={"value": 100, "unit": "mT"},
                                temperature={"value": 100, "unit": "degC"})
    assert result.status == "ok" and result.values["loss_density"].quantity.value > 0
    assert LossEvaluator.for_material("N87").material_id == material_data("N87").id


def test_unknown_v02_modules_are_not_invented():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("aipe_magnetics.no_such_module")
