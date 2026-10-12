"""Constants, crystallography guards, parameter strictness and output safety (numpy only)."""

import math
import unittest

import numpy as np

import _helpers  # noqa: F401  (puts code/ on sys.path)
import holo_common as hc
import holo_optics as ho


def test_wavelength_and_interaction_constant_200kV():
    # abTEM 1.0.10: energy2wavelength(200e3) = 0.025079340317328468, energy2sigma(200e3) = 7.288401085927866e-4.
    # abTEM takes m_e c² from scipy (CODATA 2022, 510998.95069 eV); we use CODATA 2018 (510998.950 eV) as in
    # docs/physics_conventions.md: the two differ by 5e-9 relative.
    assert abs(hc.wavelength_A(200.0) / 0.025079340317328468 - 1) < 1e-8
    assert abs(hc.interaction_constant(200.0) / 7.288401085927866e-4 - 1) < 1e-6
    # docs/physics_conventions.md: λ = 0.02507934 Å, k = 250.5323 rad/Å
    assert abs(2 * math.pi / hc.wavelength_A(200.0) - 250.5323) < 1e-3


def test_diamond_structure_factor_guards():
    for hkl in ([2, -2, 2], [6, -6, 6], [10, -10, 10], [0, 0, 2], [0, 0, 6]):
        assert abs(ho.diamond_structure_factor(hkl)) < 1e-9, hkl  # kinematically forbidden
    assert abs(abs(ho.diamond_structure_factor([4, -4, 4])) - 8) < 1e-9
    assert abs(abs(ho.diamond_structure_factor([1, -1, 1])) - 4 * math.sqrt(2)) < 1e-9
    assert abs(abs(ho.diamond_structure_factor([0, 0, 8])) - 8) < 1e-9


def test_specular_spot_vector_and_reflection_geometry():
    import si110_cleave_slab_generator as gen
    a = 5.4309
    g = ho.spot_vector([4, -4, 4], a, gen.slab_rotation_matrix())
    assert np.allclose(g, [4 * math.sqrt(3) / a, 0, 0], atol=1e-12)
    r = gen.reflection_geometry([4, -4, 4], a, 200.0, 12.0)
    # docs/03_physics_summary.md: (4,-4,4) external peak angle 13.6 mrad at 200 kV, V0 = 12 V; Δ = 6.98e-5
    assert abs(r["theta_ext_at_bragg_peak_mrad"] - 13.64) < 0.01
    assert abs(r["theta_B_vacuum_mrad"] - 16.00) < 0.01
    assert abs(r["refraction_Delta"] - 6.98e-5) < 1e-7
    for bad in ([6, -6, 6], [2, -2, 0]):  # forbidden; not specular (inaccessible in reflection)
        try:
            gen.reflection_geometry(bad, a, 200.0, 12.0)
        except SystemExit:
            continue
        raise AssertionError(f"{bad} was accepted")


def test_parameters_are_strict():
    P = hc.Section({"a": 1.0, "typo_key": 2})
    assert P.num("a") == 1.0
    try:
        P.finish()
    except hc.ParamError as e:
        assert "typo_key" in str(e)
    else:
        raise AssertionError("unused key accepted")
    try:
        hc.Section({}).num("missing")
    except hc.ParamError as e:
        assert "missing" in str(e)
    else:
        raise AssertionError("missing key accepted")
    try:
        hc.Section({"b": True}).num("b")  # a boolean is not a number
    except hc.ParamError:
        pass
    else:
        raise AssertionError("bool accepted as number")


def test_shipped_parameter_files_parse():
    names = [p.name for p in _helpers.PARAMS.glob("*.yaml")]
    assert len(names) >= 10
    for n in names:
        d = _helpers.load_yaml(n)
        assert isinstance(d, dict) and d, n


def test_output_refuses_raw_and_nonempty(tmp_path):
    proj = tmp_path / "proj"
    (proj / "raw").mkdir(parents=True)
    (proj / "gemicro.json").write_text("{}")
    (proj / "gemicro.json").write_text('{"raw_roots": ["data/microscope"]}')  # gemicro's declared raw root
    for bad in (proj / "raw" / "x", proj / ".gemicro" / "y", proj, proj / "data" / "microscope" / "s1"):
        try:
            hc.Output(bad)
        except SystemExit:
            continue
        raise AssertionError(f"Output accepted {bad}")
    out = hc.Output(proj / "derived" / "a")
    out.save_array("z", np.zeros((2, 2)), units="1", axes=["x", "y"], sampling_A=(1, 1), description="t")
    out.publish()
    assert (proj / "derived" / "a" / "z.npy").is_file()
    assert not list((proj / "derived" / "a").glob(".staging-*"))
    try:
        hc.Output(proj / "derived" / "a")
    except SystemExit:
        pass
    else:
        raise AssertionError("non-empty output accepted without --overwrite")
    try:
        out2 = hc.Output(proj / "derived" / "b")
        out2.save_array("bad", np.array([np.nan]), units="1", axes=["x"], description="nan")
    except SystemExit:
        pass
    else:
        raise AssertionError("NaN array saved")


def test_to_host_uses_get_for_device_arrays():
    class FakeCupy:
        def __init__(self, a):
            self.a = a

        def get(self):
            return self.a

        def __array__(self, *a, **k):
            raise TypeError("Implicit conversion to a NumPy array is not allowed. Please use .get()")

    out = hc.to_host(FakeCupy(np.arange(3)))
    assert isinstance(out, np.ndarray) and out.tolist() == [0, 1, 2]
    try:
        np.asarray(FakeCupy(np.arange(3)))
    except TypeError:
        pass
    else:
        raise unittest.SkipTest("numpy did not call __array__")
