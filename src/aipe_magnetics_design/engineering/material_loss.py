"""Material loss density from the database's Steinmetz parameter sets (Design: loss prediction).

Moved from ``aipe_magnetics.database.query`` (v0.2) because it *predicts* loss with a model; the Database
package only serves the parameter sets and measured points.
"""

from __future__ import annotations

from typing import Any, Literal

from aipe_magnetics_database.common.errors import AIPEMagneticsError, InvalidInputError
from aipe_magnetics_database.common.quantity import Quantity
from aipe_magnetics_database.common.results import EngineeringResult
from aipe_magnetics_database.database.query import _q

CAP_MATERIAL_LOSS = "aipe.magnetics.database.estimate_material_loss"


def estimate_material_loss(material: str, frequency: Any, flux_density_peak: Any, temperature: Any, *, waveform: str = "sinusoidal",
                           duty: float = 0.5, interpolate_temperature: bool = True, policy: Literal["reject", "warn"] = "reject",
                           volume: Any = None, catalog: Any | None = None) -> EngineeringResult:
    """Loss density (and loss for a given volume) with optional temperature interpolation between parameter sets.

    Without interpolation this is numerically identical to :func:`aipe_magnetics_design.api.estimate_core_loss`; the
    interpolated path is reported as such (sets, weights, warnings).
    """
    inputs = {"material": material, "frequency": frequency, "flux_density_peak": flux_density_peak, "temperature": temperature,
              "waveform": waveform, "duty": duty, "interpolate_temperature": interpolate_temperature, "policy": policy}
    try:
        from aipe_magnetics_design.engineering.loss_evaluator import FluxShape, LossEvaluator
        from aipe_magnetics_design.engineering.materials import evidence_sources, lookup_material
        record, props = lookup_material(material, catalog)
        f, b, t = _q(frequency, "Hz", "frequency"), _q(flux_density_peak, "T", "flux_density_peak"), _q(temperature, "K", "temperature")
        if f is None or b is None or t is None:
            raise InvalidInputError("frequency, flux_density_peak and temperature are required")
        shape = {"sinusoidal": lambda: FluxShape.sinusoid(), "triangular": lambda: FluxShape.triangular(duty),
                 "trapezoidal": lambda: FluxShape.trapezoidal(duty)}.get(waveform)
        if shape is None:
            raise InvalidInputError("waveform must be sinusoidal, triangular or trapezoidal (duty = rise fraction)")
        ev = LossEvaluator(record.id, props.steinmetz_parameter_sets).loss_density(f, b, t, shape(), interpolate_temperature=interpolate_temperature,
                                                                                  policy=policy)
        result = EngineeringResult(capability=CAP_MATERIAL_LOSS, inputs=inputs)
        result.add_value("loss_density", "Core loss density", Quantity(value=float(ev.loss_density), unit="W/m^3"), status="estimated")
        vol = _q(volume, "m^3", "volume")
        if vol is not None:
            result.add_value("core_loss", "Core loss for the given volume", Quantity(value=float(ev.loss_density) * vol, unit="W"), status="estimated")
        result.data.update({"model": ev.model, "parameter_sets": ev.sets, "weights": ev.weights, "interpolated": ev.interpolated})
        for w in ev.warnings:
            result.warn("loss_model_domain", w)
        if ev.interpolated:
            result.assume("temperature_interpolation", f"Loss density interpolated linearly in temperature between {ev.sets[0]} and {ev.sets[1]} "
                          f"(weights {ev.weights[0]:.2f}/{ev.weights[1]:.2f}).", "model_assumption", ["loss_density"])
        for s in evidence_sources(record):
            result.cite(s)
        result.limit("dc_bias_ignored", "Steinmetz/iGSE ignore DC bias and minor loops.")
    except AIPEMagneticsError as error:
        return EngineeringResult.rejected(CAP_MATERIAL_LOSS, error, inputs=inputs)
    from aipe_magnetics_design.verification.suite import load_bundled_registry
    model_id = "aipe.magnetics.model.steinmetz" if waveform == "sinusoidal" else "aipe.magnetics.model.igse"
    result.verification = load_bundled_registry().status_for(model_id, frequency=f, temperature=t, flux_density_peak=b, material=record.id,
                                                             excitation=waveform)
    return result


__all__ = ["CAP_MATERIAL_LOSS", "estimate_material_loss"]
