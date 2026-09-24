"""Grazing-incidence reflection multislice: the slice loop, per-realisation exit waves, the run
manifest and the resource estimate (docs/05 section 4.3; milestone M2).

Scheme (symmetric split step, DERIVED_HERE): with P(d) the band-limited vacuum propagator and T_i
the band-limited transmission function of slice i = [i dz, (i+1) dz),

    psi(L_z) = P(dz/2) T_{N-1} P(dz) ... P(dz) T_1 P(dz) T_0 P(dz/2) psi_0,     L_z = N dz,

T_i = BL[ exp(+i sigma V_p,i(x, y)) exp(-sigma W(x) dz) ], V_p,i complex (imaginary part = physical
absorption, item 21), W the NUMERICAL absorber, BL the band-limit aperture. The output is the wave on
the DECLARED exit plane z = L_z (no further propagation), one ExitWave per realisation.

Status: UNVALIDATED for atomistic reflection. Ladder rung 1 (M2 report) and rung 2 test R2-A
(continuum periodic potential, Bragg-case (0,0,8) with absorption; tests/forward/
test_rung2_bragg.py, docs/agent_reports/E1_engine_wave2a.md) pass. Rung 3 has passed ONLY for the
continuum null tests and the atomistic MOVED-beam translation; the atomistic FIXED-beam translation
check that docs/05 4.4 item 3 requires before any step-phase run has NOT passed (audit A6 S-1). The
abTEM cross-check is NOT RUN. The flat-surface rocking-curve comparison with an independent
dynamical solver was RUN (reports S5, E8): with the solver's own potential the phase differs by a
median of 0.014 rad ([100]) and 0.017 rad ([110]); more than 0.05 rad at five other angles (0.051-0.075 rad, |R|^2 0.0017-0.044) and 0.398 rad at [100] 15.0 mrad where |R|^2 is about 1e-5
(tools/plots/phase4_figures_solver_output.txt), not like-for-like along the beam and no amplitude validation (E8 M1, M2). The label is
copied into every ExitWave.metadata["validation_status"].

No function default stands in for a PROJECT_INPUT: MultisliceParams, SheetBeam, the potentials and
the absorbers have required fields only.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

import reflection_holo
from reflection_holo.forward.cell import check_reflection_geometry
from reflection_holo.forward.contracts import ExitWave, ReflectionCell
from reflection_holo.geometry.refraction import theta_int_from_ext_rad

from .backend import get_backend
from .grid import band_limit_mask, check_band, make_grid
from .illumination import (BlochShiftedGrid, SheetBeam, TiltedSheetBeam, bloch_fy_per_A,
                           bloch_record, sheet_beam_wave)
from .physics import beam_constants
from . import potentials as _potentials
from .potentials import NumericalAbsorber, absorber_profile_V
from .propagator import PROPAGATORS, propagator_kernel

ENGINE_NAME = "reflection_holo.forward.multislice"
VALIDATION_STATUS = (
    "UNVALIDATED: of the docs/05 4.4 ladder, rung 1 (refraction-only analytic limit) and rung 2 "
    "test R2-A (laterally uniform periodic continuum potential, Bragg-case (0,0,8) amplitude and "
    "phase across the plateau against the exact semi-infinite solution, TEST_ONLY absorption "
    "r = 0.1 and 0.05, both propagators; P2 report section 8, tests/forward/test_rung2_bragg.py) "
    "pass in tests/forward; rung 3 has passed ONLY for the continuum null tests and the atomistic "
    "MOVED-beam translation: the atomistic FIXED-beam translation check that docs/05 4.4 item 3 "
    "requires before any step-phase run has NOT passed; R2-B (r = 0) is optional and qualitative; "
    "the abTEM cross-check (transmission and reflection-like configurations) was NOT RUN; the "
    "flat-surface rocking-curve comparison with an independent dynamical solver (sim-trhepd-rheed, "
    "flat Si(001), [100] and [110], TEST_ONLY r = 0.1; reports S5, E8) was RUN: with the solver's "
    "own potential the phase differs by a median of 0.014 rad ([100]) and 0.017 rad ([110]), up to "
    "0.05 rad at five other angles (0.051-0.075 rad) and 0.398 rad at [100] 15.0 mrad where |R|^2 is "
    "about 1e-5 (tools/plots/phase4_figures_solver_output.txt), but the "
    "comparison is not like-for-like along the beam and its amplitude tolerance has no power "
    "(E8 M1, M2): not an amplitude validation")
PLANE_TEXT = "exit plane z = L_z (no further propagation)"


@dataclass(frozen=True)
class MultisliceParams:
    """Engine parameters; every field is required (no defaults).

    energy_keV         200 (PROJECT_INPUT item 1; asserted)
    nx, ny             grid points; the pixel sizes are DERIVED (extent / n) and asserted
    dz_A               slice thickness; L_z / dz_A must be an integer, and for atomic cells the
                       lattice period along the beam must be an integer multiple of dz_A
    propagator         "exact" | "fresnel"
    band_limit         "2/3" (UNVERIFIED source) | "half_nyquist" (SECTION_READ)
    backend            "numpy" | "cupy"
    precision          "complex64" | "complex128"
    threads            FFT worker threads (numpy backend; recorded in the manifest)
    absorber           NumericalAbsorber (strength and profile; NUMERICAL, not physical)
    theta_out_ext_rad  external glancing angle of the OUTGOING beam (item 7; equals theta_in for
                       the specular beam) for the band and geometry assertions
    buildup_depth_A    normal penetration depth for the build-up assertion (20 to 100 A)
    working_reflections_hkl
                       the reflection(s) that carry the run's working condition, PROJECT_INPUT
                       item 9 (the configuration's target reflection, e.g. ((0, 0, 8),) for the
                       B17 stand-in), as integer (h, k, l) of the cubic crystal frame of the
                       cell's structure metadata. The band assertion requires the transmission
                       function to carry each one (grid.check_band; H2 N8, H5 A7). Required and
                       non-empty for an atomic cell; () for a structureless (continuum) cell,
                       which has no reciprocal lattice. The harmonics of a periodic continuum
                       potential (ContinuumPeriodicPotential, rung 2) are part of the
                       potential's definition and are asserted inside the band from the
                       potential itself (reflection_setup), not declared here.
    """
    energy_keV: float
    nx: int
    ny: int
    dz_A: float
    propagator: str
    band_limit: str
    backend: str
    precision: str
    threads: int
    absorber: NumericalAbsorber
    theta_out_ext_rad: float
    buildup_depth_A: float
    working_reflections_hkl: tuple

    def to_dict(self) -> dict:
        d = asdict(self)
        d["absorber"] = self.absorber.describe()
        return d


def _n_slices(cell: ReflectionCell, dz: float) -> int:
    if not (np.isfinite(dz) and dz > 0):
        raise ValueError("dz_A must be > 0")
    r = cell.length_z_A / dz
    n = int(round(r))
    if n < 1 or abs(r - n) > 1e-6:
        raise ValueError(f"L_z = {cell.length_z_A} A is not an integer number of slices of "
                         f"dz = {dz} A (ratio {r:.8f}); the exit plane must be z = L_z exactly")
    return n


def _commensurability(cell: ReflectionCell, dz: float) -> dict:
    p = cell.metadata["layout"].get("z_period_A")
    if p is None:
        return dict(z_period_A=None, note="continuum cell: no lattice period along the beam")
    r = p / dz
    if abs(r - round(r)) > 1e-6 or round(r) < 1:
        raise ValueError(f"slice thickness dz = {dz} A is not commensurate with the lattice "
                         f"period along the beam {p:.6f} A (ratio {r:.6f}; docs/05 4.3 item 5)")
    return dict(z_period_A=p, slices_per_period=int(round(r)))


def working_reflection_vectors(cell: ReflectionCell, working_reflections_hkl) -> dict:
    """name -> (g_x, g_y, g_z) in cycles/A (cell frame) of each declared working reflection
    (MultisliceParams.working_reflections_hkl): g = hkl / a in the cubic crystal frame, projected
    on the cell axes x (outward normal), y, z (beam) recorded by the structure builder
    (metadata["structure"]["frame"]). DERIVED_HERE. Raises if the declaration is missing, empty
    for an atomic cell, non-empty for a continuum cell, or not integer triples."""
    hkls = working_reflections_hkl
    if hkls is None or isinstance(hkls, (str, bytes)) or not isinstance(hkls, (tuple, list)):
        raise TypeError("working_reflections_hkl must be a tuple of integer (h, k, l) triples "
                        "(PROJECT_INPUT item 9), () only for a structureless cell")
    kind = cell.metadata.get("kind")
    if kind == "continuum":
        if len(hkls):
            raise ValueError("a structureless (continuum) cell has no reciprocal lattice: "
                             "working_reflections_hkl must be ()")
        return {}
    if not len(hkls):
        raise ValueError(
            "an atomic cell needs its working reflection(s) declared in "
            "MultisliceParams.working_reflections_hkl (PROJECT_INPUT item 9, e.g. ((0, 0, 8),) "
            "for the B17 stand-in): the band assertion checks that the transmission function "
            "carries them (H2 N8, H5 A7); no default is assumed")
    st = cell.metadata.get("structure") or {}
    try:
        a = float(st["lattice"]["a_A"])
        fr = st["frame"]
        R = np.array([fr["x_hat_crystal"], fr["y_hat_crystal"], fr["z_hat_crystal"]], float)
    except (KeyError, TypeError) as exc:
        raise ValueError("the cell's structure metadata lacks the cubic lattice parameter or the "
                         "crystal frame needed to place the working reflections") from exc
    out = {}
    for hkl in hkls:
        v = np.asarray(hkl)
        if v.shape != (3,) or not np.all(np.equal(np.mod(v, 1), 0)):
            raise ValueError(f"working reflection {hkl!r} is not an integer (h, k, l) triple")
        t = tuple(int(x) for x in v)
        if t == (0, 0, 0):
            raise ValueError("(0, 0, 0) is not a working reflection")
        g = R @ (np.asarray(t, float) / a)
        out[str(t)] = (float(g[0]), float(g[1]), float(g[2]))
    return out


def propagate_slices(psi, *, realised, n_slices: int, backend, P_full, P_half, band_mask, sigma,
                     absorber_factor):
    """The slice loop (module docstring): P(dz/2) T_{N-1} P(dz) ... T_0 P(dz/2) psi.

    realised: object with slice_key(i) (hashable or None; equal consecutive keys reuse the
    transmission function) and projected(i) (complex projected potential, V A). absorber_factor:
    exp(-sigma W(x) dz) broadcastable to (nx, ny). Returns (psi, number of transmission functions
    built)."""
    be, xp = backend, backend.xp
    psi = be.ifft2(be.fft2(psi) * P_half)
    key_prev, t_bl, n_built = object(), None, 0
    for i in range(n_slices):
        key = realised.slice_key(i)
        if key is None or key != key_prev:
            t = xp.exp(1j * sigma * realised.projected(i)) * absorber_factor
            t_bl = be.ifft2(be.fft2(t) * band_mask)
            key_prev = key
            n_built += 1
        psi = psi * t_bl
        psi = be.ifft2(be.fft2(psi) * (P_full if i < n_slices - 1 else P_half))
    return psi, n_built


def reflection_setup(cell: ReflectionCell, *, potential, beam: SheetBeam,
                     params: MultisliceParams) -> dict:
    """Run every assertion of a reflection calculation and return the derived quantities (grid,
    beam constants, slices, band record, geometry record) without propagating."""
    bc = beam_constants(params.energy_keV)
    if params.propagator not in PROPAGATORS:
        raise ValueError(f"propagator must be one of {PROPAGATORS}")
    if not isinstance(params.absorber, NumericalAbsorber):
        raise TypeError("params.absorber must be a NumericalAbsorber")
    grid = make_grid(cell, nx=params.nx, ny=params.ny)
    n = _n_slices(cell, params.dz_A)
    comm = _commensurability(cell, params.dz_A)
    V0 = float(potential.mean_inner_potential_V())
    th_in, th_out = float(beam.theta_in_ext_rad), float(params.theta_out_ext_rad)
    th_int_in = theta_int_from_ext_rad(th_in, params.energy_keV, V0)
    th_int_out = theta_int_from_ext_rad(th_out, params.energy_keV, V0)
    refl = working_reflection_vectors(cell, params.working_reflections_hkl)
    # a periodic continuum potential (rung 2) has no reciprocal lattice to declare, but its
    # harmonics ARE its definition: they are asserted inside the band like working reflections
    harm = (dict(potential.band_harmonics_per_A())
            if hasattr(potential, "band_harmonics_per_A") else {})
    angles = dict(incident_ext=th_in, outgoing_ext=th_out, incident_int=th_int_in,
                  outgoing_int=th_int_out)
    # continuum oxide (report E4): a cell built with the layer needs the layer's potential (its
    # consumed crystal layers are gone), and the layer's own internal angles join the band check
    ov = None
    if (cell.metadata.get("layout") or {}).get("overlayer") is not None:
        if not hasattr(potential, "overlayer_setup"):
            raise ValueError("the cell carries a continuum oxide (its consumed crystal layers are "
                             "removed): the potential must be multislice.ContinuumOxidePotential "
                             "wrapping the crystal potential")
        ov = potential.overlayer_setup(grid=grid, energy_keV=params.energy_keV,
                                       theta_in_ext_rad=th_in, theta_out_ext_rad=th_out)
        angles.update(incident_int_layer=ov["internal_angle_in_layer_in_rad"],
                      outgoing_int_layer=ov["internal_angle_in_layer_out_rad"])
    elif hasattr(potential, "overlayer_setup"):
        raise ValueError("ContinuumOxidePotential on a cell without a continuum oxide")
    band = check_band(grid, rule=params.band_limit, wavelength_A=bc["wavelength_A"],
                      angles_rad=angles,
                      reflections_per_A={**{k: v[:2] for k, v in refl.items()}, **harm})
    for k, v in refl.items():
        band["working_reflections"][k]["g_z_per_A"] = v[2]
    band["working_reflections_source"] = (
        "MultisliceParams.working_reflections_hkl (PROJECT_INPUT item 9), g = hkl/a in the cubic "
        "crystal frame projected on the cell axes; (g_x, g_y) must lie inside the band"
        + ("; plus the harmonics of the periodic continuum potential "
           "(ContinuumPeriodicPotential.band_harmonics_per_A)" if harm else ""))
    band["internal_angles_from"] = (f"SM04 refraction with the potential's mean inner potential "
                                    f"{V0:.4f} V")
    # azimuthal (y) tilt of a TiltedSheetBeam (convergence member, report E3): carried by the Bloch
    # form, so every beam of the member has native f_y' = 0 and the x-angles above are the whole
    # band assertion; theta_in / theta_out are the member's own glancing angles
    fb = bloch_fy_per_A(beam, bc["wavelength_A"])
    if isinstance(beam, TiltedSheetBeam):
        band["azimuthal_tilt"] = dict(
            direction_cosine_y=float(beam.direction_cosine_y), fy_per_A=fb,
            native_fy_of_every_beam_per_A=0.0, tilt_label=beam.tilt_label,
            note="Bloch form (illumination.py): the envelope's beams sit at f_y' = 0, so the band "
                 "assertion is the x-angle check above with this member's glancing angles; the "
                 "physical beams are at f_y' + fy_per_A")
    geo = check_reflection_geometry(cell, beam_height_A=beam.height_A,
                                    beam_x_bottom_A=beam.x_bottom_A, theta_in_ext_rad=th_in,
                                    theta_out_ext_rad=th_out, theta_int_rad=th_int_in,
                                    buildup_depth_A=params.buildup_depth_A)
    out = dict(bc=bc, grid=grid, n_slices=n, commensurability=comm, V0_potential_V=V0,
               theta_int_in_rad=th_int_in, theta_int_out_rad=th_int_out, band=band, geometry=geo,
               bloch_fy_per_A=fb)
    if ov is not None:
        out["overlayer"] = ov
    return out


def run_realisation(cell: ReflectionCell, *, potential, beam: SheetBeam, params: MultisliceParams,
                    realisation: int, seed: int | None) -> ExitWave:
    """One realisation (static lattice or one frozen-phonon configuration) -> ExitWave on the exit
    plane z = L_z. seed: required int for frozen phonons (generator seeded with
    [seed, realisation]); must be None for a static potential. Low-level kernel: production runs
    use ``simulate`` (writes the manifest)."""
    t_start = time.perf_counter()
    s = reflection_setup(cell, potential=potential, beam=beam, params=params)
    bc, grid, N = s["bc"], s["grid"], s["n_slices"]
    fp = getattr(potential, "frozen_phonons", None)
    if fp is not None:
        if seed is None or int(seed) != seed:
            raise ValueError("frozen phonons need an integer seed")
        rng = np.random.default_rng([int(seed), int(realisation)])
    else:
        if seed is not None:
            raise ValueError("seed must be None for a static potential (nothing is random)")
        rng = None
    be = get_backend(params.backend, params.precision, params.threads)
    lam, sigma = bc["wavelength_A"], bc["sigma_rad_per_VA"]
    mask = band_limit_mask(grid, params.band_limit)
    # y tilt (TiltedSheetBeam): kernels at the physical frequencies f_y' + f_y (Bloch form); the
    # untilted path (f_y = 0) is unchanged
    fb = s["bloch_fy_per_A"]
    kgrid = grid if fb == 0.0 else BlochShiftedGrid(grid, fb)
    P_full, n_ev = propagator_kernel(kgrid, dz_A=params.dz_A, wavelength_A=lam,
                                     kind=params.propagator, band_mask=mask)
    P_half, _ = propagator_kernel(kgrid, dz_A=0.5 * params.dz_A, wavelength_A=lam,
                                  kind=params.propagator, band_mask=mask)
    P_full = be.asarray(P_full, dtype=be.complex_dtype)
    P_half = be.asarray(P_half, dtype=be.complex_dtype)
    maskb = be.asarray(mask, dtype=be.real_dtype)
    W = absorber_profile_V(grid, cell, params.absorber)
    absfac = be.asarray(np.exp(-sigma * W * params.dz_A)[:, None], dtype=be.real_dtype)
    psi = be.asarray(sheet_beam_wave(beam, grid, lam), dtype=be.complex_dtype)
    t_setup = time.perf_counter()
    realised = potential.realise(grid=grid, dz_A=params.dz_A, n_slices=N, backend=be, rng=rng)
    sig = be.real_dtype(sigma)

    psi, n_built = propagate_slices(psi, realised=realised, n_slices=N, backend=be,
                                    P_full=P_full, P_half=P_half, band_mask=maskb, sigma=sig,
                                    absorber_factor=absfac)
    psi_np = be.to_numpy(psi).astype(params.precision)
    t_end = time.perf_counter()

    alpha = max(beam.theta_in_ext_rad, params.theta_out_ext_rad)
    k = bc["k_rad_per_A"]
    meta = dict(
        engine=dict(name=ENGINE_NAME, package_version=reflection_holo.__version__,
                    scheme="symmetric split step P(dz/2) T_0 P(dz) ... T_{N-1} P(dz/2)"),
        validation_status=VALIDATION_STATUS,
        carrier=("psi is the envelope relative to exp(i k z): the full wave is "
                 "psi * exp(i k z_A); convention exp(+i k.r), numpy FFT sign"),
        axes=["x: surface normal (outward), row index", "y: in-plane transverse, column index"],
        units="angstrom, rad",
        grid=dict(nx=grid.nx, ny=grid.ny, dx_A=grid.dx_A, dy_A=grid.dy_A, x0_A=grid.x0_A,
                  y0_A=grid.y0_A, pixel_note="derived: extent / n"),
        beam=bc, illumination=beam.describe(lam),
        theta_out_ext_rad=float(params.theta_out_ext_rad),
        theta_int_in_rad=s["theta_int_in_rad"], theta_int_out_rad=s["theta_int_out_rad"],
        propagator=dict(kind=params.propagator, evanescent_components_removed=n_ev,
                        evanescent_rule="components with 2 pi |f| >= k are set to zero",
                        paraxial_error_estimate_rad=(
                            float(k * cell.length_z_A * np.sin(alpha) ** 4 / 8.0)
                            if params.propagator == "fresnel" else 0.0),
                        paraxial_error_note="k L sin^4(alpha)/8 at the largest declared beam "
                                            "angle (docs/03 section 5)"),
        band_limit=s["band"],
        slices=dict(dz_A=params.dz_A, n_slices=N, transmission_functions_built=n_built,
                    **s["commensurability"]),
        absorbers=dict(numerical=params.absorber.describe(),
                       bulk_absorber_x_A=cell.metadata["layout"]["bulk_absorber_x_A"],
                       top_absorber_x_A=cell.metadata["layout"]["top_absorber_x_A"]),
        potential=dict(potential.provenance(), realised=realised.metadata),
        mean_inner_potential_V=dict(
            value=s["V0_potential_V"],
            note="mean inner potential of the potential actually used (independent-atom value for "
                 "atomic cells; declared V0 for continuum cells); used for the internal angles of "
                 "the band and geometry assertions; compare the sourced V0 (PROJECT_INPUT item 20, "
                 "12.0 V ASSUMPTION B1)"),
        geometry_checks=s["geometry"],
        cell=dict(kind=cell.metadata.get("kind"), atoms_sha256=cell.metadata.get("atoms_sha256"),
                  n_atoms=int(len(cell.Z)), extent_x_A=cell.extent_x_A,
                  extent_y_A=cell.extent_y_A, length_z_A=cell.length_z_A,
                  crystal_start_z_A=cell.crystal_start_z_A, surface_x_A=cell.surface_x_A,
                  terraces=cell.metadata.get("terraces")),
        backend=be.describe(), params=params.to_dict(),
        timing_s=dict(setup=t_setup - t_start, propagation=t_end - t_setup,
                      total=t_end - t_start),
    )
    if "overlayer" in s:                   # continuum oxide (report E4): what the layer changes
        meta["overlayer"] = s["overlayer"]
        meta["mean_inner_potential_V"]["overlayer_treatment"] = s["overlayer"][
            "mean_inner_potential_treatment"]
    brec = bloch_record(beam, lam)
    if brec is not None:                   # TiltedSheetBeam: psi is the Bloch envelope (report E3)
        meta["bloch"] = brec
        meta["carrier"] = (meta["carrier"] + "; y tilt: psi is the Bloch envelope, the full wave "
                           "is psi * exp(2 pi i fy_per_A y) * exp(i k z_A) (metadata['bloch'])")
    return ExitWave(psi=psi_np, dx_A=grid.dx_A, dy_A=grid.dy_A, x0_A=grid.x0_A, y0_A=grid.y0_A,
                    plane=PLANE_TEXT, z_A=float(N * params.dz_A), energy_keV=bc["energy_keV"],
                    theta_in_ext_rad=float(beam.theta_in_ext_rad), realisation=int(realisation),
                    seed=None if seed is None else int(seed), metadata=meta)


def _canonical_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def simulate(cell: ReflectionCell, *, potential, beam: SheetBeam, params: MultisliceParams,
             realisations: int, seed: int | None, outputs_root, run_name: str,
             save_waves: bool, config, input_paths,
             caller_record: dict | None) -> tuple[list[ExitWave], Path]:
    """Production entry point: run ``realisations`` realisations and write the run manifest
    (reflection_holo.provenance.manifest) under outputs_root/manifests; with save_waves the exit
    waves are written as .npz (exitwave_io) under outputs_root/exit_waves and hashed into the
    manifest. Every argument is required; ``caller_record`` is a mapping recorded verbatim in the
    manifest's extra.caller (e.g. the pipeline's purpose and configuration hashes, audit A3 m1), or
    None, stated explicitly and recorded as "no caller record". Returns (exit waves, manifest
    path)."""
    from reflection_holo.provenance.manifest import build_manifest, write_manifest

    from .exitwave_io import save_exit_wave
    if int(realisations) != realisations or realisations < 1:
        raise ValueError("realisations must be a positive integer")
    waves = [run_realisation(cell, potential=potential, beam=beam, params=params,
                             realisation=r, seed=seed) for r in range(int(realisations))]
    root = Path(outputs_root)
    files = []
    if save_waves:
        (root / "exit_waves").mkdir(parents=True, exist_ok=True)
        for ew in waves:
            p = root / "exit_waves" / f"{run_name}_r{ew.realisation:04d}.npz"
            save_exit_wave(p, ew)
            files.append(p)
    run_cfg = dict(params=params.to_dict(), beam=beam.describe(waves[0].metadata["beam"]
                                                                ["wavelength_A"]),
                   potential=waves[0].metadata["potential"], cell=waves[0].metadata["cell"],
                   realisations=int(realisations), seed=seed)
    git = None
    try:
        from reflection_holo.provenance.manifest import git_state
        git = git_state()
    except Exception:                                     # pragma: no cover
        pass
    engines = {ENGINE_NAME: dict(version=reflection_holo.__version__,
                                 commit=(git or {}).get("commit"),
                                 dirty=(git or {}).get("dirty"),
                                 licence="this repository",
                                 status=VALIDATION_STATUS)}
    if getattr(potential, "kind", None) == "atomic":
        pv = waves[0].metadata["potential"]
        engines["abTEM (Kirkland parameterisation functions only)"] = dict(
            version=pv["abtem_version"], commit=pv["abtem_commit"],
            licence="GPL-3.0-or-later (optional dependency)")
    manifest = build_manifest(
        run_name=run_name, config=config, input_paths=list(input_paths) + files,
        seeds={"frozen_phonons": seed}, thread_count=params.threads,
        precision={"complex": params.precision},
        engines=engines, wave_planes={f"exit_wave_r{ew.realisation}": ew.plane for ew in waves},
        beam_energy_keV=params.energy_keV,
        extra=dict(configuration_sha256=_canonical_hash(run_cfg),
                   input_hashes=dict(cell_atoms_sha256=cell.metadata.get("atoms_sha256"),
                                     structure_positions_sha256=cell.metadata.get(
                                         "structure_positions_sha256"),
                                     parameterisation_data_sha256=waves[0].metadata["potential"]
                                     .get("data_file_sha256")),
                   run_configuration=run_cfg,
                   timing_s=[ew.metadata["timing_s"] for ew in waves],
                   ensemble_rule="intensities are averaged after squaring (after hologram "
                                 "formation); the complex waves are never averaged",
                   validation_status=VALIDATION_STATUS,
                   caller=(dict(caller_record) if caller_record is not None
                           else "no caller record")))
    return waves, write_manifest(manifest, outputs_root=root)


# ---------------------------------------------------------------------------------------------
# Resource estimate (HPC planning)
# ---------------------------------------------------------------------------------------------
GPU_ASSUMED = dict(
    label="ASSUMPTION (not measured: no GPU on the build machine): a data-centre GPU with "
          "~1 TB/s effective memory bandwidth, cuFFT at 1/3 of that for 2D complex64 FFTs, "
          "~10 TFLOP/s effective complex64 GEMM and ~10 us per kernel launch",
    bandwidth_Bps=1.0e12, fft_efficiency=1 / 3, gemm_flops=1.0e13, launch_s=1.0e-5,
    kernels_per_slice=25)


def _slice_counts(cell, dz, n):
    if len(cell.Z) == 0:
        return np.zeros(n, np.int64)
    idx = np.floor((np.asarray(cell.atoms_xyz_A)[:, 2] + 1e-9) / dz).astype(np.int64)
    return np.bincount(np.clip(idx, 0, n - 1), minlength=n)


# Memory model (bytes). DERIVED_HERE from the statements of run_realisation, propagate_slices,
# potentials._RealisedAtomic, propagator.propagator_kernel and illumination.sheet_beam_wave with
# numpy's semantics (a binary operator reuses a temporary operand of the result dtype; ufunc calls
# and astype allocate), and checked against tracemalloc measurements of run_realisation (numpy
# backend) in tests/forward/test_memory_model.py (H5 finding M4; report H7).
MEM_KERNEL_TRANSIENT_B_PER_PX = 41     # propagator_kernel: phase f8 + evanescent mask b1 + 1j*phase
#                                        c16 + exp c16 (host numpy, before the cast)
MEM_SCATTERING_F_B_PER_PX = 16         # realise: f2 grid f8 + abTEM F(f^2) f8 (the abTEM 1.0.10
#                                        expression itself peaks no higher: tracemalloc)
MEM_EXP_B_PER_ELEMENT = 32             # potentials.py: each structure-factor exponential is formed
#                                        from a complex128 argument (16 B) into a complex128 result
#                                        (16 B) before the cast (32 B per element of nx*n or ny*n;
#                                        with more than 2 * potentials.EXP_BLOCK_ROWS rows, per
#                                        element of a block of EXP_BLOCK_ROWS rows, plus the
#                                        preallocated result, cb B per element: _exp_stage_B)
MEM_CELL_B_PER_ATOM = 32               # cell atoms_xyz_A f8 x3 + Z i8 (held by the caller)
MEM_REALISED_B_PER_ATOM = 40           # _RealisedAtomic: sorted xyz f8 x3, idx_sorted i8, Z i8
MEM_REALISE_PEAK_B_PER_ATOM = 112      # _RealisedAtomic.__init__: the 40 above + unsorted copy 24,
#                                        idx 8, order 8, offsets 8, and three f8 temporaries of the
#                                        boundary count 24 (the hash's tobytes copy is also 24)
MEM_REALISE_F_STAGE_B_PER_ATOM = 88    # the same arrays while the scattering factors are built
MEM_OXIDE_BUILD_B_PER_PX = 32          # overlayer.ContinuumOxidePotential.layer_arrays (host numpy):
#                                        the complex128 accumulator and one complex128 product
#                                        (profile x y fraction) of every terrace (audit A8 m3)
MEMORY_MODEL_LABEL = (
    "DERIVED_HERE from the engine's statements (numpy semantics), checked with tracemalloc on "
    "the numpy backend (tests/forward/test_memory_model.py); the cupy figures are the same "
    "statements on the device, UNVERIFIED on a GPU (cuFFT/cuBLAS workspaces and the cupy memory "
    "pool are not included, so they are lower bounds)")


def _exp_stage_B(rows: int, n: int, cb: int) -> int:
    """Bytes while one structure-factor exponential of `rows` x n is formed, the result included
    (potentials._phase_factors): 32 rows n unblocked; cb rows n + 32 EXP_BLOCK_ROWS n blocked."""
    blk = int(_potentials.EXP_BLOCK_ROWS)
    if rows <= 2 * blk:
        return MEM_EXP_B_PER_ELEMENT * rows * n
    return cb * rows * n + MEM_EXP_B_PER_ELEMENT * blk * n


def overlayer_memory_arguments(cell: ReflectionCell) -> dict | None:
    """The ``overlayer`` argument of memory_model for a cell: None without a continuum oxide, else
    dict(staircase_axis, n_terraces) from the cell's layout (audit A8 m3)."""
    ov = (cell.metadata.get("layout") or {}).get("overlayer")
    if ov is None:
        return None
    return dict(staircase_axis=str(ov["staircase_axis"]), n_terraces=len(ov["per_terrace"]))


def memory_model(*, nx: int, ny: int, n_slices: int, n_atoms: int, atoms_per_slice_max: int,
                 n_species: int, precision: str, overlayer: dict | None) -> dict:
    """Peak memory of one realisation of run_realisation (bytes), phase by phase (H5 M4).

    Every argument is required. ``overlayer`` is None (no continuum oxide) or dict(staircase_axis
    "y" | "z", n_terraces) for a cell built with the continuum oxide (report E4; audit A8 m3,
    overlayer_memory_arguments): the layer adds one working-precision complex array per pixel
    resident during the slice loop when its terraces lie along y (or there is one terrace), and
    n_terraces x nx complex values when they lie along z; it is built on the host in complex128
    (MEM_OXIDE_BUILD_B_PER_PX per pixel, a transient of the realise stage; on the cupy backend a
    host transient). The physical absorption is assumed non-zero (the larger of the
    two code paths of _RealisedAtomic.projected; zero absorption needs cb bytes per pixel less in
    the potential-construction stage). The cell's own atom arrays (32 B/atom, held by the caller)
    are included; the structure-builder objects of the caller, Python objects and arrays of size
    O(nx + ny + n_slices) other than fx, fy and the slice index are not. FFT library scratch
    buffers (pocketfft, cuFFT) are not visible to tracemalloc and are not included. Written for
    the atomic potential; for a structureless (continuum) cell it is an upper bound (by about one
    complex array). The temporaries follow numpy's temporary elision (numpy 2.x, as tested).

    Returns dict(numpy=dict(phases, peak), cupy=dict(device_phases, device_peak, host_phases,
    host_peak), loop_residents, per_atom_B, ...)."""
    if precision not in ("complex64", "complex128"):
        raise ValueError("precision must be complex64 or complex128")
    cb = np.dtype(precision).itemsize
    rb = cb // 2
    px = int(nx) * int(ny)
    # continuum oxide layer arrays (audit A8 m3): resident in the loop, and the host build transient
    if overlayer is None:
        layer_res_B = layer_build_B = 0
    else:
        if not isinstance(overlayer, dict) or set(overlayer) != {"staircase_axis", "n_terraces"}:
            raise ValueError("overlayer must be None or dict(staircase_axis, n_terraces)")
        axis, nt = overlayer["staircase_axis"], int(overlayer["n_terraces"])
        if axis not in ("y", "z") or nt < 1:
            raise ValueError(f"overlayer: staircase_axis 'y' or 'z' and n_terraces >= 1, got "
                             f"{overlayer!r}")
        if axis == "y" or nt == 1:
            layer_res_B, layer_build_B = cb * px, MEM_OXIDE_BUILD_B_PER_PX * px
        else:
            layer_res_B, layer_build_B = cb * nt * int(nx), MEM_OXIDE_BUILD_B_PER_PX * nt * int(nx)
    n = int(atoms_per_slice_max)
    nsp = max(1, int(n_species))
    cell_B = MEM_CELL_B_PER_ATOM * int(n_atoms)
    starts_B = 8 * (int(n_slices) + 1)
    fxfy_B = 8 * (int(nx) + int(ny))
    # arrays resident on the backend during the slice loop
    residents = {"propagators P(dz), P(dz/2)": 2 * cb * px,
                 "entrance wave (held by run_realisation during the loop)": cb * px,
                 "band mask (real, backend)": rb * px,
                 f"scattering factor x {nsp} species": rb * px * nsp,
                 "fx, fy (float64)": fxfy_B}
    if overlayer is not None:
        residents["continuum oxide layer arrays (audit A8 m3)"] = layer_res_B
    dev_pers = int(sum(residents.values()))
    # potential construction of the largest slice (_RealisedAtomic.projected), above its caller
    pos_B = 25 * n                                           # selected positions f8 x3 + mask b1
    pix_proj = (3 * cb + rb) * px                            # acc, ifft, V (real), V*(1+ir), astype
    ex_x, ex_y = _exp_stage_B(int(nx), n, cb), _exp_stage_B(int(ny), n, cb)
    if nsp == 1:
        atom_stage = pos_B + max(ex_x, cb * nx * n + ex_y)
    else:                                                    # upper bound (not measured)
        pix_proj += 2 * cb * px                              # acc and S of the previous species
        atom_stage = pos_B + cb * (nx + ny) * n + ex_x + ex_y
    pix_stage = pos_B + cb * (nx + ny) * n + pix_proj
    proj = max(atom_stage, pix_stage)
    # slice loop above the residents: psi, t_bl and t of the previous slice stay alive while the
    # next potential is built; transmission / propagation steps hold at most 5 arrays
    in_loop = max(5 * cb * px, 3 * cb * px + proj)
    host_mask = 1 * px                                       # boolean aperture (host numpy)
    k128 = 16 * px
    numpy_phases = {
        "setup: propagator kernels (complex128 host temporaries)":
            host_mask + k128 + MEM_KERNEL_TRANSIENT_B_PER_PX * px + cell_B,
        "setup: entrance wave (complex128 before the cast)":
            host_mask + 2 * cb * px + rb * px + 16 * px + (cb * px if cb != 16 else 0) + cell_B,
        "realise: scattering factors":
            host_mask + 3 * cb * px + rb * px + rb * px * (nsp - 1) + MEM_SCATTERING_F_B_PER_PX * px
            + (rb * px if cb != 16 else 0) + MEM_REALISE_F_STAGE_B_PER_ATOM * n_atoms + cell_B,
        "realise: atom sorting and records":
            host_mask + 3 * cb * px + rb * px + rb * px * nsp + 8 * px + fxfy_B
            + MEM_REALISE_PEAK_B_PER_ATOM * n_atoms + starts_B + cell_B,
        **({} if overlayer is None else {
            "realise: continuum oxide layer arrays (complex128 host build)":
                host_mask + 3 * cb * px + rb * px + rb * px * nsp + fxfy_B + layer_build_B
                + MEM_REALISED_B_PER_ATOM * n_atoms + starts_B + cell_B}),
        "slice loop (largest slice)":
            host_mask + dev_pers + in_loop + MEM_REALISED_B_PER_ATOM * n_atoms + starts_B + cell_B,
        "after the loop: exit wave copy":
            host_mask + dev_pers + cb * px + MEM_REALISED_B_PER_ATOM * n_atoms + starts_B + cell_B,
    }
    dev_phases = {"slice loop (largest slice)": dev_pers + in_loop,
                  "after the loop": dev_pers + cb * px}
    cupy_host = {
        "setup: propagator kernels": host_mask + k128 + MEM_KERNEL_TRANSIENT_B_PER_PX * px + cell_B,
        "setup: entrance wave": host_mask + 16 * px + cell_B,
        "realise: scattering factors": host_mask + MEM_SCATTERING_F_B_PER_PX * px
            + MEM_REALISE_F_STAGE_B_PER_ATOM * n_atoms + cell_B,
        "realise: atom sorting and records": host_mask + 8 * px + MEM_REALISE_PEAK_B_PER_ATOM
            * n_atoms + starts_B + cell_B,
        **({} if overlayer is None else {
            "realise: continuum oxide layer arrays (complex128 host build)":
                host_mask + layer_build_B + MEM_REALISED_B_PER_ATOM * n_atoms + starts_B + cell_B}),
        "slice loop": host_mask + MEM_REALISED_B_PER_ATOM * n_atoms + starts_B + cell_B,
        "after the loop: exit wave to host": host_mask + 2 * cb * px
            + MEM_REALISED_B_PER_ATOM * n_atoms + cell_B}
    numpy_phases = {k: int(v) for k, v in numpy_phases.items()}
    return dict(
        label=MEMORY_MODEL_LABEL,
        assumptions="non-zero physical absorption (upper of the two code paths); atoms per slice "
                    "from the static positions (frozen-phonon displacements move atoms across "
                    "slice boundaries, a few per cent more or fewer per slice)",
        overlayer=(None if overlayer is None else dict(
            overlayer, resident_B=int(layer_res_B), host_build_B=int(layer_build_B),
            note="continuum oxide layer arrays (report E4; audit A8 m3): resident in the slice "
                 "loop (device on cupy), built on the host in complex128")),
        loop_residents=residents,
        largest_slice=dict(atoms=n, exponentials_B=int(atom_stage), pixel_stage_B=int(pix_stage),
                           exp_block_rows=int(_potentials.EXP_BLOCK_ROWS),
                           formula="max(E(nx), cb nx n + E(ny)) and cb (nx + ny) n + "
                                   "(3 cb + rb) px (one species); E(m) = 32 m n for m <= 2 B, "
                                   "cb m n + 32 B n otherwise (B = exp_block_rows)"),
        numpy=dict(phases=numpy_phases, peak=int(max(numpy_phases.values())),
                   peak_phase=max(numpy_phases, key=numpy_phases.get)),
        cupy=dict(device_phases={k: int(v) for k, v in dev_phases.items()},
                  device_peak=int(max(dev_phases.values())),
                  host_phases={k: int(v) for k, v in cupy_host.items()},
                  host_peak=int(max(cupy_host.values()))),
        per_atom_B=dict(cell=MEM_CELL_B_PER_ATOM, realised=MEM_REALISED_B_PER_ATOM,
                        realise_peak=MEM_REALISE_PEAK_B_PER_ATOM,
                        note="host; the caller's structure-builder objects are extra"),
        cell_atom_arrays_B=int(cell_B))


def estimate_resources(cell: ReflectionCell, params: MultisliceParams, *, realisations: int,
                       calibrate_cpu: bool) -> dict:
    """Memory (memory_model: peak of one realisation, phase by phase) and time estimates for CPU
    and GPU.

    memory_bytes["total"] is the peak of one realisation on the numpy backend (everything on the
    host, including the cell's atom arrays); memory_bytes["device_peak_cupy"] is the GPU memory
    of the cupy backend (the same statements, UNVERIFIED on a GPU, a lower bound) and
    memory_bytes["host_peak_cupy"] the host memory of that run.
    CPU: if calibrate_cpu, the FFT, GEMM and element-wise costs are MEASURED on this machine at
    the requested grid with the requested precision and thread count, then scaled by the slice
    and atom counts of the cell. GPU: a bandwidth/launch model with the labelled ASSUMPTION
    constants GPU_ASSUMED (not measured). Neither includes the structure build."""
    grid = make_grid(cell, nx=params.nx, ny=params.ny)
    N = _n_slices(cell, params.dz_A)
    cb = np.dtype(params.precision).itemsize
    npx = grid.nx * grid.ny
    counts = _slice_counts(cell, params.dz_A, N)
    nonempty = int(np.count_nonzero(counts)) if len(cell.Z) else (1 if N else 0)
    n_max = int(counts.max()) if len(cell.Z) else 0
    n_mean = float(counts[counts > 0].mean()) if len(cell.Z) else 0.0
    mm = memory_model(nx=grid.nx, ny=grid.ny, n_slices=N, n_atoms=int(len(cell.Z)),
                      atoms_per_slice_max=n_max, n_species=len(np.unique(cell.Z)) if len(cell.Z)
                      else 1, precision=params.precision,
                      overlayer=overlayer_memory_arguments(cell))
    fft_flops = 5.0 * npx * np.log2(max(npx, 2))
    n_fft = 2 * N + 3 * nonempty          # propagation per slice + (FFT, IFFT of t, IFFT of V)
    gemm_flops = 8.0 * npx * float(counts.sum())
    out = dict(grid=dict(nx=grid.nx, ny=grid.ny, dx_A=grid.dx_A, dy_A=grid.dy_A),
               n_slices=N, nonempty_slices=nonempty, atoms_per_nonempty_slice_mean=n_mean,
               atoms_per_slice_max=n_max, n_atoms=int(len(cell.Z)), realisations=int(realisations),
               precision=params.precision,
               memory_bytes=dict(total=mm["numpy"]["peak"],
                                 device_peak_cupy=mm["cupy"]["device_peak"],
                                 host_peak_cupy=mm["cupy"]["host_peak"],
                                 model=mm,
                                 note="per concurrent realisation: 'total' is the numpy-backend "
                                      "peak (host); a cupy run needs device_peak_cupy on the GPU "
                                      "and host_peak_cupy on the host; exit waves stored: "
                                      f"{cb * npx} B each"),
               flops=dict(fft=n_fft * fft_flops, gemm=gemm_flops))
    if calibrate_cpu:
        be = get_backend("numpy", params.precision, params.threads)
        rng = np.random.default_rng(0)
        a = (rng.standard_normal(grid.shape) + 1j * rng.standard_normal(grid.shape)).astype(
            params.precision)
        be.fft2(a)
        t0 = time.perf_counter()
        for _ in range(6):
            b = be.fft2(a)
        t_fft = (time.perf_counter() - t0) / 6
        t0 = time.perf_counter()
        for _ in range(6):
            b = a * b * a
        t_elem = (time.perf_counter() - t0) / 6 / 2
        m = max(n_max, 1)
        Ex = a[:, :1].repeat(m, axis=1)
        Ey = a[:1, :].T.repeat(m, axis=1)
        t0 = time.perf_counter()
        for _ in range(3):
            np.exp(1j * np.angle(Ex))
            np.exp(1j * np.angle(Ey))
            Ex @ Ey.T
        t_pot = (time.perf_counter() - t0) / 3 * (n_mean / m if m else 0.0)
        per_empty = 2 * t_fft + 4 * t_elem
        per_full = per_empty + 3 * t_fft + 6 * t_elem + t_pot
        t_real = (N - nonempty) * per_empty + nonempty * per_full
        out["cpu"] = dict(measured_on_this_machine=True, threads=params.threads,
                          fft_s=t_fft, elementwise_pass_s=t_elem,
                          potential_slice_s=t_pot, seconds_per_realisation=t_real,
                          seconds_total=t_real * realisations,
                          note="component timings measured here, scaled by slice and atom counts")
    g = GPU_ASSUMED
    t_fft_g = max(g["launch_s"], 2 * cb * npx * np.log2(max(npx, 2)) / 4 /
                  (g["bandwidth_Bps"] * g["fft_efficiency"]))
    t_el_g = max(g["launch_s"], 3 * cb * npx / g["bandwidth_Bps"])
    t_pot_g = max(g["launch_s"], 8.0 * npx * n_mean / g["gemm_flops"])
    per_e = 2 * t_fft_g + 4 * t_el_g
    per_f = per_e + 3 * t_fft_g + 6 * t_el_g + t_pot_g
    t_real_g = (N - nonempty) * per_e + nonempty * per_f
    out["gpu"] = dict(model=dict(g), seconds_per_realisation=t_real_g,
                      seconds_total=t_real_g * realisations,
                      memory_bytes=mm["cupy"]["device_peak"],
                      memory_note="device peak of the memory model (cupy backend; UNVERIFIED on "
                                  "a GPU, lower bound: library workspaces and pool not included)",
                      note="ASSUMPTION-based model, NOT MEASURED")
    return out
