"""Retrieve measured core-loss data from AIPE-Magnetics-Database and consume it in AIPE-Magnetics-Design.

1. Database: find the Princeton MagNet measurement table of TDK N87 and read the sinusoidal, zero-DC-bias rows
   at 90 degC (original measured values, SI units, with provenance and licence).
2. Design: fit a classical Steinmetz set to those rows (a *derived* result, labelled as such) and compare it with
   the Design core-loss API, which uses the curated catalogue parameter sets of the same material.

Run: ``python examples/database_to_design.py``
"""

from __future__ import annotations

import json

import numpy as np

import aipe_magnetics_database.api as db
import aipe_magnetics_design.api as design
from aipe_magnetics_design.models.empirical.steinmetz_fit import fit_steinmetz


def run(material: str = "TDK N87", temperature: str = "90 degC") -> dict:
    hits = db.find_measurements(material=material, quantity="core_loss", data_class="experimental_measurement",
                                temperature=temperature, waveform="sinusoidal")
    record_id = hits[0]["id"]
    table = db.get_table(record_id, temperature=temperature, waveform="sinusoidal", dc_bias="0 A/m",
                         frequency="50 kHz..500 kHz", flux_density="0.01 T..0.3 T")
    cols = [c["name"] for c in table["columns"]]
    rows = np.array([[r[cols.index("frequency")], r[cols.index("flux_density_peak")], r[cols.index("loss_density")]] for r in table["rows"]])
    k, alpha, beta, metrics = fit_steinmetz(rows[:, 0], rows[:, 1], rows[:, 2])
    point = {"frequency": {"value": 100, "unit": "kHz"}, "flux_density_peak": {"value": 100, "unit": "mT"},
             "temperature": {"value": 90, "unit": "degC"}}
    estimate = design.estimate_core_loss(material="N87", **point)
    fitted = k * 100e3 ** alpha * 0.1 ** beta
    return {
        "database_record": record_id,
        "license": db.provenance(record_id)["license"],
        "rows_used": len(rows),
        "derived_steinmetz_fit": {"k_W_per_m3": k, "alpha": alpha, "beta": beta, "fit_metrics": metrics,
                                  "note": "derived from measurements by this example; not a manufacturer value"},
        "fit_at_100kHz_100mT_W_per_m3": fitted,
        "design_api_estimate_W_per_m3": estimate.values["loss_density"].quantity.value if estimate.status == "ok" else None,
        "design_api_status": estimate.status,
        "design_api_model": estimate.model.id if estimate.model else None,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
