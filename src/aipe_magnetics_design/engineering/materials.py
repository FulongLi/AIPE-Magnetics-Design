"""Material comparison at an operating point (Design layer).

Material lookup and inspection (``lookup_material``, ``evidence_sources``, ``saturation_flux_density_at``,
``material_summary``, ``list_materials``, ``get_material``) are Database functions
(:mod:`aipe_magnetics_database.database.materials`) re-exported here for v0.2 compatibility; comparison adds
Steinmetz loss density and saturation margins, which are model predictions and therefore Design code.
"""

from __future__ import annotations

from typing import Any

from aipe_magnetics_database.common.errors import DataNotFoundError, InvalidInputError, OutOfDomainError
from aipe_magnetics_database.common.quantity import Quantity
from aipe_magnetics_database.common.results import EngineeringResult, SourceReference
from aipe_magnetics_database.data.records import ConditionedValue, MagneticRecord, MaterialProperties
from aipe_magnetics_database.database.materials import (
    CAP_GET,
    CAP_LIST,
    _catalog,
    evidence_sources,
    get_material,
    list_materials,
    lookup_material,
    material_summary,
    saturation_flux_density_at,
)

CAP_COMPARE = "aipe.magnetics.compare_materials"


def compare_materials(materials: list[str], frequency: Quantity | None = None, flux_density_peak: Quantity | None = None,
                      temperature: Quantity | None = None, catalog: Any | None = None, registry: Any | None = None) -> EngineeringResult:
    """Compare materials; when an operating point is given, add Steinmetz loss density and saturation margin.

    The verification block is derived from the evidence registry for the Steinmetz model under the requested
    conditions (per material in ``data.comparison[].loss_verification``); it is never asserted.
    """
    if not isinstance(materials, (list, tuple)) or not materials or not all(isinstance(m, str) and m.strip() for m in materials):
        raise InvalidInputError("compare_materials needs a non-empty list of material ids, names or grades (strings)")
    if registry is None:
        from aipe_magnetics_design.verification.suite import load_bundled_registry
        registry = load_bundled_registry()
    result = EngineeringResult(capability=CAP_COMPARE, inputs={
        "materials": list(materials),
        "frequency": None if frequency is None else frequency.model_dump(mode="json", exclude_none=True),
        "flux_density_peak": None if flux_density_peak is None else flux_density_peak.model_dump(mode="json", exclude_none=True),
        "temperature": None if temperature is None else temperature.model_dump(mode="json", exclude_none=True)})
    rows: list[dict[str, Any]] = []
    for query in materials:
        record, props = lookup_material(query, catalog)
        row: dict[str, Any] = {"query": query, "id": record.id, "name": record.name, "grade": props.grade,
                               "material_class": props.material_class, "synthetic": record.synthetic,
                               "initial_permeability": props.initial_permeability.value.value if props.initial_permeability else None,
                               "curie_temperature_K": props.curie_temperature.value.value if props.curie_temperature else None,
                               "curie_temperature_note": props.curie_temperature.note if props.curie_temperature else None,
                               "loss_density_W_per_m3": None, "loss_model": None, "parameter_set": None,
                               "saturation_flux_density_T": None, "saturation_margin": None, "notes": []}
        for source in evidence_sources(record):
            result.cite(source)
        if temperature is not None:
            try:
                bsat, status, _refs = saturation_flux_density_at(props, temperature)
                row["saturation_flux_density_T"] = bsat.value
                row["saturation_status"] = status
                if flux_density_peak is not None:
                    row["saturation_margin"] = 1.0 - flux_density_peak.to("T").value / bsat.value
            except (DataNotFoundError, OutOfDomainError) as error:
                row["notes"].append(f"saturation: {error.message}")
        if frequency is not None and flux_density_peak is not None:
            try:
                from aipe_magnetics_design.models.empirical.steinmetz import SteinmetzModel, select_parameter_set
                t_k = None if temperature is None else temperature.to("K").value
                pset = select_parameter_set(props.steinmetz_parameter_sets, t_k)
                model = SteinmetzModel.from_parameter_set(pset, material_id=record.id, sources=evidence_sources(record))
                out = model.loss_density(frequency=frequency.to("Hz").value, flux_density_peak=flux_density_peak.to("T").value,
                                         temperature=t_k, policy="warn")
                row["loss_density_W_per_m3"] = out.values["loss_density"].value
                row["loss_model"] = f"{out.model.id}@{out.model.version}"
                row["parameter_set"] = pset.id
                row["loss_verification"] = registry.status_for(out.model.id, frequency=frequency.to("Hz").value, temperature=t_k,
                                                               flux_density_peak=flux_density_peak.to("T").value, material=record.id,
                                                               excitation="sinusoidal").model_dump(mode="json")
                if not out.domain.inside:
                    row["notes"].append("loss: outside parameter-set validity: " + "; ".join(out.domain.violations))
            except (DataNotFoundError, OutOfDomainError, InvalidInputError) as error:
                row["notes"].append(f"loss: {error.message}")
        rows.append(row)
    ranked = sorted(rows, key=lambda r: (r["loss_density_W_per_m3"] is None, r["loss_density_W_per_m3"] or 0.0))
    result.data["comparison"] = ranked
    result.assume("sinusoidal_comparison", "Loss densities in the comparison use the classical Steinmetz equation "
                  "(sinusoidal flux) with the parameter set covering the requested temperature.", "model_assumption",
                  ["comparison"])
    result.limit("comparison_scope", "The comparison ranks datasheet-derived Steinmetz losses and saturation margin only; "
                 "it is not a thermal, cost or availability assessment.")
    missing = [r["id"] for r in rows if r["loss_density_W_per_m3"] is None]
    if missing and frequency is not None and flux_density_peak is not None:
        result.warn("loss_not_available", f"No loss estimate for {', '.join(missing)} at this operating point (see notes).")
    evaluated = [r for r in rows if r.get("loss_verification")]
    if evaluated and frequency is not None and flux_density_peak is not None:
        model_id = evaluated[0]["loss_model"].split("@")[0]
        status = registry.status_for(model_id, frequency=frequency.to("Hz").value,
                                     temperature=None if temperature is None else temperature.to("K").value,
                                     flux_density_peak=flux_density_peak.to("T").value, excitation="sinusoidal")
        result.verification = status
        result.verification.statement = (f"Steinmetz model (evidence registry): {status.statement} Per-material status in "
                                         "data.comparison[].loss_verification; the datasheet parameters themselves are transcriptions "
                                         "and remain unreviewed.")
    else:
        result.verification.state = "verified"
        result.verification.level = "L1"
        result.verification.statement = ("No loss model was evaluated (no complete operating point or no covering parameter set); "
                                         "the comparison is a deterministic read of validated catalogue records (L1).")
    return result


__all__ = [
    "CAP_COMPARE", "CAP_GET", "CAP_LIST", "ConditionedValue", "MagneticRecord", "MaterialProperties", "SourceReference", "_catalog",
    "compare_materials", "evidence_sources", "get_material", "list_materials", "lookup_material", "material_summary",
    "saturation_flux_density_at",
]
