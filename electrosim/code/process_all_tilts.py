#!/usr/bin/env python3
"""Batch: image wave -> holograms -> reconstruction -> step heights for every tilt of an exit-wave tilt series.

Runs in: em-holography (CPU). One gemicro record for the whole series:

    gemicro run --kind analysis --name tilt-series-holo --input sims/tilt-series/exit_waves.npy \
        --params params/process_all_tilts.yaml --output derived/tilt-series-holo -- \
        /opt/envs/em-holography/bin/python code/process_all_tilts.py --params params/process_all_tilts.yaml \
        --exit-wave sims/tilt-series --slab sims/slab-reflection --output derived/tilt-series-holo

The parameter file holds one section per stage, exactly as the single-stage parameter files, except that
`specular_filter` has no tilt_select_mrad / tilt_tolerance_mrad (set per tilt here) and `step_height` has
theta_ext_mrad: null (the angle of each tilt's specular beam is read from its image-wave record; θx < 0 sends the
beam onto the (1,-1,1) surface, outward normal +x, from the vacuum side). Writes tilt_<θx>_<θy>/{image-wave, hologram,
holo-recon, step-height}/ and tilt_series_summary.json (+ a plot of Δφ against tilt).

Replaces the si110 batch driver (audit M10: it called a renamed script, used a hard-coded HPC path and
expected one folder per tilt that the runner never wrote; it exited 0 after failing).
"""

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402
import hologram_formation  # noqa: E402
import holo_recon  # noqa: E402
import specular_filter  # noqa: E402
import step_height_reflection_formula as shf  # noqa: E402


def sub_run(parent, rel, stage, module_run, params, argv, args, inputs):
    with hc.Output(parent.staging / rel) as out:
        res = module_run(hc.Section(params), *args, out)
        physics, summary = res[0], res[1]
        hc.write_sidecar(out, stage, params, hc.provenance(argv, argv_params(argv), inputs), physics, summary)
        out.publish()
    return out.final, physics, summary


def argv_params(argv):
    return argv[argv.index("--params") + 1] if "--params" in argv else ""


def main(argv=None):
    ap = hc.common_cli("Tilt-series holography batch (env: em-holography)",
                       [("--exit-wave", "output folder of multislice_tilt_series_runner.py"),
                        ("--slab", "output folder of si110_cleave_slab_generator.py")])
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    P = hc.Section(raw)
    sel = P.req("tilts_mrad")
    tol = P.num("tilt_tolerance_mrad", lo=0.0, lo_open=True)
    sections = {k: P.req(k) for k in ("specular_filter", "hologram", "recon", "step_height")}
    P.finish()
    for k in ("tilt_select_mrad", "tilt_tolerance_mrad"):
        if k in sections["specular_filter"]:
            raise hc.ParamError(f"specular_filter.{k} is set per tilt by this script; remove it")
    if sections["step_height"] is not None and sections["step_height"].get("theta_ext_mrad") is not None:
        raise hc.ParamError("step_height.theta_ext_mrad must be null here: the angle of each tilt's specular beam is "
                            "read from its image-wave record")

    ew = hc.Stage(a.exit_wave, "exit_wave")
    if not ew.has("tilts_mrad"):
        raise SystemExit(f"{a.exit_wave} is not a tilt series (no tilts_mrad.npy)")
    available = np.asarray(ew.array("tilts_mrad"), float).tolist()
    tilts = available if sel == "all" else sel
    if not isinstance(tilts, list) or not tilts:
        raise hc.ParamError("tilts_mrad must be 'all' or a list of [θx, θy]")

    with hc.Output(a.output, a.overwrite) as out:
        argv_full = sys.argv if argv is None else ["process_all_tilts.py"] + list(argv)
        rows = []
        for t in tilts:
            tag = f"tilt_{t[0]:+.3f}_{t[1]:+.3f}".replace("+", "p").replace("-", "m")
            sf = copy.deepcopy(sections["specular_filter"])
            sf["tilt_select_mrad"] = [float(t[0]), float(t[1])]
            sf["tilt_tolerance_mrad"] = tol
            img, ph_img, _ = sub_run(out, f"{tag}/image-wave", "image_wave", specular_filter.run, sf, argv_full,
                                     (a.exit_wave, a.slab), {"exit_wave": ew.sidecar_path})
            holo, ph_h, _ = sub_run(out, f"{tag}/hologram", "hologram", hologram_formation.run,
                                    copy.deepcopy(sections["hologram"]), argv_full, (img,), {})
            rec, ph_r, sm_r = sub_run(out, f"{tag}/holo-recon", "recon", holo_recon.run,
                                      copy.deepcopy(sections["recon"]), argv_full, (holo,), {})
            row = {"tilt_mrad": [float(t[0]), float(t[1])], "folder": tag,
                   "carrier_inv_A": ph_r["carrier"]["q_refined_inv_A"], "contrast_ref": ph_r["contrast_reference_median"],
                   "residues": ph_r["residues_in_overlap"]}
            if sections["step_height"] is not None:
                sh = copy.deepcopy(sections["step_height"])
                sh["theta_ext_mrad"] = None
                _, ph_s, _ = sub_run(out, f"{tag}/step-height", "step_height", shf.run, sh, argv_full,
                                     (rec, a.slab), {})
                row["theta_ext_mrad"] = ph_s["theta_ext_mrad"]
                row["wrap_period_A"] = ph_s["wrap_period_A"]
                row["steps"] = [{k: s.get(k) for k in ("from", "to", "delta_phi_wrapped_rad", "sigma_rad", "result",
                                                      "height_A", "true_height_A", "true_delta_phi_wrapped_rad")}
                                for s in ph_s["steps"]]
            rows.append(row)
            print(f"   {tag}: done")

        plots = []
        plt = hc._plt()
        if plt is not None and rows and "steps" in rows[0]:
            fig, ax = plt.subplots(figsize=(6.4, 4.2))
            th = [r["theta_ext_mrad"] for r in rows]
            for k in range(len(rows[0]["steps"])):
                meas = [r["steps"][k]["delta_phi_wrapped_rad"] for r in rows]
                sig = [r["steps"][k]["sigma_rad"] for r in rows]
                ln = ax.errorbar(th, meas, yerr=sig, fmt="o-", ms=3, label=f"step {rows[0]['steps'][k]['from']}->"
                                                                          f"{rows[0]['steps'][k]['to']}")
                tr = [r["steps"][k].get("true_delta_phi_wrapped_rad") for r in rows]
                if all(v is not None for v in tr):
                    ax.plot(th, tr, ":", color=ln[0].get_color())
            ax.set_xlabel("θ_ext of the specular beam (mrad)")
            ax.set_ylabel("Δφ wrapped (rad)")
            ax.set_title("measured (points) vs kinematic geometric phase (dotted)", fontsize=9)
            ax.legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(out.path("step_phase_vs_tilt.png"), dpi=140)
            plt.close(fig)
            plots.append("step_phase_vs_tilt.png")
        out.save_json("tilt_series_summary.json", rows)
        summary = {"tilts": len(rows), "folders": [r["folder"] for r in rows], "plots": plots}
        hc.write_sidecar(out, "tilt_series_holo", raw, hc.provenance(argv_full, a.params, {"exit_wave": ew.sidecar_path}),
                         {"rows": rows}, summary)
        out.publish()
    hc.print_summary("tilt-series holography", summary, out.final, out.files)


if __name__ == "__main__":
    main()
