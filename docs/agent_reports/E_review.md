# E. Adversarial review of the reflection-holography documentation set

Reviewer: agent E, 2026-09-21. Working to
`ba72277e-si110_reflection_holography_agent_instructions.txt` sections 1, 9, 10.
Documents under review: `README.md`, `docs/03_physics_summary.md`,
`docs/05_final_repository_specification.md`, `docs/physics_conventions.md`,
`docs/model_assumptions.md`, `docs/06_project_inputs_required.md`,
`docs/source_map.tsv`, `tools/provenance_checks/README.md`.
Supporting material read: `docs/agent_reports/{B,C,D}*`, `C_calculator_output.txt`,
`orchestrator_sanity_numbers.txt`, `tools/reflection_step_phase_calculator.py`,
the read-only clone of `si110-reflection-holography`.

All numbers below labelled "E recomputed" come from an independent numpy script
(`scratchpad/e_check.py`), written without reading the calculator's implementation
of the quantity concerned.

Verification scripts: `scratchpad/e_check.py`, `e_check2.py`, `e_check3.py`, `e_paraxial.py`.
The calculator was also executed (`25/25 PASS`, output byte-identical to the committed
`C_calculator_output.txt`).

Review complete: 3 Blockers, 11 Major, 19 Minor, 6 Nit, plus a list of 20 items verified correct.

---

## INDEX OF FINDINGS

| ID | Severity | File | One line |
|---|---|---|---|
| B1 | Blocker | 03 §5, SM08, assumptions A1 | paraxial error is 0.106 rad, not "below 0.04"; C and D disagree by exactly 3x and SM08 cites both |
| B2 | Blocker | README (+05 §1, §6) | index points at 5 files that do not exist (00, 01, references.bib, A report) |
| B3 | Blocker | 03 §3 | attributes a table and `Delta = V0/T` to the instruction file, which contains neither |
| M1 | Major | 03 §3, 05 §2, §4.1 | `(nnn)` is not the specular rod of a `(1,-1,1)` surface; must be `(n,-n,n)` |
| M2 | Major | 03 §3 | "total external reflection" does not exist for electrons (`V0>0`); it is the internal escape angle |
| M3 | Major | 03 §2, assumptions A4 | "refraction is the entire signal" holds only at an exact bulk-Bragg point |
| M4 | Major | 05 §0 | AC2/AC3 untestable; AC3 asserts Osakabe used Si(111), which model_assumptions calls UNVERIFIED |
| M5 | Major | source_map SM07 | attributes the 1/40-1/70 foreshortening figure to P23; B says its provenance is unresolved |
| M6 | Major | 03, 05 (absent) | grazing-incidence shadowing missing: 444 nm of dead surface behind a 10 nm mesa |
| M7 | Major | 06 item 3, 05 §5.4 | convergence semi-angle is not marked blocking, yet 0.02 mrad kills a 10 nm step phase |
| M8 | Major | 03 §4 | "0.003 A at (444)" is the (666) number; at (444) it is 0.0041 A |
| M9 | Major | 05 §5.7, 03 §3 | height formula drops the sign the conventions file says is never dropped |
| M10 | Major | 05 §5 | charging, biprism Fresnel fringes and drift are nowhere in the forward model |
| M11 | Major | 05 §0.2, §4.3-4.5, §8 | nothing independently validates the reflection PHASE, only the intensity |


---

## BLOCKERS

### B1. The paraxial-propagator error is understated by a factor of 3; the quoted 0.04 rad is wrong (0.106 rad)

*File:* `docs/03_physics_summary.md` §5, first bullet; `docs/source_map.tsv` SM08;
`docs/model_assumptions.md` A1; `docs/05_final_repository_specification.md` §4.3 item 9.

Quoted (03 §5): "the longitudinal component is unchanged, so the wave is forward-propagating along the
beam axis and **the paraxial Fresnel error over a 200 A cell is below 0.04 rad** (C section 5.1)."
Quoted (SM08): "Paraxial Fresnel propagator error over 198 A cell below 0.04 rad at 64 mrad ...
Conventions: `exp(-i pi lambda dz q^2)`".

**What is wrong.** The multislice Fresnel propagator is `exp(-i pi lambda dz q^2)` (SM08 states this
itself), i.e. it expands `k_z = sqrt(k^2 - q^2)` in the transverse WAVEVECTOR `q`, giving
`k_z ~ k(1 - sin^2(alpha)/2)`. The error is therefore

    err = dz [ k - q^2/(2k) - sqrt(k^2-q^2) ] = k dz sin^4(alpha)/8 + O(sin^6)

C section 5.1 instead evaluates `|k L (sqrt(1-sin^2 alpha) - (1 - alpha^2/2))| = k L |cos alpha - 1 + alpha^2/2|
= k L alpha^4/24`, i.e. it compares the exact `cos alpha` against a Taylor series of `cos alpha` in the
ANGLE. That is not the paraxial propagator, and it is exactly a factor 3 too small.

**E recomputed** (exact minus `exp(-i pi lambda dz q^2)`, L = 198.2 A, 200 keV):

| alpha | C's number (quoted in 03/SM08) | correct Fresnel error |
|---|---|---|
| 24.0 mrad | 0.00069 rad | 0.00206 rad |
| 45.0 mrad (full specular scattering angle 2*theta) | 0.00849 rad | 0.0255 rad |
| 64.3 mrad (2/3 band edge at 0.13 A) | 0.03537 rad | 0.1061 rad |

The calculator itself prints the correct value in parentheses on the same line
(`~k L alpha^4/8 = 0.10613 rad`, `C_calculator_output.txt` section 9) and the documents quoted the
wrong one of the two.

**Why it matters beyond the factor 3.** 0.0255 rad at the full specular scattering angle is the same
size as the phase precision the documents elsewhere claim (`sigma_phi = 0.028 rad`, 03 §4), and the
step phases being measured are 0.96-4.54 rad. The sentence "the propagator is not the obstacle" is
still defensible (the error is common-mode between two terraces at the same `k_out` and cancels in the
step phase) but that argument is not made, and the headline number is wrong.

**Proposed wording (03 §5):** "the paraxial Fresnel error `k dz sin^4(theta)/8` over the 198 A cell is
0.002 rad at the 24 mrad tilt, 0.026 rad at the 45 mrad specular scattering angle and 0.106 rad at the
64 mrad band edge; it is common-mode between two terraces reflecting into the same `k_out` and so
cancels in the step phase, but it is not negligible against the 0.03 rad phase-noise target for
absolute phases, which is why an exact propagator is preferred (05 §4.3.9)."
Also fix SM08 and the same claim in `model_assumptions.md` A1 ("below 0.04 rad over the 198 A cell").

### B2. README points at five files that do not exist in the repository

*File:* `README.md`, "Read in this order" table and §"Reproducing the numbers".

Quoted: "| `docs/00_executive_summary.md` | Findings and decisions in two pages. |",
"| `docs/01_repository_audit.md` | ... |",
"`docs/physics_conventions.md`, `docs/model_assumptions.md`, `docs/source_map.tsv`, `docs/references.bib` |",
"`docs/agent_reports/` | The full reports of the **four** delegated audits: **A (code)**, B (literature),
C (physics derivations), D (software provenance) ...".

**What is wrong.** `ls docs/` gives only `03_physics_summary.md`, `05_final_repository_specification.md`,
`06_project_inputs_required.md`, `model_assumptions.md`, `physics_conventions.md`, `source_map.tsv`,
`agent_reports/{B,C,D}...`. `docs/00_executive_summary.md`, `docs/01_repository_audit.md`,
`docs/references.bib` and the A (code) report do not exist. They are also cited as if they existed from
inside the documents under review: 05 §1 ("The itemised audit is in `docs/01_repository_audit.md`"),
05 §6 and 05 §3 (`docs/references.bib`), and the README's own numbering (00, 01, 03, 05, 06) advertises
02 and 04 as missing as well.

A source-policy repository whose own index points at absent evidence files is the single most
embarrassing defect in the set: every claim marked "see the audit" is currently unsupported.

**Proposed fix:** either commit the four missing artefacts, or delete/mark them as "not written in this
analysis" and remove the "four delegated audits" claim (there are three), and re-point 05 §1 at
`docs/agent_reports/D_software_provenance.md` + `C_physics_derivations.md`, which do contain the audit.

### B3. `03 §3` attributes to the instruction file a table and a formula that are not in it

*File:* `docs/03_physics_summary.md` §3, paragraph after the table.

Quoted: "**The instruction-file version of the same table** using the non-relativistic `Delta = V0/T`
gives 14.00 mrad and exactly pi at (444); that form underestimates `Delta` by 16 percent and must not
be used."

**What is wrong.** `ba72277e-si110_reflection_holography_agent_instructions.txt` contains no such table,
no `Delta`, no `V0`, no `12 V`, and no rod-order angles (verified by reading the whole file and by
`grep -n -i 'delta\|V0\|12 V\|mrad'`). The provenance is the orchestrator's own task prompt to agent C
(C §3.3 calls it "the task's form"), not the instruction file. Attributing a number to a source that
does not contain it is exactly what instruction §1.2/§1.5 forbids, and here the "source" is the
instruction file itself.

**Proposed wording:** "A non-relativistic treatment (`Delta = V0/T`) would give 14.00 mrad and a step
phase of 3.140 rad (indistinguishable from pi) at (444); it underestimates `Delta` by 14 percent and
must not be used." (See M3 for the 16 percent.)

---

## MAJOR

### M1. `(nnn)` is not the specular rod of a `(1,-1,1)` surface; it should be `(n,-n,n)` throughout

*Files:* `docs/03_physics_summary.md` §3 table ("Rod order (nnn)" / rows 333-888);
`docs/05_final_repository_specification.md` §2 CFG-A ("(444), (555), (777), (888); never (666) or
(222)") and §4.1 ("`F_hkl = 0` refuses (222), (666), (10,10,10), (002), (006)").

**What is wrong.** `docs/physics_conventions.md` fixes the outward normal as `[1,-1,1]/sqrt(3)`.
The specular rod is therefore `G || [1,-1,1]`, i.e. the reflections `(n,-n,n)`, not `(n,n,n)`.
E recomputed: `ghat_(444) . n_hat = 1/3`, not 1 — (444) is a NON-specular reflection from this
surface, inclined at 70.5 degrees to the rod, and it is not the reflection whose angles the
03 §3 table gives. The correct labels are (3,-3,3), (4,-4,4), (5,-5,5), (6,-6,6), (7,-7,7),
(8,-8,8). The numbers in the table are right (the d-spacings and structure factors are identical
because `|F|` depends only on the parity of `h,k,l` and on `h+k+l mod 4`, both invariant under
`k -> -k`), but the Miller indices are wrong for the stated surface.

The documents already know this: `03 §5` and `model_assumptions` A2 both write
"the Laue-transmitted `(n,-n,n)` beam", and the C report's table is headed
"(nnn)/(n,-n,n) rod". Only the two specification tables were left in the wrong notation — which
is precisely where an implementer will copy `target_hkl = (4,4,4)` from.

**Proposed fix.** Write the rod orders as `(n,-n,n)` in the 03 §3 table header and in CFG-A, with
one sentence: "`(n,-n,n)` and `(n,n,n)` have identical `d` and `|F|`; only `(n,-n,n)` is specular
for this surface." In 05 §4.1 list the forbidden specular orders as (2,-2,2), (6,-6,6),
(10,-10,10) alongside (002)/(006) for CFG-B.

### M2. "critical angle for total external reflection" is the wrong phenomenon for electrons

*File:* `docs/03_physics_summary.md` §3, formula box: "`theta_c = 8.356 mrad (critical angle for
total external reflection)`". (Same wording in `C_physics_derivations.md` §3.6 and in the
calculator's INACCESSIBLE message, so it propagates.)

**What is wrong.** Silicon's mean inner potential is POSITIVE, so the electron is accelerated on
entry and the refractive index is `n = k_int/k > 1`. Total external reflection is the `n < 1`
phenomenon (X-rays); for electrons it does not exist. From `sin^2(theta_int) = (sin^2(theta_ext)
+ Delta)/(1+Delta)` every externally incident beam has a real `theta_int >= theta_c` and always
enters the crystal. `theta_c` here is the INTERNAL critical angle for escape: a beam inside the
crystal with `theta_int < theta_c` is totally INTERNALLY reflected and never reaches the vacuum.
That is exactly how the document itself uses it (the accessibility rule is about the Bragg-reflected
beam getting OUT).

**Proposed wording:** "`theta_c = 8.356 mrad`: the internal glancing angle below which a beam
inside the crystal cannot escape into vacuum (total internal reflection at the surface barrier).
Because `V0 > 0` the refractive index exceeds 1 and there is no total EXTERNAL reflection for
electrons; every externally incident beam enters, with `theta_int >= theta_c`."

### M3. "Refraction is the entire signal" is an overstatement, and it contradicts the report's own §4.4 and its only accessible description of the experiment

*Files:* `docs/03_physics_summary.md` §2 last bullet ("refraction is the entire signal") and §3
("The entire holographic step signal at a specular Bragg condition is a refraction effect" in C);
`docs/model_assumptions.md` A4 ("At the vacuum Bragg angle a single-bilayer step is invisible
(2 pi n); refraction is the entire signal").

**What is wrong.** The statement is true only under four simultaneous conditions: (i) the beam is
set exactly at a BULK Bragg point of the specular rod, (ii) the step vector `R` is a bulk lattice
translation, (iii) the terraces are identical so the dynamical phase `arg A` cancels, and (iv) the
reflection is specular so `q_par . R_par = 0`. Remove (i) and the claim collapses: at any other
glancing angle `Delta_phi = -2 h k sin(theta_ext)` is a perfectly ordinary geometric path-difference
phase that is nonzero whether or not refraction exists. C §4.4 says this explicitly ("off the
Bragg peak the phase still follows `-q.R` with the *actual* in/out wavevectors"), and B's only
accessible description of Osakabe's own method (P08 abstract) describes exactly that:
"geometrical path differences produced by the surface topography are measured in units of
wavelengths". Real REM is normally operated at a surface-resonance or CTR condition, not at a
bulk Bragg point, and the (00) rod carries truncation-rod intensity at all angles.

There is also a quantitative trap the sentence hides: at a genuine Bragg-case reflection there is
a total-reflection (Darwin) plateau of finite angular width, and `dDelta_phi/dtheta = 1.571
rad/mrad` for `h = d_111` (E recomputed). Any angular acceptance - plateau width, illumination
convergence, or a rocking step - integrates the phase over that range (see M7).

**Proposed wording:** "At an exact bulk-Bragg condition of the specular rod the vacuum momentum
transfer would be `G` and a lattice-translation step would be invisible; the measured phase there
is entirely the refractive departure of the vacuum momentum transfer from `G`. Away from a bulk
Bragg point (a truncation-rod or resonance condition, which is how REM is usually operated) the
step phase is the ordinary geometric path difference `-2 h k sin(theta_ext)` and is not a
refraction effect. Both regimes must be supported by the model; the operating point decides."

### M4. Acceptance criteria 2 and 3 are not testable, and AC3 contradicts `model_assumptions` §3

*File:* `docs/05_final_repository_specification.md` §0.

Quoted AC2: "...and a flat-surface rocking-curve benchmark against an independent dynamical
reflection solver, **within stated tolerances**." No tolerance is stated anywhere, and §4.4 admits
"Which quantities the chosen solver exposes must be verified from its documentation (UNVERIFIED
here: only its README was readable)" - the benchmark may not expose a phase at all, in which case
the criterion cannot be met as written.

Quoted AC3: "The Osakabe-type benchmark (**monatomic steps on Si(111)**, phase step versus glancing
angle) is reproduced with the refraction-corrected geometric phase plus a quantified dynamical
residual."

**What is wrong with AC3.** The surface, energy and reflection of Osakabe 1988 are unknown to this
analysis. `model_assumptions.md` §3 says so in as many words ("its surface, energy, reflection,
reference-wave arrangement, equation and measured values are unknown to this analysis"), and 05's
own §2 records CFG-O as "UNVERIFIED (P01 not readable here)". AC3 nevertheless asserts Si(111) and
monatomic steps as fact, and "a quantified dynamical residual" has no threshold. An acceptance
criterion that cannot be evaluated is not an acceptance criterion.

**Proposed wording:** AC2 - "...within tolerances recorded in `configs/benchmarks.yaml` (to be set
when the solver is chosen); if the solver exposes only intensities, the criterion is restricted to
peak positions and widths and that restriction is recorded." AC3 - "A monatomic-step benchmark on
the configuration Ali specifies (CFG-A or CFG-B) reproduces the refraction-corrected geometric
phase versus glancing angle with a dynamical residual below <X> rad. Comparison with Osakabe 1988
is deferred until P01 is read; its surface and conditions are currently UNVERIFIED."

### M5. `source_map.tsv` SM07 attributes the 1/40-1/70 foreshortening statement to P23; the B report says its provenance is unresolved

*File:* `docs/source_map.tsv`, SM07, source column: "P23 (Yagi 1987 review, index-level 1/40-1/70
statement)".

**What is wrong.** `B_literature.md` §9.6 introduces that sentence as: "Source level
(`+ABSTRACT(index)`, **provenance of the exact sentence unresolved**)". B's P23 entry records only
"UHV-REM characterises monolayer-level surface structure: steps, reconstructed domains and their
boundaries, and dynamic processes"; it does not contain 1/40-1/70. Attaching the quantitative
statement to a specific paper that the report declines to identify as its source is exactly the
misattribution mode instruction §1.2/§1.6 exists to prevent, and it is the only such case I found
in the source map.

**Proposed fix:** source column -> "none (the 1/40-1/70 range appeared in a search summary whose
source sentence B could not resolve; recorded as context only, not as evidence)". Keep the
evidence level `DERIVED_HERE`; the derivation and the numbers are the report's own
(E recomputed: `1/sin(theta_ext)` = 116, 73, 55, 44, 37, 32 for orders 3-8, which brackets
1/40-1/70 between orders 4 and 6).

### M6. Geometric shadowing at grazing incidence is absent from the specification, and it dominates CFG-B

*Files:* `docs/03_physics_summary.md` §4 bullet 2 and §6; `docs/05_final_repository_specification.md`
§4.5, §5.2, §7.4. The word "shadow" does not occur in any document under review.

**What is wrong.** At a glancing angle `theta` an up-step of height `h` casts a geometric shadow of
length `h/tan(theta)` along the beam, within which there is no reflected object wave at all.
E recomputed at `theta_ext = 22.495 mrad`: a single `d_111` bilayer shadows **139 A**; a 1.36 A
Si(001) layer shadows 60 A; **a 10 nm patterned mesa - exactly CFG-B, "Ali's experiment" - shadows
4445 A = 444 nm of surface.** 03 §4 says "the hologram measures the shape of terraces, not the
riser height", but does not say that several hundred nanometres of the terrace behind each riser
carry no signal, that the shadowed strip is 44x wider in the image than the riser itself, or that
the shadow direction fixes the sign of the step in the image. C §2.1 has the mechanism (and notes
the repository's benchmark avoids it by running the step edges parallel to the beam); it never
reached 03 or 05.

**Proposed fix.** Add to 03 §4 and to 05 §4.5/§5.2: "Steps transverse to the beam shadow the
surface behind them over `h/tan(theta)` (139 A per bilayer, 444 nm for a 10 nm mesa at 22.5 mrad).
Within the shadow there is no object wave and the reconstructed phase is meaningless; the shadow
length and its direction (which distinguishes an up-step from a down-step in the image) must be
computed for every configuration and masked before quantification. The geometric-phase model must
raytrace visibility, not only `-q.R`." Add a test: "shadowed-region mask matches `h/tan(theta)`".

### M7. Illumination convergence is treated as a non-blocking input, but it is a first-order contrast killer for the intended nm-scale features

*Files:* `docs/06_project_inputs_required.md` item 3 (not marked blocking);
`docs/05_final_repository_specification.md` §5.4 (partial coherence listed with no numbers);
`docs/03_physics_summary.md` §4 (gives the tilt-step requirement but not the divergence requirement).

**What is wrong.** The same derivative that sets the rocking-series tilt step,
`d(Delta_phi)/d(theta) = (4 pi h/lambda) cos(theta)`, also converts the illumination convergence
semi-angle into an irreducible phase spread across the incoherent illumination ensemble. A tilt
step can always be made finer; a convergence angle cannot. E recomputed at 200 keV:

| h | `dDelta_phi/dtheta` | convergence semi-angle giving 1 rad of phase spread |
|---|---|---|
| `d_111` = 3.14 A | 1.571 rad/mrad | 0.64 mrad |
| 1 nm | 5.011 rad/mrad | 0.20 mrad |
| 10 nm | 50.11 rad/mrad | **0.020 mrad** |

So the 10 nm patterned features that motivate the project need an illumination divergence below
about 0.02 mrad before the fringe contrast survives at all - a far harder requirement than the
0.06 mrad tilt STEP quoted in 03 §4, and one that is set by the source, not by the operator.
By contrast the energy spread is harmless: `dln(lambda)/dE = -2.909e-6/eV`, so a 0.7 eV FEG spread
gives 7e-5 rad at `h = d_111` and 2.3e-3 rad at `h = 10 nm` (E recomputed) - worth saying, because
it removes a suspicion cheaply.

**Proposed fix.** Mark 06 item 3 "(blocking)" and add the table above to 03 §4 and to the
uncertainty budget in 05 §7.6, with the explicit statement that the convergence limit, not the
phase noise, is what decides whether a 10 nm feature is measurable.

### M8. The phase-precision-to-height conversion in 03 §4 is the (666) number, quoted as the (444) number

*File:* `docs/03_physics_summary.md` §4, first bullet: "with fringe contrast 0.5 and 1e4 counts in
the aperture area, `sigma_phi = 0.03 rad`, i.e. **0.003 A at (444)**."

**E recomputed.** `sigma_phi = sqrt(2)/(0.5*sqrt(1e4)) = 0.02828 rad`. `sigma_h = h_2pi
sigma_phi/(2 pi)`. At (444) `h_2pi = 0.9193 A` -> `sigma_h = 0.00414 A`. The quoted 0.003 A is the
(666) value (`h_2pi = 0.5575 A` -> 0.00251 A), which is where C §7.4 computes it. (666) is
forbidden and the same document forbids its use.

**Proposed wording:** "...`sigma_phi = 0.028 rad`, i.e. 0.004 A at (444) (`h_2pi = 0.919 A`)."

### M9. The quantification formula in 05 §5.7 drops the sign that `physics_conventions.md` says must never be dropped

*Files:* `docs/05_final_repository_specification.md` §5 item 7 versus `docs/physics_conventions.md`
"Step phase" row.

Conventions: "`Delta_phi = ... = -(k_out - k_in).R` ... For the specular beam this is
`Delta_phi = -(4 pi/lambda) h sin(theta_ext)`; **the sign is reported with the convention, never
dropped**."
Spec §5.7: "`h = Delta_phi lambda/(2 pi (sin theta_in,ext + sin theta_out,ext))`" - no minus sign,
so an up-step (`Delta_phi < 0` in the declared convention) returns a negative height. 03 §3 has the
same problem: "the vacuum step phase for `h = m d` is `Delta_phi = 2 pi m n sin(theta_ext)/
sin(theta_int)`" is written positive and unsigned, and 03 §2 uses `|Delta_phi|` in the
specular bullet but an unsigned sum in the general bullet
("`|Delta_phi| = (2 pi/lambda) h (sin theta_in + sin theta_out) + (in-plane part) ...`" - an
absolute value cannot equal a signed sum).

**Proposed fix:** 05 §5.7 -> "`h = -Delta_phi lambda/(2 pi (sin theta_in,ext + sin theta_out,ext))`
in the `exp(+ik.r)` convention of `physics_conventions.md`; the sign test (a down-step must reverse
the sign) is a required unit test." 03 §3 -> "`|Delta_phi| = 2 pi m n rho`". 03 §2 -> put the whole
right-hand side inside the modulus.

### M10. Model elements missing from the specification that the experiment will certainly contain

*File:* `docs/05_final_repository_specification.md` §5 (optics/hologram/reconstruction) and §11.

None of the following appears anywhere in the documents under review (verified by grep over all
eight files):

1. **Specimen charging.** Ion-milled, air-exposed Si with a native oxide, illuminated at grazing
   incidence over a footprint of order `L/sin(theta)` (tens of microns), is a classic charging
   geometry. A charging patch adds an unknown, drifting phase that is indistinguishable from
   topography. It deserves at minimum a PROJECT_INPUT item and an explicit ASSUMPTION row
   ("surfaces are conductive enough that charging is negligible") with a test (phase drift versus
   dose/time).
2. **Biprism Fresnel fringes and wire artefacts.** 05 §10 cites Tanigaki 2014 for holography
   "without Fresnel fringes" but §5 never lists the biprism's own diffraction fringes, wire
   charging, vignetting or the finite overlap width as things the hologram model must contain.
   They modulate contrast and phase across the exact field of view being measured.
3. **Drift.** 06 item 6 asks the lab for "drift during exposure" but 05 §5.5 (detector) models only
   MTF, gain and Poisson noise. Drift during a long grazing-incidence exposure is a coherent
   envelope loss, not shot noise, and must be in the forward model if it is to be fitted.

Everything else the brief asked me to look for IS present and correctly placed: absorptive/inelastic
treatment (B6, §4.3.7, item 21), surface reconstruction (B3, §4.2), oxide/damage layer (B7, item 12,
§4.2), detector MTF/dose (§5.5, item 6), foreshortened sampling anisotropy (§5.2).

### M11. Nothing in the validation chain independently tests the reflection PHASE - the measurand

*File:* `docs/05_final_repository_specification.md` §0.2, §4.3 ("Engine plan"), §4.4, §4.5, §8.

The chain as specified is: custom numpy/cupy kernel = reference engine, "benchmarked in a
**transmission** configuration against abTEM 1.1 and Prismatic, then used in reflection"; abTEM as
cross-check; `sim-trhepd-rheed` (or a Bragg-case Bloch-wave solver) as the flat-surface benchmark,
supplying "rocking curves `|A(theta)|^2` and, **where the code exposes it**, the reflection phase"
(§4.4), with §11 conceding "Which quantities `sim-trhepd-rheed` exposes (phase of the reflected
beams or intensities only)" is unsettled.

**What is wrong.** Instruction §9.3 says in terms that "a transmission-only benchmark does not settle
reflection validity", and instruction §10 that "a synthetic inversion using exactly the same model
... is not an independent test of physical accuracy". As written:

* the only cross-engine benchmark of the custom kernel is in transmission;
* the only reflection benchmark is a rocking-curve INTENSITY comparison (AC2), which constrains
  `|A|`, not `arg A`;
* the geometric-phase model (§4.5) and the expected multislice phase come from the same
  translation-covariance identity, so agreement between them is a consistency check, not a test;
* consequently **the quantity the whole project measures - the phase - has no independent
  validation anywhere in the acceptance criteria.**

**Proposed fix.** Add an explicit phase-validation ladder to §4.3/§8, all of which are available
without reading anything new:
1. *Refraction-only analytic limit.* A structureless slab whose potential is the constant `V0`
   reflects with an analytically known amplitude and phase (a 1-D step barrier in the
   surface-normal momentum). Since the documents argue the step signal IS the refraction
   (finding M3), this tests exactly the disputed part, and it separates the propagator and the
   boundary treatment from the lattice.
2. *Bragg-case Bloch-wave two-beam solution* for one allowed reflection, which gives `arg A` in
   closed form across the Darwin plateau; require the multislice to reproduce the phase sweep, not
   only the plateau width.
3. *Null tests with an exact expected phase:* a step of exactly `h_2pi` must give zero phase step;
   a lattice-translation step at an exact vacuum Bragg angle must give zero (this is the document's
   own invisibility statement, and it is a strong test of the whole chain); reversing the step
   must reverse the sign.
Then rewrite AC2 to require phase agreement, with a tolerance, and say explicitly which of 1-3
supplies it if `sim-trhepd-rheed` turns out to expose intensities only.


---

## MINOR

### m1. "underestimates `Delta` by 16 percent" - the underestimate is 14 percent (three files)

`03 §3`: "that form underestimates `Delta` by 16 percent and must not be used."
`physics_conventions.md`: "The non-relativistic form `Delta = V0/T` underestimates `Delta` by 16
percent at 200 keV." `source_map.tsv` SM04: "non-relativistic V0/T form rejected (16 percent low)."

E recomputed: `Delta_rel = 6.982e-5`, `Delta_nonrel = V0/T = 6.000e-5`. The non-relativistic value
is `(6.982-6.000)/6.982 = 14.06 %` BELOW the correct one; the correct one is `16.37 %` ABOVE the
non-relativistic one. "Underestimates by 16 percent" is the wrong direction of normalisation.
C §3.1 is the origin ("E_eff is 14.1 % below T, so ... underestimates the refraction by 16.4 %").

**Proposed wording:** "`Delta = V0/T` is 14 percent too small (equivalently, the relativistic
`Delta` is 16 percent larger); do not use it."

### m2. 03 §2: "`G.R/2pi` equals exactly 1 (invisible), not 2/3" - the repository's value is 4/3

E recomputed for (2,-2,0) with `R = (a/2)[1,0,1]`: exact `G.R/2pi = 1.000000000`; the repository
formula `(4 pi/lambda) h sin(theta_B)(ghat.n_hat) = 8.377580 rad = 1.333333 x 2pi`, whose residue
mod 2pi is `2pi/3 = 2.094 rad` (a third of a turn per bilayer, giving the generator docstring's
`0, 2pi/3, 4pi/3, 2pi` staircase). The number "2/3" is not the repository's prediction under any
reading: it is 4/3 as a total, 1/3 as a fraction of a turn, or `2pi/3` as a phase.

**Proposed wording:** "...the full `G.R/2pi` is exactly 1 (invisible), while the repository formula
gives 4/3, i.e. `2 pi/3` of phase per bilayer - the origin of the `0, 2pi/3, 4pi/3, 2pi` staircase
in the generator docstring."

### m3. `model_assumptions.md` B1: the angle sensitivity quoted for (444) is the (666) value

Quoted: "`dDelta_phi/dV0` about -0.34 rad/V at the (444) condition, 200 keV; **angle shift about
-0.13 mrad/V**."

E recomputed (central difference over 11-13 V): at (444) `dtheta_ext/dV0 = -0.2133 mrad/V` and
`d|Delta_phi|/dV0 = -0.3351 rad/V`; at (666) they are -0.1294 mrad/V and -0.2032 rad/V.
The phase figure is the (444) one, the angle figure is the (666) one. C §3.7 quotes -0.13 mrad/V
correctly, but for (666).

**Proposed wording:** "...-0.34 rad/V at (444) (-0.20 rad/V at the (666) setting the repository
uses); angle shift -0.21 mrad/V at (444) (-0.13 mrad/V at (666))."

Related, in the same row and in 06 item 20: "about -0.05 A/V in height" is the phase change
re-expressed as a height at FIXED `K_ext` (E recomputed -0.0486 A/V). The systematic error in the
height INFERRED from a fixed measured phase has the opposite sign, +0.0502 A/V. State which one is
meant.

### m4. The exit-plane-to-surface mapping in 03 §6 and 05 §5.2 is internally inconsistent by `L_z`

03 §6: "a surface feature at position `z_s` along the beam appears at exit-plane height
`x = x_0 + (L_z - z_s) tan(theta)`; the surface coordinate is recovered as
`z_s = (x_0 - x)/tan(theta)`."

Inverting the first expression gives `z_s = L_z + (x_0 - x)/tan(theta)`. The two statements differ
by `L_z` (198 A / 44x = 8800 A of surface coordinate). The slope and the sign are right; only the
origin is lost. 05 §5.2 repeats the second form alone. (The same slip is in C §6.)

**Proposed wording:** "`x = x_0 - z_s tan(theta)` with `x_0` the exit-plane height of the feature at
`z_s = 0`; hence `z_s = (x_0 - x)/tan(theta)`."

### m5. `physics_conventions.md` defines `theta_c` inconsistently with the accessibility rule it states four lines later

The file gives `sin(theta_c) = sqrt(Delta/(1+Delta)) = dK/k_int` (which is the correct internal
glancing critical angle) and then states the rule as `G.n_hat >= 2 k sin(theta_c)` with the
EXTERNAL `k`. The derivation (C eq. 3.5) is `G.n_hat > 2 dK`, i.e. `2 k_int sin(theta_c)`.
E recomputed: `2 dK = 4.18680`, `2 k sin(theta_c)` with the file's definition = `4.18666`,
with C's (`dK/k`) = `4.18680` rad/A. Numerically irrelevant (3.5e-5 relative, and (2,-2,0) fails at
`G.n_hat = 2.6718` either way) but this is the file whose job is to fix definitions.

**Proposed fix:** state the rule in the form that is exact - "`G.n_hat >= 2 dK` with
`dK = k sqrt(Delta)`" - and note that `2 k sin(theta_c)` is the same quantity to 3.5e-5.

### m6. `T` in eV versus keV is never stated where `Delta` is written

`03 §3` writes `Delta = V0 (1+T/m_e c^2)/(T (1+T/2 m_e c^2))` with `T` undefined in that box, while
`physics_conventions.md` declares "Beam energy in keV" in its units table and "T the kinetic energy
in eV" in its refraction bullet. With `T` in keV and `V0` in V the expression is wrong by 1000.
Instruction §9.8 asks specifically for "electronvolts from kiloelectronvolts".

**Proposed fix:** add "(`T` in eV, `V0` in V)" to the 03 §3 box, and make the conventions units table
say "beam energy stored in keV, converted to eV in every formula containing `V0`".

### m7. 03 §5 mixes the 2/3 rule and the engine's half-Nyquist rule when judging the 0.5 A default

Quoted: "the generator's default 0.5 A pixel supports 17 mrad and cannot represent a 24 mrad tilt
(check T22). Prismatic in particular anti-aliases at half Nyquist, ceiling `lambda/(4 dx)` = 48
mrad at 0.13 A."

For the engine actually used, the ceiling at 0.5 A (achieved `dx = 0.4845 A`) is
`lambda/(4 dx) = 12.9 mrad` (D §2c, REPRODUCED), not 16.7 mrad. Quoting the 2/3 number for the
failing case and the half-Nyquist number for the working case understates by 30 percent how far
outside the band the default sits.

**Proposed wording:** "...the generator's default 0.5 A pixel supports 16.7 mrad under the 2/3 rule
and only 12.9 mrad under Prismatic's half-Nyquist rule, so it cannot represent the 24 mrad tilt
under either (check T22; D §2c reproduces the resulting `IndexError`)."

### m8. 03 §5 "`L_z tan(theta)` = 3 to 4.5 A" conflates two different lengths

C §5.2 gives `L_z,si tan(theta) = 3.111 A` (rise over the crystal, which is what the 31 percent
refers to) and `L_z tan(theta) = 4.460 A` (rise over the whole 198 A cell, which is what T19 and the
"< x_vac" assertion refer to). E recomputed both. A single symbol `L_z` cannot take both values.

**Proposed wording:** "only rays within `L_z,si tan(theta) = 3.11 A` of the surface reach it inside
the crystal (31 percent of the nominal 10 A gap, 16 percent of the true 20 A periodic channel); the
reflected beam rises 4.46 A over the full 198 A cell, which is what must stay below `x_vac`."

### m9. `source_map.tsv` SM10 and SM11 over-label the evidence

SM10 carries "SECTION_READ + REPRODUCED" across a claim bundle in which only part was reproduced.
D §7 item 3 states plainly: "the ΔZ/2 back-propagation, the half-Nyquist mask and the normalisation
have **not** been confirmed against a real output file". The 5-D schema, `complex64`, image pixel
= 2x potential pixel and descending `r_y` WERE reproduced (D command 16); the back-propagation and
the band limit are SECTION_READ of C++ only. Split the row, or label per clause.

SM11 carries "REPRODUCED" for four claims, one of which D labels `DERIVED_HERE` (fact 43, the
pixel-size factor of 2 - arithmetic on two reproduced facts, not an executed check). SM11 also
states "tilt index 0 is not the intended tilt" unconditionally, whereas D §3.4 shows it is correct
for `multislice_forward_model.py` (one tilt at 0,0) and wrong only for
`multislice_tilt_series_runner.py`.

### m10. SM06's locator points at the wrong section of C

SM06 gives "C section 3.5" for the accessibility rule. The rule is **equation (3.5) in C §3.3**;
C §3.5 is Table A (the rod table). Equation numbers and section numbers collide throughout C
(3.4, 3.5, 3.6 all exist as both); the source map should give "C §3.3, eq. (3.5)".

### m11. 05 §10 puts search-summariser text in quotation marks

"Osakabe 1992 review (P08, "phase shift of a Bragg-reflected electron wave", "geometrical path
differences measured in units of wavelengths")". B §1.4 obtained these "near-verbatim ... by three
queries" from a machine summariser, not from the paper. Instruction §1.2 forbids inventing a
quotation and §1.5 forbids using a summariser as evidence. The section header does say "index-level
evidence only", but quotation marks assert verbatim text from P08.

**Proposed wording:** "...P08, reported at abstract-index level as measuring the 'phase shift of a
Bragg-reflected electron wave' through 'geometrical path differences ... measured in units of
wavelengths' (`+ABSTRACT(index)`; the paper was not read)."

### m12. The oxide path length is a single pass; the measurement is a round trip

06 item 12 and `model_assumptions` B7: "At 20 mrad glancing incidence a 1 nm amorphous overlayer is
traversed over about 50 nm of path". E recomputed `1/sin(20 mrad) = 50.0 nm` - correct for one pass,
but the reflected beam crosses the same layer again, so the attenuating path is about **100 nm**.
Since the point of the sentence is that the overlayer "can suppress the Bragg-reflected object wave
entirely", the factor 2 belongs in it.

### m13. 05 §9 milestone M5 omits the two PROJECT_INPUT items its own protocol needs

M5 "depends on M4 and PROJECT_INPUT items 1 to 19", but 05 §7.1 calibrates `V0` (item 20) and §4.3.7
requires the absorptive potential parameters (item 21). Change to "items 1 to 21".

### m14. Prismatic is called both "1.2.0" and "2.x" for the same tree

`model_assumptions` §3 ("Prismatic 1.2.0 tree at commit d155fb9") versus SM10's validity regime
("Prismatic 2.x"). Both come from D §1.4, which records `setup.py: version="1.2.0"` on a tree whose
HRTEM mode exists only in the 2.x generation. Say it once: "Prismatic, `prism-em/prismatic` @
d155fb9 (2026-01-30), `setup.py` version 1.2.0, HRTEM-capable 2.x generation".

### m15. Smaller numerical looseness

* 03 §3 "the non-relativistic form ... gives 14.00 mrad and **exactly pi** at (444)". E recomputed:
  `theta_ext = 13.997 mrad`, phase mod 2pi = **3.1403 rad**, i.e. pi - 0.0013. Write "indistinguishable
  from pi (3.140 rad)".
* 03 §6 "a vacuum reference ... is inclined by `2 theta` (**25 to 60 mrad**)". E recomputed
  `2 theta_ext` = 17.2 / 27.3 / 36.3 / 45.0 / 53.4 / 61.8 mrad for orders 3-8. Write "17 to 62 mrad
  over orders 3 to 8 (27 to 62 mrad over the allowed orders 4 to 8)".
* 03 §3 "(Values: ... checks **T4 to T14**)". T4-T14 cover only the (666)/(444)/(555)/(888) phases
  and `h_2pi`; the (333) and (777) rows, the `theta_int` column and the foreshortening column (T20)
  are not in that range. Write "checks T4-T14 and T20; the (333) and (777) rows are tabulated but
  not asserted".
* 03 §4 "(check T23)" is appended to a sentence carrying two numbers; only the `h = 1 nm` value
  (0.6270 mrad) is T23. The 0.06 mrad figure is `h = 10 nm` and is unasserted.
* 05 §8 never assigns T10-T14, T16 or T21-T23 to any bullet, though §9 M1 promises "tests T1 to T23".
* Author spellings: 05 §10 writes "Hytch" and "Meissner"; the publisher forms in B are **Hÿtch** and
  **Meißner**. The instruction file is explicit about preserving publisher bibliographic forms.

### m16. In the supporting material (will be committed): C §2.1's 131 A is the wrong angle and is not produced by the calculator

C §2.1: "the step's projected width in the image is `h/tan(theta)` = **131 A** at `h = d_111`,
`theta = 22.5 mrad`". E recomputed: `3.1355/tan(22.495 mrad) = 139.4 A`; 130.6 A is the value at the
repository's 23.997 mrad. The number also does not appear in `C_calculator_output.txt`, which
contradicts C's own header claim that "Every number in every table below is produced by that script".

### m17. 05's own quantitative claims carry no evidence label and no source-map row, which breaks its acceptance criterion 4

05 §0.4 requires that "Every physical claim, material parameter and algorithm has a
`docs/source_map.tsv` record with an evidence label". 05 §4.3 then states, unlabelled and
unrecorded: the 890 A footprint minimum, the 0.1-0.4 um dynamical build-up length, "grids of order
1500 x 600 pixels and thousands of 1 A slices", and the 64 mrad / 48 mrad sampling ceilings. The
source map has rows for the wavelength, structure factor, step phase, refraction, wrap period,
accessibility, foreshortening, propagator, repository footprint, Prismatic semantics, hologram and
ensembles - but **no row for the 2/3 anti-aliasing rule or for the required-cell geometry**, even
though T21/T22 assert the first and T17-T19 the second. Add SM15 (sampling/anti-aliasing, T21-T22)
and SM16 (reflection-cell geometry requirements, DERIVED_HERE, no test yet), and label 05 §4.3's
numbers.

### m18. "about 200 lines" understates the custom kernel, whose hardest part is the potential

05 §4.3, Engine plan: "a small custom numpy/cupy multislice as the reference implementation (about
200 lines; explicit absorber, band limit, tilt and output plane)". The 200 lines cover the
propagation loop. They do not cover the projected atomic potential - the Kirkland/Peng-type
parameterisation, its Fourier-space construction, sub-slice `z` sampling, and the resulting mean
inner potential, which §4.3 item 6 itself requires to be "reported and compared with the sourced
`V0`". That parameterisation is a sourced physical input (instruction §1.1/§1.3), not boilerplate,
and it is the part D §5.4 names as what a custom kernel "costs". Say so, and give it its own
source-map row and test (mean inner potential of the implemented parameterisation versus the
sourced `V0`).

### m19. The GPL/MIT licence question raised by report D never reaches the provenance requirements

D §1.5 records that Prismatic is GPL and `prismatique` GPLv3 while the inspected repository is MIT,
and says "it belongs in the provenance record". 05 §6 (Provenance requirements) lists versions,
commits, seeds, precision, hashes - but no licence field, and §4.4 adds a second GPL dependency
(`sim-trhepd-rheed`, GPL Fortran). Add "licence of every engine invoked" to the run manifest and a
one-line statement of the distribution decision.


---

## NIT

* `README.md` "the full reports of the **four** delegated audits: A (code), B, C, D" - three reports
  exist; there is no A. (Same defect as B2, recorded here because the word "four" also has to change.)
* `C_physics_derivations.md` header names its companion script `reports/reflection_step_phase_
  calculator.py`; in this repository it is `tools/reflection_step_phase_calculator.py`.
* "Dark-field" is never defined for reflection geometry. In transmission DFEH it means "not the
  direct beam"; in reflection there is no transmitted beam in the image, so 03 §1.3's "this is the
  dark-field object wave" should say what it is dark relative to (one selected reflected rod out of
  the RHEED pattern).
* `tools/provenance_checks/*.py` do `sys.path.insert(0, _HERE)`, so a stub renamed to
  `pyprismatic.py` in that directory would shadow a real installed `pyprismatic` for anything run
  from there. The README warns in prose; a two-line guard (`import importlib.util; assert
  importlib.util.find_spec("pyprismatic") is None`) would make it structural.
* `model_assumptions` B6 and 05 §4.3.7 say "instruction file B15 warning"; B15 is a bibliography
  entry, not an instruction section. Write "the warning attached to [B15] in the instruction file".
* 05 §4.3 item 4 "of order 0.1 to 0.4 um" and 03 §5 "of order 0.2 um" for the same quantity; make
  them the same sentence or state the angle each assumes.

---

## ARCHITECTURE VERDICT (asked for explicitly)

**Sound, with one structural hole.** The ranking of engines is justified by evidence rather than
taste: D verified from source that Prismatic has no absorbing boundary and no `absorbing_layers`
API, that it anti-aliases at half Nyquist, that it back-propagates the saved wave by `ΔZ/2`, that
its "tilt window" simulates every grid tilt inside the window, and that upstream is unmaintained -
so demoting it to a documented legacy benchmark is right. abTEM as the packaged cross-check is the
right choice for the same verified reasons (exact propagator with evanescent handling, 2/3 band,
explicit exit wave, `ensemble_mean` switch). Writing a custom kernel for the absorbing boundary is
justified because D checked and found that *no* packaged code exposes one, and the boundary
condition is the verified obstacle.

Three reservations:

1. **The reference engine is the least-scrutinised code in the stack.** Calling a bespoke ~200-line
   kernel "the reference implementation" and a widely used package "the cross-check" inverts the
   usual reliability ordering. Require agreement with abTEM to a stated tolerance in *both* a
   transmission configuration and a reflection-like configuration abTEM can still run (thick enough
   that the absorber is inert), before the absorber is enabled; and see m18 on the potential.
2. **The phase has no independent benchmark** (M11). This is the one that would actually invalidate
   the project's conclusions.
3. **abTEM's tilt range is a real risk, correctly flagged but not planned for.** D read
   `abtem/waves.py:2351`: "should generally not exceed one degree" (~17 mrad) for a
   propagator-shear tilt, against the 24-48 mrad needed here. 05 §11 lists this as unsettled but no
   milestone tests it. Add a convergence test comparing the shear tilt against an entrance-plane
   Fourier-component tilt at 24 and 48 mrad; if abTEM fails it, the "preferred packaged cross-check"
   has to change, and that affects M2/M4 in the migration plan.

---

## VERIFIED CORRECT - DO NOT TOUCH

Independently recomputed and confirmed (my script, separate constants and formulas):

1. `lambda(200 keV) = 0.02507934 A`, `k = 250.5323 rad/A`; 100 keV 0.03701437 A; 300 keV 0.01968749 A.
2. `Delta = V0(1+T/mc^2)/(T(1+T/2mc^2)) = 6.98200e-5` at 200 keV, `V0 = 12 V`; identical to the exact
   `V0(2T+V0+2mc^2)/(T(T+2mc^2)) = 6.98206e-5` to 8e-6 relative. `Delta = 2 gamma m e V0/(hbar^2 k^2)`
   is also exact - 03 §3's alternative form is right.
3. `sin^2(theta_int) = (sin^2(theta_ext)+Delta)/(1+Delta)` follows exactly from `k cos(theta_ext) =
   k_int cos(theta_int)`. `theta_c = 8.356 mrad` (8.3559 as `dK/k`, 8.3556 as `dK/k_int`).
4. The whole 03 §3 table, to every printed digit: `theta_int` 12.00 / 16.00 / 20.00 / 24.00 / 28.00 /
   32.00 mrad; `theta_ext` 8.61 / 13.64 / 18.17 / 22.50 / 26.72 / 30.89 mrad; step phase mod 2pi
   0.96 / 2.58 / 3.41 / 3.92 / 4.28 / 4.54 rad; `h_2pi` 1.456 / 0.919 / 0.690 / 0.557 / 0.469 /
   0.406 A; foreshortening 116 / 73 / 55 / 44 / 37 / 32. (666) forbidden, `F = 0`.
5. Diamond selection rule and every forbidden/allowed call in the documents: (222), (666),
   (10,10,10), (002), (006) forbidden; (004), (008), (0,0,12), (2,-2,0) allowed.
6. Translation covariance `Delta_phi = -(k_out-k_in).R`, its specular reduction
   `(4 pi/lambda) h sin(theta_ext)`, and the equivalence `q.n_hat = G.n_hat = (4 pi/lambda)
   sin(theta_B)(ghat.n_hat)` at the vacuum Bragg condition.
7. `R = (a/2)[1,0,1]` is an fcc lattice vector; `R.n_hat = d_111 = 3.135532 A` exactly for
   `n_hat = [1,-1,1]/sqrt(3)`; `|R_par| = a/sqrt(6) = 2.2172 A`, which is **not** a surface-net vector
   (the shortest (111) net vectors are 3.8402 A; `3 R_par` = 6.6515 A **is** one). The claim that the
   two terraces are exact translates is correct.
8. The Si(001) `a/4` step: no fcc vector has `R.z = a/4`; a brute-force search reproduces exactly the
   four `4_1` screw operations `Rz(+-90) + a[1/4,1/4,1/4]` and `a[3/4,3/4,1/4]`. Correct.
9. Accessibility: `G.n_hat(2,-2,0) = 2.6718 rad/A` vs `2 dK = 4.1868 rad/A` -> inaccessible;
   `ghat.n_hat = 0.81650 = 2/sqrt(6)`. Exact `G.R/2pi = 1.000000000` for a `d_111` step.
10. Footprint, to the digit: `L_z,si tan(theta) = 3.111 A` = 31.10 % of 10 A, 15.55 % of 20 A;
    end-face fraction 80.89 %; useful surface reflection 2.97 % of the whole wave;
    `x_vac/tan(theta) = 444.5 A`; `H/tan(theta) = 888.9 A` for `H = 20 A`. Cell dimensions
    `L_x = 104.659`, `L_y = 79.818`, `L_z = 198.248 A` from the stated generator defaults.
11. Sampling: 2/3 rule gives 64.31 mrad at 0.13 A and 16.72 mrad at 0.5 A; Prismatic's
    `lambda/(4 dx)` gives 48.2 mrad at 0.13 A. All correct, as is the `IndexError` causal claim in
    `tools/provenance_checks/README.md` (the tilt grid step `lambda/L_x = 0.2396 mrad` is independent
    of pixel size, so only the anti-aliasing ceiling can explain the failure at 0.5 A and the success
    at 0.13 A).
12. `sigma_phi = sqrt(2)/(mu sqrt(N))`: derivation and value 0.0283 rad at `mu = 0.5`, `N = 1e4`.
13. Carrier condition `q_c > 3B` and "resolution about three fringe spacings"; sideband/centre-band
    bandwidth bookkeeping is right.
14. Rocking series: `d|Delta_phi|/dtheta = (4 pi h/lambda) cos(theta)`; 0.627 mrad for `h = 1 nm`,
    0.0627 mrad for `h = 10 nm`; 3.41 wraps for a bilayer at (444); 109 wraps for 10 nm.
15. `dDelta_phi/dV0 = -0.335 rad/V` at (444) (-> "-0.34" is right).
16. `tools/reflection_step_phase_calculator.py` runs clean and prints 25/25 PASS, and its output is
    **byte-identical** to `docs/agent_reports/C_calculator_output.txt`. The README's reproduction
    recipe works.
17. Crystallographic frame in `physics_conventions.md`: `x_hat, y_hat, z_hat` are orthonormal and
    right-handed (`x_hat x y_hat = z_hat` exactly), and the criticism of the inspected repository's
    "(1,1,-1) facet" (`[1,1,-1].[1,1,0] = 2 != 0`) is correct.
18. Generator defaults quoted in the documents match the cloned repository exactly (`n_x_si=9`,
    `n_y=12`, `n_z_si=36`, `x_vac=10`, `z_vac=30`, `a=5.4309`, target `(2,-2,0)`, advisory pixel 0.5 A,
    tilt sweep 0-11 mrad step 0.15, terraces `0,1,2,3` bilayers), including the docstring's
    `0, 2pi/3, 4pi/3, 6pi/3` staircase claim.
19. Every software semantics claim carried into 03/05/model_assumptions/source_map is supported by
    `D_software_provenance.md` at the locator given: mid-plane `ΔZ/2` back-propagation, half-Nyquist
    rectangular anti-aliasing, tilt quantised to the FFT grid, 5-D `(cfg, defocus, tilt, r_y, r_x)`
    `complex64` dataset, image pixel = 2 x potential pixel, descending `r_y`, `absorbing_layers`
    TypeError silently swallowed, thermal effects inert, NaN intensity file, 1309 tilts for a
    74-point sweep, upstream unmaintained since January 2026.
20. Every literature ID cited in 05 §10 (P01-P03, P08, P09, P17-P21, P23, P26, P30-P33, P36,
    P42-P44) exists in `B_literature.md` with the content ascribed to it, and no DOI, page range or
    year appears in the documents under review that is not in the instruction file or in B. The
    evidence labelling in B and in `model_assumptions` §3 (Osakabe 1988 content UNVERIFIED) is
    honest; only 05 §0.3 (finding M4) and SM07 (finding M5) break it.
