"""The single seam through which AIPE-Magnetics-Design consumes AIPE-Magnetics-Database.

Everything material-, core- and property-related that the design code needs is imported from here, so the
dependency ``aipe_magnetics_design -> aipe_magnetics_database`` stays explicit and narrow. Read-only data
accessors and queries come from the Database package unchanged; the loss evaluator and the material loss
estimate are Design code (they *predict* loss from fitted parameter sets) and are re-exported for convenience.
"""

from __future__ import annotations

from aipe_magnetics_design._dependency import require_database

require_database()

from aipe_magnetics_database.database import (  # noqa: E402
    CoreData,
    MaterialData,
    core_data,
    describe_entry,
    get_core,
    get_material_properties,
    get_physical_properties,
    import_dataset,
    info,
    list_core_data,
    material_data,
    physical_property,
    property_materials,
    property_source,
    query_core_loss_data,
    query_saturation_data,
    search_cores,
    search_materials,
    validate_dataset,
)
from aipe_magnetics_design.engineering.loss_evaluator import FluxShape, LossEvaluation, LossEvaluator  # noqa: E402
from aipe_magnetics_design.engineering.material_loss import estimate_material_loss  # noqa: E402

__all__ = [
    "CoreData", "FluxShape", "LossEvaluation", "LossEvaluator", "MaterialData", "core_data", "describe_entry", "estimate_material_loss",
    "get_core", "get_material_properties", "get_physical_properties", "import_dataset", "info", "list_core_data", "material_data",
    "physical_property", "property_materials", "property_source", "query_core_loss_data", "query_saturation_data", "search_cores",
    "search_materials", "validate_dataset",
]
