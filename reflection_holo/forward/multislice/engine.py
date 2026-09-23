"""Grazing-incidence reflection multislice: the slice loop, per-realisation exit waves, the run
manifest and the resource estimate (docs/05 section 4.3; milestone M2).

Scheme (symmetric split step, DERIVED_HERE): with P(d) the band-limited vacuum propagator and T_i
the band-limited transmission function of slice i = [i dz, (i+1) dz),

    psi(L_z) = P(dz/2) T_{N-1} P(dz) ... P(dz) T_1 P(dz) T_0 P(dz/2) psi_0,     L_z = N dz,

T_i = BL[ exp(+i sigma V_p,i(x, y)) exp(-sigma W(x) dz) ], V_p,i complex (imaginary part = physical
absorption, item 21), W the NUMERICAL absorber, BL the band-limit aperture. The output is the wave on
the DECLARED exit plane z = L_z (no further propagation), one ExitWave per realisation.

Status: UNVALIDATED for atomistic reflection; the validation ladder rung 2 and the abTEM
cross-check are NOT RUN (docs/agent_reports/M2_multislice_engine.md). The label is copied into
every ExitWave.metadata["validation_status"].

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
from .illumination import SheetBeam, sheet_beam_wave
from .physics import beam_constants
from .potentials import NumericalAbsorber, absorber_profile_V
from .propagator import PROPAGATORS, propagator_kernel

ENGINE_NAME = "reflection_holo.forward.multislice"
VALIDATION_STATUS = (
    "UNVALIDATED: rung 1 (refraction-only analytic limit) and rung 3 (continuum null tests) of the "
    "docs/05 4.4 ladder pass in tests/forward; rung 2 (Bragg-case two-beam phase sweep), the abTEM "
    "cross-check (transmission and reflection-like configurations) and the flat-surface rocking "
    "curve against a dynamical solver were NOT RUN")
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
    band = check_band(grid, rule=params.band_limit, wavelength_A=bc["wavelength_A"],
                      angles_rad=dict(incident_ext=th_in, outgoing_ext=th_out,
                                      incident_int=th_int_in, outgoing_int=th_int_out))
    band["internal_angles_from"] = (f"SM04 refraction with the potential's mean inner potential "
                                    f"{V0:.4f} V")
    geo = check_reflection_geometry(cell, beam_height_A=beam.height_A,
                                    beam_x_bottom_A=beam.x_bottom_A, theta_in_ext_rad=th_in,
                                    theta_out_ext_rad=th_out, theta_int_rad=th_int_in,
                                    buildup_depth_A=params.buildup_depth_A)
    return dict(bc=bc, grid=grid, n_slices=n, commensurability=comm, V0_potential_V=V0,
                theta_int_in_rad=th_int_in, theta_int_out_rad=th_int_out, band=band, geometry=geo)


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
    P_full, n_ev = propagator_kernel(grid, dz_A=params.dz_A, wavelength_A=lam,
                                     kind=params.propagator, band_mask=mask)
    P_half, _ = propagator_kernel(grid, dz_A=0.5 * params.dz_A, wavelength_A=lam,
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


def estimate_resources(cell: ReflectionCell, params: MultisliceParams, *, realisations: int,
                       calibrate_cpu: bool) -> dict:
    """Memory (from the arrays the engine allocates) and time estimates for CPU and GPU.

    CPU: if calibrate_cpu, the FFT, GEMM and element-wise costs are MEASURED on this machine at
    the requested grid with the requested precision and thread count, then scaled by the slice
    and atom counts of the cell. GPU: a bandwidth/launch model with the labelled ASSUMPTION
    constants GPU_ASSUMED (not measured). Neither includes the structure build."""
    grid = make_grid(cell, nx=params.nx, ny=params.ny)
    N = _n_slices(cell, params.dz_A)
    cb = np.dtype(params.precision).itemsize
    rb = cb // 2
    npx = grid.nx * grid.ny
    counts = _slice_counts(cell, params.dz_A, N)
    nonempty = int(np.count_nonzero(counts)) if len(cell.Z) else (1 if N else 0)
    n_max = int(counts.max()) if len(cell.Z) else 0
    n_mean = float(counts[counts > 0].mean()) if len(cell.Z) else 0.0
    arrays = {"psi": cb * npx, "transmission (band-limited)": cb * npx,
              "propagators P(dz), P(dz/2)": 2 * cb * npx, "band mask": rb * npx,
              "scattering factor per species": rb * npx * max(1, len(np.unique(cell.Z))),
              "FFT work arrays (x3)": 3 * cb * npx,
              "structure-factor factors Ex, Ey (largest slice)": cb * (grid.nx + grid.ny) * n_max,
              "structure-factor sum S": cb * npx,
              "atom positions (float64)": 8 * 3 * len(cell.Z) * 2}
    total = int(sum(arrays.values()))
    fft_flops = 5.0 * npx * np.log2(max(npx, 2))
    n_fft = 2 * N + 3 * nonempty          # propagation per slice + (FFT, IFFT of t, IFFT of V)
    gemm_flops = 8.0 * npx * float(counts.sum())
    out = dict(grid=dict(nx=grid.nx, ny=grid.ny, dx_A=grid.dx_A, dy_A=grid.dy_A),
               n_slices=N, nonempty_slices=nonempty, atoms_per_nonempty_slice_mean=n_mean,
               atoms_per_slice_max=n_max, n_atoms=int(len(cell.Z)), realisations=int(realisations),
               precision=params.precision,
               memory_bytes=dict(arrays, total=total,
                                 note="per concurrent realisation; exit waves stored: "
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
                      seconds_total=t_real_g * realisations, memory_bytes=total,
                      note="ASSUMPTION-based model, NOT MEASURED")
    return out
