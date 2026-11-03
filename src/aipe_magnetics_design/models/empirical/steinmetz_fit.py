"""Classical Steinmetz fits to measured MagNet core-loss data (Design: model fitting).

Moved from ``aipe_magnetics.data.sources.princeton_magnet_db`` (v0.2): reading the MagNet databases is a Database
function (:func:`aipe_magnetics_database.data.sources.princeton_magnet_db.read_magnet_database`), fitting a model to
them is not. Fits are *derived data*: store them with ``basis: measurement_fit`` and the inputs they came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from aipe_magnetics_database.common.errors import DataIntegrityError, DataNotFoundError
from aipe_magnetics_database.data.sources.princeton_magnet_db import MagnetDatabase


@dataclass
class SteinmetzFit:
    material: str
    temperature_degC: float
    k: float
    alpha: float
    beta: float
    n_points: int
    frequency_range_Hz: tuple[float, float]
    flux_density_range_T: tuple[float, float]
    max_rel_error: float
    mean_abs_rel_error: float
    rms_log10_residual: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "material": self.material, "temperature_degC": self.temperature_degC,
            "k_W_per_m3": self.k, "alpha": self.alpha, "beta": self.beta, "n_points": self.n_points,
            "frequency_range_Hz": list(self.frequency_range_Hz), "flux_density_range_T": list(self.flux_density_range_T),
            "fit_metrics": {"max_rel_error": self.max_rel_error, "mean_abs_rel_error": self.mean_abs_rel_error,
                            "rms_log10_residual": self.rms_log10_residual},
        }


def fit_steinmetz(frequency: np.ndarray, flux_density: np.ndarray, loss_density: np.ndarray) -> tuple[float, float, float, dict[str, float]]:
    """Ordinary least squares in log space: ``log Pv = log k + alpha log f + beta log B``.

    Returns ``(k, alpha, beta, metrics)`` with k in W/m^3 for f in Hz and B in T. Requires at least 10
    points with positive values; raises :class:`DataIntegrityError` otherwise.
    """
    f, b, p = (np.asarray(frequency, float), np.asarray(flux_density, float), np.asarray(loss_density, float))
    mask = np.isfinite(f) & np.isfinite(b) & np.isfinite(p) & (f > 0) & (b > 0) & (p > 0)
    if mask.sum() < 10:
        raise DataIntegrityError(f"not enough valid points for a Steinmetz fit ({int(mask.sum())})")
    f, b, p = f[mask], b[mask], p[mask]
    design = np.column_stack([np.ones_like(f), np.log(f), np.log(b)])
    coefficients, *_ = np.linalg.lstsq(design, np.log(p), rcond=None)
    log_k, alpha, beta = (float(x) for x in coefficients)
    prediction = np.exp(design @ coefficients)
    rel = prediction / p - 1.0
    metrics = {"max_rel_error": float(np.max(np.abs(rel))), "mean_abs_rel_error": float(np.mean(np.abs(rel))),
               "rms_log10_residual": float(np.sqrt(np.mean((np.log10(prediction) - np.log10(p)) ** 2))), "n_points": int(mask.sum())}
    return float(np.exp(log_k)), alpha, beta, metrics


def fit_steinmetz_by_temperature(db: MagnetDatabase, *, frequency_range: tuple[float, float] | None = None,
                                 flux_density_range: tuple[float, float] | None = None,
                                 min_points: int = 30) -> list[SteinmetzFit]:
    """Fit one classical Steinmetz set per measured temperature from sinusoidal, zero-bias points."""
    mask = db.sinusoidal_zero_bias()
    f, b, t, p = db.column("Frequency"), db.column("Flux_Density"), db.column("Temperature"), db.column("Power_Loss")
    if frequency_range:
        mask &= (f >= frequency_range[0]) & (f <= frequency_range[1])
    if flux_density_range:
        mask &= (b >= flux_density_range[0]) & (b <= flux_density_range[1])
    fits: list[SteinmetzFit] = []
    for temperature in sorted(set(np.round(t[mask], 0).tolist())):
        sel = mask & (np.round(t, 0) == temperature)
        if sel.sum() < min_points:
            continue
        k, alpha, beta, metrics = fit_steinmetz(f[sel], b[sel], p[sel])
        fits.append(SteinmetzFit(material=db.material, temperature_degC=float(temperature), k=k, alpha=alpha, beta=beta,
                                 n_points=metrics["n_points"], frequency_range_Hz=(float(f[sel].min()), float(f[sel].max())),
                                 flux_density_range_T=(float(b[sel].min()), float(b[sel].max())),
                                 max_rel_error=metrics["max_rel_error"], mean_abs_rel_error=metrics["mean_abs_rel_error"],
                                 rms_log10_residual=metrics["rms_log10_residual"]))
    if not fits:
        raise DataNotFoundError(f"{db.material}: no temperature group with at least {min_points} sinusoidal zero-bias points")
    return fits


__all__ = ["SteinmetzFit", "fit_steinmetz", "fit_steinmetz_by_temperature"]
