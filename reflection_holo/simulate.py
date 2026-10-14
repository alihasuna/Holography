"""Task execution: one task = one multislice march of a batch of beams through one
structure realisation.  A task is a plain dict (JSON-serialisable) in which every
physical input is explicit; nothing physical has a default here (specification
section 0, item 5).  See reflection_holo/campaign.py for how tasks are generated.
"""
from __future__ import annotations

import hashlib
import time

import numpy as np

from .analysis import (smooth_window, truncation_bound, vdp_pattern, vdp_reflectivity,
                       vdp_spectrum)
from .backend import get_xp, to_numpy
from .beams import entrance_wave, plan_beam
from .constants import interaction_constant, k_rad_per_A, wavelength_A
from .crystal import SurfaceCell, TerraceStructure, flat, steps_parallel, steps_transverse
from .grid import Grid
from .multislice import Propagator, run_multislice
from .potential import (PotentialBuilder, absorber_profile, mean_inner_potential,
                        onset_profile)
from .reference1d import layers_from_profile, parratt

REQUIRED_PHYSICS = ("beam_energy_keV", "lattice_parameter_A", "parametrization",
                    "absorptive_fraction", "inelastic_absorption_W_V",
                    "absorption_onset_width_A")


def physics_value(task, name):
    """Physical inputs are dicts {value, label, source}; refuse anything else."""
    try:
        item = task["physics"][name]
    except KeyError as exc:
        raise KeyError(f"physical input {name!r} missing from the task: refusing to "
                       "substitute a default") from exc
    if not isinstance(item, dict) or not {"value", "label", "source"} <= set(item):
        raise ValueError(f"physical input {name!r} must carry value, label and source")
    return item["value"]


# --------------------------------------------------------------------------
# construction helpers
# --------------------------------------------------------------------------

def make_grid(num, Ly):
    Lx = num["Nx"] * num["dx_A"]
    return Grid(num["Nx"], num["Ny"], Lx, Ly, x0=num["x0_A"], y0=0.0)


def make_absorber(grid, num):
    return absorber_profile(grid.x, bottom_top=grid.x0 + num["absorber_bottom_width_A"],
                            bottom_width=num["absorber_bottom_width_A"],
                            top_start=grid.x0 + grid.Lx - num["absorber_top_width_A"],
                            top_width=num["absorber_top_width_A"],
                            W_max=num["absorber_W_max_V"], power=num["absorber_power"])


def level_map(st, Ly):
    kind = st["kind"]
    if kind == "flat":
        return flat(st.get("level", 0)), max(0, st.get("level", 0))
    if kind == "steps_parallel":
        lev = st["levels"]
        return steps_parallel(Ly, lev), max(lev)
    if kind == "steps_transverse":
        lev = st["levels"]
        return steps_transverse(st["edges_z_A"], lev), max(lev)
    raise ValueError(kind)


def make_structure(task, grid):
    a = physics_value(task, "lattice_parameter_A")
    cell = SurfaceCell(task["surface"], a)
    lm, max_level = level_map(task["structure"], grid.Ly)
    return TerraceStructure(cell, Ly=grid.Ly, x_bottom=grid.x0 + task["numerics"]["atoms_bottom_margin_A"],
                            level=lm, max_level=max_level,
                            y_offset=task["structure"].get("y_offset_A", 0.0))


class AtomicTransmission:
    """Transmission functions of the planes of a structure (cached when static).

    The inelastic absorption W_in S(x - cut(level(y, z))) follows the local terrace
    (onset at the mid-gap cut above the local top sheet)."""

    def __init__(self, structure, builder, grid, plane_idx, plane_z, dz, W_in, onset_w,
                 phonon=None):
        self.s, self.b, self.g = structure, builder, grid
        self.idx, self.z, self.dz = plane_idx, plane_z, dz
        self.W_in, self.onset_w = float(W_in), float(onset_w)
        self.phonon = phonon
        self.cache = {}
        self.wcache = {}
        self.n_atoms = 0
        self.n_distinct = 0

    def W_extra(self, z):
        if self.W_in == 0.0:
            return None, b""
        lev = self.s.level(self.g.y, z)
        key = np.ascontiguousarray(lev).tobytes()
        W = self.wcache.get(key)
        if W is None:
            cut = self.s.cut(lev)                                  # (Ny,)
            Wn = self.W_in * onset_profile(self.g.x[:, None] - cut[None, :], self.onset_w)
            W = self.b.xp.asarray(Wn.astype(self.b.rtype))
            self.wcache[key] = W
        return W, key

    def __call__(self, i):
        p, z = int(self.idx[i]), float(self.z[i])
        W, wkey = self.W_extra(z)
        if self.phonon is not None:
            ss = np.random.SeedSequence([int(self.phonon["seed"]), p + (1 << 40)])
            rng = np.random.default_rng(ss)
            x, y = self.s.plane_atoms(p, z, rng=rng, u_rms=self.phonon["u_rms_A"])
            self.n_atoms += len(x)
            return self.b.transmission(self.b.projected(x, y), self.dz, W_extra=W)
        x, y = self.s.plane_atoms(p, z)
        key = hashlib.sha1(np.ascontiguousarray(x).tobytes()
                           + np.ascontiguousarray(y).tobytes() + wkey).hexdigest()
        t = self.cache.get(key)
        if t is None:
            t = self.b.transmission(self.b.projected(x, y), self.dz, W_extra=W)
            self.cache[key] = t
            self.n_atoms += len(x)
            self.n_distinct += 1
        return t


def max_specular_angle(grid, lam):
    """Largest specular glancing angle the band can couple: 2 sin(theta)/lam <= q_band."""
    return float(np.arcsin(min(1.0, grid.q_band * lam / 2.0)))


def window_half_range(lam, w0, rel=1e-3):
    """Half range of glancing angle where the beam spectrum exceeds rel of its peak."""
    return np.sqrt(-np.log(rel)) * lam / (np.pi * w0)


def plan_windows(task, grid, lam, x_surface_top, delay_allowance):
    """Beams, detector lines and march lengths for the angle windows of a task.

    Each beam has its waist on the surface plane and clears the structure at the
    entrance plane; its virtual-detector line x_det lies above the beam's top edge at
    the entrance plane (where the descending beam is highest), so that only up-going
    waves cross it.  The march for the beam ends when the latest reflected
    contribution (emerging delay_allowance downstream of the far end of the
    footprint) has risen above x_det at the lowest angle of the window.
    """
    num = task["numerics"]
    beams, z_end, x_det, info = [], [], [], []
    th_lim = max_specular_angle(grid, lam)
    top_absorber = grid.x0 + grid.Lx - num["absorber_top_width_A"]
    ns = num["clearance_sigmas"]
    for win in task["beams"]:
        th0 = win["theta0_mrad"] * 1e-3
        half = window_half_range(lam, win["w0_A"])
        if th0 + half > th_lim:
            raise ValueError(f"window {win} exceeds the band-limited specular angle "
                             f"{th_lim*1e3:.1f} mrad of this grid")
        beam, z_hit = plan_beam(th0, win["w0_A"], lam, ns, num["clearance_margin_A"],
                                x_surface_top)
        w_in = beam.width_at(z_hit, lam)
        top_in = beam.axis_height(0.0) + ns * w_in
        xd = top_in + num["detector_margin_A"]
        if xd + num["detector_spacing_A"] + num["detector_top_margin_A"] > top_absorber:
            raise ValueError(f"window {win}: detector line {xd:.1f} A does not fit below "
                             f"the top absorber at {top_absorber:.1f} A")
        th_low = max(th0 - half, 0.5 * th0)
        footprint = ns * beam.w0 / np.tan(th0)
        ze = (z_hit + footprint + delay_allowance
              + (xd + num["detector_spacing_A"]) / np.tan(th_low)
              + win.get("exit_extra_A", 0.0))
        beams.append(beam)
        z_end.append(ze)
        x_det.append(xd)
        info.append(dict(theta0_mrad=win["theta0_mrad"], w0_A=win["w0_A"], z_hit_A=z_hit,
                         z_end_A=ze, x_det_A=xd, top_at_entrance_A=top_in,
                         theta_low_mrad=1e3 * th_low, half_range_mrad=1e3 * half))
    return beams, np.array(z_end), np.array(x_det), info


def extraction_window(grid, num):
    x_hi = grid.x0 + grid.Lx - num["absorber_top_width_A"] - num["window_top_margin_A"]
    return smooth_window(grid.x, num["window_bottom_A"], num["window_ramp_A"], x_hi,
                         num["window_ramp_A"]), x_hi


# --------------------------------------------------------------------------
# task runners
# --------------------------------------------------------------------------

def run_task(task, log=print):
    kind = task["kind"]
    if kind in ("flat_rocking", "averaged_1d", "uniform_1d", "step_image"):
        return _run_reflection(task, log)
    raise ValueError(kind)


def delay_allowance_A(task, sigma):
    """Cell length allowed for dynamically reflected waves to re-emerge.

    A contribution reflected at normal depth D re-emerges 2 D / tan(theta_int)
    downstream and is weighted by exp(-2 D Im K_int) with Im K_int ~ k sigma W / K_int
    (uniform imaginary potential W).  Requiring that weight to fall to exp(-n) gives a
    delay n / (sigma W), independent of the angle (DERIVED_HERE, docs/08 appendix A).
    Without inelastic absorption the configured minimum is used and the run is
    flagged as not stationary.
    """
    num = task["numerics"]
    W = float(physics_value(task, "inelastic_absorption_W_V"))
    base = float(num["exit_extra_A"])
    if W > 0:
        return max(base, num["delay_decay_lengths"] / (sigma * W)), True
    return base, False


def _run_reflection(task, log):
    t_start = time.time()
    for name in REQUIRED_PHYSICS:
        physics_value(task, name)
    num = task["numerics"]
    xp = get_xp(task["backend"])
    ctype = np.dtype(num["precision"])
    E = float(physics_value(task, "beam_energy_keV"))
    if E != 200.0:
        raise ValueError("the beam energy of this project is 200 keV (docs/06 item 1)")
    lam = float(wavelength_A(E))
    k = float(k_rad_per_A(E))
    sigma = interaction_constant(E)
    a = physics_value(task, "lattice_parameter_A")
    param = physics_value(task, "parametrization")
    alpha = float(physics_value(task, "absorptive_fraction"))
    W_in = float(physics_value(task, "inelastic_absorption_W_V"))
    onset_w = float(physics_value(task, "absorption_onset_width_A"))

    if task["kind"] == "uniform_1d":
        Ly = num["dx_A"]                     # one pixel, isotropic sampling
        cell_Py = None
    else:
        cell = SurfaceCell(task["surface"], a)
        cell_Py = cell.periods[1]
        Ly = cell_Py * task["structure"].get("n_y_periods", 1)
        if num["Ny"] and abs(Ly / num["Ny"] - num["dx_A"]) > 0.25 * num["dx_A"]:
            raise ValueError(f"dy = {Ly / num['Ny']:.4f} A differs from dx = "
                             f"{num['dx_A']:.4f} A by more than 25 percent")
    grid = make_grid(num, Ly)
    W_abs = make_absorber(grid, num)
    mode = task.get("mode", "static")
    dwB = 0.0
    if mode == "debye_waller":
        u = physics_value(task, "u_rms_A")
        dwB = 8.0 * np.pi**2 * u**2
    builder = PotentialBuilder(grid, xp, E, parametrization=param, debye_waller_B=dwB,
                               absorptive_fraction=alpha, absorber_W=W_abs, dtype=ctype,
                               atom_chunk=num.get("atom_chunk", 4096))
    delay, stationary = delay_allowance_A(task, sigma)
    out = dict(task_id=task["task_id"], kind=task["kind"], grid=grid.describe(),
               wavelength_A=lam, k_rad_per_A=k, sigma_rad_per_VA=sigma,
               max_specular_angle_mrad=1e3 * max_specular_angle(grid, lam),
               V0_parametrization_V=mean_inner_potential(param, a),
               delay_allowance_A=delay, stationary_by_absorption=stationary)

    # -- structure, plane schedule and transmission ------------------------------
    profile_V = None
    W_in_profile = None
    if task["kind"] == "uniform_1d":
        prof = task["profile"]
        profile_V = prof["V0_V"] / (1.0 + np.exp(np.clip(grid.x / prof["width_A"], -60, 60)))
        W_in_profile = W_in * onset_profile(grid.x, onset_w)
        dz_plane = num["uniform_dz_A"]
        t_uni = builder.transmission(builder.uniform(profile_V, dz_plane), dz_plane,
                                     W_extra=xp.asarray(np.repeat(W_in_profile[:, None], grid.Ny, 1)))
        transmission = lambda i: t_uni  # noqa: E731
        x_surface_top = prof["clearance_ref_A"]
        z_offset = 0.5 * dz_plane
        structure = None
    else:
        structure = make_structure(task, grid)
        dz_plane = structure.slice_thickness()
        x_surface_top = float(structure.cut(_max_level(task)))
        z_offset = num["crystal_start_z_A"]
        if task["kind"] == "averaged_1d":
            stat = PotentialBuilder(grid, xp, E, parametrization=param, debye_waller_B=dwB,
                                    absorptive_fraction=0.0, absorber_W=None, dtype=ctype)
            vbar = np.zeros(grid.Nx)
            for t_i, zt in enumerate(structure.plane_z):
                x_, y_ = structure.plane_atoms(t_i, zt)
                vbar += to_numpy(stat.projected(x_, y_)).mean(axis=1)
            profile_V = vbar / structure.Pz              # laterally averaged V(x) [V]
            # march on a one-pixel-wide grid: the averaged potential has no y structure
            grid = Grid(grid.Nx, 1, grid.Lx, grid.dx, x0=grid.x0)
            builder = PotentialBuilder(grid, xp, E, parametrization=param, debye_waller_B=dwB,
                                       absorptive_fraction=alpha, absorber_W=W_abs, dtype=ctype)
            out["grid_march"] = grid.describe()
            W_in_profile = W_in * onset_profile(grid.x - structure.cut0, onset_w)
            t_uni = builder.transmission(builder.uniform(profile_V, dz_plane), dz_plane,
                                         W_extra=xp.asarray(np.repeat(W_in_profile[:, None], grid.Ny, 1)))
            transmission = lambda i: t_uni  # noqa: E731
            x_surface_top = float(structure.cut0)

    beams, z_plan, x_det, binfo = plan_windows(task, grid, lam, x_surface_top, delay)
    out["beams"] = binfo
    # adaptive cell length: each beam marches at least to its planned length and
    # stops when its detector record has decayed below tail_tol of its peak, or at
    # the cap (cell_cap_factor times the planned length)
    z_cap = z_plan * num["cell_cap_factor"]
    z_end = float(z_cap.max()) + dz_plane
    if structure is None:
        plane_z = np.arange(z_offset, z_end, dz_plane)
        plane_idx = np.arange(len(plane_z))
    else:
        plane_idx, plane_z = structure.plane_positions(z_offset, z_end, z_offset=z_offset)
        if task["kind"] != "averaged_1d":
            phonon = None
            if mode == "frozen_phonon":
                phonon = dict(seed=int(task["seed"]), u_rms_A=float(physics_value(task, "u_rms_A")))
            transmission = AtomicTransmission(structure, builder, grid, plane_idx, plane_z,
                                              dz_plane, W_in, onset_w, phonon=phonon)
    out["n_planes"] = int(len(plane_z))
    out["slice_thickness_A"] = float(dz_plane)

    psi0, a_list = [], []
    for beam in beams:
        p0, aq = entrance_wave(beam, grid, lam, xp, ctype)
        psi0.append(p0)
        a_list.append(aq)
    psi0 = xp.stack(psi0)
    x_mask = grid.x < x_surface_top + 1.0
    I0 = to_numpy(xp.abs(psi0[:, :, 0]) ** 2)
    out["incident_fraction_below_surface"] = (I0[:, x_mask].sum(1) / I0.sum(1)).tolist()
    if max(out["incident_fraction_below_surface"]) > num["max_end_face_fraction"]:
        raise ValueError("incident beam overlaps the crystal end face: "
                         f"{out['incident_fraction_below_surface']}")

    # virtual-detector rows (two lines detector_spacing apart)
    ix1 = np.searchsorted(grid.x, x_det)
    n_sp = max(1, int(round(num["detector_spacing_A"] / grid.dx)))
    rows = np.stack([ix1, ix1 + n_sp], axis=1)
    x_det_grid = grid.x[ix1]
    delta = grid.x[ix1 + n_sp] - grid.x[ix1]

    prop = Propagator(grid, lam, xp, ctype, kind=num.get("propagator", "exact"))
    exits, records, z_stop, side, stats = run_multislice(
        psi0, plane_z, transmission, z_cap, prop, xp, record_rows=rows,
        z_min=z_plan, tail_tol=num["tail_tol"], tail_window=num["tail_window_planes"],
        check_every=num["tail_check_every"],
        side_view_every=num.get("side_view_every", 0),
        progress=lambda n, N, s: log(f"  plane {n}/{N} {s:.1f}s"))
    out["march"] = stats
    if isinstance(transmission, AtomicTransmission):
        out["distinct_static_planes"] = transmission.n_distinct
        out["atoms_projected"] = transmission.n_atoms
    if side is not None:
        out["side_view_z_A"] = side["z"]
        out["side_view_I"] = side["I"]

    out["windows"] = []
    for b, (beam, ze, aq) in enumerate(zip(beams, z_stop, a_list)):
        rec = records[b]                                  # (2, n_planes, Ny)
        n_used = int(np.searchsorted(plane_z, ze, side="right"))
        rec = rec[:, :n_used, :]
        zr = plane_z[:n_used]
        f = to_numpy(rec.mean(axis=2))                    # ky = 0 component, (2, n)
        bi = binfo[b]
        th0 = bi["theta0_mrad"] * 1e-3
        half = bi["half_range_mrad"] * 1e-3
        dth = num["theta_step_mrad"] * 1e-3
        # absolute angle grid (multiples of theta_step) shared by every window
        th = np.arange(np.ceil((th0 - half) / dth), np.floor((th0 + half) / dth) + 1) * dth
        th = th[th > 0]
        q = np.sin(th) / lam
        A_neg = grid.Lx * beam.spectrum(-q, lam)
        weight = np.abs(A_neg) / (grid.Lx * np.abs(beam.spectrum(np.array([-np.sin(th0) / lam]), lam))[0])
        x1, x2 = float(x_det_grid[b]), float(x_det_grid[b] + delta[b])
        r, d_rel, r_single = vdp_reflectivity(f[0], f[1], zr, q, lam, x1, x2, 0.0, A_neg)
        r_bound, tail_rho = truncation_bound(f[0], zr, q, lam, A_neg,
                                             num.get("truncation_segment_planes", 1000))
        absf = np.abs(f[0])
        nedge = max(1, n_used // 50)
        wres = dict(theta0_mrad=bi["theta0_mrad"], w0_A=bi["w0_A"], z_end_A=float(ze),
                    z_planned_A=float(z_plan[b]), z_cap_A=float(z_cap[b]),
                    stopped_at_cap=bool(ze >= z_cap[b] - dz_plane),
                    x_det_A=x1, x_det2_A=x2, theta=th, q=q, r=r, weight=weight,
                    r_truncation_bound=r_bound, tail_rho=tail_rho,
                    down_over_incident=np.abs(d_rel),
                    single_line_minus_r=np.abs(r_single - r),
                    record_head_rel=float(absf[:nedge].max() / absf.max()),
                    record_tail_rel=float(absf[-nedge:].max() / absf.max()),
                    record_ky0_line1=f[0].astype(np.complex64),
                    record_ky0_line2=f[1].astype(np.complex64),
                    record_z_A=zr)
        if task["kind"] == "step_image" or task.get("save_spectrum", False):
            # complex spectrum for image formation, total angle <= theta0 + margin
            spec = vdp_spectrum(rec[0], rec[1], x1, x2, zr, lam, grid,
                                theta_max=th0 + num["spectrum_theta_margin_mrad"] * 1e-3,
                                qy_max_mrad=num.get("spectrum_qy_max_mrad", None), xp=xp)
            wres.update(spec)
        if cell_Py is not None and task["kind"] != "step_image":
            # intensity pattern (RHEED rods and diffuse) binned in the exit angle
            spec_p = vdp_spectrum(rec[0], rec[1], x1, x2, zr, lam, grid,
                                  theta_max=num["pattern_theta_max_mrad"] * 1e-3, xp=xp)
            wres["pattern_down_to_up_power"] = spec_p["spectrum_down_to_up_power"]
            wres["pattern"] = vdp_pattern(spec_p, lam, num["pattern_bin_mrad"],
                                          num["pattern_theta_max_mrad"])
            wres["pattern_qy"] = spec_p["spec_qy"]
            wres["pattern_bin_mrad"] = num["pattern_bin_mrad"]
            del spec_p
        if profile_V is not None:
            top = num["reference_top_A"]
            up8 = int(num.get("reference_upsample", 8))
            xf = np.arange(grid.x[0], top, grid.dx / up8)
            if task["kind"] == "uniform_1d":
                prof = task["profile"]
                Vf = prof["V0_V"] / (1.0 + np.exp(np.clip(xf / prof["width_A"], -60, 60)))
                Wf = W_in * onset_profile(xf, onset_w)
            else:
                Vf = _fourier_upsample(profile_V, grid, xf)
                Wf = W_in * onset_profile(xf - structure.cut0, onset_w)
            Vcf = Vf * (1.0 + 1j * alpha) + 1j * (Wf + np.interp(xf, grid.x, W_abs))
            Vl, d, xb = layers_from_profile(xf, Vcf, x_top=top - 1e-9)
            for model in ("multislice", "schroedinger"):
                wres[f"r_parratt_{model}"] = parratt(2 * np.pi * q, k, sigma, Vl, d,
                                                     x_top=xb, x_ref=0.0, model=model)
        out["windows"].append(wres)
    if profile_V is not None:
        out["profile_x_A"] = grid.x
        out["profile_V"] = profile_V
        out["profile_W_in"] = W_in_profile
    out["seconds_total"] = time.time() - t_start
    return out


def _max_level(task):
    """Highest terrace level that the incident beam must clear.  A flat reference
    for a step image carries clearance_level = the step's highest level so that its
    beam, detector line and planes coincide with those of the step run."""
    st = task["structure"]
    lev = st.get("level", 0) if st["kind"] == "flat" else max(st["levels"])
    return max(lev, st.get("clearance_level", lev))


def _fourier_upsample(v, grid, xf):
    """Band-limited (trigonometric) interpolation of a periodic profile."""
    c = np.fft.fft(v) / grid.Nx
    c = c * (np.abs(grid.qx) <= grid.q_band)
    out = np.zeros(len(xf), complex)
    for s in range(0, len(xf), 4096):
        xs = xf[s:s + 4096]
        out[s:s + 4096] = np.exp(2j * np.pi * np.outer(xs - grid.x0, grid.qx)) @ c
    return out.real
