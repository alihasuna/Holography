# A13 - Re-audit of X7 (fixes of re-audit A12 on the item-12 oxide label policy of comparison runs)

Auditor: agent A13, 2026-09-24. Status: FINAL (written incrementally).

Scope (narrow, as instructed): repository /home/user/Holography, branch
claude/electron-holography-orchestration-nakd7r, commit 0c5bba3 (`git rev-parse HEAD`). Read in full:
docs/agent_reports/A12_X6_reaudit.md and docs/agent_reports/X7_a12_fixes.md. Read in the code:
`structure/oxide.py` lines 1-200, 430-460 and 540-760 (constants, the interval, the bound, the
guard); `pipeline/config.py` lines 1030-1560 and 1645-1760 (allowlist, refusal lists, record
checks, the count variant) and 1905-1925. Also read: `tools/review/x7/x7_oxide_numbers.py` with its
output, `x7_parity_variants_output.txt` (and the record set-up of `x7_parity_variants.py`),
`x7_demo_bitid_output.txt`, `mutate_x7.py`; rows B7, B12 and B43; docs/06 item 12
(`git show 0c5bba3 -- docs/`); and the docs/references.bib entries cited below (their notes only;
I did not read the papers).

Rules kept:
* This report is the only repository file I wrote. Code, tests and docs were not modified;
  mutations were made in scratch copies only.
* Nothing was committed.
* Nothing was written under outputs/: `git status --short` showed only this report, and
  `git status --short outputs/` was empty.
* Scratch: SP/a13/, SP = /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad.
* Every run was single-threaded (OMP/OPENBLAS = 1), because the full suite was running at the same time.

Accepted as known limits (the instruction; not re-reported here):
* the gate cannot verify a record;
* a fabricated but well-formed record passes;
* the refusal list fails closed;
* digit-for-letter spellings;
* the physical effect of the non-nearest parity variant is not computed.

Grades:
* MAJOR: must be resolved before the policy is called final for comparison runs.
* minor.
* note.

## Summary of findings

| id | grade | subject |
|---|---|---|
| A13-M1 | MAJOR | Three allowlist ids admit measurements of a different quantity: CBED for the potential of an amorphous layer; the energy-filtered REFLECTION (and plan-view transmission) ratio for V'_ox; and RHEED/reflection rocking-curve fits whose V0 is the crystal's. docs/06 offers them to the laboratory as acceptable. |
| A13-m1 | minor | One record, with the V_ox method list, covers both a-Si potentials (V_a and V'_a). A comparison run needs V'_a > 0, but no absorption method (EELS) is admissible except `other_measurement`. |
| A13-m2 | minor | The width and EELS ids are physically able but need qualifiers: an erf sigma of the laterally averaged profile, deconvolved; the weak X-ray contrast at SiO2/Si; the interfacial-layer models; AFM scan size; lambda at a stated energy and collection angle. |
| A13-n1 | note | The Monte Carlo range 95.27-95.64 % covers three chosen scenarios and is not a bound. X7's own output prints 97.76 %, and I find 94.7-94.9 % for other one-sided cases. "About 95 %" (docs) is fair. |
| A13-n2 | note | The independence of t and rho is stated in the code but not in docs/06 or B7. At r = +0.5 the coverage is 93.4 %, at r = +1 91.3 %. |
| A13-n3 | note | "Each uncertainty must move the depth by less than two layers" (docs/06, B7). The code bounds k u, so a standard uncertainty must move the depth by less than one layer. |
| A13-n4 | note | "the 2.0 nm demo record" (docs/06, B12): the variant runs used a fabricated TEST record with the demo's values and half-width uncertainties. The B41 demo record refuses uncertainties. |

Verified correct (question 1): the sensitivities, the A12 example, the quadrature, the one-sided
a-Si rule, the linear box, and the a/2 bound. The bound refuses no record that would otherwise run.
Question 3: 5 of 5 reversions reproduced with my own texts, with the same failure counts as X7.
The B41 demo is 26 of 26 bitwise identical.

## Question 1: the quadrature interval (D1, `SP/a13/d1_interval.py`, output `d1_interval.out`)

Parts A-D use no package import (a = 5.4309 A, M_Si = 28.0855, M_O = 15.9994, N_A exact).

    f(2.20) = 0.441507; a/4 = 1.357725 A; a/2 = 2.7155 A; rho_Si = 2.3292
    dD/dt = f = 0.3252 layer/A; dD/drho = f t/rho = 2.9562 layer per g/cm^3 (x0.05 = 0.1478); dD/dt_a = 0.7365 layer/A
    f linear in rho: f(2.25) - f(2.20) = 0.010034260 = f x 0.05/2.2 (so c_rho = f t h/rho exactly)
    A12 example (standard 1 A, 0.05 g/cm^3, 0.1 A): nominal 6.5036; c_t 0.6504, c_rho 0.2956, c_a 0.1473 layer (= sensitivity x 2u)
      lower sqrt(c_t^2 + c_rho^2) = 0.7144; upper sqrt(c_t^2 + c_rho^2 + c_a^2) = 0.7294; 5.789-7.233 -> [6, 7]
      X6 box (+-2u linear): 5.587-7.626 -> [6, 7, 8]
      box width 2 c_t + 2 c_rho + h_a + min(h_a, t_a) = 2.039272 = box hi - lo = 2.039272

Every number X7 prints for these (x7 output, sections 1-3) is reproduced.

**The "worst-case linear sum" for half-widths is exact, not first order.** Because f is linear in
rho, the width is (1 + x)(t + h) - (1 - x)(t - h) = 2h + 2xt with x = h_rho/rho. So the corner box
of `_depth_counts` has width exactly 2 c_t + 2 c_rho + h_a + min(h_a, t_a), and the product terms
cancel. The docstring and docs/06 ("the linear sum") are correct.

**The one-sided a-Si rule is correct.**
* The lower half-width takes min(k u_a, t_a) (`oxide.py:700`), so the lower end never asks for a
  negative a-Si thickness.
* The upper side always takes the full k u_a, so a stated detection limit enters as 2 DL for the
  kind "standard". This is conservative, and docs/06 says so.
* Centring on the nominal depth is the right choice for a quantity bounded at zero.

**The coverage statement.** "About 95 % coverage for a normally distributed depth" (code, docs/06,
B7) is honest. My Monte Carlo (own seed 13013, 2e6 draws; independent normal t and rho) reproduces
X7's four printed cases within the standard error (0.015 %):

| a-Si model (t 20 +- 1 A, rho +- 0.05 unless stated) | X7 | A13 |
|---|---|---|
| 5.0 +- 0.5 A, normal | 95.44 | 95.44 |
| exactly 0 (u_a = 0.1 A detection limit) | 95.64 | 95.67 |
| half-normal abs(N(0, 0.1 A)) | 95.27 | 95.26 |
| t +- 0.1, rho +- 0.01, exactly 0 | 97.76 | 97.78 |
| t +- 0.1, rho +- 0.01, half-normal | - | 95.06 |
| uniform in [0, DL] | - | 95.55 |
| exactly at DL | - | 95.29 |
| max(0, N(0.3, 0.5)) (t_a 0.3 +- 0.5, the clip active) | - | 94.73 |

A scan of the one-sided case (t_a = 0, true a-Si half-normal; interval [-2s, 2 sqrt(s^2 + u_a^2)])
by quadrature gives a minimum of 94.87 % at u_a/s = 0.7. The coverage tends to 95.45 % at both
ends of the scan. See A13-n1 for how the range is quoted.

The coverage of the COUNT, which is what decides the run, is higher: 98.2-100 % in every case
above. The depth interval rounds outwards to whole counts.

**The a/2 per-uncertainty bound cannot refuse a record that would otherwise run with at most two
counts.**
* Analytic (DERIVED_HERE):
  * If a contribution c_i = s_i k u_i is at least 2 q (q = a/4), the depth interval is at least
    2 q wide. For the standard kind, both sides then carry at least that c_i, except the a-Si term
    on the lower side; the upper side always carries it. For half-widths the width is the linear
    sum.
  * An interval [x, x + w] with w >= 2 (in layers) contains floor(x + 0.5) ... floor(x + w + 0.5):
    at least 3 nearest counts.
  * `_oxide_count_variant` (`config.py:1715-1722`) refuses more than two counts in EVERY purpose
    once uncertainties are stated, and uncertainties are refused under the stand-ins
    (`config.py:1674-1679`). So nothing that the bound refuses could have run.
* Numeric (D1 part D): 200 000 random records near the bound (t 3-40 A, rho 1.9-2.4, t_a 0 or
  0-10 A, both kinds). 76 944 are refused by the bound, and none of them has at most two counts.
* Package against the independent formula (part E): 19 252 admissible random records. The count
  lists are identical, the largest difference at the interval ends is 7.1e-15 layer, and there
  are 0 unexpected refusals.

## Question 2: the allowlist, physics of each id

The model's definitions (`oxide.py` docstring):
* V_ox + i V'_ox is a uniform continuum potential of the amorphous layer, and V'_ox is "the
  electronic absorption of the layer" (lines 9-11).
* The widths are the w of E(x; x0, w) = erfc((x - x0)/(sqrt 2 w))/2, whose gradient is a Gaussian
  of standard deviation w (lines 68-70). So w is an rms (sigma) width of the laterally averaged
  profile.
* One label `amorphous_si_potential` covers BOTH `amorphous_si_V_real_V` and
  `amorphous_si_V_imag_V` (`config.py`, `OXIDE_LABEL_VALUES`).

Source status: the bib entries below are cited from their notes in docs/references.bib only (I
read none of the papers). Reasoning not in a source is marked DERIVED_HERE.

| id -> parameter | physically able? | recommendation |
|---|---|---|
| `offaxis_holography_wedge` -> V_ox, V_a | YES. The phase per unit projected thickness of a specimen of known thickness is C_E V_0 and needs no crystal. Wedge method: GAJDARDZISKA93 (title). Amorphous SiO2 11.5 +- 0.3 V by holography of spheres: LEE2000MT (L8 note, SECTION_READ). Oxide layers on Si wedges: RAU1996 (content UNVERIFIED). V'_a: the amplitude image gives t/lambda only with an energy-filtered or modelled amplitude (DERIVED_HERE) | keep. Broaden the wording to "a specimen of known thickness (wedge, cleaved edge, sphere, cross-section of the layer)"; spheres (LEE2000MT) are otherwise pushed into `other_measurement` (note) |
| `cbed_rocking_curve_fit` -> V_ox, V_a | **NO** (A13-M1 a). An amorphous layer gives no Bragg disks, so there is nothing to fit. For a crystal, the g = 0 coefficient V_0 multiplies every beam by the same phase in transmission and does not enter the CBED intensities to first order (DERIVED_HERE). CBED yields V_g (g != 0) and absorption: VOSS80 (Si CBED, the real V_g and the mean ABSORPTION V'_000 = 0.61 V; L6 note, SECTION_READ) | **remove** for both parameters |
| `rheed_rocking_curve_fit`, `reflection_rocking_curve_fit` -> V_ox, V_a | **Only under conditions** (A13-M1 c). By Snell's law the perpendicular wave vector inside the crystal depends only on the crystal's potential, so the refraction shift of the Bragg positions gives the CRYSTAL's V0, whatever overlayers lie on top (DERIVED_HERE). This V0 is the usual output of a RHEED rocking-curve analysis (HORIO22: V000 of Si set to 12 eV in a RHEED analysis; L6 note). V_ox enters only through the phase k_z,ox t across the layer and its interface reflections, so it is correlated with t, w_v, w_i and V'_ox (DERIVED_HERE). RHEED sees the crystal through a thin chemical oxide (KOROBTSOV2007, 0.8 nm; L7 note). Fitting the holograms that are to be compared would make the comparison a fit (DERIVED_HERE). For a-Si buried under the oxide the sensitivity is weaker still | **merge** into one id **with a stated qualifier**: "fit of a model containing the oxide layer, with V_ox a free parameter and the oxide thickness fixed from an independent measurement; not the crystal's V0 from Bragg-peak refraction; not fitted to the data being compared". Otherwise remove. Remove for V_a |
| `other_measurement` -> V_ox, V_a | form only (accepted limit) | keep |
| `eels_inelastic_mean_free_path` -> V'_ox | YES, if it is measured on the oxide itself (a cross-section of the witness oxide, or a film of known thickness). lambda depends on the beam energy and the collection angle, and amorphous and crystalline SiO2 differ by about 10 % (IAKOUBOVSKII2008PRB, L8 note; BASHA2022, MFP against collection angle at 80 and 200 keV). The model's V'_ox = 1/(2 sigma Lambda) needs lambda at the simulation's energy and aperture (DERIVED_HERE). For a 2 nm film, surface (begrenzungs) losses change the apparent lambda (DERIVED_HERE) | keep, with the qualifier "on the oxide itself; beam energy and collection semi-angle stated" (A13-m2) |
| `energy_filtered_intensity_ratio` -> V'_ox | **transmission through the oxide itself: yes (the log-ratio t/lambda of EFTEM); reflection or plan-view transmission: NO** (A13-M1 b). A reflected beam loses intensity in the crystal as well as in the oxide, and above all to surface plasmons: about 1.44 excitations per reflection on clean Si(111) at 200 kV (TANISHIRO2003, B6 (iii); SECTION_READ via L7/E6). The project carries those losses separately (B38), and V'_ox must not be multiplied with B38 (E9 M1; `oxide.py:91`). A plan-view transmission ratio measures the whole stack (DERIVED_HERE) | **remove "reflection"**. Restrict to "energy-filtered log-ratio t/lambda of the oxide layer itself (cross-section or film of known thickness), beam energy and collection angle stated". Or fold it into the EELS id |
| `xrr_fit` -> w_v, w_i | YES for w_v: the XRR roughness sigma is the rms of an erf (Gaussian-gradient) profile, which is the model's definition. For w_i it is weakly constrained: the X-ray density contrast SiO2/Si is about 5 % (0.662 vs 0.699 e/A^3 at 2.20 and 2.329 g/cm^3; DERIVED_HERE). Thin oxides are often fitted with a denser interfacial LAYER instead of an erf (KOMIYA1997: 0.8-1.4 nm at 2.35-2.41 g/cm^3, interface roughness 0.2-0.3 nm; L8 note), and a layer is not an erf width | keep, with the qualifier "sigma of a single-interface erf model; an interfacial-layer model must be converted and stated" (A13-m2) |
| `cross_section_tem_profile` -> w_v, w_i | YES as a projected (through-foil) average profile, which is close to the laterally averaged profile of the model. But HRTEM phase-contrast profiles depend on defocus (Fresnel fringes), and HAADF/EELS/EDX profiles are convolved with the probe and with beam spreading (DERIVED_HERE) | keep, with the qualifier "erf sigma after deconvolution of the probe or defocus; state the signal (HAADF, EELS, EDX; not an HRTEM profile at unknown defocus)" (A13-m2) |
| `afm_surface` -> w_v | YES as topography. For a Gaussian height distribution the laterally averaged profile is an erf with sigma = the rms height (DERIVED_HERE). The rms depends on the scan size and the tip, and AFM sees the topmost surface (contamination included: AZUMA2007, 0.1-0.2 nm hydrocarbon, L7 note), not a potential grading | keep, with the qualifier "rms height over a stated scan size" (A13-m2) |
| ellipsometry refused for w_v, w_i | correct | keep |

## Findings

### MAJOR

**A13-M1. Three allowlist ids admit measurements of another quantity, and docs/06 item 12 offers
them to the laboratory as acceptable. A comparison run can then carry a value of the wrong
quantity labelled PROJECT_INPUT "measured".**

Where: `pipeline/config.py:1062-1088` (`MEASUREMENT_METHODS`); docs/06 item 12 (i) and (ii); B43
("V_ox: ... RHEED, convergent-beam or reflection rocking-curve fit"; "V'_ox: ... energy-filtered
transmission or reflection intensity ratio").

* (a) `cbed_rocking_curve_fit` for V_real and `amorphous_si_potential`. An amorphous layer has no
  Bragg disks. V_0 does not enter the intensities of transmission diffraction to first order. CBED
  gives V_g and absorption of a crystal (VOSS80). An honest supplier cannot produce this
  measurement. Anything supplied under this id would be the Si crystal's value, or a crystalline
  SiO2 polymorph's, whose density differs.
* (b) `energy_filtered_intensity_ratio`, "transmission or reflection". A reflection ratio includes
  the crystal's absorption and the surface-plasmon losses (TANISHIRO2003: 1.44 excitations per
  reflection). The project models those in B38, and E9 M1 forbids combining them with V'_ox. A
  V'_ox taken from this ratio double-counts. A plan-view transmission ratio measures the stack.
* (c) `rheed_rocking_curve_fit` and `reflection_rocking_curve_fit`. The V0 that a rocking-curve
  analysis normally returns is the crystal's (the Bragg refraction shift). The oxide's potential
  enters only in correlation with its thickness and grading. A laboratory following docs/06 would
  most likely supply the Si crystal's V0 (about 12-14 V) as V_ox.

Why it matters: the allowlist was introduced (A12-M1, decision 1) to keep non-measurements from
being labelled measured. These three ids let a genuine measurement of a DIFFERENT quantity be
labelled a measurement of V_ox or V'_ox. This happens in the lab-facing text, not through evasion.

Reproduction: `test_oxide_pipeline_a12_fixes.py:108-113` pins the table (the ids and their
parameters). The mutation probe O3 (removing the cbed id) is in the D3 table below.

Fix (small, text and table only):
* remove `cbed_rocking_curve_fit` for both parameters;
* restrict `energy_filtered_intensity_ratio` to the log-ratio of the oxide itself, or fold it into
  the EELS id, and drop "reflection";
* merge the two rocking-curve ids into one, with the overlayer-fit qualifier of the table above,
  or remove it;
* remove the rocking-curve ids for V_a;
* update docs/06 (i)-(ii), B43 and the pinned test.

### minor

**A13-m1. The a-Si potential record: one method for two quantities, taken from the V_ox list.**
* `amorphous_si_potential` labels V_a and V'_a together (`OXIDE_LABEL_VALUES`).
* In a comparison run its only admissible label is PROJECT_INPUT: B41 is refused there, and B43
  does not cover the a-Si potentials (`config.py` label rules).
* V'_a = 0 needs ASSUMPTION (`oxide.py:447-449`). So V'_a > 0 must be "measured".
* The record has one method, from the V_ox list (`MEASUREMENT_METHODS`: holography, rocking
  curves, other). The method for an absorption, EELS, is admissible only through
  `other_measurement`. A truthful record of a holography V_a and an EELS V'_a cannot be written
  with a listed id.

Fix: either one record per key (amorphous_si_V_real, amorphous_si_V_imag), with the V_ox list and
the V'_ox list respectively, or admit the V'_ox ids for `amorphous_si_potential` and let the record
state one method per key. B43's "whose method ids are those of V_ox" changes accordingly.

**A13-m2. The width ids and the EELS id need qualifiers (the table above).** Each is physically
able, but the quantity has to match the model's definition:
* an erf sigma of a single-interface profile (XRR interfacial-layer models are not one);
* deconvolved of the probe or defocus (cross-section);
* the rms height over a stated scan size (AFM);
* lambda on the oxide itself, at a stated beam energy and collection angle (EELS).

These are sentences in docs/06 item 12 (iii)-(iv) and B43; the gate cannot check them.

### note

* **A13-n1. The quoted Monte Carlo range is not a bound.**
  * "95.27-95.64 %" (X7 report and commit message) covers three chosen scenarios.
  * X7's own output prints a fourth, 97.76 %.
  * I find 94.87 % (the minimum of the one-sided scan) and 94.73 % (clipped normal).
  * docs/06 and B7 quote only "about 95 % coverage for a normally distributed depth", which holds.
* **A13-n2. The independence of t and rho is not stated in docs/06 or B7.**
  * The code states it (`combination`: "first-order propagation of independent quantities").
  * D1 part C (a-Si 5 +- 0.5 A): r(t, rho) = -0.5: 97.29 %; +0.5: 93.39 %; +0.9: 91.72 %; +1.0:
    91.33 % (analytic 91.30 %).
  * A thickness and density from one fit (XRR, ellipsometry) are usually anti-correlated, because
    the areal density rho t is better determined. That is conservative (DERIVED_HERE).
  * Add "independent" to the docs/06 and B7 sentence.
* **A13-n3. The wording of the bound.** docs/06 says "Each uncertainty must move the consumed
  depth by less than two layers", and B7 has the same. The code bounds the interval half-width
  k u (`oxide.py:689-698`), so a STANDARD uncertainty must move the depth by less than one layer
  (u_t < 3.0752 A at 2 nm, not 6.15 A; x7 output, section "A12 n1"). Write "each interval
  half-width (2 u for a standard uncertainty) must move ...".
* **A13-n4. "the 2.0 nm demo record" (docs/06; B12 "for the 2.0 nm demo record").** The runs of
  `x7_parity_variants.py` (lines 7-9, 39-45) used a FABRICATED TEST record: the demo's 2.0 nm and
  2.20 g/cm^3, PROJECT_INPUT labels, half-widths 1 A, 0.05 g/cm^3 and 0.1 A. The B41 demo record
  itself refuses uncertainties and the parity key. Write "a TEST record with the 2.0 nm demo
  values".
* **A13-n5.** docs/06 item 12 cites `tools/review/x6/x6_oxide_numbers_output.txt` for 0.3252,
  0.1478 and 0.7365. They are there (lines 4-6). That file's standard-uncertainty lines are
  historical (X6's box), as the commit message states; the docs cite x7 for the example.
  Acceptable.

## Question 3: reversions and the B41 demo (D3, D4)

D3 (`SP/a13/d3_mutate.py`; outputs `d3_mutate.out`, `d3b_mutate.out`):
* Each copy of `reflection_holo/`, `tests/`, `configs/`, `tools/` and `pyproject.toml` is a
  throw-away git repository, deleted after its run.
* The runs use X7's 9 test files.
* Each copy imported its own package: the printed `reflection_holo/__init__.py` lies in
  `SP/a13/mut/<name>/`.
* The replacement texts are my own, not X7's.

| mine | reverts (X7 id) | my replacement | A13 result | X7 result |
|---|---|---|---|---|
| Z0 | control | none | 883 passed | 883 passed |
| Z1 | W24, box for standard | the quadrature lines replaced by the corner formula f_lo (t - h_t) + t_a - h_a,lo and f_hi (t + h_t) + t_a + h_a | 17 failed | 17 failed |
| Z2 | W25, a-Si symmetric below | `ha_lo = ha if kind == 'standard' else min(ha, t_a)` | 17 failed | 17 failed |
| Z3 | W28, depth bound off | `bound = 1.0e6 * q` | 12 failed | 12 failed |
| Z4 | W2, per-parameter check off | `if parameter not in OXIDE_RECORDED_PARAMETERS:` | 34 failed | 34 failed |
| Z5 | W20, date floor off | `MEASUREMENT_DATE_FLOOR = _dt.date(1, 1, 1)` | 5 failed | 5 failed |
| O1 (own) | k = 1.96 instead of 2 | `STANDARD_COVERAGE_FACTOR = 1.96` | 22 failed | - |
| O2 (own) | EELS also allowed for the a-Si potential (A13-m1 edit) | table entry | 1 failed (`test_the_allowlist_is_the_decided_table`) | - |
| O3 (own) | cbed id removed (A13-M1 edit) | table entry deleted | 1 failed (the same test), 877 passed (5 parametrised cbed cases no longer collected) | - |

All five reproduced reversions fail tests, with X7's counts. O2 and O3 show that the recommended
table edits cost one pinned test each, and nothing else in these 9 files.

D4 (`SP/a13/d4_bitid.py`, my own script; output `d4_bitid.out`). Geometric `oxide_2p0nm` at
0c5bba3, 4.0 s:

    vs X7:   26 vs 26 arrays; byte-identical 26
    vs A12:  26 vs 26 arrays; byte-identical 26      (A12's run of 33fd484)
    vs X6:   26 vs 26 arrays; byte-identical 26
    vs A10b: 26 vs 26 arrays; byte-identical 26
    example exit_psi_r0: shape (1031, 128) complex128; max|diff| vs A10b 0.0
    item-12 record vs X7: keys differing []; vs X6: ['measurement_rule'] (the allowlist text)
    spec_sha256 equal X6: True 094102edc907

The multislice demo was NOT RUN by me (X7's saved output: 26 of 26).

## Question 4: rows B7, B12, B43 and docs/06 item 12 (committed text)

| quoted (where) | printed by | verdict |
|---|---|---|
| 0.3252 layer/A, 0.1478 per 0.05 g/cm^3, 0.7365 layer/A (docs/06) | x6 output, lines 4-6; x7 output, section 2 | OK; D1 recomputes them |
| "1 A, 0.05 g/cm^3 and 0.1 A as standard uncertainties admit the counts 6 and 7" (docs/06) | x7 output, section 3 | OK; D1: 5.789-7.233 -> [6, 7] |
| "combined in quadrature ... +- 2 combined standard uncertainties, about 95 % coverage for a normally distributed depth" (docs/06, B7) | code; x7 output (95.45 %) | OK. Independence not stated (A13-n2) |
| a-Si "one-sided below ... a detection limit given as a standard uncertainty enters there as twice its value" (docs/06) | code `oxide.py:700-710` | OK |
| "half-widths are taken as their worst case (the linear sum)" (docs/06, B7) | code | OK; exact (D1) |
| "Each uncertainty must move the consumed depth by less than two layers (a/2 = 2.7155 A); a larger one would admit more than two counts, which is refused anyway" (docs/06; B7 likewise) | x7 output, line 1 (2.7155); code | the claim holds for the interval half-width (D1 part D: 0 of 76 944). The wording is loose for standard uncertainties (A13-n3) |
| "records which of the two is the nearest count" (docs/06, B7, B12) | code `config.py:1944`; x7 output, section "A12 m3" ('upper') | OK |
| "the geometric engine gave identical results for both runs of the 2.0 nm demo record" (docs/06); "26 of 26 ... 5 of 26 ... 0.795 against 0.619 ... 1.355 A" (B12) | x7_parity_variants_output.txt | numbers OK; "demo record" is a TEST record (A13-n4) |
| "at most 1.5 a/4 = 2.0366 A (2.0 nm, lower variant: +0.6838 A) ... nearest-count variant stays within a/8 (2.0 nm, upper: -0.6739 A)" (B12) | x7 output, section "A12 m3"; x6 output, line 1 | OK |
| the allowlist ids per parameter (docs/06 (i)-(iv), B43) | code `config.py:1066-1092` | the text matches the code; the physics of three ids does not hold (A13-M1), and qualifiers are missing (A13-m2) |
| "not before 1990-01-01 and not after the date of this supply" (docs/06); "between 1990-01-01 and the item-12 supply date" (B7, B43) | code `config.py:1095`, `1481-1490` | OK |
| "a fabricated but well-formed record passes" (B7, B43) | accepted limit | OK, not overstated |
| "B43 does not cover the a-Si potentials ... whose method ids are those of V_ox" (B43) | code | TRUE, but see A13-m1 (V'_a) |

Nothing in B7, B12, B43 or docs/06 item 12 overstates a number. The overstatement is in the physics
of three allowlist ids (A13-M1).

## Command log

PY = `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=. venv/bin/python` from
/home/user/Holography.

| # | command | purpose | result |
|---|---|---|---|
| C0 | `git status`, `git log --oneline -5`, `git show --stat 0c5bba3`, `git rev-parse HEAD`, `git show 0c5bba3 -- docs/...` | scope | HEAD 0c5bba3; tree clean before this report |
| D1 | `PY SP/a13/d1_interval.py > d1_interval.out` | question 1 | first run FAILED (my script: `np.trapz` is absent in this numpy); fixed to `np.trapezoid` with scipy's erf; second run exit 0, 10.6 s |
| D3 | `OMP_NUM_THREADS=1 venv/bin/python SP/a13/d3_mutate.py > d3_mutate.out` (background) | reversions | Z0-Z5 and O1 as tabled. The run STOPPED at O2 (my anchor text did not match; SystemExit); O3 not reached |
| D3b | the same script with O2's anchor corrected: `... d3_mutate.py O2_eels_for_asi_potential O3_cbed_removed > d3b_mutate.out` | own table probes | exit 0; 1 failed each |
| D4 | `PY SP/a13/d4_bitid.py > d4_bitid.out` | B41 bit-identity | 26 of 26 against X7, A12, X6 and A10b |
| C1 | `git status --short`; `git status --short outputs/` | nothing written | only this report; outputs/ empty |

Read-only commands (grep, sed -n, awk, cat, ls, a python extraction of bib notes, /proc/loadavg)
are not listed one by one. `rm -rf SP/a13/mut/O2_eels_for_asi_potential` removed the stale scratch
copy of the stopped run.

## NOT RUN

* The full test suite (it was running concurrently; not my run). Only X7's 9 oxide test files were
  run, in the mutated copies (control 883 passed).
* 34 of X7's 39 reversions; `tools/review/x7/mutate_x7.py` itself.
* The multislice B41 demo bit-identity; the parity-variant runs (`x7_parity_variants.py`); the
  rerun of `x7_oxide_numbers.py`. Its numbers were recomputed independently in D1 instead.
* The physical effect of the non-nearest variant (accepted limit).
* The papers cited in question 2: only their docs/references.bib notes were read. The physics
  statements marked DERIVED_HERE are my reasoning and are not computed. In particular, I did not
  compute the sensitivity of a RHEED rocking curve to V_ox for a 2 nm layer.
* Probes of the record gate's text refusals (out of scope: accepted limits).

## Verdict

**The interval arithmetic, the bound and the guards are final.**
* The quadrature and the one-sided a-Si rule are correct, and the linear box is exact.
* "About 95 %" is an honest statement.
* The a/2 bound never refuses a record that could otherwise run.
* The reversions are caught.
* The B41 demo path is bitwise unchanged.

**The oxide item-12 policy can be called final for comparison runs only after the allowlist
edits of A13-M1:**
* remove `cbed_rocking_curve_fit`;
* restrict `energy_filtered_intensity_ratio` to the oxide itself, without "reflection";
* merge the rocking-curve ids with the overlayer-fit qualifier, or remove them, and remove them
  for the a-Si potential;
* update docs/06 (i)-(ii), B43 and the one pinned test (O2 and O3 show that is the whole test cost).

With those edits, and preferably A13-m1 (a separate method for V'_a) and A13-m2 (the qualifiers
in docs/06), I have no remaining objection. Notes n1-n5 are wording.
