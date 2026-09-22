# Model assumptions, approximations, limitations and open questions

Status: revision 3, 2026-09-22 (Phase 1 literature pass with network access, reports B3 and L1 to L5);
revision 2, 2026-09-21 (corrected after `docs/agent_reports/E_review.md`), written during the
analysis of `hussienba/si110-reflection-holography` (commit 6694959). This file must be updated with
every physics change (instruction file section 10). Labels follow section 1.4 of the instruction file.

## 1. Assumptions inherited from the inspected repository (all must be re-examined)

| # | Assumption | Label | Status |
|---|---|---|---|
| A1 | Transmission multislice with slices perpendicular to the beam is usable for grazing-incidence reflection. | ASSUMPTION | Partly supportable: the paraxial propagator error `k dz sin^4(alpha)/8` over the 198 A cell is 0.026 rad at the 45 mrad specular scattering angle and 0.106 rad at the 64 mrad band edge (common-mode between terraces, so it cancels in a step phase but not in an absolute phase); the boundary conditions and scattering channel of the current cell are wrong (C sections 5.2 to 5.5, D section 2f). Must be validated against a dynamical reflection benchmark, never a transmission one. |
| A2 | A free-standing plate (vacuum above and below) with periodic boundaries along the surface normal represents a semi-infinite crystal surface. | ASSUMPTION | Not supportable with the default cell: 81 percent of the incident wave (on the declared geometry; 85 percent on the realised atom positions) enters the end face, only 3 percent reflects from the top surface, and the Laue-transmitted (n,-n,n) beam is collinear with the specular beam (C sections 5.2 and 5.3). |
| A3 | The (6,-6,6) specular condition is a usable Bragg reflection for Si(111). | ASSUMPTION | False: (6,-6,6) is kinematically forbidden in diamond-cubic Si (F = 0; C section 3.4). Use (4,-4,4), (5,-5,5), (7,-7,7) or (8,-8,8). |
| A4 | The step phase is `Delta_phi = 4 pi h sin(theta_B)(g_hat.n_hat)/lambda` with the vacuum Bragg angle. | ASSUMPTION | The kinematic rigid-translation form is correct only with the EXTERNAL glancing angles of the actual beams, with the sign of the convention, and only for lattice-translation steps and specular (or fully in-plane-resolved) reflections. At an exact vacuum Bragg angle a single-bilayer step is invisible (2 pi n) and the measured phase at the reflectivity maximum is the refractive departure from that condition; away from bulk Bragg points the phase is the ordinary geometric path difference (C sections 2 to 4; `docs/03_physics_summary.md` section 2). |
| A5 | The saved `image_wavefunctions` array is the exit-surface wave. | ASSUMPTION | False: it is Fresnel back-propagated to the supercell mid-plane (D section 2a; SECTION_READ of the engine source, not confirmed on an executed output file). |
| A6 | A phase obtained as `arg()` of a Fourier-filtered simulated complex wave is a holographic phase measurement. | ASSUMPTION | False in the sense of instruction 9.1: no reference wave, no intensity hologram, no reconstruction is involved (D section 4; C section 7.3; A section 6). |
| A7 | The thermal RMS displacement 0.076 A per axis is applied. | ASSUMPTION | Inert: thermal effects are never enabled (D section 2d). |
| A8 | The absorbing layer configured in meta.json is applied on the bulk side. | ASSUMPTION | Inert: the keyword is rejected by the API and silently dropped; the configured axis (z) is also not the bulk side (x) in the cleave frame (D section 3.1; C section 5.3). |

## 2. Assumptions adopted in this repository's analysis (to be sourced or measured)

| # | Assumption | Label | Sensitivity |
|---|---|---|---|
| B1 | Si mean inner potential `V0 = 12.0 V`. | ASSUMPTION | `d|Delta_phi|/dV0` = -0.34 rad/V at (4,-4,4) and -0.20 rad/V at the (6,-6,6) setting, 200 keV; external peak angle shift -0.21 mrad/V at (4,-4,4), -0.13 mrad/V at (6,-6,6). A height inferred from a fixed measured phase is too small by about 0.049 A per volt by which `V0` is underestimated, at (4,-4,4) (`tools/phase1_numbers.py`; sign corrected in revision 3). Candidate source to read: Kruse et al., Ultramicroscopy 106 (2006) 105-113 (METADATA_VERIFIED only, no value taken from it). One DFT value is now read: 12.53 V, the Si endpoint (fit intercept) printed in Fig. 2c of Schowalter, Kruse and Rosenauer, arXiv:2607.05948v1 (WIEN2k GGA, bulk-terminated (110) slab, innermost monolayer; no uncertainty stated; SECTION_READ, L5 section 4). It is not adopted: 12.53 V instead of 12.0 V would change the bilayer step phase at (4,-4,4) by -0.178 rad and the a/2 step phase at (0,0,8) by -0.128 rad (`tools/phase1_numbers.py`). The mean inner potential is surface-dependent (abstracts of Pennington et al. 2015 and Auslender et al. 2024, SECTION_READ of the abstract only), so a slab value is a proxy for an oxide-covered, ion-milled Si(001) surface; a measured value (upload 11) or the rocking-curve calibration of the real sample (item 9) is required. |
| B2 | Silicon lattice parameter 5.4309 A at room temperature. | ASSUMPTION (standard) | Negligible for phases (1e-5 relative). |
| B3 | Surface terminations are bulk-terminated: Si(111) bilayer termination, Si(001) unreconstructed. | ASSUMPTION | The Si(001) 2x1 dimer reconstruction and the Si(111) 7x7 reconstruction change the reflectivity amplitude and its phase; they cancel between identical terraces only. |
| B4 | Two terraces separated by a lattice-translation step have identical complex reflectivity (so the dynamical reflection phase cancels). | DERIVED_HERE | Exact for an infinite terrace of a perfect crystal; violated near the step riser, for Si(001) a/4 steps (terraces related by the diamond 4_1 screw, not a translation), for reconstructed or strained terraces, and for any overlayer. |
| B5 | The reference wave is one of the idealisations R1 (vacuum plane wave), R2 (self-reference from a flat region), R3 (reference with residual curvature and tilt). | ASSUMPTION | The custom biprism's real behaviour is PROJECT_INPUT (see docs/06_project_inputs_required.md). Published arrangements: R1 is the Hitachi patent US 4,998,788 (a direct wave that does not illuminate the specimen; col. 1 l. 36-41, both embodiments; SM21); R2 is the arrangement of the P01 abstract (two regions of a Pt(111) reflection image overlapped by a biprism; SM22), which the same patent describes as the prior art (interference between reflected waves, about ten fringes; col. 1 l. 13-33); R3 has no source. An R1 reference must pass the dark-field objective aperture: the model declares a second aperture hole, a condenser-biprism pre-tilt of `2 theta_ext`, or no aperture. |
| B6 | Inelastic scattering is represented by an absorptive potential and a loss of coherence, not simulated explicitly. | ASSUMPTION | Required for penetration-depth and rocking-curve widths; parameters must be sourced (the warning attached to [B15] in the instruction file). |
| B7 | The surfaces are clean. | ASSUMPTION | Ion-milled, air-exposed Si carries native oxide and an amorphous damage layer; at 20 mrad the beam crosses a 1 nm layer over about 50 nm on the way in and again on the way out, about 100 nm of attenuating path in total. This can suppress the Bragg-reflected object wave entirely; it must be a modelled option and a PROJECT_INPUT. |
| B8 | The surface does not charge under the beam. | ASSUMPTION | An oxide-covered surface illuminated over a footprint of tens of micrometres at grazing incidence can charge; a charging patch adds a drifting phase indistinguishable from topography. Requires a phase-drift-versus-dose test on the real sample and a PROJECT_INPUT (item 22). |
| B9 | Shadowed regions are excluded from quantification. | DERIVED_HERE | A step transverse to the beam shadows `h/tan(theta_ext)` of surface (139 A per bilayer and 444 nm for a 10 nm mesa at 22.5 mrad; 230 A and 733 nm at the (4,-4,4) angle of 13.6 mrad); the model must ray-trace visibility at the operating angle. |
| B10 | The illumination convergence is small enough that the step phase is not averaged out. | PROJECT_INPUT | 1 rad of phase spread at 0.64 mrad semi-angle for a bilayer, 0.20 mrad for 1 nm, 0.020 mrad for 10 nm (200 keV). |

## 3. Known limitations of the analysis performed here

* No multislice or dynamical reflection simulation was executed in this analysis. Every engine
  statement in `docs/agent_reports/D_software_provenance.md` is from reading version-matched source
  code (prismatique 0.0.1, embeam 0.0.1; Prismatic from `prism-em/prismatic` at commit d155fb9,
  2026-01-30, `setup.py` version 1.2.0, the HRTEM-capable 2.x generation) and from exercising the
  Python API without the compiled engine. In particular the mid-plane back-propagation, the
  half-Nyquist mask and the normalisation are SECTION_READ of the C++ source and have not been
  confirmed against an executed output file.
* Revision 2 was written with every scholarly host blocked; the network is now Full (2026-09-22).
  Every bibliography record has been checked against Crossref or the publisher (report B3); P04, P07,
  the Hitachi patent, the prismatique documentation, the Prismatic pages, P49 (preprint), P02E, the C03
  accepted manuscript and the Hytch et al. 2010 companion of P31 are read in full (reports L1, L2, L5);
  the publisher tables of contents of B01 to B15 are recorded (L3). P01, P08, P09, P02, P03, P06 and
  P31 are closed and are known only from their abstracts; P05 is open access (CC BY) but its hosts
  block automated clients; no book chapter has been read. The body of Osakabe et al. 1988 (P01) is
  still UNREAD: its energy, reflection, glancing angle, equation and measured values are UNVERIFIED;
  its abstract gives Pt(111), a biprism overlapping two regions of the reflection image, optical
  reconstruction and a sensitivity of the order of 0.01 nm.
* All physics in `docs/agent_reports/C_physics_derivations.md` and `docs/03_physics_summary.md` is
  DERIVED_HERE from stated premises and reproduced by `tools/reflection_step_phase_calculator.py`;
  it has not been checked against the textbook sections of B07 (Ichimiya and Cohen) or B08 (Peng,
  Dudarev and Whelan), which must be done before publication. Two numerical slips in the C report
  were found by the adversarial review and are corrected in the summary documents, not in the report
  itself: the paraxial-error values in C section 5.1 (three times too small) and the 131 A step
  projection width in C section 2.1 (139 A at 22.5 mrad). See `docs/agent_reports/E_review.md`.

## 4. Open questions

1. What exactly did Osakabe et al. 1988 measure (surface, energy, reflection, reference geometry, phase values)? Needed to define the reproduction benchmark. Partial answer at abstract level: Pt(111), glancing incidence, a biprism overlapping two regions of the reflection image, optical reconstruction, sensitivity of the order of 0.01 nm on monatomic steps. Energy, reflection, angle, equation and measured values remain open (upload 1).
2. Which reflection and glancing angle does the laboratory use, and is it a Bragg-Bragg or Bragg-channelling resonance condition (Yao and Cowley 1990, P26)? The double-contour step contrast of REM is tied to this.
3. How large is the dynamical reflection phase difference between the two 90-degree-rotated terraces of an Si(001) single-layer step at the working azimuth? Only a dynamical calculation can answer this.
4. What is the reflected amplitude from an oxide-covered, ion-milled surface at the working angle, and is there enough coherent Bragg-reflected intensity to form a hologram at all?
5. How is the intrinsic `2 theta` angle between a vacuum reference and the specular object wave compensated in the laboratory's optics, and what carrier fringe spacing results? Two published schemes exist (US 4,998,788): objective over-focus with a diverging image-side biprism and a two-hole aperture, and a condenser-side biprism pre-tilt equal to the sum of the incidence and reflection angles followed by two image-side biprisms. Which one (if either) the laboratory's gun-side biprism realises is PROJECT_INPUT (items 15, 16).
6. Does the laboratory's illumination convergence permit any phase contrast for the nanometre-scale patterned features (item B10), or must the experiment target atomic steps?
7. Ptychography milestone (M6): the chapter C03 (accepted manuscript) states the multiplicative exit-wave model (sec. 3.4, Eq. (2)) and a multislice ptychography that "does not account for backwardly propagating waves that have been reflected off the layers" (sec. 6.2, AM p. 76); glancing-angle reflection ptychography is described only for EUV (sec. 5.9). No reflection-electron update exists in what was read; a dynamical forward model is required before any ptychographic inversion of reflection data.
