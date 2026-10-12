#!/usr/bin/env python3
"""Wrap an experimental object hologram and its vacuum reference hologram as a `hologram` stage folder, so
holo_recon.py reconstructs them with exactly the code used for simulations (spec §5.7: one code path).

Runs in: em-holography (HyperSpy 2.4 / RosettaSciIO for .dm3/.dm4/.emd/.tif/.hspy; numpy for .npy).

    gemicro run --kind process --name import-holo --input raw/<session>/obj.dm4 --input raw/<session>/ref.dm4 \
        --params params/import_holograms.yaml --output derived/hologram-exp -- \
        /opt/envs/em-holography/bin/python code/import_experimental_holograms.py \
        --params params/import_holograms.yaml --object raw/<session>/obj.dm4 --reference raw/<session>/ref.dm4 \
        --output derived/hologram-exp

raw/ is only read. The arrays are transposed to this pipeline's [ix, iy] order (HyperSpy stores [row = y,
column = x]). The pixel size comes from the file's axes unless pixel_size_A is set, in which case the file
value is still recorded next to the override. No truth arrays are written: holo_validate.py cannot run on
experimental data; the controls are the vacuum-flatness and mask-sensitivity numbers of holo_recon.py.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402

LENGTH_TO_A = {"nm": 10.0, "Å": 1.0, "A": 1.0, "angstrom": 1.0, "pm": 0.01, "µm": 1e4, "um": 1e4}


def load_image(path):
    """(array [ix, iy] float64, pixel size in Å or None, note)."""
    p = Path(path)
    if p.suffix.lower() == ".npy":
        return np.load(p, allow_pickle=False).astype(np.float64), None, ".npy: no pixel size in the file"
    import hyperspy.api as hs
    s = hs.load(str(p), lazy=False)
    if isinstance(s, list):
        raise SystemExit(f"{p} holds {len(s)} signals; export the hologram alone")
    if s.axes_manager.navigation_dimension != 0 or s.axes_manager.signal_dimension != 2:
        raise SystemExit(f"{p}: expected one 2-D image, got navigation {s.axes_manager.navigation_shape} "
                         f"signal {s.axes_manager.signal_shape}")
    ax = s.axes_manager.signal_axes  # [x (columns), y (rows)]
    units = {str(a.units) for a in ax}
    pix = None
    if len(units) == 1 and next(iter(units)) in LENGTH_TO_A:
        f = LENGTH_TO_A[next(iter(units))]
        pix = (float(ax[0].scale) * f, float(ax[1].scale) * f)
    return np.asarray(s.data, dtype=np.float64).T, pix, f"units {sorted(units)}, scales {[a.scale for a in ax]}"


def main(argv=None):
    ap = hc.common_cli("Experimental holograms -> hologram stage folder (env: em-holography)",
                       [("--object", "object hologram (.dm3/.dm4/.emd/.tif/.hspy/.npy)"),
                        ("--reference", "vacuum reference hologram, same biprism/exposure/detector region")])
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    P = hc.Section(raw)
    energy = P.num("energy_keV", lo=1.0)
    pix_override = P.vec("pixel_size_A", 2, allow_none=True)
    cpe = P.num("counts_per_electron", lo=0.0, lo_open=True)
    crop = P.vec("crop_px", 4, allow_none=True, integer=True)
    P.finish()
    obj, pix_o, note_o = load_image(a.object)
    ref, pix_r, note_r = load_image(a.reference)
    if obj.shape != ref.shape:
        raise SystemExit(f"object {obj.shape} and reference {ref.shape} differ in shape")
    if pix_o and pix_r and not np.allclose(pix_o, pix_r, rtol=1e-6):
        raise SystemExit(f"object pixel {pix_o} Å and reference pixel {pix_r} Å differ")
    pix = tuple(pix_override) if pix_override is not None else pix_o
    if pix is None:
        raise SystemExit("no pixel size in the files: set pixel_size_A (from the calibration, /calibrate)")
    if crop is not None:
        x0, x1, y0, y1 = crop
        obj, ref = obj[x0:x1, y0:y1], ref[x0:x1, y0:y1]
    with hc.Output(a.output, a.overwrite) as out:
        units = f"counts ({cpe} per electron)"
        out.save_array("hologram", obj, units=units, axes=["x", "y"], sampling_A=pix,
                       description=f"experimental object hologram from {a.object}")
        out.save_array("reference_hologram", ref, units=units, axes=["x", "y"], sampling_A=pix,
                       description=f"experimental vacuum reference hologram from {a.reference}")
        out.save_array("overlap_mask", np.ones(obj.shape, bool), units="bool", axes=["x", "y"], sampling_A=pix,
                       description="whole field (crop_px selects the overlap region)")
        physics = {"energy_keV": energy, "wavelength_A": hc.wavelength_A(energy), "detector_pixel_A": list(pix),
                   "pixel_size_source": "parameter override" if pix_override is not None else "file axes",
                   "file_pixel_A": {"object": pix_o, "reference": pix_r}, "file_notes": [note_o, note_r],
                   "detector": {"counts_per_electron": cpe}, "crop_px": crop, "simulated": False}
        summary = {"shape": list(obj.shape), "pixel_A": list(pix), "mean_counts_object": float(obj.mean()),
                   "mean_counts_reference": float(ref.mean()), "plots": []}
        prov = hc.provenance(sys.argv, a.params, {"object": a.object, "reference": a.reference})
        hc.write_sidecar(out, "hologram", raw, prov, physics, summary)
        out.publish()
    hc.print_summary("imported holograms", summary, out.final, out.files)


if __name__ == "__main__":
    main()
