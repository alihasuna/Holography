# Model assumptions, approximations, limitations and open questions

Status: 2026-09-21, initial version written during the analysis of
`hussienba/si110-reflection-holography` (commit 6694959). This file must be updated with every
physics change (instruction file section 10). Labels follow section 1.4 of the instruction file.

## 1. Assumptions inherited from the inspected repository (all must be re-examined)

| # | Assumption | Label | Status |
|---|---|---|---|
| A1 | Transmission multislice with slices perpendicular to the beam is usable for grazing-incidence reflection. | ASSUMPTION | Partly supportable: the paraxial propagator error is below 0.04 rad over the 198 A cell (C section 5.1), but the boundary conditions and scattering channel of the current cell are wrong (C section 5.2 to 5.5, D section 2f). Must be validated against a dynamical reflection benchmark, never a transmission one. |
| A2 | A free-standing plate (vacuum above and below) with periodic boundaries along the surface normal represents a semi-infinite crystal surface. | ASSUMPTION | Not supportable with the default cell: 81 percent of the incident wave enters the end face, only 3 percent reflects from the top surface, and the Laue-transmitted (n,-n,n) beam is collinear with the specular beam (C section 5.2 and 5.3). |
| A3 | The (666) specular condition is a usable Bragg reflection for Si(111). | ASSUMPTION | False: (666) is kinematically forbidden in diamond-cubic Si (F = 0; C section 3.4). Use (444), (555), (777) or (888). |
| A4 | The step phase is `Delta_phi = 4 pi h sin(theta_B)(g_hat.n_hat)/lambda` with the vacuum Bragg angle. | ASSUMPTION | Kinematic rigid-translation form is correct only with the EXTERNAL glancing angles of the actual beams and only for lattice-translation steps and specular (or fully in-plane-resolved) reflections. At the vacuum Bragg angle a single-bilayer step is invisible (2 pi n); refraction is the entire signal (C sections 2 to 4). |
| A5 | The saved `image_wavefunctions` array is the exit-surface wave. | ASSUMPTION | False: it is Fresnel back-propagated to the supercell mid-plane (D section 2a). |
| A6 | A phase obtained as `arg()` of a Fourier-filtered simulated complex wave is a holographic phase measurement. | ASSUMPTION | False in the sense of instruction 9.1: no reference wave, no intensity hologram, no reconstruction is involved (D section 4; C section 7.3). |
| A7 | The thermal RMS displacement 0.076 A per axis is applied. | ASSUMPTION | Inert: thermal effects are never enabled (D section 2d). |
| A8 | The absorbing layer configured in meta.json is applied on the bulk side. | ASSUMPTION | Inert: the keyword is rejected by the API and silently dropped; the configured axis (z) is also not the bulk side (x) in the cleave frame (D section 3.1; C section 5.3). |

## 2. Assumptions adopted in this repository's analysis (to be sourced or measured)

| # | Assumption | Label | Sensitivity |
|---|---|---|---|
| B1 | Si mean inner potential `V0 = 12.0 V`. | ASSUMPTION | dDelta_phi/dV0 about -0.34 rad/V at the (444) condition, 200 keV; angle shift about -0.13 mrad/V. Candidate source to read: Kruse et al., Ultramicroscopy 106 (2006) 105-113 (METADATA_VERIFIED only, no value taken from it). |
| B2 | Silicon lattice parameter 5.4309 A at room temperature. | ASSUMPTION (standard) | Negligible for phases (1e-5 relative). |
| B3 | Surface terminations are bulk-terminated: Si(111) bilayer termination, Si(001) unreconstructed. | ASSUMPTION | The Si(001) 2x1 dimer reconstruction and the Si(111) 7x7 reconstruction change the reflectivity amplitude and its phase; they cancel between identical terraces only. |
| B4 | Two terraces separated by a lattice-translation step have identical complex reflectivity (so the dynamical reflection phase cancels). | DERIVED_HERE | Exact for an infinite terrace of a perfect crystal; violated near the step riser, for Si(001) a/4 steps (terraces related by the diamond 4_1 screw, not a translation), for reconstructed or strained terraces, and for any overlayer. |
| B5 | The reference wave is one of the idealisations R1 (vacuum plane wave), R2 (self-reference from a flat region), R3 (reference with residual curvature and tilt). | ASSUMPTION | The custom biprism's real behaviour is PROJECT_INPUT (see docs/06_project_inputs_required.md). |
| B6 | Inelastic scattering is represented by an absorptive potential and a loss of coherence, not simulated explicitly. | ASSUMPTION | Required for penetration-depth and rocking-curve widths; parameters must be sourced (instruction B15 warning). |
| B7 | The surfaces are clean. | ASSUMPTION | Ion-milled, air-exposed Si carries native oxide and an amorphous damage layer; at 20 mrad the beam path inside a 1 nm layer is about 50 nm. This can suppress the Bragg-reflected object wave entirely; it must be a modelled option and a PROJECT_INPUT. |

## 3. Known limitations of the analysis performed here

* No multislice or dynamical reflection simulation was executed in this analysis. Every engine
  statement in `docs/agent_reports/D_software_provenance.md` is from reading version-matched source
  code (prismatique 0.0.1, embeam 0.0.1, Prismatic 1.2.0 tree at commit d155fb9) and from
  exercising the Python API without the compiled engine.
* All scholarly hosts (publishers, doi.org, Crossref, Semantic Scholar, OpenAlex, PMC, arXiv) were
  blocked by the network policy of the analysis environment. No paper or book chapter was read.
  Literature statements are index-level (`METADATA_VERIFIED(index)`, `+ABSTRACT(index)`) and are
  labelled as such in `docs/agent_reports/B_literature.md`. In particular the content of Osakabe
  et al. 1988 (P01) is UNVERIFIED here: its surface, energy, reflection, reference-wave arrangement,
  equation and measured values are unknown to this analysis.
* All physics in `docs/agent_reports/C_physics_derivations.md` and `docs/03_physics_summary.md` is
  DERIVED_HERE from stated premises and reproduced by `tools/reflection_step_phase_calculator.py`;
  it has not been checked against the textbook sections of B07 (Ichimiya and Cohen) or B08 (Peng,
  Dudarev and Whelan), which must be done before publication.

## 4. Open questions

1. What exactly did Osakabe et al. 1988 measure (surface, energy, reflection, reference geometry, phase values)? Needed to define the reproduction benchmark.
2. Which reflection and glancing angle does the laboratory use, and is it a Bragg-Bragg or Bragg-channelling resonance condition (Yao and Cowley 1990, P26)? The double-contour step contrast of REM is tied to this.
3. How large is the dynamical reflection phase difference between the two 90-degree-rotated terraces of an Si(001) single-layer step at the working azimuth? Only a dynamical calculation can answer this.
4. What is the reflected amplitude from an oxide-covered, ion-milled surface at the working angle, and is there enough coherent Bragg-reflected intensity to form a hologram at all?
5. How is the intrinsic 2 theta angle between a vacuum reference and the specular object wave compensated in the laboratory's optics, and what carrier fringe spacing results?
