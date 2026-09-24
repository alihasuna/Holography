"""Command line of the pipeline.

    python -m reflection_holo.pipeline run --config C --out D [--variant V] [--allow-no-git]
                                           [--members-dir M]
    python -m reflection_holo.pipeline dry-run --config C [--variant V] [--calibrate-cpu]
    python -m reflection_holo.pipeline list-inputs --config C [--variant V]
    python -m reflection_holo.pipeline members --config C [--variant V]
    python -m reflection_holo.pipeline run-member --config C --member K --out D [--variant V]
                                                  [--allow-no-git]

Convergence ensembles (report E3; PROJECT_INPUT item 3): ``members`` prints the job list as JSON
(n_members and one record per incidence direction); ``run-member`` runs ONE member's engine run
into an empty directory (exit waves always saved, engine manifest, member.json with the SHA-256 of
every file); ``run --members-dir M`` assembles every member job found under M/*/member.json (same
resolved configuration and quadrature; each member exactly once) instead of running the members.

Exit status: 0 success; 2 usage; 3 configuration refused (a missing PROJECT_INPUT, an unregistered
stand-in, a schema error); 4 engine unavailable; 5 output directory not empty; 6 git state
unavailable (refused before any computation unless --allow-no-git). A refusal by the model scope
(the geometric engine's B4 check) is a configuration refusal (3); a multislice run or dry run whose
array backend is unusable (cupy not importable or no GPU) exits 4 (audit A3 m5, m8). A reader that
closes the pipe early (``... | head``) ends the command quietly with status 0 (A3 M4).

A run that returns no height (for example because the no-step control failed or was not performed)
still exits 0: the refusal is the result, printed first as "NO HEIGHT: ..." and recorded in
summary.json["height_verdict"].
"""
from __future__ import annotations

import argparse
import json
import sys

from reflection_holo.forward.geometric import OutsideB4ScopeError
from reflection_holo.io.config import ConfigError, MissingProjectInputError
from reflection_holo.pipeline.config import (format_inputs, list_inputs, load_pipeline_file,
                                             read_pipeline_file)
from reflection_holo.pipeline.engines import EngineUnavailableError
from reflection_holo.provenance.manifest import GitStateError


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m reflection_holo.pipeline",
                                description="Reflection-mode dark-field holography pipeline "
                                            "(200 keV; no default replaces a PROJECT_INPUT).")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="run the pipeline")
    r.add_argument("--config", required=True)
    r.add_argument("--out", required=True, help="output directory (created; must be empty)")
    r.add_argument("--variant", default=None)
    r.add_argument("--allow-no-git", action="store_true",
                   help="record, instead of refusing, a missing git state in the manifest")
    r.add_argument("--members-dir", default=None,
                   help="convergence ensemble: assemble the member jobs under this directory "
                        "(written by run-member) instead of running the members")
    me = sub.add_parser("members", help="convergence ensemble: print the member job list (JSON)")
    me.add_argument("--config", required=True)
    me.add_argument("--variant", default=None)
    rm = sub.add_parser("run-member", help="convergence ensemble: run one member's engine run")
    rm.add_argument("--config", required=True)
    rm.add_argument("--member", required=True, type=int)
    rm.add_argument("--out", required=True, help="output directory (created; must be empty)")
    rm.add_argument("--variant", default=None)
    rm.add_argument("--allow-no-git", action="store_true",
                    help="record, instead of refusing, a missing git state")
    d = sub.add_parser("dry-run", help="validate the configuration and print resource estimates")
    d.add_argument("--config", required=True)
    d.add_argument("--variant", default=None)
    d.add_argument("--calibrate-cpu", action="store_true",
                   help="multislice: measure the FFT and potential costs on this machine")
    d.add_argument("--report-json", default=None,
                   help="also write the full dry-run report (with the configuration's path and "
                        "SHA-256) to this JSON file; the Alliance kit reads the GPU memory need "
                        "from it (kit.py --gpu-mem-from-dry-run)")
    li = sub.add_parser("list-inputs", help="show every PROJECT_INPUT and its status")
    li.add_argument("--config", required=True)
    li.add_argument("--variant", default=None)
    return p


def _human_bytes(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TiB"


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "list-inputs":
            data = read_pipeline_file(args.config)
            print(f"purpose: {data.get('purpose')}")
            print(format_inputs(list_inputs(data, variant=args.variant)))
            try:
                load_pipeline_file(args.config, variant=args.variant)
                print("run-level gate: PASS")
            except ConfigError as exc:
                print(f"run-level gate: REFUSED ({type(exc).__name__}): {exc}")
                return 3
            return 0
        cfg = load_pipeline_file(args.config, variant=args.variant)
        if args.command == "members":
            from reflection_holo.pipeline.convergence import members_table
            print(json.dumps(members_table(cfg), indent=1, default=str))
            return 0
        if args.command == "run-member":
            from reflection_holo.pipeline.convergence import run_member_job
            from reflection_holo.pipeline.run import OutputDirectoryError
            try:
                rec = run_member_job(cfg, args.member, args.out, allow_no_git=args.allow_no_git)
            except OutputDirectoryError as exc:
                print(f"refused: {exc}", file=sys.stderr)
                return 5
            print(f"member {rec['member']['index']} of {rec['quadrature']['n_members']}: "
                  f"glancing angle {rec['member']['glancing_angle_rad'] * 1e3:.6f} mrad, "
                  f"y direction cosine {rec['member']['direction_cosine_y']:.3e}, weight "
                  f"{rec['member']['weight']:.6g}; {len(rec['exit_waves'])} exit wave(s) and "
                  f"member.json in {args.out}")
            return 0
        if args.command == "dry-run":
            from reflection_holo.pipeline.estimates import dry_run
            rep = dry_run(cfg, calibrate_cpu=args.calibrate_cpu)
            if args.report_json:
                import hashlib
                from pathlib import Path
                cpath = Path(args.config).resolve()
                Path(args.report_json).write_text(json.dumps(dict(
                    schema="reflholo_pipeline_dry_run_report/1", config_path=str(cpath),
                    config_sha256=hashlib.sha256(cpath.read_bytes()).hexdigest(),
                    variant=args.variant, report=rep), indent=1, default=str))
            print(f"purpose: {cfg.purpose}")
            print(f"configuration valid (run level); engine {rep['engine']}; glancing angle "
                  f"{rep['glancing_angle_mrad']:.6f} mrad "
                  f"({cfg.glancing_angle.get('rule') or 'value'}; V0 {cfg.glancing_angle.get('V0_V')} V)")
            if rep["engine"] == "geometric":
                gm = rep["geometric"]
                print(f"exit plane {gm['exit_plane_shape']} px, field {gm['field_length_A']:.1f} A "
                      f"along the beam, memory ~{_human_bytes(rep['total_memory_bytes'])}, "
                      f"~{gm['estimated_seconds']:.1f} s (scaled from the smoke demo)")
            else:
                if not rep["multislice_available"]:
                    print(f"multislice engine NOT available: {rep['multislice_status']}")
                    return 4
                est = rep["multislice"]
                print(f"cell {rep['cell']}")
                print(f"grid {est['grid']}, slices {est['n_slices']}, atoms {est['n_atoms']}, "
                      f"realisations {est['realisations']}")
                mb = est["memory_bytes"]
                print(f"memory per realisation ~{_human_bytes(mb['total'])} (numpy backend, host); "
                      f"cupy backend: device ~{_human_bytes(mb['device_peak_cupy'])} (lower bound: "
                      f"library workspaces not included), host ~{_human_bytes(mb['host_peak_cupy'])}")
                if "cpu" in est:
                    print(f"CPU (measured here) ~{est['cpu']['seconds_total']:.0f} s")
                print(f"GPU (ASSUMPTION model, not measured) ~{est['gpu']['seconds_total']:.0f} s")
            print(json.dumps(rep, indent=1, default=str)[:4000])
            be = rep.get("backend")
            if be is not None and not be["available"]:
                print(f"multislice backend {be['name']} NOT available: {be['status']} (the "
                      f"geometry checks above ran; a run would be refused)")
                return 4
            return 0
        from reflection_holo.pipeline.run import OutputDirectoryError, run
        try:
            s = run(cfg, args.out, allow_no_git=args.allow_no_git,
                    members_dir=args.members_dir)
        except OutputDirectoryError as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 5
        print(s["banner"])
        print(f"engine: {s['engine'].get('label')}")
        verdict = s["height_verdict"]
        bar = "*" * 100
        if verdict["heights_returned"] == 0:
            print(bar)
            print(verdict["line"])
            print(bar)
        else:
            print(f"heights: {verdict['line']}")
        for st in s["quantification"]["steps"]:
            h = st.get("height")
            txt = (f"h = {h['h_A']:+.4f} +- {h['sigma_h_A']:.4f} A (branch {h['branch_index']}, "
                   f"wrap period {h['wrap_period_A']:.4f} A)" if h else f"no height: {st.get('reason')}")
            print(f"step field terraces {st['from_field_terrace']}->{st['to_field_terrace']} "
                  f"({st['type']}): {txt}")
        if "feature" in s:                                   # feature path (agent T2)
            q = s["quantification"]
            m = q["measurable"]
            iso = m.get("isolated_reliable_on_footprint") or {}
            print(f"feature {s['feature']['shape']['sub_kind']}: measurable {m['measurable_px']} of "
                  f"{m['detector_px']} detector px; ring footprint: {m['measurable_footprint_px']} "
                  f"of {m['footprint_source_px']} lit footprint px measurable; isolated reliable "
                  f"footprint px (height modulo h_2pi only): {iso.get('n_px', 0)}")
            for name, c in q["profile_cuts"].items():
                f = (lambda v: "-" if v is None else f"{v:.4f}")
                print(f"profile {name}: {c['n_measurable']} of {c['n_px']} px measurable "
                      f"({c['n_measurable_on_footprint']} of {c['n_on_footprint']} on the "
                      f"footprint); rms vs layer {f(c['rms_vs_layer_A'])} A, vs continuous "
                      f"{f(c['rms_vs_continuous_A'])} A")
            print(f"resolution: {q['resolution']['summary']}")
        deg = s["quantification"].get("sign_degeneracy") or {}
        if any(p.get("degenerate_single_step") for p in deg.get("pairs", [])):
            print(f"note: {deg['note']}")
        c = s["quantification"]["no_step_control"]
        print(f"no-step control: {'PASS' if c.get('passed') else 'NOT PASSED or not performed'} "
              f"{c}")
        print(f"outputs in {args.out}: summary.json, manifest.json, arrays.npz "
              f"{' '.join(s['quicklooks'])}")
        return 0
    except MissingProjectInputError as exc:
        print(f"REFUSED (missing PROJECT_INPUT, docs/06 items {exc.items}): {exc}", file=sys.stderr)
        return 3
    except ConfigError as exc:
        print(f"REFUSED (configuration): {exc}", file=sys.stderr)
        return 3
    except EngineUnavailableError as exc:
        print(f"REFUSED (engine): {exc}", file=sys.stderr)
        return 4
    except GitStateError as exc:
        print(f"REFUSED (git state, before any computation): {exc}", file=sys.stderr)
        return 6
    except OutsideB4ScopeError as exc:
        print(f"REFUSED (model scope B4, configuration): {exc}", file=sys.stderr)
        return 3


def _entry() -> int:
    try:
        return main()
    except BrokenPipeError:
        # the reader closed the pipe (e.g. `| head`): stop writing quietly (audit A3 M4)
        import os
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(_entry())
