"""End-to-end through the command-line scripts with the SHIPPED parameter files (small synthetic exit wave).

No GPU and no abTEM: the exit-wave stage is written by the test. Needs PyYAML and scikit-image (em-holography);
HoloSpy is used when importable, otherwise the numpy engine with the same tanh aperture.
"""

import json

import numpy as np

import _helpers


def _synthetic_exit_wave(folder):
    n, d = (256, 256), (0.1, 0.1)
    phi = _helpers.smooth_step(n, d, 10.0, 0.4, 1.2) - _helpers.smooth_step(n, d, 20.0, 0.4, 1.2)
    amp = 1.0 - 0.1 * phi / 1.2
    return _helpers.write_exit_wave_stage(folder, amp * np.exp(1j * phi), d, gt=phi)


def _params(tmp, name, edits):
    d = _helpers.load_yaml(name)
    for path, value in edits.items():
        node = d
        keys = path.split(".")
        for k in keys[:-1]:
            node = node[k]
        assert keys[-1] in node, f"{name}: {path} is not a key of the shipped file"
        node[keys[-1]] = value
    return _helpers.write_yaml(tmp / name, d)


def _check(proc):
    assert proc.returncode == 0, f"exit {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    return proc


def test_pipeline_and_controls_through_the_cli(tmp_path):
    _helpers.need("yaml")
    _helpers.need("skimage")
    has_holospy = True
    try:
        _helpers.need("holospy")
    except Exception:
        has_holospy = False
    ew = _synthetic_exit_wave(tmp_path / "sims" / "exit-wave")
    sf = _params(tmp_path, "specular_filter.yaml", {})
    hg = _params(tmp_path, "hologram.yaml", {})
    engine = {} if has_holospy else {"engine": "numpy"}
    rc = _params(tmp_path, "holo.yaml", engine)
    va = _params(tmp_path, "validate.yaml", {"edge_margin_A": 2.0, "profile_edges": {"enabled": False}})
    vc = _params(tmp_path, "validate_control.yaml", {"edge_margin_A": 2.0, "profile_edges": {"enabled": False}})
    d = tmp_path / "derived"
    _check(_helpers.run_script("specular_filter.py", "--params", sf, "--exit-wave", ew, "--output", d / "image-wave"))
    p = _check(_helpers.run_script("hologram_formation.py", "--params", hg, "--image-wave", d / "image-wave",
                                   "--output", d / "hologram"))
    assert "pixels_per_fringe" in p.stdout
    _check(_helpers.run_script("holo_recon.py", "--params", rc, "--hologram", d / "hologram", "--output", d / "rec"))
    v = _check(_helpers.run_script("holo_validate.py", "--params", va, "--recon", d / "rec", "--hologram",
                                   d / "hologram", "--exit-wave", ew, "--output", d / "val"))
    assert "PASS as expected" in v.stdout
    res = json.loads((d / "val" / "validate.json").read_text())
    assert res["physics"]["comparisons"]["T_holo"]["ncc"] > 0.97
    assert abs(res["physics"]["comparisons"]["T_holo"]["slope"] - 1) < 0.03
    holo = json.loads((d / "hologram" / "hologram.json").read_text())["physics"]["contrast"]
    assert abs(holo["measured_vacuum_contrast_clean_reference"] / holo["predicted_vacuum_contrast"] - 1) < 0.01

    for ctl in ("holo_control_no_reference.yaml", "holo_control_wrong_sideband.yaml"):
        cp = _params(tmp_path, ctl, engine)
        name = ctl.replace(".yaml", "")
        _check(_helpers.run_script("holo_recon.py", "--params", cp, "--hologram", d / "hologram",
                                   "--output", d / name))
        cv = _check(_helpers.run_script("holo_validate.py", "--params", vc, "--recon", d / name, "--hologram",
                                        d / "hologram", "--output", d / f"val-{name}"))
        assert "FAIL as expected" in cv.stdout, cv.stdout
        r = json.loads((d / f"val-{name}" / "validate.json").read_text())["physics"]["comparisons"]
        if "wrong_sideband" in ctl:
            assert r["T_holo"]["slope"] < -0.95
        else:
            assert r["residual_vs_injected_distortion_ncc"] > 0.9

    # a validation that expected "pass" on a control must exit non-zero
    bad = _helpers.run_script("holo_validate.py", "--params", va, "--recon", d / "holo_control_wrong_sideband",
                              "--hologram", d / "hologram", "--output", d / "val-mismatch")
    assert bad.returncode == 3

    ov = _params(tmp_path, "output_validator.yaml", {})
    chk = _check(_helpers.run_script("output_validator.py", "--params", ov, "--stage",  # (ew is synthetic: no plots)
                                     d / "image-wave", "--stage", d / "hologram", "--stage", d / "rec",
                                     "--stage", d / "val", "--output", d / "check"))
    assert "all_ok  : True" in chk.stdout


def test_unknown_parameter_is_refused(tmp_path):
    _helpers.need("yaml")
    ew = _synthetic_exit_wave(tmp_path / "ew")
    d = _helpers.load_yaml("specular_filter.yaml")
    d["objective"]["radius_mrd"] = 6.0  # typo
    p = _helpers.write_yaml(tmp_path / "sf.yaml", d)
    r = _helpers.run_script("specular_filter.py", "--params", p, "--exit-wave", ew, "--output", tmp_path / "o")
    assert r.returncode != 0 and "radius_mrd" in r.stderr
    assert not (tmp_path / "o").exists()  # a failed run leaves no output folder or staging behind


def test_too_few_pixels_per_fringe_is_refused(tmp_path):
    _helpers.need("yaml")
    ew = _synthetic_exit_wave(tmp_path / "ew")
    sf = _params(tmp_path, "specular_filter.yaml", {})
    _check(_helpers.run_script("specular_filter.py", "--params", sf, "--exit-wave", ew, "--output", tmp_path / "i"))
    hg = _params(tmp_path, "hologram.yaml", {"biprism.fringe_spacing_A": 0.5})  # 2.5 px per fringe
    r = _helpers.run_script("hologram_formation.py", "--params", hg, "--image-wave", tmp_path / "i",
                            "--output", tmp_path / "h")
    assert r.returncode != 0 and "pixels per fringe" in r.stderr


def test_specular_spot_is_at_2_sin_theta_over_lambda_and_steps_need_it(tmp_path):
    _helpers.need("yaml")
    import math as m
    import holo_common as hc
    import step_height_reflection_formula as shf
    n, d = (256, 256), (0.1, 0.1)
    ew = _helpers.write_exit_wave_stage(tmp_path / "ew", np.ones(n, complex), d, tilt_mrad=(-13.64, 0.0))
    sf = _helpers.load_yaml("specular_filter.yaml")
    sf["spot"] = {"mode": "specular", "surface_normal_xy": [1.0, 0.0], "refine_radius_inv_A": None}
    sf["objective"]["radius_mrad"] = 3.0
    _check(_helpers.run_script("specular_filter.py", "--params", _helpers.write_yaml(tmp_path / "sf.yaml", sf),
                               "--exit-wave", ew, "--output", tmp_path / "img"))
    spot = json.loads((tmp_path / "img" / "image_wave.json").read_text())["physics"]["spot"]
    lam = hc.wavelength_A(200.0)
    assert abs(spot["predicted_q_inv_A"][0] - 2 * m.sin(13.64e-3) / lam) < 1e-9   # 1.0877 1/Å, not g_x = 1.2757
    assert abs(spot["theta_in_ext_mrad"] - 13.64) < 1e-9
    th, _ = shf.angle_from_chain({"spot": spot}, None)
    assert abs(th - 13.64e-3) < 1e-12
    try:
        shf.angle_from_chain({"spot": {"mode": "hkl"}}, None)  # a bulk Bragg beam: the relation does not apply
    except SystemExit:
        pass
    else:
        raise AssertionError("step height accepted a bulk-Bragg (hkl) spot")
    away = _helpers.write_exit_wave_stage(tmp_path / "ew2", np.ones(n, complex), d, tilt_mrad=(13.64, 0.0))
    r = _helpers.run_script("specular_filter.py", "--params", tmp_path / "sf.yaml", "--exit-wave", away,
                            "--output", tmp_path / "img2")
    assert r.returncode != 0 and "onto a surface" in r.stderr


def test_reference_region_outside_the_biprism_overlap_is_refused(tmp_path):
    _helpers.need("yaml")
    _helpers.need("scipy")
    ew = _synthetic_exit_wave(tmp_path / "ew")
    sf = _params(tmp_path, "specular_filter.yaml", {})
    _check(_helpers.run_script("specular_filter.py", "--params", sf, "--exit-wave", ew, "--output", tmp_path / "i"))
    hg = _params(tmp_path, "hologram.yaml", {"biprism.overlap_width_A": 12.0, "biprism.fresnel_edge_width_A": 0.3})
    _check(_helpers.run_script("hologram_formation.py", "--params", hg, "--image-wave", tmp_path / "i",
                               "--output", tmp_path / "h"))
    rc = _params(tmp_path, "holo.yaml", {"engine": "numpy"})
    r = _helpers.run_script("holo_recon.py", "--params", rc, "--hologram", tmp_path / "h", "--output", tmp_path / "r")
    assert r.returncode != 0 and "outside the biprism overlap" in r.stderr
