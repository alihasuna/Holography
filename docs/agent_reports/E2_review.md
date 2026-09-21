# E2. Second-pass adversarial review

Reviewer: agent E2, 2026-09-21. Working to
`ba72277e-si110_reflection_holography_agent_instructions.txt` sections 1, 9, 10.

**Part A** verifies every finding of the first review (`docs/agent_reports/E_review.md`)
against the revised files. **Part B** reviews the four documents the first review never saw:
`docs/00_executive_summary.md`, `docs/01_repository_audit.md`,
`docs/02_literature_position.md`, `docs/04_software_provenance_summary.md`.

Independent verification: all physics numbers were recomputed from scratch in numpy
(`scratchpad/e2_check.py`, `e2_nonrel.py`) without reading the calculator's implementation;
`tools/reflection_step_phase_calculator.py` was re-executed (25/25 PASS, output still
**byte-identical** to `docs/agent_reports/C_calculator_output.txt`); every number in 00, 01,
02 and 04 was traced to the locator implied, in `A_code_audit.md`, `B_literature.md`,
`B2_bib_verification_log.md`, `C_physics_derivations.md`, `D_software_provenance.md` or the
read-only clone of the inspected repository.

**Verdict: 1 Blocker, 7 Major, 12 Minor, 13 Nit.** All 42 first-review findings (3 blockers, 11 major, 19 minor, 6 nits, 3 architecture reservations) are applied or
defensibly declined; three are applied in the revised files but **re-introduced verbatim in
the new document 01**, and the new documents contain two evidence-label upgrades that the
source policy forbids.

---

## PART A. STATUS OF EVERY FIRST-REVIEW FINDING

| ID | Status | Quoted revised text (or note) |
|---|---|---|
| **B1** paraxial error | **APPLIED** | 03 §5: "The paraxial Fresnel error `k dz sin^4(alpha)/8` over the 198 A default cell is 0.002 rad at the 24 mrad tilt, 0.026 rad at the 45 mrad specular scattering angle and 0.106 rad at the 64 mrad band edge". E2 recomputed exactly (exact minus `exp(-i pi lambda dz q^2)`, L=198.248 A): **0.002060 / 0.025450 / 0.106054 rad**. SM08, `model_assumptions` A1 and 05 §4.3.9 all carry the same three numbers; 05 §8 carries "expected 0.026 rad at 45 mrad over 198 A". Consistent everywhere. (See N19 for a notation nit.) |
| **B2** README points at absent files | **APPLIED** | All five now exist: `docs/00_…`, `01_…`, `02_…`, `04_…`, `references.bib` (96 `@` entries), `agent_reports/A_code_audit.md` (1413 lines, as 01 states). README no longer says "four": "The full reports of the delegated audits: A (code), B (literature) with B2 …, C …, D …, E (adversarial review …)". 05 §1 "The itemised audit is in `docs/01_repository_audit.md`" now resolves. |
| **B3** table attributed to the instruction file | **APPLIED** | 03 §3: "A non-relativistic treatment (`Delta = V0/T`) would give 14.00 mrad and a step phase of 3.140 rad (indistinguishable from pi) at (4,-4,4)". No attribution to the instruction file survives. (See N20 for a 4th-digit nit.) |
| **M1** `(n,-n,n)` | **APPLIED** | 03 Notation: "an implementer must copy `(4,-4,4)`, not `(4,4,4)`"; table header "Rod order (n,-n,n)"; 05 §2 CFG-A "(4,-4,4), (5,-5,5), (7,-7,7), (8,-8,8); never (6,-6,6) or (2,-2,2)"; 05 §4.1 "(2,-2,2), (6,-6,6), (10,-10,10)"; `physics_conventions` "`(4,4,4)` is inclined at 70.5 degrees to the rod" (E2 confirms `arccos(1/3) = 70.53 deg`). |
| **M2** total external reflection | **APPLIED** | 03 §3: "the internal glancing angle below which a beam inside the crystal cannot escape into vacuum … Because V0 > 0 the refractive index exceeds 1 … there is no total external reflection for electrons." Same in `physics_conventions`. (Formatting nit N21.) |
| **M3** "refraction is the entire signal" | **APPLIED** | 03 §2 final bullet: "Two operating regimes must both be supported. … Away from a bulk Bragg point (a truncation-rod or surface-resonance condition, which is how REM is commonly operated, see B report P26) the step phase is the ordinary geometric path difference `-2 h k sin(theta_ext)` and is not a refraction effect." Mirrored in `model_assumptions` A4 and in 00 headline 3. |
| **M4** AC2/AC3 untestable | **APPLIED** | 05 §0.2: "If that solver exposes only intensities, the rocking-curve criterion is restricted to peak positions and widths and that restriction is recorded; the phase is then validated by rungs 1 to 3 of the ladder." AC3: "a dynamical residual below a threshold recorded in `configs/benchmarks.yaml` (proposed initial value 0.1 rad, ASSUMPTION). Comparison with Osakabe 1988 is deferred until P01 is read; its surface and conditions are currently UNVERIFIED." The Si(111) assertion is gone. |
| **M5** SM07 misattributed to P23 | **APPLIED** | SM07 source column: "none (the 1/40-1/70 range that appears in the B report came from a search summary whose source sentence could not be resolved; recorded as context only, not as evidence)". |
| **M6** shadowing absent | **APPLIED** | 03 §4: "casts a geometric shadow of length `h/tan(theta_ext)` … 139 A per Si(111) bilayer, 60 A per Si(001) layer and 444 nm for a 10 nm mesa at 22.5 mrad … the geometric-phase model must ray-trace visibility". E2 recomputed 139.4 A, 60.35 A, 444.5 nm. Also in 05 §4.5, §5.2, CFG-A, CFG-B, `model_assumptions` B9, SM07, 06 item 13, and as a test in 05 §8. (See F8 for the angle chosen.) |
| **M7** convergence not blocking | **APPLIED** | 06 item 3 now "(blocking)" with "1 rad of spread at 0.64 mrad for a 3.1 A bilayer, 0.20 mrad for a 1 nm step, 0.020 mrad for a 10 nm step". E2 recomputed 0.6365 / 0.19958 / 0.019958 mrad. Same numbers in 03 §4, 05 §5.4, `model_assumptions` B10; 05 §7.6 uncertainty budget lists "illumination convergence". **But 00 drops item 3 from its list of blocking inputs — see F2.** |
| **M8** 0.003 A is the (666) number | **APPLIED** | 03 §4: "`sigma_phi = 0.028 rad`, i.e. 0.004 A at (4,-4,4) (`h_2pi = 0.919 A`)". E2: `sqrt(2)/(0.5*100) = 0.028284`; `0.9192*0.028284/(2 pi) = 0.004138 A`. |
| **M9** dropped sign | **APPLIED** | 05 §5.8: "`h = -Delta_phi lambda/(2 pi (sin theta_in,ext + sin theta_out,ext))` … (a down-step must reverse the sign; this is a required unit test)"; `physics_conventions` carries the same inverse relation; 03 §2 general bullet is now fully signed, `Delta_phi = -[ … + 2 pi g_par . R_par ]`; 03 §3 uses `|Delta_phi| = 2 pi m n sin(theta_ext)/sin(theta_int)`. |
| **M10** charging / biprism / drift | **APPLIED** | 05 §5.5 "the biprism's own Fresnel fringes and finite overlap width; specimen drift during the exposure as a coherent envelope loss; specimen charging as an added, slowly varying phase (ASSUMPTION B8 and PROJECT_INPUT item 22)"; `model_assumptions` B8 added; 06 item 22 added; 03 §6 and 05 §3 `optics/` list them. |
| **M11** phase never validated | **APPLIED** | 05 §4.4 "the phase-validation ladder" with rungs 1 (constant-`V0` slab, analytic), 2 (two-beam Bragg-case `arg A` across the Darwin plateau), 3 (null tests); plus "Agreement between the geometric-phase model and the multislice near a step is a consistency check … not an independent validation." AC2 and 05 §8 reference it. |
| **m1** "16 percent" | **APPLIED** | 03 §3 "`V0/T` is 14 percent too small (equivalently the relativistic `Delta` is 16 percent larger)"; `physics_conventions` same; SM04 "non-relativistic V0/T form rejected (14 percent too small)". E2: 14.065 % / 16.367 %. |
| **m2** 2/3 vs 4/3 | **APPLIED** | 03 §2: "the full `G.R/2 pi` is exactly 1 (invisible), while the repository formula gives 4/3, i.e. `2 pi/3` of phase per bilayer". |
| **m3** V0 sensitivities | **APPLIED** | `model_assumptions` B1: "-0.34 rad/V at (4,-4,4) and -0.20 rad/V at the (6,-6,6) setting … -0.21 mrad/V at (4,-4,4), -0.13 mrad/V at (6,-6,6). A height inferred from a fixed measured phase is biased by about +0.05 A per volt by which `V0` is underestimated". E2 recomputed -0.3350 / -0.2031 rad/V, -0.2132 / -0.1293 mrad/V, +0.0492 A/V. 03 §3 and SM04 agree. 06 item 20 states the case but not the sign (N22). |
| **m4** exit-plane mapping off by `L_z` | **APPLIED** | 03 §6 and 05 §5.2: "`x = x_0 - z_s tan(theta)`, with `x_0` the exit-plane height of a feature at `z_s = 0`; the surface coordinate is recovered as `z_s = (x_0 - x)/tan(theta)`". Self-consistent. Same in `physics_conventions` and SM07. |
| **m5** `theta_c` definition | **APPLIED** | `physics_conventions`: "`sin(theta_c) = dK/k_int` with `dK = k sqrt(Delta)`" and "accessibility … `G.n_hat >= 2 dK` (equal to `2 k sin(theta_c)` to 3.5e-5 relative)". E2 confirms `2 k_int sin(theta_c) = 2 dK` exactly and `2 k sin(theta_c) = 2 dK/sqrt(1+Delta)`, i.e. 3.49e-5 low. |
| **m6** `T` in eV vs keV | **APPLIED** | 03 §3 "(`T` in eV, `V0` in V)"; `physics_conventions`: "Beam energy is stored in keV and converted to eV in every formula that contains `V0`". |
| **m7** 2/3 vs half-Nyquist at 0.5 A | **APPLIED, with a new slip** | 03 §5: "supports 16.7 mrad under the 2/3 rule and only 12.9 mrad under Prismatic's half-Nyquist rule". Both numbers are individually right but they use **different pixel sizes** — see F9. |
| **m8** `L_z tan(theta)` conflated | **APPLIED in 03, RE-INTRODUCED in 01** | 03 §5 now correct: "`L_z,si tan(theta) = 3.11 A` … the reflected beam rises 4.46 A over the full 198 A cell". **01 §3.3 reverts to the conflated form: "Only rays within `L_z tan(theta)` of the surface (3 to 4.5 A)" — see F6.** |
| **m9** SM10/SM11 over-labelled | **APPLIED, with a new over-label** | Split into SM10a (SECTION_READ + REPRODUCED) / SM10b ("SECTION_READ only (C++ source; NOT confirmed on an executed output file)") and SM11a / SM11b ("the factor-2 consequence is DERIVED_HERE (D fact 43)"; the tilt-index claim is now conditioned on which script). **SM11a still bundles A-C1, which A labels SECTION_READ, under REPRODUCED — see F1.** |
| **m10** SM06 locator | **APPLIED in SM06, RE-INTRODUCED in 01** | SM06: "C section 3.3, equation (3.5)". **01 §1 reverts to "(C section 3.5)", which is C's Table A — see F7.** |
| **m11** quotation marks on summariser text | **APPLIED** | 05 §10: "P08 is reported at abstract-index level as measuring the 'phase shift of a Bragg-reflected electron wave' through 'geometrical path differences … measured in units of wavelengths' (`+ABSTRACT(index)`; the paper was not read)." 00 and 02 paraphrase without quotation marks. |
| **m12** oxide round trip | **APPLIED** | `model_assumptions` B7 and 06 item 12: "crossed over about 50 nm of path on the way in and again on the way out (about 100 nm in total)". |
| **m13** M5 depends on items 1-19 | **APPLIED** | 05 §9: "M4 and PROJECT_INPUT items 1 to 22" (06 now lists 22 items; 00 and README also say 22). |
| **m14** Prismatic 1.2.0 vs 2.x | **APPLIED** | One canonical string in `model_assumptions` §3, 04 and SM10b: "`prism-em/prismatic` at commit d155fb9, 2026-01-30, `setup.py` version 1.2.0, the HRTEM-capable 2.x generation". |
| **m15a** "exactly pi" | **APPLIED** | "a step phase of 3.140 rad (indistinguishable from pi)". |
| **m15b** "25 to 60 mrad" | **APPLIED** | 03 §6: "inclined by `2 theta_ext` to the specular beam, 17 to 62 mrad over orders 3 to 8". E2: 17.22 … 61.78 mrad. |
| **m15c** "checks T4 to T14" | **APPLIED** | "checks T4 to T14 and T20; the (3,-3,3) and (7,-7,7) rows and the `theta_int` column are tabulated by the script but not asserted." |
| **m15d** "(check T23)" over two numbers | **APPLIED** | "below 0.63 mrad for `h = 1 nm` (check T23) and about 0.06 mrad for `h = 10 nm` (not asserted by a check)". |
| **m15e** unassigned test IDs in 05 §8 | **APPLIED, one mislabel** | T1-T25 are now all assigned. **T16 is filed under "accessibility (T15, T16)" but the calculator defines T16 as "exact G.R / 2pi for (2,-2,0) and a d_111 step (integer!)" — an invisibility test, as SM03 correctly records. See F13.** |
| **m15f** author spellings | **APPLIED** | 05 §10 and 02 both write "Hÿtch" and "Meißner". (02 introduces "Jorgensen" for Jørgensen — N23.) |
| **m16** C's 131 A | **APPLIED (declared, report left unedited)** | `model_assumptions` §3: "Two numerical slips in the C report were found by the adversarial review and are corrected in the summary documents, not in the report itself: the paraxial-error values in C section 5.1 (three times too small) and the 131 A step projection width in C section 2.1 (139 A at 22.5 mrad)." README repeats this. Defensible. |
| **m17** unlabelled 05 §4.3 numbers | **APPLIED** | 05 §4.3 header: "Requirements independent of the engine (numbers DERIVED_HERE, source-map rows SM15 and SM16)". SM15 (sampling/anti-aliasing, T21/T22) and SM16 (reflection-cell geometry, NOT RUN) added. |
| **m18** "about 200 lines" | **APPLIED** | The phrase is gone. 05 §4.3.6: "The projected atomic potential (a Kirkland- or Peng-type parameterisation, its Fourier-space construction and sub-slice sampling) is a sourced physical input and the largest part of any custom kernel, not boilerplate", with its own row SM17 (labelled UNVERIFIED, test NOT RUN). |
| **m19** licence | **APPLIED** | 05 §6: "engine commit and build flags and licence (Prismatic and prismatique are GPL; `sim-trhepd-rheed` is GPL; the distribution licence of this repository must be decided against them)"; `provenance/` manifest writer lists "licences"; 04 has a licence row. |
| **nit** "four" audits | **APPLIED** | See B2. |
| **nit** C's `reports/…calculator.py` path | **NOT APPLIED — defensibly declined** | The agent reports are deliberately frozen ("the agent reports themselves are kept unedited as the record", README). The correct path is given everywhere in the summaries. |
| **nit** "dark-field" undefined | **APPLIED** | 03 Notation: "'Dark-field' here means that the image is formed from one selected reflected rod of the RHEED pattern, chosen by the objective aperture; no transmitted beam exists in reflection geometry". |
| **nit** `sys.path` shadowing guard | **PARTIAL — the guard does not work** | All four scripts now carry `if importlib.util.find_spec("pyprismatic") is None: sys.path.insert(0, _HERE)`. See F12: CPython already prepends the script's directory, so the stub still shadows a real engine. |
| **nit** "instruction file B15 warning" | **APPLIED** | "the warning attached to [B15] in the instruction file" (`model_assumptions` B6, 05 §4.3.7). Instruction line 293-295 does carry that warning. |
| **nit** "0.1 to 0.4 um" vs "0.2 um" | **APPLIED in 03/05, loose in 00** | 03 §5, 05 §4.3.4 and SM16 all say "0.08 to 0.42 um at `theta_int` = 24 mrad" (E2: 0.0833 / 0.4166 um). 00 says "0.1 to 0.4 um" — N24. |
| **Arch. 1** reference engine least scrutinised | **APPLIED** | 05 §4.3 Engine plan: "Because it is the least-scrutinised code in the stack, it is not trusted until it agrees with abTEM 1.1 to a stated tolerance in both a transmission configuration and a reflection-like configuration that abTEM can still run (crystal thick enough that the absorber is inert); only then is the absorber enabled." |
| **Arch. 2** phase unvalidated | **APPLIED** | See M11. |
| **Arch. 3** abTEM tilt range | **APPLIED** | "a convergence test comparing the shear tilt against an entrance-plane Fourier-component tilt at 24 and 48 mrad is part of milestone M2, and if abTEM fails it the cross-check engine changes"; listed in M2 and in 05 §8 Propagation. |


---

## PART B. NEW FINDINGS (severity-ranked)

### BLOCKER

#### F1. The executive summary, the new audit and the source map all promote SECTION_READ claims to REPRODUCED

*Files:* `docs/00_executive_summary.md` headline 4; `docs/01_repository_audit.md` §3.1 heading;
`docs/source_map.tsv` SM11a.

Quoted (00, headline 4): "the saved wave is Fresnel back-propagated to the supercell mid-plane,
not an exit wave; **the tilt runner writes no wavefunction at all** (two nonexistent keyword
arguments make it fall back to "save nothing"); … **All of this was reproduced against the
pinned prismatique 0.0.1 API and the Prismatic source, without running the engine.**"

Quoted (01): "### 3.1 Scripts that do not produce what they claim (**REPRODUCED against the
pinned API**)" — whose first bullet is A-C1, the `save_probe_complex` /
`wavefunction_z_planes` defect.

Quoted (SM11a): "… tilt runner saves no wavefunctions (invalid keywords) | … | **REPRODUCED**
(D commands 14, 17; A section 5)".

**What is wrong.** Two of the listed facts are explicitly SECTION_READ in the reports they
summarise, and the documents themselves say so elsewhere:

* **A-C1.** `A_code_audit.md` §4 C1 ends "`SECTION_READ` of the pinned source; the `TypeError`
  follows from the signature with certainty", and A §5.7 states "`multislice_forward_model.py`
  and `multislice_tilt_series_runner.py` were **NOT** executed … **C1, C2, M3 are therefore
  established from the pinned source of prismatique 0.0.1 …, not from a run.**" I verified that
  `tools/provenance_checks/check_api.py` contains no `save_probe_complex` and no
  `wavefunction_z_planes` call (it exercises `hrtem.image.Params` only with valid keywords),
  and that `D_software_provenance.md` never mentions either keyword. So neither D command 14
  nor 17 nor A §5 reproduced this behaviour; the locator in SM11a is empty.
* **The mid-plane back-propagation.** `SM10b` says "SECTION_READ only (C++ source; **NOT
  confirmed on an executed output file**)"; `04_software_provenance_summary.md` says "engine
  behaviour is SECTION_READ of the C++/CUDA source and has not been confirmed against an
  executed output file"; `model_assumptions` §3 says the same. 00 puts it in a list it then
  declares "all … reproduced".

01 also contradicts its own preamble, which defines "REPRODUCED means the behaviour was
executed or the API exercised here".

**Why it is a blocker.** Instruction §1.4 defines REPRODUCED as "a specified result was
reproduced, **with saved test evidence**", §1.4 adds "A source can be SECTION_READ without any
result being REPRODUCED", and the FINAL OPERATING RULE forbids presenting "an unrun validation
as established fact". The whole document set's defence is that its labels are exact. The first
document a reader opens (00) and the audit that 05 §1 points at (01) both break that, and the
source map records the break as a formal row. An external reader who asks "where is the saved
evidence that the runner writes nothing?" finds none.

**Proposed corrections.**
* 00: "…the tilt runner writes no wavefunction at all (two keyword arguments that do not exist
  in prismatique 0.0.1 make it fall back to 'save nothing'; SECTION_READ of the pinned
  signatures, not executed) … The absorber rejection, the 1309-tilt window and the NaN
  intensity file were reproduced against the pinned prismatique 0.0.1 API; the mid-plane
  back-propagation and the runner's silent output loss are SECTION_READ of the engine and
  wrapper source. No engine was run."
* 01 §3.1 heading: "Scripts that do not produce what they claim (evidence per bullet)", and add
  "(SECTION_READ of the pinned signatures; A §5.7 — not executed)" to the A-C1 bullet.
* SM11a: split into SM11a (absorber TypeError, thermal inert, NaN intensity — REPRODUCED,
  D commands 14/17) and a new SM11c (tilt runner saves no wavefunctions — SECTION_READ,
  `A_code_audit.md` §4 C1, `prismatique/hrtem/image.py:203-206, 427-434`; test NOT RUN).

---

### MAJOR

#### F2. 00's list of blocking laboratory inputs contradicts 06 — it drops the two that 06 marks blocking and adds two that it does not

*File:* `docs/00_executive_summary.md`, "What is needed from the laboratory".

Quoted: "`docs/06_project_inputs_required.md` lists 22 items. **The blocking ones:** accelerating
voltage, the selected reflection and objective-aperture angle, the external glancing angle and
its calibration …, the beam azimuth, the sample orientation and surface state …, **the pattern
heights**, the reference-wave trajectory, and **the measured carrier fringe spacing and
overlap**."

**What is wrong.** 06 marks exactly nine items "(blocking)": 1, 3, 4, 5, 7, 8, 11, 12, 15.
00's list omits **item 3 (illumination convergence semi-angle)** and **item 5 (image pixel size
at the detector and the magnification)**, and promotes **item 13 (pattern geometry / heights)**
and **item 16 (carrier fringe spacing and overlap)**, neither of which is marked blocking.

Item 3 is the worst omission: the first review's M7 was applied precisely by marking it
blocking, 06 item 3 now says "This decides whether nanometre-scale features can show any phase
contrast at all", and 03 §4 says the convergence limit "decides whether a 10 nm feature is
measurable". The executive summary — the only page most readers will see — leaves it out of the
blocking list altogether.

**Proposed wording:** "06 lists 22 items, nine of them blocking: the accelerating voltage (1),
the illumination convergence semi-angle (3 — this alone decides whether nanometre features can
show phase contrast), the objective-aperture semi-angle and which beam it selects (4), the
detector pixel size and magnification (5), the external glancing angle and its calibration (7),
the beam azimuth (8), the surface orientation (11) and preparation state (12 — oxide and
ion-milling damage can suppress the Bragg-reflected object wave entirely), and the
reference-wave trajectory (15). The most valuable non-blocking input is a measured rocking
curve (9), because it fixes the angle scale and the mean inner potential together."

#### F3. "The best end-to-end result … is 0.12 A" is not what the code audit calls the best result

*File:* `docs/00_executive_summary.md`, headline 5.

Quoted: "**The best end-to-end result on ideal synthetic data with the defaults is 0.12 A for a
3.14 A step.**"

**What is wrong.** `A_code_audit.md` §5.5 gives an end-to-end table on exactly that synthetic
data. Its default rows give 0.122 A; the row A labels in bold is
"`A, --manual-peak 252,490, --rin 20, --no-detrend` | **2.130** | **0.797** | **best
achievable: 1.7 % phase error; still 4x below the true 3.1355 A because of the wrap (C4)**".
So A's "best achievable" is **0.797 A**, and 0.122 A is the *default* result, not the best one.
Writing "the best … with the defaults is 0.12 A" reads as "even at best the pipeline returns
0.12 A", which contradicts the report it summarises and hides the more interesting point: even
after the carrier bin is forced, the aperture widened and the detrend disabled, the answer is
still four times low **because of the 2 pi wrap**, which is a physics defect rather than a
processing one.

**Proposed wording:** "With the repository's own defaults the end-to-end result on ideal
synthetic data is 0.12 A for a 3.14 A step. Forcing the true carrier bin, widening the aperture
and disabling the detrend recovers the phase to 1.7 percent (2.130 rad against 2.094) but still
returns only 0.80 A, because the 2 pi branch is never resolved (A report §5.5)."

#### F4. 01 omits A-M9 — the repository's only self-validation path is broken — while its "what survived scrutiny" section reports that the rotation matrix is clean

*File:* `docs/01_repository_audit.md` §3 (defect list) and §4 ("What survived scrutiny").

Quoted (01 §4): "The slab rotation matrix is orthonormal (2e-16) and right-handed; the facet is
{111} and the beam is a <110> in-plane direction."

**What is wrong.** 01 claims to be "the itemised audit" (05 §1) and lists 18 A-defects, but it
never mentions **A-M9**: "`multislice_tilt_series_runner.py:597-665` rotates every atom by
θ_B … but rewrites the **same** cell dimensions. `REPRODUCED`: `R·(0,Ly,0)` differs from
`(0,Ly,0)` by **0.301 Å** and `R·(Lx,0,0)` … by **0.558 Å** (Si–Si bond 2.35 Å), so the periodic
images no longer register; and **168 atoms end up outside the y range** … The 'validation'
therefore compares a beam tilt against a *sheared, non-periodic* crystal." It also drops the
`%.6f` regression A records in the same defect ("can flip atoms across step boundaries").

This matters twice over. (i) `--sample-tilt-validation` is the only internal cross-check the
repository has, and it is invalid — a fact that belongs in an audit whose purpose is to say what
can be trusted. (ii) 01 §4 states that *the rotation matrix* is orthonormal; that is the
**generator's** `slab_rotation_matrix()` (A `:61-73`), not the runner's
`_build_sample_tilt_variant`. A reader of 01 alone would conclude the rotations are sound.

01 also omits **A-M17** (`estimate_wave_memory_gb` mis-counts by 30x on the pre-interpolation
grid and `HRTEM_TARGET_MEM_GB` then coarsens the pixel from that number) — which is the
mechanism that produces the advisory 0.5 A pixel whose consequences 01 §3.3 does report.

**Proposed fix.** Add to 01 §3.3: "A-M9: `--sample-tilt-validation` rotates the atoms but keeps
the old cell vectors, so `R·a1` and `R·a2` miss the cell by 0.56 A and 0.30 A and 168 atoms
leave the box; the only 'validation' in the repository compares a beam tilt against a sheared,
non-periodic crystal, and the writer drops to `%.6f`, which the generator's own comment says
can flip atoms across step boundaries. A-M17: the memory estimate over-counts by ~30x and then
coarsens the pixel automatically, which is where the unusable 0.5 A advisory pixel comes from."
In 01 §4, change "The slab rotation matrix" to "**The generator's** slab rotation matrix
(`si110_cleave_slab_generator.py:61-73`; the runner's sample-tilt rotation is a separate defect,
A-M9)".

#### F5. 02 lists a journal paper among "software actually verified from READMEs", upgrading its evidence level

*File:* `docs/02_literature_position.md`, last bullet of "Methodological analogues".

Quoted: "Modern reflection simulation software **actually verified from READMEs**:
`sim-trhepd-rheed` (dynamical, Fortran, GPL), `rheedium` (JAX, kinematic with optional
multislice, pre-1.0), **Kudo et al. 2023 (fast ODE reformulation of the RHEED boundary-value
problem)**. abTEM and py_multislice have no reflection mode."

**What is wrong.** Kudo et al. is [P49] in `B_literature.md`, a paper, not a code repository.
B's record is: "(arXiv:2306.00271, 2023); journal version title reported as … *Comput. Phys.
Commun.* (Nov 2023) … `METADATA_VERIFIED(index) +ABSTRACT(index)`, **title discrepancy
`UNVERIFIED`**". No README was read for it; no software was located for it. Placing it inside a
sentence whose subject is "software actually verified from READMEs" asserts a source access that
B explicitly did not have — the exact upgrade instruction §1.4/§1.6 forbids. (The other three
statements are correct: B read the `sim-trhepd-rheed`, `rheedium`, `abTEM` and `py_multislice`
READMEs verbatim.)

**Proposed wording:** "Modern reflection simulation software, verified from READMEs read
verbatim: `sim-trhepd-rheed` (dynamical, Fortran, GPL, Ichimiya-type surface-parallel slicing)
and `rheedium` (JAX, kinematic with optional multislice, pre-1.0); abTEM and py_multislice
have no reflection mode. Separately, Kudo et al. 2023 (`+ABSTRACT(index)`; no code located,
and the journal title differs from the preprint title — UNVERIFIED) reformulate the
RHEED/TRHEPD boundary-value problem as an initial-value matrix ODE."

#### F6. 03 §5 calls the *nominal* 20 A vacuum channel "true"; the code audit measured 16.1 A

*File:* `docs/03_physics_summary.md` §5, bullet 2 (and, in the opposite direction,
`docs/00_executive_summary.md` headline 2 and `docs/01_repository_audit.md` §1).

Quoted (03 §5): "only rays within `L_z,si tan(theta) = 3.11 A` of the surface reach it inside
the crystal (31 percent of the **nominal** 10 A gap, 16 percent of the **true 20 A** periodic
channel)".

**What is wrong.** 20 A is 2 x the *declared* `x_vacuum_A = 10.0`; it is the nominal figure, not
the true one. `A_code_audit.md` §2a measures the realised cell: crystal from 8.4322 A to
97.0110 A in a 104.659 A cell, i.e. "7.648 + 8.432 = **16.081 Å** (atom centre to atom centre)"
of vacuum, and "`x_vacuum_A = 10.000` … **7.6484 Å**, −23.5 %". So the *true* periodic channel
is 16.1 A and the *nominal* one is 20 A — the labels are swapped. With the measured channel the
fraction is 3.11/16.08 = **19 percent**, not 16 percent. 00 ("a 16 to 20 A periodic channel")
and 01 ("a 16 A image gap") use the audited value; only 03 calls 20 A "true".

**Proposed wording:** "(31 percent of the declared 10 A top gap; 19 percent of the realised
16.1 A periodic vacuum channel between plate images, which the generator declares as 2 x 10 A —
`A_code_audit.md` §2a)."

#### F7. 01 §4 reports that "the two wavelength formulas are algebraically identical" — there are three, and the third is the cause of the NaN file 01 reports in §3.1

*File:* `docs/01_repository_audit.md` §4, bullet 3.

Quoted: "The two wavelength formulas are algebraically identical (1e-6 percent difference)."

**What is wrong.** `A_code_audit.md` §2b is headed "**Three** wavelength formulas exist in the
repository" and tabulates four constant sets with three distinct values: generator 0.025079340,
forward-model/step-height 0.025079341 (the two that are algebraically identical, −1e-6 %),
the runner's tilt-snapping fit `12.2643/sqrt(V(1+0.978476e-6 V))` = 0.025079422 (**+3.25e-4 %**),
and embeam's own 0.025079337. A adds, in bold, "it is enough to break prismatique's exact-float
tilt-weight test … which is why it matters at all", and warns "I state this explicitly because
it would be easy to over-claim."

Placing only the reassuring half in a section headed "What survived scrutiny (REPRODUCED)" is
that over-claim. 01 §3.1 itself says the NaN intensity file arises because "the tilt weights use
an exact float comparison against a snapped offset **computed with a different wavelength**" —
so 01 contradicts itself across two sections.

**Proposed wording:** "Two of the repository's three hard-coded wavelength formulas are
algebraically identical and differ only in their constants (1e-6 percent); the third, used only
for tilt snapping, is 3.25e-4 percent off, which is what breaks prismatique's exact-float
tilt-weight test and produces the all-NaN intensity file (§3.1). No formula is attributed to a
named constants source (instruction §9.8)."

#### F8. 02 gives P08 and P09 — the same volume of the same journal — two different journal names, and states for P08 the name B leaves unresolved

*File:* `docs/02_literature_position.md`, Osakabe table, rows P08 and P09.

Quoted: "| P08 | Osakabe, **Microsc. Res. Tech.** 20, 457 (1992) … Best accessible statement of
the method; journal masthead for volume 20 to be checked. |" and "| P09 | Banzhof, Herrmann and
Lichte, **J. Electron Microsc. Tech.** 20, 450 (1992) |".

**What is wrong.** `B_literature.md` §1.4 deliberately writes the P08 masthead as unresolved:
"[P08] Osakabe, *J. Electron Microsc. Tech. / **Microsc. Res. Tech.*** **20**(4), 457–462
(1992)". 02's Record column then states one of the two as fact while the comment column says it
must be checked — and the very next row of the same table gives the *other* name for pages
450–456 of the *same volume 20(4)*, with consecutive DOIs (`10.1002/jemt.1070200414` and
`…415`). Two adjacent articles of one issue cannot be in two journals; a referee will notice
immediately, and the natural (unstated) explanation — that the journal was renamed and B could
not establish which masthead volume 20 carried — is exactly what the table should say.

**Proposed wording:** use one form for both rows, "J. Electron Microsc. Tech. (renamed Microsc.
Res. Tech.) 20(4), 457–462 / 450–456 (1992)", with a single footnote: "which masthead volume 20
carried is UNVERIFIED (B §1.4); both articles are in the same issue, DOIs
10.1002/jemt.10702004{15,14}."

---

### MINOR

#### F9. 01 §3.3 re-introduces the `L_z tan(theta)` conflation that first-review m8 removed from 03

Quoted (01 §3.3): "Only rays within `L_z tan(theta)` of the surface (**3 to 4.5 A**) reach it
inside the slab".

03 §5 was corrected to distinguish the two lengths: `L_z,si tan(theta) = 3.11 A` (rise over the
crystal, the number the 31 percent refers to) from 4.46 A (rise over the whole 198 A cell, what
must stay below the vacuum margin). E2 recomputed both. "3 to 4.5 A" makes a single symbol take
two values, and the 4.46 A figure has nothing to do with rays reaching the surface.

**Proposed wording:** "Only rays within `L_z,si tan(theta) = 3.11 A` of the surface reach it
inside the slab; over the full 198 A cell the reflected beam rises 4.46 A, which is what must
stay inside the vacuum margin."

#### F10. 01 §1 re-introduces the wrong C locator that first-review m10 fixed in SM06

Quoted (01 §1, "Measured beam"): "(2,-2,0) is not accessible in reflection geometry at 200 keV
(**C section 3.5**)".

`C_physics_derivations.md` §3.5 is "Table A — Si(111)/(1,−1,1) specular rod, 200 keV, V0 = 12 V".
The accessibility rule is **equation (3.5) inside §3.3**, which is how SM06 now reads
("C section 3.3, equation (3.5)"). Section and equation numbers collide throughout C.

**Proposed wording:** "(C §3.3, eq. (3.5))".

#### F11. 01's cell description does not add up: 7.6 A on each of two faces is not a 16 A gap

Quoted (01 §1): "8.5 nm plate with two free surfaces, periodic along its own surface normal with
a **16 A image gap** (declared 10 A vacuum on each face; **measured 7.6 A**), no absorber".

A §2a measures 7.6484 A above the surface and **8.4322 A** below the back face; the 16.081 A gap
is their sum, not twice 7.6 (= 15.3). A also records the asymmetry as a defect (A-M8).

**Proposed wording:** "…with a 16.1 A image gap (10 A declared on each face; realised 7.65 A
above the surface and 8.43 A behind the back face — A-M8), no absorber".

#### F12. "81 percent", "85 percent" and "81 to 85 percent" are the same quantity computed from two different geometries, and no document says which

`03 §5`: "**81 percent** of the incident plane wave enters the crystal through the front end
face (Laue transmission through an **8.5 nm** plate)"; `model_assumptions` A2: "81 percent";
`01 §1`: "**85 percent** starts inside the crystal (end-face entry)"; `01 §3.3` and `00`:
"**81 to 85 percent**"; `SM09`: "81 percent enters the end face".

E2 recomputed: with the *nominal* geometry (crystal 84.659 A of a 104.659 A cell) the fraction
is 80.89 %, which is C's number; with the *realised* atom positions (88.579 A of 104.659 A,
A §2a) it is 84.6 %, which is A's number. Likewise "8.5 nm plate" is the nominal `Lx_si_A`
(84.659 A) while A measures 88.58 A and its own comparison table says "88.6 Å-thick plate"; and
01's "138 A slab" is C's nominal `L_z,si` (138.27 A) while A measures `L_slab = 136.328 A`.

**Proposed fix:** state the basis once, e.g. "81 percent on the declared geometry, 85 percent on
the realised atom positions (A §2a); the two differ because `meta.json` misreports the vacuum
and the slab thickness (A-M8)", and quote the plate as "8.5 nm declared / 8.86 nm realised".

#### F13. The two sampling ceilings in 03 §5 are computed at two different pixel sizes

Quoted: "the generator's default 0.5 A pixel supports **16.7 mrad** under the 2/3 rule and only
**12.9 mrad** under Prismatic's half-Nyquist rule".

The two rules differ by a fixed factor 4/3, so for one pixel size the pair must be in the ratio
1.333; 16.7/12.9 = 1.295. E2: at the *nominal* 0.5 A, 2/3 gives 16.72 mrad and half-Nyquist
12.54 mrad; at the *realised* 0.4845 A (D §2c), 17.25 and 12.94. The sentence takes 16.7 from
the nominal pixel and 12.9 from the realised one. SM15 repeats the same pair.

**Proposed wording:** "…the generator's default 0.5 A advisory pixel (realised 0.4845 A) gives
17.3 mrad under the 2/3 rule and 12.9 mrad under Prismatic's half-Nyquist rule, so it cannot
represent the 24 mrad tilt under either."

#### F14. Every shadow length is quoted at 22.5 mrad — the external angle of the forbidden (6,-6,6) — and is 1.65x larger at the reflection the documents recommend

03 §4, 05 CFG-A/CFG-B, `model_assumptions` B9 and 06 item 13 all quote "139 A per bilayer" and
"444 nm for a 10 nm mesa **at 22.5 mrad**". 22.50 mrad is the (6,-6,6) row of the 03 §3 table,
marked "NO (F = 0)" in the same document. At the first allowed order the documents actually
recommend, (4,-4,4) at 13.64 mrad, E2 recomputes the bilayer shadow as **230 A** and the 10 nm
mesa shadow as **733 nm**; at (8,-8,8) they are 102 A and 324 nm.

Nothing is numerically wrong — 22.5 mrad is used as a round illustrative angle — but a
specification that forbids (6,-6,6) and then sizes every shadow mask at its glancing angle
invites an implementer to hard-code the wrong number, and it understates the worst case by 65 %.

**Proposed fix:** quote the range, "139 A per bilayer at 22.5 mrad, 230 A at the (4,-4,4)
condition (13.6 mrad); 444 nm to 733 nm for a 10 nm mesa over the allowed orders", and say that
22.5 mrad is used only as a round illustrative angle.

#### F15. The stub-shadowing guard added to `tools/provenance_checks/*.py` does not prevent shadowing

All four scripts now carry:

```
_HERE = os.path.dirname(os.path.abspath(__file__))
if importlib.util.find_spec("pyprismatic") is None:
    sys.path.insert(0, _HERE)  # … it never shadows a real engine
```

CPython already places the script's own directory at `sys.path[0]` when a script is run as
`python check_api.py`. If the stub has been renamed to `pyprismatic.py` in that directory,
`find_spec` finds *the stub*, the guard therefore does nothing, and the stub still shadows an
installed engine. The comment's claim ("it never shadows a real engine") is false in the normal
invocation, and the first review asked for an assertion, which would have failed loudly.

**Proposed fix:** replace the conditional insert with a hard check that also detects the local
file, e.g.

```
_spec = importlib.util.find_spec("pyprismatic")
assert _spec is None or os.path.dirname(_spec.origin or "") != _HERE, \
    "the local pyprismatic stub is shadowing an installed engine; remove it"
```

#### F16. 05 §8 files T16 under "accessibility"; the calculator defines it as the invisibility test

Quoted (05 §8, Geometry): "accessibility (**T15, T16**)". The calculator prints
"T16 exact G.R / 2pi for (2,-2,0) and a d_111 step (integer!) … want 1.000000" — the
invisibility/branch test, which `SM03` correctly groups with T10-T13. 05 §8's Quantification
bullet lists "near-invisibility condition" with no test ID, which is where T16 belongs.

**Proposed fix:** "accessibility (T15)" and "near-invisibility condition (T16)".

#### F17. 01's stated cause of the 193 duplicated atoms does not follow from the code

Quoted (01 §3.3): "193 atoms are double-counted on the y = 0 plane (**a strict inequality at
both ends of the periodic direction**)".

The generator reads `in_y = (y > -Ly/2.0) & (y < Ly/2.0)`
(`si110_cleave_slab_generator.py:214`, verified in the clone). A strict inequality at both ends
*excludes* both boundary planes; on its own it cannot duplicate one. A's measurement (193 atoms
at y = 0 *and* 172 at y = Ly, gap 0.000000 A instead of 1.10858 A) can only arise because the
floating-point atom coordinates fall just inside the window at both edges. That also means A's
proposed fix (`-Ly/2 <= y < Ly/2`) is insufficient: a tolerance is needed, not just a half-open
interval, and the two counts differ (193 vs 172), so it is not a clean plane-for-plane
duplication.

**Proposed wording:** "193 atoms at y = 0 and 172 at y = Ly survive the cut
`(y > -Ly/2) & (y < Ly/2)` because the float coordinates fall marginally inside at both edges;
under the periodic boundary these are the same plane, so the plane is duplicated and the
inter-plane gap collapses from 1.109 A to 0. The fix is a half-open window **with a tolerance**,
plus an assertion on the atom count for the volume."

#### F18. 00 step 5 calls a Si(111) benchmark "Osakabe-type", which is what AC3 was corrected to stop implying

Quoted (00, next steps 5): "Only then simulate holograms of **Si(111) bilayer steps
(Osakabe-type benchmark)**".

The first review's M4 was applied by rewriting AC3 to "A monatomic-step benchmark on the
configuration Ali specifies (CFG-A or CFG-B) … Comparison with Osakabe 1988 is deferred until
P01 is read; its surface and conditions are currently UNVERIFIED", and 00's own Osakabe section
repeats that. Attaching "Osakabe-type" to the Si(111) configuration in the recommendations
re-creates the association the correction removed.

**Proposed wording:** "simulate holograms of Si(111) bilayer steps (the monatomic-step benchmark
CFG-A; whether it matches Osakabe's own configuration is UNVERIFIED until P01 is read)".

#### F19. 06 item 20 states the `V0` height bias without its sign, which is the one thing the first review asked for

Quoted (06 item 20): "a change of 1 V shifts the single-bilayer step phase at the (4,-4,4)
condition by about 0.34 rad and **biases a height inferred from a fixed measured phase by about
0.05 A**."

03 §3 and `model_assumptions` B1 both give the sign ("+0.05 A per volt of underestimate"); E2
recomputes `dh/dV0 = +0.0492 A/V` at fixed measured phase, against `-0.0486 A/V` for the phase
re-expressed as a height at fixed `k_ext`. The two differ only in sign, which is precisely why
the review asked that it be stated. Add "+" and "per volt by which `V0` is underestimated".

#### F20. 01 drops the one quantitative consequence of the Prismatic z-mirror

Quoted (01 §3.2): "D-2g: Prismatic mirrors the file z coordinate (`z = L_z - z_file`); the
generator ignores this. For this slab the mirror perpendicular to [110] is a lattice symmetry
(97 percent atom match), so the effect is **benign here**".

A §5.2 agrees the flip is "structurally benign for this orientation" but adds the residual:
"after `z → Lz − z` a shift of **+3.8402 Å** puts 97.41 % of atoms back on original sites … **Net
effect: the slab sits ≈1.92 Å further along the beam than written.**" A 1.92 A along-beam offset
is 1.92 x 44 = 85 A of *surface* coordinate after the foreshortening mapping of 03 §6, so it is
not irrelevant to feature-position comparisons. Add: "the residual is a rigid +3.84 A shift, so
the slab sits about 1.92 A further along the beam than written (85 A of surface coordinate after
foreshortening)."

---

### NIT

* **N1.** 00 "a length along the beam of order **0.1 to 0.4 um**" against "0.08 to 0.42 um at
  `theta_int` = 24 mrad" in 03 §5, 05 §4.3.4 and SM16. E2: 0.0833 / 0.4166 um. Use one form.
* **N2.** "a step phase of **3.140 rad**" for the non-relativistic case. With the document's own
  refraction relation `sin^2 th_int = (sin^2 th_ext + Delta)/(1+Delta)` and `Delta = V0/T`,
  E2 gets **3.1411 rad**; 3.1403 follows only from the approximate form `sin^2 th_ext =
  sin^2 th_int - Delta` that `physics_conventions` tells the reader not to use. Immaterial to
  "indistinguishable from pi", but quote 3 digits (3.14) or say which form was used.
* **N3.** SM08 uses `dz` for two different lengths in one row: the propagator convention column
  says `exp(-i pi lambda dz q^2)` (slice thickness) while the claim column says
  `k dz sin^4(alpha)/8 … over the 198 A cell` (total path). Write `k L sin^4(alpha)/8` with
  `L = 198 A`.
* **N4.** 03 §4 / 06 item 2: "a 0.7 eV spread changes the step phase by **less than 0.003 rad**
  even for a 10 nm step". E2: 1.4e-3 rad at (4,-4,4), 2.3e-3 at (6,-6,6) and **3.15e-3 at
  (8,-8,8)** — marginally above the stated bound at the highest allowed order. Write "below
  0.004 rad over the whole allowed rod".
* **N5.** 02 writes "**Jorgensen** 2024"; B records "P. S. **Jørgensen** … *Optica* 11(2),
  197–204 (2024)". Same class of defect as the Hÿtch/Meißner correction already applied.
* **N6.** 05 §2 CFG-A lists the usable specular conditions as "(4,-4,4), (5,-5,5), (7,-7,7),
  (8,-8,8)" but 03 §3's table marks **(3,-3,3) allowed** (8.61 mrad external, above
  `theta_c` = 8.356 mrad). Either list it or say why it is excluded.
* **N7.** 05 §4.1's CFG-B forbidden list is "(002), (006)"; **(0,0,10)** (all even,
  h+k+l = 10, not 4n) is equally forbidden and equally likely to be tried.
* **N8.** 03 §3 puts three sentences of prose ("`theta_c` = 8.356 mrad: the internal glancing
  angle … no total external reflection for electrons.") *inside* a fenced code block with the
  two formulas. Move the prose out of the fence.
* **N9.** 01 §3.3: "the illumination must travel 444 A **to fall the declared 10 A gap**" —
  missing preposition; "to descend the declared 10 A gap".
* **N10.** 03 §4 "a 10 nm patterned step is **about 100 wraps**"; at (4,-4,4) it is 108.8
  (`h_2pi` = 0.9192 A). "About 110" or "of order 100".
* **N11.** 01 §3.1 "864 x 640 at 0.121 A instead of 216 x 160 at 0.485 A" quotes only the x
  pixel; A §2c gives (0.1211, 0.1247) A and (0.4845, 0.4989) A. The anisotropy is real and 05
  §5.2 requires "anisotropic sampling stated on both axes".
* **N12.** 01 §3.4 writes the accessibility bound as "`2 k sin theta_c` = 4.19 rad/A" while the
  revised `physics_conventions` prefers the exact "`2 dK`, `dK = k sqrt(Delta)`" (they differ by
  3.5e-5). Use the conventions file's form in the audit too.
* **N13.** 03 §5 compares the paraxial error against "the **0.03 rad** noise target" while 03 §4
  gives `sigma_phi = 0.028 rad`. Quote the same number.

---

## VERIFIED CORRECT — DO NOT TOUCH

1. All three first-review blockers, all eleven Major items, all nineteen Minor items, the six
   nits and the three architecture reservations are applied in the revised files; the only
   declined item (C's internal path to its companion script) is declined for a stated reason
   (the agent reports are frozen as the record).
2. `tools/reflection_step_phase_calculator.py` still runs clean, prints **25/25 checks pass**,
   and its output is **byte-identical** to `docs/agent_reports/C_calculator_output.txt`. The
   README recipe works as written.
3. Every corrected physics number recomputed independently and confirmed: paraxial error
   0.00206 / 0.02545 / 0.10605 rad; `Delta = 6.98200e-5`; 14.06 % / 16.37 %; the whole
   `(n,-n,n)` rod table to every printed digit (`theta_int`, `theta_ext`, step phase mod 2 pi,
   `h_2pi`, foreshortening); `sigma_phi` = 0.02828 rad and `sigma_h` = 0.00414 A at (4,-4,4);
   `dphi/dV0` = -0.3350 and -0.2031 rad/V, `dtheta/dV0` = -0.2132 and -0.1293 mrad/V,
   height bias +0.0492 A/V; 1.571 / 5.011 / 50.11 rad/mrad and 0.6365 / 0.1996 / 0.01996 mrad;
   shadows 139.4 A, 60.4 A, 444.5 nm; footprint 888.9 A and 444.4 A; build-up 0.083-0.417 um;
   2/3 and half-Nyquist ceilings 64.31 / 48.23 mrad at 0.13 A; `2 theta_ext` 17.2-61.8 mrad;
   `arccos(1/3) = 70.53 deg` for (4,4,4) against the rod; `2 dK = 2 k_int sin(theta_c)` exactly.
4. Every number checked in 00 and 01 traces to `A_code_audit.md` at the locator implied:
   84.6 % end-face entry and 1.0 % / 3.1 % vacuum-side arrival (A §3, 9.3); 16.081 A image gap
   and 7.6484 A / 88.579 A against the declared 10.0 / 84.659 (A §2a, A-M8); 193 atoms at y = 0
   (A-M7); 97.41 % z-mirror atom match (A §5.2); 1309 tilts for 74 requested and the 0.657 mrad
   nearest grid tilt (A-C2, D command 15); 864 x 640 at 0.121 A vs the printed 216 x 160
   (A-C2); the sideband threshold `2 arctan(pi/2) = 2.0078 rad` (A-C3, re-derived here from
   `|c0| = |cos(D/2)|`, `|c1| = 2|sin(D/2)|/pi`); 0.5236 rad measured step (A-C3);
   27 % detrend loss (A-M5); the aperture sweep 0.122 / 0.553 / 0.106 / 84.9 A (A-M6);
   `d_111/4 = 0.7839 A` and 8.378 rad (A-C4); +1.146 rad for an imposed -2 pi/3 step (A-C8);
   3.136 A for the falsy zero (A-M11); 2.130 rad at 1.7 % with the carrier forced (A-C3);
   A is 1413 lines.
5. 01's eight section-9 verdicts match `A_code_audit.md` §3 exactly (FAIL / PARTIAL / FAIL /
   FAIL(NA) / FAIL / FAIL / FAIL / FAIL), and every defect ID it cites (A-C1..C8, A-M5..M8,
   A-M10..M15, D-2a, D-2c, D-2g, D-1.3, D-3.1, D-3.4, D-3.5, D-5.2) exists in
   `A_code_audit.md` §4 / `D_software_provenance.md` with the content ascribed to it. 01 §5
   reproduces A §7's priority order faithfully.
6. 02's bibliographic details all trace to the instruction file or to B: P01 (JJAP 27, L1772,
   1988; authors in the instruction file's order), P02 + P02E (PRL 62, 2969; PRL 63, 584),
   P03 (Ultramicroscopy 48, 475), P07 (PMC7850541), P08 (20, 457, 1992), P09 (20, 450, 1992),
   PAT01 (US 4,998,788), P17 (JJAP 22, 176), P18 (Acta Cryst A42, 545), P19 (Surf. Sci. 199,
   609), P26 (Ultramicroscopy 33, 237), P30 (Nature 453, 1086), P31 (Ultramicroscopy 111,
   1328), P36 (APL 106, 101604), P35/P37/P38/P39/P40, P42-P47, Z. L. Wang 1996 ch. 3
   "Dynamical theories of RHEED" (B2 entry 12), and the bibliography counts 96 / 78 / 18
   (verified: `references.bib` has 96 `@` records; B2 records 78 above the delimiter).
   No DOI, page range or year appears in any summary document that is not in the instruction
   file or in B.
7. 02's evidence handling is otherwise honest: P01's content is UNVERIFIED and the pi / 0.9 pi
   values are returned to P09; the patent description is labelled UNVERIFIED; "geometrical path
   differences measured in units of the wavelength" is paraphrased without quotation marks and
   labelled abstract-index; and the "nothing since 1993" point is stated as a search failure in
   00, 02 and 05 §10, exactly as `B_literature.md` §6.1 demands
   ("Do not write 'no one has done this since 1993' on the strength of this review").
8. Every row of 04 was checked against `D_software_provenance.md`: all 22 file:line locators
   occur in D, and every label matches D's own (SECTION_READ for the mid-plane back-propagation,
   the propagator/anti-aliasing/tilt ceiling, the HRTEM path and the upstream notice;
   SECTION_READ + REPRODUCED for the 5-D schema, the tilt window, the absorber TypeError, the
   thermal settings and the NaN weights; REPRODUCED for the `pyprismatic` declaration and the
   0.0.1/0.0.4 byte-identity). The 1309/74, 0.076 A per-axis RMS, 2017 `pyprismatic` 1.1.x,
   January 2026 notice, GPL/GPLv3/MIT and abTEM "one degree" (~17 mrad) facts are all D's,
   at D's labels.
9. Cross-document consistency, after revision, holds for: the paraxial triple (03, 05, SM08,
   `model_assumptions` A1, 05 §8); the convergence triple 0.64 / 0.20 / 0.020 mrad (03, 05,
   06, `model_assumptions` B10); the `V0` sensitivities (03, `model_assumptions` B1, SM04, 00);
   the shadow lengths (03, 05 x2, `model_assumptions` B9, 06); the wrap period 0.4-1.5 A;
   `h = -Delta_phi lambda / (2 pi (sin th_in + sin th_out))` in both 05 §5.8 and
   `physics_conventions`; the 22-item PROJECT_INPUT count in 00, README, 05 §9 and 06; and the
   T1-T25 assignment in 05 §8 (one mislabel, F16).
10. No source-policy violation of the quotation kind remains in the summary documents: the only
    quoted strings in 00, 01 and 04 are repository identifiers, file names and printed messages;
    02's quoted strings are paper titles from the instruction file or from B; 05 §10's P08 quote
    now carries `+ABSTRACT(index)` and "the paper was not read".

**END OF E2 REVIEW.**
