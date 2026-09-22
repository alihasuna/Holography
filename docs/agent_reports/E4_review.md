# E4: adversarial review of the Phase 2 documentation changes (0de75f8..HEAD)

Status: FINAL, 2026-09-22. The documents under review were not edited. Only this file was written
(scratch scripts outside the repository, pasted in appendix A).

Reviewer: adversarial scientific reviewer (agent E4), 2026-09-22.

Scope: `git diff 0de75f8 HEAD` of README.md, docs/03, docs/05 (with the new section 9.1), docs/06,
docs/model_assumptions.md (B4, B5, B9, B11-B18, open question 3), docs/physics_conventions.md,
docs/source_map.tsv (SM03, SM07, SM26, SM27 and the implementation, test and status columns),
configs/*.yaml (as documents) and tools/phase1_numbers.py. The review started at HEAD d35b751. Two
commits arrived during the review (296d0ee adds the re-audit A2b; 6de15bb snapshots this report): no
file under review changed (`git diff --stat d35b751 HEAD` lists only the two reports). Uncommitted
round-2 changes by another agent appeared in the working tree during the review. They touch
configs/*.yaml, pyproject.toml, reflection_holo/io/config.py, quantification/rocking.py and
reconstruction/sideband.py, tests/ and tools/physics_checks/q2_carrier_trap.py, and add a new
reflection_holo/io/assumption_registry.yaml. They are NOT reviewed. Every config quote below is from
the committed HEAD (`git show HEAD:configs/...`). Every run cited as REPRODUCED used committed code.

Record consulted: S1a, S1b, S1c, S2, S3 (build reports), A2 (code audit of 7874c85), A2b (re-audit
of d35b751, committed 296d0ee), C2 with tools/physics_checks/. I read the package source only to
check statements about it (the carrier locator, b4_statement, the Delta form, the module list). I
did this after my own recomputation of each quantity.

Method: every number was recomputed with scripts written for this review (appendix A). I wrote
them before opening the corresponding C2 script or package function. Labels used here: REPRODUCED
means executed by me with the output saved in appendix A or quoted verbatim.

## Summary

0 Blocker, 3 Major, 9 Minor, 10 Nit. The new physics is right: the a/4 symmetry result, the sign of
the covariance relation, the carrier-trap numbers, the R2 twin, the Delta forms, the shadow
lengths and the B16 bound. All reproduce. The test counts (527 at bd654c2 and at d35b751) also
reproduce. The defects are in scope and status:

* M1: the <100> a/4 result is stated for beams, surfaces and illumination beyond what C2 derived.
  It holds for the specular beam and other beams in the incidence plane, with in-plane rods carrying
  (-1)^p. It fails for a beam leaving the incidence plane (own Foldy-Lax check). In five places the
  2x1/overlayer caveat is missing, and B18 also lacks "bulk-terminated".
* M2: docs/05 section 9.1 cites the pre-fix audit A2 as support and omits the re-audit's open Major
  N1 (PROJECT_INPUT gate bypass) and Minors N2 to N6. Its "Not implemented yet" list omits items that
  the package itself declares not implemented.
* M3: the R2 step-strip sign in docs/03 section 6 is right only when the shift points towards the
  upper terrace. In the other case the strip is +Delta (own check, 1.207 rad for Delta = 1.2 rad).

## Findings

### Blocker

None found.

### Major

#### M1. The <100> a/4 result is carried without its scope conditions (beam, reconstruction, illumination)

Quoted text:

* docs/06_project_inputs_required.md:20 (item 8): "For Si(001) single-layer (a/4) steps a <100>
  azimuth makes the bulk-terminated step a clean geometric-phase step (C2 section 1); ... The a/2
  step is clean at every azimuth."
* docs/source_map.tsv:30 (SM26): "at an exact <100> azimuth the d-glide in the incidence plane (glide
  (a/4)[+-1,0,1]) fixes k_in and k_out, so A_up = exp(-i (k_out - k_in).t) A_low and the a/4 step
  phase is purely geometric; at <110> a dynamical residual delta = phi_R,P - phi_R,T remains".
* docs/model_assumptions.md:28 (B4): "or by a bulk-terminated Si(001) a/4 step viewed at an exact
  <100> azimuth (...), have identical complex reflectivity up to `exp(-i (k_out - k_in).t)`".
* docs/03_physics_summary.md:43-46: "the d-glide whose plane contains the beam and the normal ...
  leaves `k_in` and `k_out` unchanged, so ... the step phase is exactly
  `-(4 pi/lambda)(a/4) sin(theta_ext)`".
* docs/05_final_repository_specification.md:63 (CFG-B row): "at an exact <100> azimuth also
  glide-related, so the step phase is purely geometric for bulk-terminated terraces"; :36-38
  (criterion 3): "the geometric phase holds only at an exact <100> azimuth for bulk-terminated
  terraces".
* docs/model_assumptions.md:42 (B18): "the a/4 step is geometric only at an exact <100> azimuth
  (B4, SM26)".
* configs/cfg_b_si001_patterned.yaml:16-18 (description) and :98 (`step_translations.single_layer.relation`).

Evidence:

1. Beam restriction. The (010) glide fixes a wavevector only if the wavevector lies in the
   incidence plane. C2 section 1.3 "Other rods" (C2:219-222; check E8) says so: "At `[100]` the
   relation is rod-by-rod only for rods in the incidence plane: a rod `G_par = p (4 pi/a)[100]`
   carries the extra factor ... `(-1)^p`, while a zeroth-Laue-zone rod `G` perpendicular to the beam
   on one terrace is related to the rod `-G` on the other. Which beam the aperture selects is
   PROJECT_INPUT item 4". S1b open issue 1 says "for beams in that plane (the specular beam)". My
   Foldy-Lax check at exact [100] (appendix A.2) gives these ratios:
   * specular: `A_up e^{iq.t}/A_low = 1` to 2.7e-13;
   * in-plane non-specular: ratio 1 to 6e-15, but the phase then contains the in-plane glide term
     `-q_x t_x` (for crystal rods this is the (-1)^p of C2);
   * beam 0.1 rad out of the (010) plane: `0.528 exp(-0.322 i)`;
   * beam 0.3 rad out of the (010) plane: `1.672 exp(+0.193 i)`. The relation then holds only
     against the mirrored `k_out` (ratio 1 to 8e-15).

   As worded, "fixes k_in and k_out", "identical complex reflectivity" and "clean geometric-phase
   step" hold only for the specular beam. Other beams in the incidence plane obey the covariance
   relation with the full glide vector, including its in-plane part. Beams outside the plane obey no
   such relation. Item 4
   (which beam the aperture selects) is still an open, blocking PROJECT_INPUT, so item 8's advice
   depends on it.
2. Reconstruction and overlayer. Only docs/03 section 2, B4 and SM26 say "a 2x1 reconstruction can
   break it". Item 8, the CFG-B row, criterion 3, B18 and the CFG-B yaml do not. B18 also lacks
   "bulk-terminated". C2 section 1.4 shows that the broken case is realistic: twisted-dimer toy,
   screw variants with no [100]-compatible operation. The surface is ion-milled (item 12), and C2
   notes the overlayer has "no crystal symmetry at all" (C2:275-276).
3. Illumination. The exact result is for a plane wave at the exact azimuth. C2 states that "whether
   the ensemble-averaged sideband keeps the exact relation ... is NOT analysed here (B10,
   PROJECT_INPUT item 3)" (C2:213-217; C2 section 5). No document carries this.
4. "remains" in SM26 states as fact what C2 derives only generically. C2 says it is nonzero once
   the specular beam couples to non-specular beams, with a value "UNKNOWN until a many-beam dynamical
   calculation is done" (C2:283-286).

Proposed wording. Use one clause everywhere the <100> result is stated (item 8, B4, SM26, CFG-B row,
criterion 3, B18, CFG-B yaml; docs/03 section 2 needs only the beam and illumination parts):

> "For the specular beam (and, with the in-plane glide term `-q_par.t_par` = `p pi`, for other beams
> in the incidence plane) of a plane wave at the exact <100> azimuth, bulk-terminated a/4 terraces
> reflect identically up to `exp(-i (k_out - k_in).t)` (C2 section 1.3). This does not hold for beams
> leaving the incidence plane (item 4), for a 2x1 reconstruction whose upper-terrace domain is not a
> <100>-glide image of the lower one, or for an overlayer. The effect of an azimuthal spread
> (convergence, item 3) is not analysed. At <110> the residual `delta` is not forced to vanish by
> symmetry; its value is unknown (open question 3)."

In docs/03:44 replace "leaves `k_in` and `k_out` unchanged" by "leaves `k_in` and every `k_out` in
the incidence plane unchanged", and in :46 write "the specular step phase is exactly ...". In SM26
replace "remains" by "is not forced to vanish by symmetry (value unknown)".

#### M2. docs/05 section 9.1 claims more than the build and audit record supports

Quoted text (docs/05_final_repository_specification.md):

* :317-318 "Implemented in `reflection_holo/` and tested (full suite ...: 527 passed at commit
  bd654c2; build reports S1a, S1b, S1c, S2, S3 and audit A2 under `docs/agent_reports/`)".
* :336 "`io/` (schema-gated configuration loader: a missing or null PROJECT_INPUT fails at run level)".
* :339-341 "Not implemented yet: the reflection forward model (M2), biprism Fresnel fringes, drift,
  detector MTF, partial-coherence generators, the R1 `2 theta_ext` compensation model, an
  experimental data loader, and configuration fields for PROJECT_INPUT items 2, 6, 10, 16, 17, 19,
  21 and 22."

Evidence:

1. A2 audited 7874c85, before the fixes: 1 Blocker, 2 Major, 10 Minor. It is evidence of defects,
   not of the state at bd654c2. The fixes (S3) were re-audited in A2b, audited state d35b751, which
   is exactly the state that 9.1 describes. A2b finds:
   * N1 (Major): the gate is bypassed by labelling a stand-in DERIVED_HERE, SECTION_READ,
     REPRODUCED or METADATA_VERIFIED. All eight blocking CFG-B inputs then pass at run level, and an
     ASSUMPTION stand-in passes with any existing row (A3, B2, B17).
   * N2: B16 `sigma_h` excludes accepted intercept residuals. A 0.1 rad residual biases h by -9.2
     sigma_h.
   * N3: noise under-declared by 31 % gives a wrong-branch rate of 1.75e-2, 7x the bound.
   * N4: on uniform tilt grids with |h| > h_max, every accepted height is wrong (622 of 622 and
     1981 of 1981 accepted).
   * N5: the validity-aware unwrapper stops at the first invalid pixel of column 0.
   * N6: the median-relative amplitude threshold fails when the overlap covers less than about half
     the field.

   "a missing or null PROJECT_INPUT fails at run level" is literally true. The protection it
   implies, acceptance criterion 5, is not achieved. The CFG-B header (:7-8) makes the same
   promise.
2. The "Not implemented yet" list omits items that the record declares not implemented:
   * dark-field aperture selection, projection along k_out and lens transfer (docs/05 section 5
     items 1-2), which `reflection_holo/optics/__init__.py:5-6` itself lists as "Not implemented";
   * magnification/pixel mapping, gain other than 1, zero padding, real-space windows,
     residue-aware unwrapping and sub-pixel R2 shifts (S1c "NOT IMPLEMENTED");
   * terrace segmentation with uncertainties (section 5 item 8) and the height sensitivity to
     convergence and V0 (section 8) (S1a "NOT RUN"; S3 m9 "Not added");
   * the geometric-phase model of section 4.5 (no `forward/` package exists);
   * atomistic mesas, trenches and overlayer (S1b; B12).

   Read with the bullet "Section 5, synthetic data only: ...", the list suggests that section 5 is
   complete apart from the listed items.

Proposed wording for :317-318: "Implemented in `reflection_holo/` with tests (527 passed at bd654c2
and at d35b751; build reports S1a to S3). The code audit A2 (state 7874c85) and its re-audit A2b
(state d35b751) are the verification record. Open after A2b: N1 (Major, the PROJECT_INPUT gate
accepts a stand-in labelled other than ASSUMPTION) and N2 to N6 (B16 sigma_h and noise
declaration, aliasing on uniform tilt grids, unwrapper, validity threshold)." Extend "Not implemented
yet" with the items of point 2.

#### M3. The sign of the R2 step strip is wrong when the shift points towards the lower terrace

Quoted text: docs/03_physics_summary.md:231-232, "a step inside the overlap appears with its twin
as a strip of phase `-Delta` whose width is the shift component normal to the step edge". The
source is C2:505-506 ("a strip of phase `-Delta` of width `|s_y|`").

Evidence. With `phi = Delta H(n.r - c)` (upper terrace on the `+n` side, Delta = phi(upper) -
phi(lower) as in docs/physics_conventions.md), `phi(r) - phi(r + s)` is
`Delta [H(n.r - c) - H(n.r - c + s_n)]`, with `s_n = n.s`. That is a strip of width `|s_n|` and
phase `-sign(s_n) Delta`. REPRODUCED (appendix A.3, own hologram and sideband reconstruction,
Delta = +1.2 rad):
* s_n = +20 px: strip [160, 180) at -1.208 rad;
* s_n = -20 px: strip [180, 200) at +1.207 rad.

C2's check Q3-C1 tested only one sign (s = (96, 40), strip rows 228..276 at -1.0003; C2:526-528). The
twin rule in the same docs/03 sentence (sign-inverted, translated by -s) is correct. Only the strip
clause fails, for half of all geometries. An R2 reconstruction read with this rule would assign the
wrong side to the upper terrace.

Proposed wording: "a step inside the overlap appears with its twin as a strip of width `|n.s|`
(`n` the step normal pointing to the upper terrace) and phase `-Delta` if `s` points towards the
upper terrace, `+Delta` if it points towards the lower one". Correct C2 section 3.2 the same way (a
report, so by an addendum), and add the negative-shift case to q3 / test_self_reference_R2.py.

### Minor

m1. docs/03_physics_summary.md:243-244, "and it comes as an exactly equal Hermitian pair, one bin
in each sideband"; SM27 (source_map.tsv:31), "as an exactly equal Hermitian pair". The same sentence
names "a sharp 50/50 step". For a sharp step all four first-harmonic bins tie, two in each sideband.
My check gives a relative spread of 3.2e-15 (appendix A.3). C2 gives 1.9e-16 (C2:374-375) and adds
that "for a perfectly sharp 50/50 step all four harmonics tie and the calculator's order would have
picked the correct sideband, giving -0.78 rad" (C2:432-433). The single brighter pair exists only
because of the calculator's tanh edge (1.56 % split). Proposed: "the four first-harmonic bins
(`q_c +- 1` along the step normal and their Hermitian partners) are equal for a sharp step. In the
calculator's smoothed-edge hologram one Hermitian pair is brighter by 1.56 %, and its two members,
one in each sideband, are exactly equal."

m2. The carrier-location rule differs between the documents:
* docs/03:247-248: "on an empty hologram or on the sideband envelope";
* B15 (model_assumptions.md:39) and SM27: "empty or flat-region hologram";
* docs/05:243 (section 5 item 7) and :332-333 (section 9.1): "empty hologram".

The package (`reconstruction/sideband.py:11, 215, 226`) accepts EMPTY or flat-region holograms and
refuses object holograms, so it has no sideband-envelope method. Proposed: one rule everywhere,
"on an empty or flat-region hologram (never on the object hologram), inside a declared one-sideband
search region". Either drop "sideband envelope" from docs/03, or add it to B15/SM27 and to the
not-implemented list.

m3. Two statements were not updated for the <100> result:
* docs/05:209-211 (section 4.5): "explicit detection of the invisibility condition (`g.R` integer)
  and of screw-related terraces where the model is not valid";
* docs/03:130-131 (section 3): "Si(001), single-layer step `a/4 = 1.358 A` (terraces NOT
  translation-related; the kinematic value is only indicative)". At an exact <100> azimuth this
  value is exact for the specular beam of bulk-terminated terraces. Proposed for docs/03:130-131:
  "(terraces NOT translation-related; the value is exact at an exact <100> azimuth for the specular
  beam of bulk-terminated terraces and indicative at <110>, section 2)".

On section 4.5: a/4 terraces are always screw-related.
Criterion 3, docs/03 section 2 and `b4_statement` (si001.py:353-379) now say that the model is valid
at an exact <100> azimuth (specular beam). A2 m3 pointed at this very sentence. Proposed: "... and of
terraces related neither by a lattice translation nor by an operation fixing `k_in` and `k_out` (the
Si(001) a/4 step at any azimuth other than an exact <100>, and off-plane beams at <100>), where the
model is not valid".

m4. B16 (model_assumptions.md:40): "Monte Carlo in the tests: 0 wrong branches among 3987 accepted
series (2000 trials per regime, seed 20260922; bound 2.7e-3 by the 3-sigma criterion)". The numbers
are right: 1993 + 1994 = 3987, REPRODUCED by `pytest -s tests/quantification/test_quant_rocking_noise.py`;
891 = 1 + 136 + 567 + 133 + 54 (A2 e10); P(|Z| > 3) = 2.6998e-3 (my check). The Monte Carlo has no
power against the bound. Its regimes have sigma_c = 0.163 and 0.903 rad. For these the bound formula
`P(|Z| >= (2 pi - 3 sigma_c)/sigma_c)` gives about 1e-276 and 7.6e-5 per series, so 0 wrong is
expected either way (about 0.15 expected in 1994). The boundary test is A2b's: 35 wrong of 19 968 =
1.75e-3 at sigma_c = 1.04. The row also dropped S3's "violated by" clause (S3:341: a dynamical
residual or an a/4 step at <110> is "caught by the intercept check only if larger than 3 sigma_c";
|h| > h_max). It does not state that `sigma_h` is conditional on a zero intercept residual (A2b N2),
nor the under-declaration sensitivity (A2b N3). Proposed addition: "The bound holds per accepted
series for correctly declared Gaussian noise and correct unwrapping. Its worst case is sigma_c ->
pi/3, tested in A2b (1.75e-3 at sigma_c = 1.04). The two regimes of the tests are far from that
case. `sigma_h` assumes a zero intercept residual: a residual up to 3 sigma_c (for example the a/4
residual delta at <110>, or an angle offset) is accepted and biases h (A2b N2). Noise under-declared
by 31 % raises the rate to 1.75e-2 (A2b N3). A uniform tilt grid aliases |h| > h_max (A2b N4)."

m5. configs/cfg_b_si001_patterned.yaml:4-6 (HEAD), "Every blocking input that has not been supplied
is null with its docs/06 item number: a run-level load FAILS and names items 3, 4, 5, 7, 8, 12, 13
and 15". Item 13 is not marked blocking (docs/06:28). Item 11 is blocking (docs/06:26), but its
unsupplied parts (miscut angle and direction, terrace widths, which terrace type lies where) have no
field, so the load does not fail on them. The field list in docs/05:341 also omits item 11. Proposed:
"... names items 3, 4, 5, 7, 8, 12, 13 (not blocking, required here) and 15; the unsupplied parts of
item 11 (miscut, terrace widths, terrace types) have no field yet".

m6. docs/03_physics_summary.md:89, "(first order in V0; see below)". Nothing below in docs/03 gives
the exact form. It is only in docs/physics_conventions.md:48-50. Proposed: "(first order in V0; the
exact form, used by the calculator and the package, is in docs/physics_conventions.md; they differ
by 8.4e-6 relative)".

m7. Shadow wording outside the four places that were updated:
* docs/06:28 (item 13): "A feature of height h transverse to the beam shadows `h/tan(theta)` of
  surface behind it";
* docs/05:123-124 (section 4.2): "the shadowed strips computed from the geometry for every incidence
  angle".

Neither mentions the blocked-view strip in front of a rising edge (a mesa's front edge) or the exit
angle, which docs/03:161-166, docs/05 section 4.5, B9 and SM07 now require and the code implements
(`structure/shadows.py:163`; tests/structure/test_structure_shadows.py:141-197). Proposed for item 13:
"masks `h/tan(theta_in)` behind a falling edge and `h/tan(theta_out)` in front of a rising edge".

m8. docs/05:63 (CFG-B row) and CFG-B yaml keep "screw-related" as the type name
(`single_layer_a4_screw_related`, cfg_b:88). This is harmless as a name, but combined with section
4.5 (m3) it steers an implementer to refuse the <100> case. Consider `single_layer_a4` with the
relation in `step_translations`.

m9. Source-map test columns (docs/source_map.tsv), compared with 0de75f8:
* SM15 (line 19) went from test_id "T21, T22; tilt_test (IndexError at 0.5 A)" and status "PASS;
  REPRODUCED" to "tests/geometry/test_geom_sampling.py (T21, T22)" and "PASS 2026-09-22 in
  reflection_holo". The REPRODUCED engine-level evidence that docs/03:203-204 still cites ("D report
  section 2c reproduces the resulting `IndexError`") is no longer referenced by the sampling row.
* SM13 (line 17) is now "PASS" for the whole claim. Its second half ("illumination convergence
  produces a phase spread (4 pi h/lambda) cos(theta) per radian") has no implementation and no test:
  there is no convergence model (S3 m9 "Not added"; docs/05 section 9.1 lists the partial-coherence
  generators as not implemented).
* SM01 to SM09 dropped the calculator from the implementation column, and SM01 dropped "independently
  reconfirmed by E review" from its status. The package tests still take their reference values and
  tolerances from the calculator, and docs/05 section 4.1 still names the calculator the reference
  implementation.

Proposed:
* SM15: keep "tools/provenance_checks/tilt_test.py (IndexError at 0.5 A): REPRODUCED 2026-09-21".
* SM13: "PASS for the ensemble average after squaring; convergence phase spread NOT RUN (no model)".
* SM01 to SM09: add "reference: tools/reflection_step_phase_calculator.py (25/25)" to the
  implementation column.

### Nit

n1. docs/03:157, "(revision 3 corrects 102 A;". The correction is Phase 2 commit 5d59c41, after
revision 3 (0de75f8, "Phase 1 final"). README.md:28, "The physics numbers added in revision 3 (...,
shadow lengths)": the shadow lengths were added in 5d59c41. The docstring of
tests/geometry/test_geom_projection.py:69-71 still says "102 A ... Reference value kept as printed",
while the check uses 101.0. The test also passes by only 0.02 A: 101.48 against 101.0 +- 0.5.

n2. The status lines were not updated for Phase 2: docs/03:3 ("revision 2"), docs/05:3-6 ("version
0.3"), docs/06:3 ("revision 3 ... items 11 and 12 partly supplied"), model_assumptions.md:3
("revision 3").

n3. B17 (model_assumptions.md:41), "exits well above `theta_c` (16.5 mrad at `V0` = 12 V)". This
compares an external exit angle with the internal escape angle (physics_conventions: `theta_c` is
INTERNAL). Proposed: "exits at 16.5 mrad (external), far from grazing exit".

n4. B1 (model_assumptions.md:25) does not name docs/06 item 20, although CFG-A and CFG-B use B1 as
the stand-in for item 20. B17 and B18 do name their items. Proposed: add "Stands in for PROJECT_INPUT
item 20".

n5. docs/06:26 (item 11): "which of the two terrace types (top-layer bonds parallel or
perpendicular to the beam)". Proposed: "top-layer back-bonds, at a <110> azimuth". At <100> both
types are at 45 degrees, and C2:292-294 says the clause is then not needed.

n6. docs/05:63 (CFG-B row) gives mesa shadows at 22.5 mrad and at the (4,-4,4) angle, which are Si(111)
conditions. At CFG-B's own (0,0,8) condition (16.47 mrad) a 10 nm mesa masks 606.9 nm. At (0,0,12)
it masks 378.4 nm (appendix A.3).

n7. docs/05:38, "(it must vanish)". Proposed: "(it must vanish to a tolerance recorded in
configs/benchmarks.yaml; the simulation grid must respect the glide: in-plane component a/4 along the
beam, glide plane a/8 from the atom rows)".

n8. docs/03:49, "it alternates in sign along a staircase of a/4 steps". C2:195 says "along a
monotonic staircase". Along a staircase that rises and falls, the sign follows the order of the
terrace types.

n9. physics_conventions.md:50, "at most 5.1e-5 rad in an a/4 step phase". This is the maximum over the
(00L) Bragg conditions (004) to (0,0,16) (C2 J1b). At lower exit angles the change is larger: 1.0e-4
rad at 2 mrad and 2.0e-4 rad at 1 mrad (appendix A.3). Still negligible, but state the conditions.

n10. CFG-A at HEAD: `target_reflection_hkl` and `recommended_reflections_hkl` (cfg_a:59, :65) carry
`item: 9` with label DERIVED_HERE. They are a benchmark definition, not a laboratory input. The
uncommitted working tree is removing this (A2b N1); record the change when it is committed. SM27's
test_status "PASS 2026-09-22" gives no commit or suite count, unlike SM01-SM15.

## Verified as correct (with the evidence used)

1. a/4 symmetry (own exhaustive search, A.1):
   * Exactly four operation classes map the lower onto the upper bulk-terminated half crystal: the
     4z+ screw (4_1) and the 4z- screw (the 4_3 element, rotation -90 deg with +a/4), the (100)
     d-glide and the (010) d-glide. All have t_z = a/4.
   * No pure translation, and nothing on an a/8 translation grid.
   * The (010) glide vectors are (+a/4, 0, a/4) on the plane y = a/8 and (-a/4, 0, a/4) on
     y = 3a/8, so "(a/4)[+-1,0,1], normal component a/4" is right.
   * At [100] exactly one operation fixes the beam and the normal (the (010) glide), and one maps
     u -> -u (the (100) glide, via reciprocity). At [110], [1-10] and [210] there are none, also none
     via reciprocity.
   * The self-maps of a terrace are {1, 2z, m(110), m(1-10)}.
   * The top-layer back-bonds project on [1-10] (lower terrace) and on [110] (upper terrace), which
     confirms the P/T naming.
2. Consequence (own Foldy-Lax and kinematic sums, A.2):
   * at [100], A_up = exp(-i (k_out - k_in).t) A_low to 2.7e-13 (k = 250.5/A) and 3.4e-15 (k = 6/A),
     sign as in exp(+ik.r);
   * at [110] the kinematic residual is 1e-13, the Foldy-Lax residual +0.161 / -0.029 rad, and the
     sign is opposite at [1-10];
   * the misalignment residual is exactly odd.

   docs/03 section 2, B4, open question 3 and SM26 are right within the scope stated in M1.
3. `b4_statement` (si001.py:353-379) matches SM26 and B4: "applies for bulk-terminated terraces
   (d-glide in the incidence plane)" at <100> only when the glide is measured on the built atoms,
   and "does not apply" at <110>.
4. Carrier trap:
   * 2 arctan(pi/2) = 2.00777 rad (discrete threshold 2.00775 rad for N = 256);
   * 0.78 = -2.36 + pi = 0.78159;
   * recentring on a correct-sideband harmonic gives -0.784 rad and on a conjugate one +0.784 rad;
   * the ramp is worth pi between the terrace medians (A.3).

   Items 10, 16 and 19 exist and cover sign, carrier and processing.
5. R2: phi(r) - phi(r + s) to 6.6e-3 rad (band limit). The twin is sign-inverted and translated by
   -s: correlation 0.93, against 0.14 / -0.05 for a mirrored copy (A.3).
6. Delta:
   * the exact form in physics_conventions.md:49 equals my derivation from the relativistic momenta;
   * the relative difference is 8.4388e-6, V0/(2(T + m c^2));
   * the a/4 phase change is at most 5.094e-5 rad at (004);
   * the calculator (`E_eff_V`, calculator:170-182) and the package (`refraction_delta`,
     refraction.py:59-65) both use the exact form;
   * V0/T is 14.06 % too small, and the relativistic value is 16.37 % larger;
   * theta_c = 8.3556 mrad.
7. Shadow lengths, with the internal Bragg condition 2 k_int sin(theta_int) = G:
   * 22.5 mrad: 139.33 A (bilayer), 60.33 A (a/4), 444.37 nm (10 nm);
   * (4,-4,4): theta_ext 13.6415 mrad, 229.84 A (bilayer), 733.01 nm (10 nm);
   * (8,-8,8): theta_ext 30.888 mrad, 101.48 A (bilayer), 323.65 nm (10 nm).

   So "101 A" and "324 nm" are right, and no document under review still gives 102 A as the value
   (docs/03:157 mentions it only as the corrected figure).
   tools/phase1_numbers.py prints the same values (17/17). The blocked-view geometry (length
   h/tan(theta_out) in front of the riser when the upper terrace is downstream) is right and is
   tested.
8. The CFG-B numbers are right: (0,0,8) theta_int 18.47 mrad, theta_ext 16.47 mrad, wrap 0.761 A,
   61x; (004) exits at 3.93 mrad. The forbidden list (002), (006), (0,0,10) follows the h+k+l = 4n
   rule.
9. B16 bound: a wrong branch needs |c - c_true| >= 2 pi - 3 sigma_c > 3 sigma_c when sigma_c < pi/3.
   The worst case is P(|Z| >= 3) = 2.6998e-3. S3's Monte Carlo is REPRODUCED (1993 + 1994 = 3987,
   0 wrong).
10. Test counts: `venv/bin/pytest -q` gives 527 passed on the clean tree at d35b751 and 527 passed at
    bd654c2 (temporary worktree, removed afterwards). The package and tests are identical between
    the two commits. The calculator and the checks run at the stated counts: calculator 25/25,
    phase1_numbers 17/17, q1 41/41, q2 21/21, q3 7/7. All of these ran on committed code, before the
    other agent's uncommitted round-2 edits reached the files involved.
11. Every implementation and test file named in the source-map columns exists in git (scripted check).
12. Labels and sources:
    * no DOI, page or year in the diff lies outside the literature record. The only DOI (P01,
      10.1143/JJAP.27.L1772, L1772-L1774) matches references.bib:311-314;
    * DERIVED_HERE results are labelled DERIVED_HERE, and none is attributed to a source;
    * the stand-ins are complete in the committed configs: V0 (item 20, B1), (0,0,8) and (0,0,12)
      (item 9, B17), step types (item 14, B18);
    * B2 is not a stand-in (docs/06 has no item for the lattice parameter);
    * SM27's REPRODUCED is backed by saved output (S1c log item 1, C2 appendix A.2).

13. Against docs/05 sections 4.2 and 5, nothing implemented contradicts the specification. The
    structure is built as truncations of one lattice, with periodic continuity and a/4 and a/2
    relations measured on the atoms. The 2x1 reconstruction and the atomistic overlayer are refused
    or declared. R1, R2 and R3 are selectable by name. The ensemble average is taken after squaring
    (mutation-tested). Raw and noisy holograms are both kept. Raw and unwrapped phase, masks and
    explicit ramp fits are preserved, and the resolution is reported. The height is signed, with
    refusal instead of division. The differences are items not implemented (M2), the flat-region
    extension of section 5 item 7 (m2) and section 4.5 (m3).
14. Traceability: every new number traces to the report it cites:
    * C2 sections 1 to 3 for the a/4 result, the carrier trap and R2;
    * C2 J1/J1b for 8.4e-6 and 5.1e-5 rad;
    * tools/phase1_numbers.py for the shadow lengths;
    * S3 for the B16 Monte Carlo and the 891 (A2 e10 rows);
    * S3's final run for 527 at bd654c2.

## Work log (incremental)

* Started: diff read; full test suite launched (527 passed at d35b751, clean tree).
* (a) Own exhaustive search on the truncated half crystals and own Foldy-Lax model (A.1, A.2).
  These found the missing beam restriction: the relation fails for a beam leaving the incidence plane.
* (b)-(f) Own numbers (A.3): threshold, 0.78, the four-way tie for a sharp step, Delta, the shadows,
  the B16 bound, and the R2 strip sign (+Delta for a shift towards the lower terrace).
* Test suite: 527 passed at bd654c2 (temporary worktree, removed). phase1_numbers 17/17; q1 41/41;
  q2 21/21; q3 7/7; B16 Monte Carlo test with -s REPRODUCED.
* Then read C2, S1a, S1b, S1c, S2, S3, A2, and A2b (committed during the review as 296d0ee).
* Checked the package statements: carrier locator, b4_statement, Delta form, module list.

## Appendix A: scripts and outputs (verbatim)

All scripts live in `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/e4/` and were run with `/home/user/Holography/venv/bin/python <name>.py`
(numpy 2.4.6, scipy). None imports the package, the calculator or the C2 scripts.

### A.1 `e4_a1_symmetry_search.py` (exhaustive operation search on the truncated half crystals)

```python
"""E4 (a): exhaustive search of the operations relating two bulk-terminated Si(001) half crystals
whose top layers differ by a/4. Written for review E4 without reading C2's q1 script or the package.

Units: a/4 (so every diamond site has integer coordinates).
Diamond sites: all-even with x+y+z = 0 (mod 4), or all-odd with x+y+z = 3 (mod 4)
(FCC at (0,0,0) + basis (1,1,1) in units of a/4).
Lower half crystal L: sites with z <= 0.  Upper half crystal U: sites with z <= 1 (a/4 higher).
Candidate operations g = {W|t}: W any of the 48 signed permutation matrices (m-3m), t any vector
mapping one chosen top-layer atom of L onto any atom of U inside a search box, then also a finer
a/8 grid of t (half-integers) to show that nothing between lattice-compatible translations works.
An operation is accepted if it maps the core of L into U and the core of U into L (inverse).
"""
import itertools
import numpy as np

def diamond_sites(xr, yr, zr):
    pts = []
    for x in range(xr[0], xr[1] + 1):
        for y in range(yr[0], yr[1] + 1):
            for z in range(zr[0], zr[1] + 1):
                if x % 2 == 0 and y % 2 == 0 and z % 2 == 0 and (x + y + z) % 4 == 0:
                    pts.append((x, y, z))
                elif x % 2 == 1 and y % 2 == 1 and z % 2 == 1 and (x + y + z) % 4 == 3:
                    pts.append((x, y, z))
    return np.array(pts, dtype=float)

def is_diamond(p):
    """p: (N,3) array of possibly non-integer coords (units a/4); True where p is a diamond site."""
    r = np.round(p)
    ok = np.all(np.abs(p - r) < 1e-9, axis=1)
    r = r.astype(int)
    even = np.all(r % 2 == 0, axis=1) & ((r.sum(axis=1) % 4) == 0)
    odd = np.all(r % 2 == 1, axis=1) & ((r.sum(axis=1) % 4) == 3)
    return ok & (even | odd)

def in_L(p):
    return is_diamond(p) & (p[:, 2] <= 0 + 1e-9)

def in_U(p):
    return is_diamond(p) & (p[:, 2] <= 1 + 1e-9)

# 48 signed permutation matrices
Ws = []
for perm in itertools.permutations(range(3)):
    for signs in itertools.product([1, -1], repeat=3):
        W = np.zeros((3, 3))
        for i in range(3):
            W[i, perm[i]] = signs[i]
        Ws.append(W)
assert len(Ws) == 48

# core region of L and U (test points; membership is tested analytically, so no box-edge effects)
core_L = diamond_sites((-12, 12), (-12, 12), (-12, 0))
core_U = diamond_sites((-12, 12), (-12, 12), (-11, 1))

def accepts(W, t):
    img = core_L @ W.T + t
    if not np.all(in_U(img)):
        return False
    pre = (core_U - t) @ np.linalg.inv(W).T
    return bool(np.all(in_L(pre)))

a0 = np.array([0.0, 0.0, 0.0])  # a top-layer atom of L
found = []
# (1) lattice-compatible candidates: t = u - W a0 for u in U within a box
for W in Ws:
    for u in diamond_sites((-8, 8), (-8, 8), (-8, 1)):
        t = u - W @ a0
        if accepts(W, t):
            found.append((W, t))
# (2) finer grid: half-integer translations (a/8 steps) with every W, to show nothing else works
extra = 0
grid = np.arange(-4.0, 4.01, 0.5)
for W in Ws:
    for tx in grid:
        for ty in grid:
            for tz in np.arange(-3.0, 3.01, 0.5):
                t = np.array([tx, ty, tz])
                if np.all(np.abs(t - np.round(t)) < 1e-9):
                    continue  # integer t already covered by (1) when reachable
                if accepts(W, t):
                    extra += 1

def name(W):
    table = {
        "1": np.eye(3),
        "2z": np.diag([-1, -1, 1]),
        "4z+ (x,y,z)->(-y,x,z)": np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]),
        "4z- (x,y,z)->(y,-x,z)": np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]]),
        "m_x (plane (100))": np.diag([-1, 1, 1]),
        "m_y (plane (010))": np.diag([1, -1, 1]),
        "m_(1-10) (x,y)->(y,x)": np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]]),
        "m_(110) (x,y)->(-y,-x)": np.array([[0, -1, 0], [-1, 0, 0], [0, 0, 1]]),
    }
    for k, v in table.items():
        if np.allclose(W, v):
            return k
    return "other:" + str(W.astype(int).tolist())

classes = {}
for W, t in found:
    classes.setdefault(name(W), []).append(t)

print("Operations g={W|t} with g(L) = U (units a/4); t listed modulo nothing (all found in box):")
for k, ts in classes.items():
    tz = sorted(set(float(t[2]) for t in ts))
    print(f"  {k:28s} count={len(ts):4d}  t_z values (a/4 units) = {tz}")
print("pure translations found:", len(classes.get("1", [])))
print("extra accepted operations with non-integer (a/8-grid) translations:", extra)

# Glide vectors of the m_y class: g: (x,y,z) -> (x+tx, -y+ty, z+tz); plane y0 = ty/2; glide (tx,0,tz)
print("m_y class: distinct (glide vector mod a along x, plane position y0 mod a/2) in units of a:")
gl = set()
for t in classes.get("m_y (plane (010))", []):
    tx = (t[0] / 4.0) % 1.0
    y0 = (t[1] / 8.0) % 0.5
    gl.add((round(tx, 4), round(y0, 4), t[2] / 4.0))
for g in sorted(gl):
    print(f"   glide x-component {g[0]:.4f} a (i.e. {g[0] if g[0] <= 0.5 else g[0]-1:+.4f} a), plane y0 = {g[1]:.4f} a, t_z = {g[2]:.4f} a")

# Which accepted operations fix the beam direction u and the normal (hence k_in and k_out of the
# specular beam and of any beam in the incidence plane), and which map u -> -u (reciprocity partner)?
az = {"[100]": [1, 0, 0], "[010]": [0, 1, 0], "[110]": [1, 1, 0], "[1-10]": [1, -1, 0],
      "[210] (general)": [2, 1, 0]}
print("Azimuth test (normal [001]):")
for lab, u in az.items():
    u = np.array(u, float) / np.linalg.norm(u)
    fix = sorted(set(name(W) for W, t in found if np.allclose(W @ u, u)))
    rec = sorted(set(name(W) for W, t in found if np.allclose(W @ u, -u)))
    print(f"  {lab:16s} ops fixing u and n: {fix if fix else 'NONE'};  ops with W u = -u (reciprocity): {rec if rec else 'NONE'}")

# Self-maps of L (z-preserving, t_z = 0 mod a/2): for the misalignment and P/T discussion
self_found = set()
for W in Ws:
    for u in diamond_sites((-8, 8), (-8, 8), (-8, 0)):
        t = u - W @ a0
        img = core_L @ W.T + t
        if np.all(in_L(img)):
            pre = (core_L - t) @ np.linalg.inv(W).T
            if np.all(in_L(pre)):
                self_found.add(name(W))
print("Self-maps of the lower half crystal (point parts):", sorted(self_found))

# Top-layer back-bond directions of L and U (for the P/T naming)
def backbonds(topz):
    top = np.array([0.0, 0.0, 0.0]) if topz == 0 else np.array([1.0, 1.0, 1.0])
    nn = [top + np.array(d, float) for d in itertools.product([1, -1], repeat=3)]
    nn = [p for p in nn if is_diamond(p[None, :])[0]]
    return [tuple((p - top).astype(int)) for p in nn if p[2] < top[2]]
print("L top-layer back-bond vectors (a/4 units):", backbonds(0))
print("U top-layer back-bond vectors (a/4 units):", backbonds(1))
```

Output (about 27 s; the numpy int64 reprs of the last two lines are cosmetic):

```
Operations g={W|t} with g(L) = U (units a/4); t listed modulo nothing (all found in box):
  m_y (plane (010))            count=  32  t_z values (a/4 units) = [1.0]
  m_x (plane (100))            count=  32  t_z values (a/4 units) = [1.0]
  4z- (x,y,z)->(y,-x,z)        count=  32  t_z values (a/4 units) = [1.0]
  4z+ (x,y,z)->(-y,x,z)        count=  32  t_z values (a/4 units) = [1.0]
pure translations found: 0
extra accepted operations with non-integer (a/8-grid) translations: 0
m_y class: distinct (glide vector mod a along x, plane position y0 mod a/2) in units of a:
   glide x-component 0.2500 a (i.e. +0.2500 a), plane y0 = 0.1250 a, t_z = 0.2500 a
   glide x-component 0.7500 a (i.e. -0.2500 a), plane y0 = 0.3750 a, t_z = 0.2500 a
Azimuth test (normal [001]):
  [100]            ops fixing u and n: ['m_y (plane (010))'];  ops with W u = -u (reciprocity): ['m_x (plane (100))']
  [010]            ops fixing u and n: ['m_x (plane (100))'];  ops with W u = -u (reciprocity): ['m_y (plane (010))']
  [110]            ops fixing u and n: NONE;  ops with W u = -u (reciprocity): NONE
  [1-10]           ops fixing u and n: NONE;  ops with W u = -u (reciprocity): NONE
  [210] (general)  ops fixing u and n: NONE;  ops with W u = -u (reciprocity): NONE
Self-maps of the lower half crystal (point parts): ['1', '2z', 'm_(1-10) (x,y)->(y,x)', 'm_(110) (x,y)->(-y,-x)']
L top-layer back-bond vectors (a/4 units): [(np.int64(1), np.int64(-1), np.int64(-1)), (np.int64(-1), np.int64(1), np.int64(-1))]
U top-layer back-bond vectors (a/4 units): [(np.int64(1), np.int64(1), np.int64(-1)), (np.int64(-1), np.int64(-1), np.int64(-1))]
```

### A.2 `e4_a2_pointscatter.py` (kinematic and Foldy-Lax point-scatterer check of A_up = exp(-i q.t) A_low)

```python
"""E4 (a), consequence A_up = exp(-i (k_out - k_in).t) A_low for the specular beam.
Own point-scatterer model (written for E4; no package or C2 code used):
isotropic point scatterers on diamond sites of finite Si(001) terrace clusters, (i) kinematic sum and
(ii) Foldy-Lax multiple scattering  psi_j = exp(i k_in.r_j) + f sum_{l!=j} G(r_j - r_l) psi_l,
G(r) = exp(i k r)/r, far-field amplitude A = f sum_j exp(-i k_out.r_j) psi_j.
Lower cluster L: diamond sites with -Z <= z <= 0 (units a/4) in a disc of radius R about the atom
at the origin.  Upper clusters built INDEPENDENTLY as lattice truncations with top layer z = 1:
  U_g: sites with 1-Z <= z <= 1 in the disc whose centre is the glide image of L's centre;
  U_s: sites with 1-Z <= z <= 1 in the disc whose centre is the 4_1-screw image of L's centre.
We check (1) U_g == glide(L) and U_s == screw(L) as sets (crystallography on the finite clusters),
(2) A(U)/A(L) versus exp(-i q.t) at [100] and [110] with the two models,
(3) the misalignment residual delta(phi) near [100] is odd and its first-order slope.
"""
import numpy as np

a = 5.4309
u = a / 4.0

def sites_disc(zmin, zmax, cx, cy, R):
    pts = []
    rng = int(R) + 4
    for x in range(int(np.floor(cx)) - rng, int(np.ceil(cx)) + rng + 1):
        for y in range(int(np.floor(cy)) - rng, int(np.ceil(cy)) + rng + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 > R * R + 1e-9:
                continue
            for z in range(zmin, zmax + 1):
                ev = x % 2 == 0 and y % 2 == 0 and z % 2 == 0 and (x + y + z) % 4 == 0
                od = x % 2 == 1 and y % 2 == 1 and z % 2 == 1 and (x + y + z) % 4 == 3
                if ev or od:
                    pts.append((x, y, z))
    return np.array(pts, dtype=float)

Z, R = 11, 10.0
L = sites_disc(-Z, 0, 0.0, 0.0, R)
# glide {m_y | (1,1,1)} (units a/4): (x,y,z) -> (x+1, -y+1, z+1)   [plane y = a/8, glide (a/4)(1,0,1)]
glide = lambda p: np.column_stack([p[:, 0] + 1, -p[:, 1] + 1, p[:, 2] + 1])
# screw 4z+ : (x,y,z) -> (-y, x, z) + t ; find t mapping L into the upper crystal (from E4 search)
def is_diamond(p):
    r = np.round(p).astype(int)
    ev = np.all(r % 2 == 0, axis=1) & (r.sum(axis=1) % 4 == 0)
    od = np.all(r % 2 == 1, axis=1) & (r.sum(axis=1) % 4 == 3)
    return ev | od
ts = None
for tx in range(-2, 3):
    for ty in range(-2, 3):
        t = np.array([tx, ty, 1.0])
        img = np.column_stack([-L[:, 1], L[:, 0], L[:, 2]]) + t
        if np.all(is_diamond(img)):
            ts = t
            break
    if ts is not None:
        break
screw = lambda p: np.column_stack([-p[:, 1], p[:, 0], p[:, 2]]) + ts
print("screw translation (a/4 units):", ts)

cg = glide(np.array([[0.0, 0.0, 0.0]]))[0]
cs = screw(np.array([[0.0, 0.0, 0.0]]))[0]
Ug = sites_disc(1 - Z, 1, cg[0], cg[1], R)
Us = sites_disc(1 - Z, 1, cs[0], cs[1], R)
def same_set(P, Q):
    a_ = {tuple(np.round(p).astype(int)) for p in P}
    b_ = {tuple(np.round(q).astype(int)) for q in Q}
    return a_ == b_
print(f"N(L) = {len(L)}, N(U_g) = {len(Ug)}, N(U_s) = {len(Us)}")
print("U_g (independent truncation) == glide(L):", same_set(Ug, glide(L)))
print("U_s (independent truncation) == screw(L):", same_set(Us, screw(L)))

def amplitudes(P_units, k, theta, azim_deg, f):
    P = P_units * u
    ph = np.deg2rad(azim_deg)
    uh = np.array([np.cos(ph), np.sin(ph), 0.0])
    kin = k * (np.cos(theta) * uh + np.array([0, 0, -np.sin(theta)]))
    kout = k * (np.cos(theta) * uh + np.array([0, 0, np.sin(theta)]))
    inc = np.exp(1j * P @ kin)
    Akin = f * np.sum(np.exp(-1j * P @ kout) * inc)
    D = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
    np.fill_diagonal(D, 1.0)
    G = np.exp(1j * k * D) / D
    np.fill_diagonal(G, 0.0)
    M = np.eye(len(P)) - f * G
    psi = np.linalg.solve(M, inc)
    Afl = f * np.sum(np.exp(-1j * P @ kout) * psi)
    q = kout - kin
    return Akin, Afl, q

def residual(Aup, Alow, q, t_units):
    t = t_units * u
    return np.angle(Aup / Alow * np.exp(1j * q @ t))

for (k, theta, f, label) in ((250.5323, 0.0165, 0.35 + 0.05j, "k = 250.53/A (200 keV), theta 16.5 mrad"),
                             (6.0, 0.35, 0.5 + 0.1j, "k = 6/A, theta 0.35 rad (strong multiple scattering)")):
    print("==", label, ", f =", f)
    for az, name in ((0.0, "[100]"), (45.0, "[110]"), (-45.0, "[1-10]"), (26.565, "[210]")):
        AkL, AfL, q = amplitudes(L, k, theta, az, f)
        AkG, AfG, _ = amplitudes(Ug, k, theta, az, f)
        AkS, AfS, _ = amplitudes(Us, k, theta, az, f)
        print(f"  {name:7s} kinematic residual: U_g {residual(AkG, AkL, q, np.array([1,1,1.])):+.2e}, "
              f"U_s {residual(AkS, AkL, q, ts):+.2e} | Foldy-Lax residual: U_g {residual(AfG, AfL, q, np.array([1,1,1.])):+.3e}, "
              f"U_s {residual(AfS, AfL, q, ts):+.3e};  |A_up/A_low| (FL, U_g) = {abs(AfG/AfL):.6f}")
    # misalignment around [100]: delta(phi) with the glide-built upper cluster
    out = []
    for dphi in (-2.0, -1.0, 1.0, 2.0):
        AkL, AfL, q = amplitudes(L, k, theta, dphi, f)
        AkG, AfG, _ = amplitudes(Ug, k, theta, dphi, f)
        out.append((dphi, residual(AfG, AfL, q, np.array([1, 1, 1.]))))
    print("  misalignment from [100] (deg -> Foldy-Lax residual rad):",
          ", ".join(f"{d:+.0f}: {r:+.3e}" for d, r in out))

# ---- beams outside the incidence plane at exact [100] (C2 section 1.3 "Other rods") --------------
def amp_general(P_units, k, kin_dir, kout_dir, f):
    P = P_units * u
    kin = k * kin_dir / np.linalg.norm(kin_dir)
    kout = k * kout_dir / np.linalg.norm(kout_dir)
    inc = np.exp(1j * P @ kin)
    D = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
    np.fill_diagonal(D, 1.0)
    G = np.exp(1j * k * D) / D
    np.fill_diagonal(G, 0.0)
    psi = np.linalg.solve(np.eye(len(P)) - f * G, inc)
    return f * np.sum(np.exp(-1j * P @ kout) * psi), kout - kin

print("== exact [100] azimuth, beams leaving the incidence plane (Foldy-Lax, k = 6/A, f = 0.5+0.1i)")
k, th, f = 6.0, 0.35, 0.5 + 0.1j
kin_dir = np.array([np.cos(th), 0.0, -np.sin(th)])
t_g = np.array([1.0, 1.0, 1.0]) * u
for psi_out in (0.0, 0.1, 0.3):
    kout_dir = np.array([np.cos(th) * np.cos(psi_out), np.cos(th) * np.sin(psi_out), np.sin(th)])
    kout_mir = kout_dir * np.array([1, -1, 1])
    AU, q = amp_general(Ug, k, kin_dir, kout_dir, f)
    AL, _ = amp_general(L, k, kin_dir, kout_dir, f)
    ALm, _ = amp_general(L, k, kin_dir, kout_mir, f)
    r_same = AU * np.exp(1j * q @ t_g) / AL
    r_mirr = AU * np.exp(1j * q @ t_g) / ALm
    print(f"  k_out azimuth {psi_out:.1f} rad out of the (010) plane: A_up e^(iq.t)/A_low(k_out) = "
          f"{abs(r_same):.6f} exp({np.angle(r_same):+.4f} i);  /A_low(m_y k_out) = {abs(r_mirr):.6f} exp({np.angle(r_mirr):+.1e} i)")

print("== exact [100] azimuth, non-specular beams IN the incidence plane (theta_out != theta_in)")
for th_out in (0.2, 0.5):
    kout_dir = np.array([np.cos(th_out), 0.0, np.sin(th_out)])
    AU, q = amp_general(Ug, k, kin_dir, kout_dir, f)
    AL, _ = amp_general(L, k, kin_dir, kout_dir, f)
    r = AU * np.exp(1j * q @ t_g) / AL
    print(f"  theta_out {th_out:.1f} rad: q_x = {q[0]:+.4f} 1/A; A_up e^(iq.t)/A_low = {abs(r):.12f} exp({np.angle(r):+.1e} i); "
          f"in-plane part of the phase -q_x t_x = {-q[0]*t_g[0]:+.4f} rad (not the specular -2k sin(theta) a/4 alone)")
```

Output (toy model; its residual values are not physical, only their zero / nonzero / odd structure):

```
screw translation (a/4 units): [-1. -1.  1.]
N(L) = 483, N(U_g) = 483, N(U_s) = 483
U_g (independent truncation) == glide(L): True
U_s (independent truncation) == screw(L): True
== k = 250.53/A (200 keV), theta 16.5 mrad , f = (0.35+0.05j)
  [100]   kinematic residual: U_g +1.03e-14, U_s +1.03e-14 | Foldy-Lax residual: U_g +2.709e-13, U_s +2.704e-13;  |A_up/A_low| (FL, U_g) = 1.000000
  [110]   kinematic residual: U_g +1.46e-13, U_s +1.46e-13 | Foldy-Lax residual: U_g +1.610e-01, U_s +1.610e-01;  |A_up/A_low| (FL, U_g) = 1.674145
  [1-10]  kinematic residual: U_g +1.38e-13, U_s +1.38e-13 | Foldy-Lax residual: U_g -1.610e-01, U_s -1.610e-01;  |A_up/A_low| (FL, U_g) = 0.597320
  [210]   kinematic residual: U_g +1.58e-13, U_s +1.58e-13 | Foldy-Lax residual: U_g +1.284e-01, U_s +1.284e-01;  |A_up/A_low| (FL, U_g) = 0.984462
  misalignment from [100] (deg -> Foldy-Lax residual rad): -2: -2.109e-01, -1: +9.228e-01, +1: -9.228e-01, +2: +2.109e-01
== k = 6/A, theta 0.35 rad (strong multiple scattering) , f = (0.5+0.1j)
  [100]   kinematic residual: U_g -7.22e-16, U_s -8.33e-16 | Foldy-Lax residual: U_g -3.442e-15, U_s -3.442e-15;  |A_up/A_low| (FL, U_g) = 1.000000
  [110]   kinematic residual: U_g -1.83e-15, U_s -2.00e-15 | Foldy-Lax residual: U_g -2.850e-02, U_s -2.850e-02;  |A_up/A_low| (FL, U_g) = 1.419564
  [1-10]  kinematic residual: U_g -1.94e-15, U_s -1.94e-15 | Foldy-Lax residual: U_g +2.850e-02, U_s +2.850e-02;  |A_up/A_low| (FL, U_g) = 0.704442
  [210]   kinematic residual: U_g -1.72e-15, U_s -1.72e-15 | Foldy-Lax residual: U_g -5.408e-02, U_s -5.408e-02;  |A_up/A_low| (FL, U_g) = 1.002877
  misalignment from [100] (deg -> Foldy-Lax residual rad): -2: +2.120e+00, -1: +7.165e-01, +1: -7.165e-01, +2: -2.120e+00
== exact [100] azimuth, beams leaving the incidence plane (Foldy-Lax, k = 6/A, f = 0.5+0.1i)
  k_out azimuth 0.0 rad out of the (010) plane: A_up e^(iq.t)/A_low(k_out) = 1.000000 exp(-0.0000 i);  /A_low(m_y k_out) = 1.000000 exp(-3.5e-15 i)
  k_out azimuth 0.1 rad out of the (010) plane: A_up e^(iq.t)/A_low(k_out) = 0.528004 exp(-0.3224 i);  /A_low(m_y k_out) = 1.000000 exp(+8.0e-15 i)
  k_out azimuth 0.3 rad out of the (010) plane: A_up e^(iq.t)/A_low(k_out) = 1.671773 exp(+0.1932 i);  /A_low(m_y k_out) = 1.000000 exp(-9.3e-16 i)
== exact [100] azimuth, non-specular beams IN the incidence plane (theta_out != theta_in)
  theta_out 0.2 rad: q_x = +0.2442 1/A; A_up e^(iq.t)/A_low = 1.000000000000 exp(+6.1e-15 i); in-plane part of the phase -q_x t_x = -0.3315 rad (not the specular -2k sin(theta) a/4 alone)
  theta_out 0.5 rad: q_x = -0.3707 1/A; A_up e^(iq.t)/A_low = 1.000000000000 exp(+1.9e-15 i); in-plane part of the phase -q_x t_x = +0.5034 rad (not the specular -2k sin(theta) a/4 alone)
```

### A.3 `e4_numbers.py` (carrier trap, R2 twin, Delta, shadow lengths, B16 bound)

```python
"""E4 independent numbers: (b) carrier trap, (c) R2 twin, (d) exact relativistic Delta,
(e) shadow lengths, (f) B16 wrong-branch bound. Written for review E4 without opening the package,
the calculator or the C2 scripts for these quantities. numpy/scipy only."""
import numpy as np
from scipy.special import erfc
from scipy.stats import norm

MEC2 = 510998.95          # eV
HC = 12398.419843320026   # eV A
A = 5.4309                # A (ASSUMPTION B2)
T = 200e3                 # eV
V0 = 12.0                 # V (ASSUMPTION B1)

lam = HC / np.sqrt(T * (T + 2 * MEC2))
k = 2 * np.pi / lam
print(f"lambda(200 keV) = {lam:.6f} A, k = {k:.4f} 1/A")

# ---------------- (d) Delta: first order vs exact -----------------------------------------------
# p^2 c^2 outside = T (T + 2 mc^2); inside (potential energy -e V0): (T+V0)(T+V0+2mc^2)
d_first = V0 * (1 + T / MEC2) / (T * (1 + T / (2 * MEC2)))
d_exact_from_p = ((T + V0) * (T + V0 + 2 * MEC2) - T * (T + 2 * MEC2)) / (T * (T + 2 * MEC2))
d_exact_doc = V0 * (2 * (T + MEC2) + V0) / (T * (T + 2 * MEC2))
print(f"(d) Delta first order = {d_first:.6e}; exact (from momenta) = {d_exact_from_p:.6e}; "
      f"doc exact form = {d_exact_doc:.6e}")
print(f"    relative difference (exact-first)/first = {(d_exact_from_p - d_first) / d_first:.4e}; "
      f"closed form V0/(2(T+mc^2)) = {V0 / (2 * (T + MEC2)):.4e}")
print(f"    non-relativistic V0/T = {V0 / T:.4e}; first/nonrel - 1 = {d_first / (V0 / T) - 1:.4f}; "
      f"nonrel/first - 1 = {(V0 / T) / d_first - 1:.4f}")
theta_c = np.arcsin(np.sqrt(d_first / (1 + d_first)))
print(f"    theta_c = {theta_c * 1e3:.4f} mrad (sin theta_c = sqrt(Delta/(1+Delta)))")

def theta_ext_from_int(theta_int, D):
    s2 = (1 + D) * np.sin(theta_int) ** 2 - D
    return np.arcsin(np.sqrt(s2))

def th_int_bragg(d_spacing, n, D):
    """internal Bragg condition 2 k_int sin(theta_int) = n 2 pi/d, k_int = k sqrt(1 + D)"""
    return np.arcsin(n * lam / (2 * d_spacing) / np.sqrt(1 + D))

# effect of the Delta form on an a/4 step phase |dphi| = (4 pi/lam) (a/4) sin(theta_ext)
print("    a/4 step phase change, exact vs first-order Delta, at the Si(001) rod Bragg conditions:")
worst = 0.0
for n in (4, 8, 12):
    dsp = A / n          # (0,0,n) spacing
    th_i = th_int_bragg(dsp, 1, d_first)
    th_e1 = theta_ext_from_int(th_i, d_first)
    th_e2 = theta_ext_from_int(th_int_bragg(dsp, 1, d_exact_from_p), d_exact_from_p)
    p1 = 4 * np.pi / lam * (A / 4) * np.sin(th_e1)
    p2 = 4 * np.pi / lam * (A / 4) * np.sin(th_e2)
    worst = max(worst, abs(p2 - p1))
    print(f"      (0,0,{n:2d}): theta_int {th_i*1e3:7.3f} mrad, theta_ext {th_e1*1e3:7.4f} mrad, "
          f"|dphi| {p1:.6f} rad, change {p2 - p1:+.3e} rad")
print(f"    largest |change| over (004),(008),(0,0,12): {worst:.3e} rad")
# at a fixed external angle (measured angle) the step phase does not depend on Delta at all
for th in (1e-3, 2e-3):
    # sensitivity if the angle were computed from an internal condition at theta_ext = th
    s2 = np.sin(th) ** 2
    dd = d_exact_from_p - d_first
    sin_int2 = (s2 + d_first) / (1 + d_first)
    s2b = (1 + d_exact_from_p) * sin_int2 - d_exact_from_p
    print(f"      at theta_ext = {th*1e3:.0f} mrad (same internal angle): a/4 phase change "
          f"{4*np.pi/lam*(A/4)*(np.sqrt(s2b)-np.sqrt(s2)):+.2e} rad")

# ---------------- (e) shadow lengths ------------------------------------------------------------
d111 = A / np.sqrt(3)
print(f"(e) d_111 = {d111:.5f} A; a/4 = {A/4:.5f} A")
for lab, n in (("(4,-4,4)", 4), ("(8,-8,8)", 8), ("(3,-3,3)", 3), ("(5,-5,5)", 5), ("(7,-7,7)", 7), ("(6,-6,6)", 6)):
    th_i = th_int_bragg(d111, n, d_first)
    th_e = theta_ext_from_int(th_i, d_first)
    print(f"    {lab}: theta_int {th_i*1e3:.3f} mrad, theta_ext {th_e*1e3:.4f} mrad; bilayer shadow "
          f"{d111/np.tan(th_e):.2f} A; 10 nm shadow {100/np.tan(th_e)/10:.2f} nm; a/4 shadow {A/4/np.tan(th_e):.2f} A")
th = 22.5e-3
print(f"    22.5 mrad: bilayer {d111/np.tan(th):.2f} A, a/4 {A/4/np.tan(th):.2f} A, 10 nm {100/np.tan(th)/10:.2f} nm")
for n in (4, 8, 12):
    dsp = A / n
    th_i = th_int_bragg(dsp, 1, d_first)
    th_e = theta_ext_from_int(th_i, d_first)
    print(f"    Si(001) (0,0,{n}): theta_int {th_i*1e3:.3f}, theta_ext {th_e*1e3:.3f} mrad, wrap "
          f"{lam/(2*np.sin(th_e)):.4f} A, foreshortening {1/np.sin(th_e):.1f}x, a/4 shadow "
          f"{A/4/np.tan(th_e):.1f} A, a/2 shadow {A/2/np.tan(th_e):.1f} A, 10 nm {100/np.tan(th_e)/10:.1f} nm")

# ---------------- (f) B16 bound ------------------------------------------------------------------
p3 = erfc(3 / np.sqrt(2))
print(f"(f) P(|Z|>3) = {p3:.4e}; one-sided P(Z>3) = {p3/2:.4e}")
# worst case: sigma_c -> pi/3: a wrong branch needs |c - c_true| >= 2 pi - 3 sigma_c
for sc in (np.pi / 3, 0.9, 0.5, 0.2):
    z = (2 * np.pi - 3 * sc) / sc
    print(f"    sigma_c = {sc:.3f} rad: wrong-branch acceptance needs |Z| >= {z:.3f}, P = {erfc(z/np.sqrt(2)):.3e}")
# rule-of-three upper bound for 0 events in 3987
print(f"    0 wrong of 3987 accepted: one-sided 95% upper bound on the rate = {1 - 0.05**(1/3987):.2e}")

# ---------------- (b) carrier trap ---------------------------------------------------------------
print("(b) threshold 2 arctan(pi/2) =", f"{2*np.arctan(np.pi/2):.5f} rad; -2.36 + pi = {-2.36 + np.pi:.5f}")
N = 256
for Nn in (64, 256, 1024):
    print(f"    discrete threshold for N={Nn}: 2 arctan(N sin(pi/N)/2) = {2*np.arctan(Nn*np.sin(np.pi/Nn)/2):.6f} rad")

def hologram_2d(Delta, N=256, qc=(40, 24), amp_r=1.0):
    y, x = np.mgrid[0:N, 0:N]
    phi = np.where(x < N // 2, 0.0, Delta)          # 50/50 sharp step, normal along x
    uo = np.exp(1j * phi)
    ur = amp_r * np.exp(-2j * np.pi * (qc[0] * x + qc[1] * y) / N)   # reference tilt
    I = np.abs(uo + ur) ** 2                          # sideband phi_o - phi_r at +qc
    return I, phi

def recon(I, center, r=12):
    N = I.shape[0]
    F = np.fft.fft2(I)
    ky, kx = np.meshgrid(np.fft.fftfreq(N) * N, np.fft.fftfreq(N) * N, indexing="ij")
    cx, cy = center
    mask = ((kx - cx) ** 2 + (ky - cy) ** 2) <= r * r
    S = np.where(mask, F, 0)
    y, x = np.mgrid[0:N, 0:N]
    w = np.fft.ifft2(S) * np.exp(-2j * np.pi * (cx * x + cy * y) / N)
    return np.angle(w)

for Delta in (2.36, 1.9, 2.1):
    I, phi = hologram_2d(Delta)
    F = np.fft.fft2(I)
    mag = np.abs(F)
    ky, kx = np.meshgrid(np.fft.fftfreq(N) * N, np.fft.fftfreq(N) * N, indexing="ij")
    m2 = mag.copy()
    m2[(np.abs(kx) <= 2) & (np.abs(ky) <= 2)] = 0      # exclude the centre band
    top = np.argsort(m2.ravel())[::-1][:6]
    vals = m2.ravel()[top]
    locs = [(int(kx.ravel()[i]), int(ky.ravel()[i])) for i in top]
    carrier = mag[ky.astype(int) == 24][(kx[ky.astype(int) == 24] == 40)][0]
    print(f"    Delta={Delta}: six brightest off-centre bins (kx,ky): {locs}")
    print(f"       magnitudes/N^2: {[round(v/N**2, 6) for v in vals]}; carrier (40,24): {carrier/N**2:.6f}")
    four = vals[:4]
    print(f"       max relative spread among the four brightest: {(four.max()-four.min())/four.max():.2e}")
    for c in locs[:4]:
        ph = recon(I, c)
        lo = np.median(ph[:, N // 8: 3 * N // 8]); hi = np.median(ph[:, 5 * N // 8: 7 * N // 8])
        d = np.angle(np.exp(1j * (hi - lo)))
        print(f"       recentre on {c}: median step = {d:+.4f} rad")
    ph = recon(I, (40, 24))
    lo = np.median(ph[:, N // 8: 3 * N // 8]); hi = np.median(ph[:, 5 * N // 8: 7 * N // 8])
    print(f"       recentre on the true carrier (40,24): median step = {np.angle(np.exp(1j*(hi-lo))):+.4f} rad")

# ---------------- (c) R2 twin --------------------------------------------------------------------
print("(c) R2: u_r(r) = u_o(r + s) with a carrier; reconstruction vs phi(r) - phi(r+s)")
N = 256
y, x = np.mgrid[0:N, 0:N]
def feature_phase():
    ph = np.zeros((N, N))
    # an asymmetric (chiral-looking) feature: an L-shaped bump with a linear ramp inside
    m = (x >= 60) & (x < 90) & (y >= 100) & (y < 110)
    ph[m] += 0.8 * (x[m] - 60) / 30
    m2 = (x >= 60) & (x < 70) & (y >= 110) & (y < 140)
    ph[m2] += 0.5
    # a step: phi = Delta for x >= 180 (upper terrace at larger x, normal +x)
    ph[:, 180:] += 1.2
    return ph
phi = feature_phase()
for s in ((20, 8), (-20, 8)):
    sx, sy = s
    phi_rs = np.roll(np.roll(phi, -sy, axis=0), -sx, axis=1)   # phi(r + s) (periodic)
    uo = np.exp(1j * phi)
    ur = np.exp(1j * phi_rs) * np.exp(-2j * np.pi * (48 * x + 32 * y) / N)
    I = np.abs(uo + ur) ** 2
    rec = recon(I, (48, 32), r=40)
    expect = np.angle(np.exp(1j * (phi - phi_rs)))
    err = np.angle(np.exp(1j * (rec - expect)))
    inner = np.abs(err)[20:-20, 20:-20]
    print(f"    s = {s}: median |rec - (phi(r)-phi(r+s))| = {np.median(inner):.2e} rad (band-limited edges excluded by median)")
    # twin of the L-feature: expected at r = p - s, sign inverted, NOT mirrored
    twin = -phi_rs
    # correlation of the reconstructed map with the translated copy vs the mirrored copy
    feat = np.zeros((N, N)); feat[100:140, 60:90] = phi[100:140, 60:90]
    trans = -np.roll(np.roll(feat, -sy, axis=0), -sx, axis=1)
    featm = np.zeros((N, N)); featm[100:140, 60:90] = feat[100:140, 60:90][:, ::-1]   # mirrored in x about x = 74.5
    mir = -np.roll(np.roll(featm, -sy, axis=0), -sx, axis=1)
    reg = np.zeros((N, N), bool); reg[100 - sy - 5:140 - sy + 5, 60 - sx - 5:90 - sx + 5] = True
    reg &= ~(feat != 0)
    reg &= (np.abs(trans) + 0) >= 0
    c_t = np.corrcoef(rec[reg], trans[reg])[0, 1]
    c_m = np.corrcoef(rec[reg], mir[reg])[0, 1]
    print(f"      twin region: corr with sign-inverted TRANSLATED copy {c_t:+.3f}, with sign-inverted MIRRORED copy {c_m:+.3f}")
    # the step: phi = 1.2 for x >= 180 ; strip between 180 - sx and 180 (sx>0) or 180 and 180+|sx|
    row = rec[60, :]
    if sx > 0:
        strip = np.median(row[180 - sx + 3: 180 - 3]); where = f"x in [{180 - sx}, 180)"
    else:
        strip = np.median(row[180 + 3: 180 - sx - 3]); where = f"x in [180, {180 - sx})"
    print(f"      step (Delta = +1.2 rad, upper terrace at larger x): strip {where}, width {abs(sx)} px, phase {strip:+.3f} rad")
```

Output:

```
lambda(200 keV) = 0.025079 A, k = 250.5323 1/A
(d) Delta first order = 6.981998e-05; exact (from momenta) = 6.982057e-05; doc exact form = 6.982057e-05
    relative difference (exact-first)/first = 8.4388e-06; closed form V0/(2(T+mc^2)) = 8.4388e-06
    non-relativistic V0/T = 6.0000e-05; first/nonrel - 1 = 0.1637; nonrel/first - 1 = -0.1406
    theta_c = 8.3556 mrad (sin theta_c = sqrt(Delta/(1+Delta)))
    a/4 step phase change, exact vs first-order Delta, at the Si(001) rod Bragg conditions:
      (0,0, 4): theta_int   9.236 mrad, theta_ext  3.9345 mrad, |dphi| 2.676641 rad, change -5.094e-05 rad
      (0,0, 8): theta_int  18.472 mrad, theta_ext 16.4744 mrad, |dphi| 11.207125 rad, change -1.217e-05 rad
      (0,0,12): theta_int  27.710 mrad, theta_ext 26.4205 mrad, |dphi| 17.971971 rad, change -7.587e-06 rad
    largest |change| over (004),(008),(0,0,12): 5.094e-05 rad
      at theta_ext = 1 mrad (same internal angle): a/4 phase change -2.00e-04 rad
      at theta_ext = 2 mrad (same internal angle): a/4 phase change -1.00e-04 rad
(e) d_111 = 3.13553 A; a/4 = 1.35773 A
    (4,-4,4): theta_int 15.997 mrad, theta_ext 13.6415 mrad; bilayer shadow 229.84 A; 10 nm shadow 733.01 nm; a/4 shadow 99.52 A
    (8,-8,8): theta_int 31.998 mrad, theta_ext 30.8882 mrad; bilayer shadow 101.48 A; 10 nm shadow 323.65 nm; a/4 shadow 43.94 A
    (3,-3,3): theta_int 11.998 mrad, theta_ext 8.6096 mrad; bilayer shadow 364.18 A; 10 nm shadow 1161.46 nm; a/4 shadow 157.69 A
    (5,-5,5): theta_int 19.997 mrad, theta_ext 18.1675 mrad; bilayer shadow 172.57 A; 10 nm shadow 550.37 nm; a/4 shadow 74.73 A
    (7,-7,7): theta_int 27.997 mrad, theta_ext 26.7216 mrad; bilayer shadow 117.31 A; 10 nm shadow 374.14 nm; a/4 shadow 50.80 A
    (6,-6,6): theta_int 23.997 mrad, theta_ext 22.4953 mrad; bilayer shadow 139.36 A; 10 nm shadow 444.46 nm; a/4 shadow 60.35 A
    22.5 mrad: bilayer 139.33 A, a/4 60.33 A, 10 nm 444.37 nm
    Si(001) (0,0,4): theta_int 9.236, theta_ext 3.934 mrad, wrap 3.1871 A, foreshortening 254.2x, a/4 shadow 345.1 A, a/2 shadow 690.2 A, 10 nm 2541.6 nm
    Si(001) (0,0,8): theta_int 18.472, theta_ext 16.474 mrad, wrap 0.7612 A, foreshortening 60.7x, a/4 shadow 82.4 A, a/2 shadow 164.8 A, 10 nm 606.9 nm
    Si(001) (0,0,12): theta_int 27.710, theta_ext 26.420 mrad, wrap 0.4747 A, foreshortening 37.9x, a/4 shadow 51.4 A, a/2 shadow 102.8 A, 10 nm 378.4 nm
(f) P(|Z|>3) = 2.6998e-03; one-sided P(Z>3) = 1.3499e-03
    sigma_c = 1.047 rad: wrong-branch acceptance needs |Z| >= 3.000, P = 2.700e-03
    sigma_c = 0.900 rad: wrong-branch acceptance needs |Z| >= 3.981, P = 6.853e-05
    sigma_c = 0.500 rad: wrong-branch acceptance needs |Z| >= 9.566, P = 1.107e-21
    sigma_c = 0.200 rad: wrong-branch acceptance needs |Z| >= 28.416, P = 1.285e-177
    0 wrong of 3987 accepted: one-sided 95% upper bound on the rate = 7.51e-04
(b) threshold 2 arctan(pi/2) = 2.00777 rad; -2.36 + pi = 0.78159
    discrete threshold for N=64: 2 arctan(N sin(pi/N)/2) = 2.007406 rad
    discrete threshold for N=256: 2 arctan(N sin(pi/N)/2) = 2.007747 rad
    discrete threshold for N=1024: 2 arctan(N sin(pi/N)/2) = 2.007768 rad
    Delta=2.36: six brightest off-centre bins (kx,ky): [(39, 24), (-39, -24), (41, 24), (-41, -24), (40, 24), (-40, -24)]
       magnitudes/N^2: [np.float64(0.588637), np.float64(0.588637), np.float64(0.588637), np.float64(0.588637), np.float64(0.380925), np.float64(0.380925)]; carrier (40,24): 0.380925
       max relative spread among the four brightest: 3.21e-15
       recentre on (39, 24): median step = -0.7842 rad
       recentre on (-39, -24): median step = +0.7842 rad
       recentre on (41, 24): median step = -0.7842 rad
       recentre on (-41, -24): median step = +0.7842 rad
       recentre on the true carrier (40,24): median step = +2.3614 rad
    Delta=1.9: six brightest off-centre bins (kx,ky): [(-40, -24), (40, 24), (39, 24), (-39, -24), (41, 24), (-41, -24)]
       magnitudes/N^2: [np.float64(0.581683), np.float64(0.581683), np.float64(0.517849), np.float64(0.517849), np.float64(0.517849), np.float64(0.517849)]; carrier (40,24): 0.581683
       max relative spread among the four brightest: 1.10e-01
       recentre on (-40, -24): median step = -1.9019 rad
       recentre on (40, 24): median step = +1.9019 rad
       recentre on (39, 24): median step = -1.2451 rad
       recentre on (-39, -24): median step = +1.2451 rad
       recentre on the true carrier (40,24): median step = +1.9019 rad
    Delta=2.1: six brightest off-centre bins (kx,ky): [(-39, -24), (39, 24), (41, 24), (-41, -24), (-40, -24), (40, 24)]
       magnitudes/N^2: [np.float64(0.552233), np.float64(0.552233), np.float64(0.552233), np.float64(0.552233), np.float64(0.497571), np.float64(0.497571)]; carrier (40,24): 0.497571
       max relative spread among the four brightest: 3.02e-15
       recentre on (-39, -24): median step = +1.0448 rad
       recentre on (39, 24): median step = -1.0448 rad
       recentre on (41, 24): median step = -0.8316 rad
       recentre on (-41, -24): median step = +0.8316 rad
       recentre on the true carrier (40,24): median step = +2.1017 rad
(c) R2: u_r(r) = u_o(r + s) with a carrier; reconstruction vs phi(r) - phi(r+s)
    s = (20, 8): median |rec - (phi(r)-phi(r+s))| = 6.62e-03 rad (band-limited edges excluded by median)
      twin region: corr with sign-inverted TRANSLATED copy +0.932, with sign-inverted MIRRORED copy +0.137
      step (Delta = +1.2 rad, upper terrace at larger x): strip x in [160, 180), width 20 px, phase -1.208 rad
    s = (-20, 8): median |rec - (phi(r)-phi(r+s))| = 6.54e-03 rad (band-limited edges excluded by median)
      twin region: corr with sign-inverted TRANSLATED copy +0.934, with sign-inverted MIRRORED copy -0.050
      step (Delta = +1.2 rad, upper terrace at larger x): strip x in [180, 200), width 20 px, phase +1.207 rad
```

### A.4 Commands run (from /home/user/Holography unless stated) and their outputs

```
$ git diff --stat 0de75f8 HEAD -- <scope>           # 11 files, 460 insertions, 40 deletions (HEAD d35b751)
$ venv/bin/pytest -q -p no:cacheprovider            # clean tree at d35b751
527 passed in 12.36s
$ git worktree add --detach <scratch>/wt_bd654c2 bd654c2; cd <scratch>/wt_bd654c2
$ PYTHONPATH=<scratch>/wt_bd654c2 venv/bin/pytest -q -p no:cacheprovider   # package imported from the worktree (checked)
527 passed in 12.04s
$ git worktree remove --force <scratch>/wt_bd654c2; git worktree prune
$ git diff bd654c2 HEAD --stat -- reflection_holo tests   # empty: package and tests identical
$ venv/bin/python tools/phase1_numbers.py | tail -1
   17/17 checks pass
$ venv/bin/python tools/physics_checks/q1_si001_quarter_step_symmetry.py | tail -1   (q2, q3 likewise)
   41/41 self-checks pass
   21/21 self-checks pass
   7/7 self-checks pass
$ venv/bin/pytest -q -s -p no:cacheprovider tests/quantification/test_quant_rocking_noise.py   (quantification/ unchanged vs HEAD in the working tree)
tilts 20.0-25.0 mrad step 0.25 (21), noise 0.05 rad, h 10.0 A: intercept s.e. 0.163 rad; accepted 1993 (correct 1993, WRONG 0, allowed <= 16 at p3 = 2.700e-03, alpha 0.0001), refused branch 7, guard 0; std(h err)/sigma_h = 1.0256 (bound 1 +- 0.0634, K = 1993); mean err +3.65e-05 A; seed 20260922, 2000 trials
tilts 20.0-25.0 mrad step 0.5 (11), noise 0.21 rad, h 3.0 A: intercept s.e. 0.903 rad; accepted 1994 (correct 1994, WRONG 0, allowed <= 16 at p3 = 2.700e-03, alpha 0.0001), refused branch 6, guard 0; std(h err)/sigma_h = 0.9802 (bound 1 +- 0.0634, K = 1994); mean err +1.75e-04 A; seed 20260922, 2000 trials
10 passed in 2.30s
$ venv/bin/python -c "... bound per series at the tested sigma_c (scipy log_ndtr) ..."
sigma_c=0.163: z=35.547, P=10^-276.04, expected wrong in 1993: 1.83e-273
sigma_c=0.903: z=3.958, P=10^-4.12, expected wrong in 1994: 0.151
sigma_c=1.040: z=3.042, P=10^-2.63, expected wrong in 19968: 47   (A2b observed 35)
sigma_c=1.047: z=3.000, P=10^-2.57, expected wrong in 1: 0.0027
$ scripted check that every *.py and reflection_holo/<dir>/ named in the implementation and test_id columns of HEAD:docs/source_map.tsv is tracked in git -> no missing file
$ git grep -n "102 A" HEAD -- docs/*.md docs/source_map.tsv README.md configs   -> only docs/03:157 ("revision 3 corrects 102 A")
$ grep for the carrier-location options in reflection_holo/reconstruction/sideband.py -> lines 11, 215, 226 ("EMPTY or flat-region"; object holograms refused unless trap_demonstration)
```

NOT RUN: any dynamical, Bloch-wave or multislice reflection calculation (none exists); the
uncommitted round-2 working-tree changes (configs/, reflection_holo/io/, tests/io/) were not
reviewed or tested; `python -O`.
