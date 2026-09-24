"""(d) Atomistic smoke run: Si(001), [110] azimuth, a/2 step with edges parallel to the beam,
specular (0,0,8) condition at 200 keV (theta_ext computed with the mean inner potential of the
Kirkland potential actually used, 13.903 V), Kirkland independent-atom potential, static lattice,
0.13 A-class pixels, 1/4 of the lattice period per slice, complex64, 4 threads.

UNVALIDATED (engine.VALIDATION_STATUS): the atomistic fixed-beam translation check of rung 3
(docs/05 4.4 item 3, required before step phases) has not passed and the abTEM cross-check was not
run (rung 2 test R2-A passes on a continuum potential), so the step phase printed here is reported
next to the geometric expectation and NOT asserted against it. Asserted: it finishes in under 2 minutes on this CPU, the geometry and band assertions pass, the
exit wave is finite and on the declared plane, and a manifest is written (to a temporary
outputs/ directory)."""
import json
import resource
import time

import numpy as np

from smoke_case import smoke_setup, terrace_regions
from reflection_holo.forward.multislice import (PLANE_TEXT, geometric_step_phase, simulate,
                                                terrace_step_phase, wrap)


def test_smoke_atomistic_a2_step_0008(tmp_path):
    t0 = time.perf_counter()
    S = smoke_setup(widths=(8, 8))
    t_build = time.perf_counter() - t0
    waves, mpath = simulate(S["cell"], potential=S["potential"], beam=S["beam"],
                            params=S["params"], realisations=1, seed=None,
                            outputs_root=tmp_path / "outputs", run_name="m2_smoke_a2_0008",
                            save_waves=False, config=None, input_paths=[],
                            caller_record=None)
    t_total = time.perf_counter() - t0
    ew = waves[0]
    lo, up = terrace_regions(S["cell"], 0.5)
    lam = ew.metadata["beam"]["wavelength_A"]
    geo = geometric_step_phase(S["h"], S["theta"], lam)
    rows = [terrace_step_phase(ew, theta_out_ext_rad=S["theta"], aperture_radius_per_A=ap,
                               upper_y_range_A=up, lower_y_range_A=lo) for ap in (0.1, 0.2)]
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    p = S["params"]
    print(f"\nSMOKE: {len(S['cell'].Z)} atoms, grid {p.nx} x {p.ny} (dx {ew.dx_A:.4f}, dy "
          f"{ew.dy_A:.4f} A), {ew.metadata['slices']['n_slices']} slices of {p.dz_A:.4f} A, "
          f"theta_ext {S['theta'] * 1e3:.4f} mrad, MIP {S['V0_mip']:.3f} V")
    print(f"SMOKE: build {t_build:.1f} s, propagation {ew.metadata['timing_s']['propagation']:.1f}"
          f" s, total {t_total:.1f} s, peak RSS {rss:.0f} MB")
    print(f"SMOKE: geometric a/2 step phase {geo:+.4f} rad (wrapped {wrap(geo):+.4f})")
    for r in rows:
        print(f"SMOKE: aperture {r['aperture_radius_per_A']} 1/A: Delta_phi {r['delta_phi_rad']:+.4f}"
              f" rad, difference to geometric {wrap(r['delta_phi_rad'] - geo):+.4f} rad, "
              f"|A_up| {r['amplitude_upper']:.4f}, |A_low| {r['amplitude_lower']:.4f}")
    print(f"SMOKE: manifest {mpath}")
    assert t_total < 120.0
    assert ew.plane == PLANE_TEXT and np.all(np.isfinite(ew.psi))
    assert all(v["passed"] for k, v in ew.metadata["geometry_checks"].items() if k != "label")
    assert "UNVALIDATED" in ew.metadata["validation_status"]
    m = json.loads(mpath.read_text())
    assert m["engines"]["abTEM (Kirkland parameterisation functions only)"]["version"] == "1.0.10"
