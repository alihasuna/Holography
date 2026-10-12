"""Optional engines: abTEM (exit wave, tilt selection by value) and HoloSpy (same sideband as the numpy engine).

Each test skips when its package is not importable: run this file in em-abtem for abTEM, in em-holography for
HoloSpy (or in one laptop venv that has both). CPU only.
"""

import json
import math

import numpy as np

import _helpers


def test_abtem_exit_wave_and_tilt_selection_by_value(tmp_path):
    _helpers.need("abtem")
    _helpers.need("ase")
    _helpers.need("scipy")
    _helpers.need("yaml")
    slab = {"lattice_constant_A": 5.4309, "n_x_si": 2, "n_y": 4, "n_z_si": 2, "x_vacuum_A": 20.0,
            "z_vacuum_A": 1.0, "terraces_bilayers": [0, 1, 1, 0], "target_reflection": None}
    sp = _helpers.write_yaml(tmp_path / "slab.yaml", slab)
    r = _helpers.run_script("si110_cleave_slab_generator.py", "--params", sp, "--output", tmp_path / "slab")
    assert r.returncode == 0, r.stderr
    ew = _helpers.load_yaml("exit_wave.yaml")
    ew["device"] = "cpu"
    ew["potential"]["sampling_A"] = 0.2
    ep = _helpers.write_yaml(tmp_path / "ew.yaml", ew)
    r = _helpers.run_script("multislice_forward_model.py", "--params", ep, "--structure",
                            tmp_path / "slab" / "si110_slab.extxyz", "--output", tmp_path / "ew")
    assert r.returncode == 0, r.stderr
    meta = json.loads((tmp_path / "ew" / "exit_wave.json").read_text())
    psi = np.load(tmp_path / "ew" / "exit_wave.npy")
    assert psi.dtype == np.complex64 and psi.ndim == 2
    g = meta["physics"]["grid"]
    assert np.allclose(meta["arrays"]["exit_wave"]["sampling_A"], [g["extent_A"][i] / g["gpts"][i] for i in (0, 1)])
    sl = json.loads((tmp_path / "slab" / "slab.json").read_text())["physics"]["geometry"]
    x = (np.arange(psi.shape[0]) + 0.5) * g["sampling_A"][0]
    vac = (x > max(sl["x_top_atom_A"]) + 8.0) & (x < g["extent_A"][0] - 8.0)
    cry = (x > sl["x_back_atom_A"] + 2.0) & (x < min(sl["x_top_atom_A"]) - 2.0)
    assert np.abs(np.abs(psi[vac]) - 1).max() < 1e-2            # vacuum: unit amplitude (edge fringes < 1 %)
    assert np.angle(psi[cry]).mean() > 0.02                      # crystal: positive mean-inner-potential phase
    gt = np.load(tmp_path / "ew" / "ground_truth_phase.npy")
    assert gt[cry].mean() > gt[vac].mean() + 0.02

    ts = _helpers.load_yaml("tilt_series.yaml")
    ts["device"] = "cpu"
    ts["potential"]["sampling_A"] = 0.2
    ts["tilt_series"] = {"mode": "explicit", "tilts_mrad": [[0.0, 0.0], [-5.0, 0.0]]}
    tp = _helpers.write_yaml(tmp_path / "ts.yaml", ts)
    r = _helpers.run_script("multislice_tilt_series_runner.py", "--params", tp, "--structure",
                            tmp_path / "slab" / "si110_slab.extxyz", "--output", tmp_path / "ts")
    assert r.returncode == 0, r.stderr
    assert np.load(tmp_path / "ts" / "exit_waves.npy").shape[:2] == (2, 1)
    sf = _helpers.load_yaml("specular_filter.yaml")
    sf["tilt_select_mrad"] = [-5.0, 0.0]
    fp = _helpers.write_yaml(tmp_path / "sf.yaml", sf)
    r = _helpers.run_script("specular_filter.py", "--params", fp, "--exit-wave", tmp_path / "ts",
                            "--output", tmp_path / "img")
    assert r.returncode == 0, r.stderr
    assert json.loads((tmp_path / "img" / "image_wave.json").read_text())["physics"]["tilt_mrad"] == [-5.0, 0.0]
    sf["tilt_select_mrad"] = [-4.0, 0.0]  # not simulated: must fail, never fall back to index 0 (audit C5)
    fp = _helpers.write_yaml(tmp_path / "sf2.yaml", sf)
    r = _helpers.run_script("specular_filter.py", "--params", fp, "--exit-wave", tmp_path / "ts",
                            "--output", tmp_path / "img2")
    assert r.returncode != 0 and "no tilt within" in r.stderr


def test_holospy_engine_selects_the_same_sideband_as_numpy():
    _helpers.need("holospy")
    import holo_optics as ho
    import holo_sideband as hs
    n, pix = (192, 128), (0.2, 0.25)
    x = (np.arange(n[0]) * pix[0])[:, None] * np.ones(n)
    phi = 0.9 * np.sin(2 * math.pi * x / (n[0] * pix[0]))
    q_c = ho.carrier_vector(1.0, 33.0)
    one = np.ones(n, complex)
    a = math.sqrt(0.5)
    I_o = ho.hologram_intensity(np.exp(1j * phi)[None], pix, q_c, a, a, 0.5, np.zeros(n), one, one)
    car = hs.locate_carrier(I_o, pix, q_c / np.linalg.norm(q_c), 0.5)
    A = hs.aperture_at_origin(n, pix, 0.3, "tanh", 0.03)
    w_np = hs.sideband_numpy(I_o, car["index"], A)
    w_hs = hs.sideband_holospy(I_o, pix, car["index"], 0.3, 0.03)
    assert np.abs(w_np - w_hs).max() < 1e-9 * np.abs(w_np).max()
    # +object phase in the sideband at +q_c with HoloSpy too (its own roll convention handled)
    I_r = ho.hologram_intensity(one[None], pix, q_c, a, a, 0.5, np.zeros(n), one, one)
    w = w_hs / hs.sideband_holospy(I_r, pix, car["index"], 0.3, 0.03)  # reference-normalised
    centre = np.angle(w[n[0] // 4, n[1] // 2] / w[0, n[1] // 2])
    assert abs(centre - 0.9) < 0.05, centre
    assert "skipped" in hs.holospy_statistics(I_r, pix, q_c, 200.0)  # non-square pixels: not trusted
    sq = (0.25, 0.25)  # square pixels, non-square image (192 × 128): a centred square crop is used
    I_s = ho.hologram_intensity(one[None], sq, q_c, a, a, 0.5, np.zeros(n), one, one)
    st = hs.holospy_statistics(I_s, sq, q_c, 200.0)
    assert abs(st["Fringe contrast"] - 0.5 / math.sqrt(2)) < 0.01   # HoloSpy reports std/mean = μ/√2
    assert abs(st["Fringe spacing (nm)"] - 0.1) < 0.005, st
