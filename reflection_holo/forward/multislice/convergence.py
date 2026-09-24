"""Convergence ensembles on the multislice engine: one INDEPENDENT engine run per incidence
direction ("member"; report E3; H2 N3; PROJECT_INPUT item 3).

A member is fully defined by the declared ``optics.coherence.ConvergenceQuadrature`` (semi-angle,
source profile, n_radial, n_azimuthal, design phase extent, tolerance), the central beam (a
``SheetBeam`` at the central glancing angle th0, item 7) and the member index. Its engine run
launches a ``TiltedSheetBeam`` with the member's own glancing angle th_s = asin(-u_x) and y direction
cosine u_y = t_b (optics.coherence equation (2)); the outgoing specular angle is th_s as well
(parallel momentum conserved), so the band assertion and the geometry checks of ``reflection_setup``
run with the member's angles. Members share nothing at run time: they can run as separate jobs
(``simulate_member``, one manifest each, the member record and the quadrature hash in the
manifest's caller record) and be assembled later (pipeline ``run --members-dir``).

Interface for a job array (report E3 section 5):
    quadrature.n_members                          number of jobs
    simulate_member(..., member_index=K, ...)     the K-th job (writes exit waves + manifest)
    check_members(...)                            every member's assertions, no propagation
"""
from __future__ import annotations

import dataclasses
import hashlib
import json

from reflection_holo.optics.coherence import ConvergenceMember, ConvergenceQuadrature

from .engine import MultisliceParams, reflection_setup, simulate
from .illumination import SheetBeam, TiltedSheetBeam


def quadrature_sha256(quadrature: ConvergenceQuadrature, theta0_rad: float) -> str:
    """SHA-256 of the canonical JSON of the quadrature record (with its member list at th0): the
    identity that every member job and the assembly must share."""
    rec = quadrature.as_record(theta0_rad)
    return hashlib.sha256(json.dumps(rec, sort_keys=True, default=str).encode()).hexdigest()


def _central(beam, params: MultisliceParams) -> float:
    if not isinstance(beam, SheetBeam) or isinstance(beam, TiltedSheetBeam):
        raise TypeError("the central beam must be an untilted SheetBeam (the members are generated "
                        "from it)")
    th0 = float(beam.theta_in_ext_rad)
    if float(params.theta_out_ext_rad) != th0:
        raise ValueError("convergence members are implemented for the specular beam: the central "
                         f"params.theta_out_ext_rad ({params.theta_out_ext_rad!r}) must equal the "
                         f"central glancing angle ({th0!r})")
    return th0


def member_beam(beam: SheetBeam, member: ConvergenceMember, quadrature: ConvergenceQuadrature
                ) -> TiltedSheetBeam:
    """The member's TiltedSheetBeam: same sheet (height, edges, bottom), glancing angle th_s, y
    direction cosine t_b; labels carry the item-7 label of the central angle and the item-3 label
    of the quadrature."""
    th0 = float(beam.theta_in_ext_rad)
    tag = (f"convergence member {member.index} of {quadrature.n_members} "
           f"({quadrature.source_profile}, alpha = {quadrature.semi_angle_rad!r} rad, n_radial = "
           f"{quadrature.n_radial}, n_azimuthal = {quadrature.n_azimuthal})")
    return TiltedSheetBeam(height_A=beam.height_A, edge_A=beam.edge_A, x_bottom_A=beam.x_bottom_A,
                           theta_in_ext_rad=member.glancing_angle_rad(th0),
                           theta_label=f"{beam.theta_label}; {tag}",
                           direction_cosine_y=member.direction_cosine_y(),
                           tilt_label=f"{quadrature.semi_angle_label}; {tag}")


def member_params(params: MultisliceParams, member: ConvergenceMember, theta0_rad: float
                  ) -> MultisliceParams:
    """The central parameters with the outgoing (specular) angle of the member."""
    return dataclasses.replace(params, theta_out_ext_rad=member.glancing_angle_rad(theta0_rad))


def check_members(cell, *, potential, beam: SheetBeam, params: MultisliceParams,
                  quadrature: ConvergenceQuadrature) -> list[dict]:
    """reflection_setup (band assertion with the member's angles, geometry checks) for EVERY
    member; raises on the first failure (SamplingError or GeometryError naming the member).
    Returns one record per member (band record, glancing angle, y direction cosine)."""
    th0 = _central(beam, params)
    out = []
    for m in quadrature.members():
        b = member_beam(beam, m, quadrature)
        p = member_params(params, m, th0)
        try:
            s = reflection_setup(cell, potential=potential, beam=b, params=p)
        except Exception as exc:
            msg = (f"convergence member {m.index} (t_a = {m.t_a_rad:.3e}, t_b = {m.t_b_rad:.3e} "
                   f"rad, glancing angle {m.glancing_angle_rad(th0):.6e} rad): {exc}")
            try:
                err = type(exc)(msg)
            except Exception:                              # pragma: no cover
                err = ValueError(msg)
            raise err from exc
        out.append(dict(member=m.as_record(th0), band=s["band"],
                        geometry_passed=all(v["passed"] for k, v in s["geometry"].items()
                                            if isinstance(v, dict) and "passed" in v)))
    return out


def simulate_member(cell, *, potential, beam: SheetBeam, params: MultisliceParams,
                    quadrature: ConvergenceQuadrature, member_index: int, realisations: int,
                    seed: int | None, outputs_root, run_name: str, save_waves: bool, config,
                    input_paths, caller_record: dict | None):
    """One member = one engine run (``simulate``: exit waves on the declared plane and the run
    manifest). The manifest's caller record carries the member record, the quadrature record and
    its SHA-256, and the central angle. Every argument is required. Returns (waves, manifest path);
    run_name gets the suffix _m<index:04d>."""
    th0 = _central(beam, params)
    m = quadrature.member(member_index)
    rec = dict(caller_record) if caller_record is not None else {}
    rec.update(convergence=dict(member=m.as_record(th0), quadrature=quadrature.as_record(),
                                quadrature_sha256=quadrature_sha256(quadrature, th0),
                                central_theta_in_ext_rad=th0,
                                rule="one independent engine run per member; the ensemble "
                                     "hologram is the weighted mean of the member intensities "
                                     "(optics.coherence (1))"))
    return simulate(cell, potential=potential, beam=member_beam(beam, m, quadrature),
                    params=member_params(params, m, th0), realisations=realisations, seed=seed,
                    outputs_root=outputs_root, run_name=f"{run_name}_m{m.index:04d}",
                    save_waves=save_waves, config=config, input_paths=input_paths,
                    caller_record=rec)
