# E6 - Adversarial review of the literature reports L6 (sourced Si parameters) and L7 (surface realism)

Reviewer: agent E6, 2026-09-23 23:49 UTC to 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`.
Status: FINAL (written incrementally; the verdict table (section 7), the CONFIRM list (section 8) and
the DO-NOT-ADOPT list (section 9) are the final state).

Scope: `docs/agent_reports/L6_sourced_si_parameters.md` (669 lines) and
`docs/agent_reports/L7_surface_realism.md` (576 lines), with the B4 merge
(`docs/agent_reports/B4_verification_log.md`, `docs/references.bib`, 218 entries). Neither report and no
other repository file was edited by E6. Files written by E6: this report, `tools/review/e6_recompute.py`
and its saved output `tools/review/e6_recompute_output.txt`. Nothing committed or pushed by E6 (the
orchestrator's snapshot commits 2da0216 and c7cccc9 picked up in-progress copies).

Severity scale: BLOCKER (must be fixed before anything is adopted), MAJOR (must be fixed or re-worded
before the affected item is adopted), MINOR (fix when adopting), NIT.

**Result in one paragraph.** No BLOCKER. Every sampled SECTION_READ value was found in the source at
the stated locator (section 1), and every derived number recomputes (section 2), with two exceptions
of wording (NITs n1, n2). The TDS absorptive potential reproduces exactly with the published Thomas et
al. code and to within 0.2 % with an independent E6 implementation (section 3). The five MAJOR findings
concern what the reports did NOT carry from sources that are in the project's own reading set:
Tanishiro 2003 (read by L7) gives a MEASURED 200 kV surface-plasmon excitation number (1.44 at 0.8
deg) and shows that plasmon-loss electrons remain partly coherent, which overturns L6's "unsourced at
200 keV" extrapolation (0.7 per reflection; amplitude factor 0.70 becomes 0.54) and L6's statement
that a plasmon-loss electron is lost for the sideband (M1, M2); the uniform bulk electronic absorption
of 0.65 V is an upper bound for the specular beam, not a value (M3); L7's overlayer formula is right
but misses that a buried step under a planarising overlayer changes the phase-to-height conversion by
up to 14 % (M4); and "Si(001) step phases have not been reported" must be scoped to the sources
searched (M5).

## 0. Log and evidence

* Read in full: L6, L7, B4 log; `docs/model_assumptions.md` (A7, B1, B3, B6, B7, B26, B30, B32),
  `docs/06_project_inputs_required.md`, `docs/physics_conventions.md`, `docs/02`, `docs/00` (lines
  84-116), `docs/05` (lines 150-160, 205-214, 345-350), `docs/03` (212-220), `docs/07` (upload list),
  `docs/source_map.tsv` (SM04, SM13, SM17, SM22); engine `reflection_holo/forward/multislice/potentials.py`
  (transmission `t = exp(+i sigma V_p) exp(-sigma W dz)`, `PhysicalAbsorption` = `V (1 + i ratio)`,
  `FrozenPhonons` = independent Gaussian per axis, intensities averaged after squaring); H2 section 6
  and H5 m5.
* Provenance: SHA-256 of every downloaded file for which the reports print a hash was recomputed
  (`scratchpad/e6_allhash.txt`). All 29 hashes printed in L6 match (27 downloaded or generated files and
  the two Crossref JSON records of table 0b). Of the 24 abbreviated hashes in L7, 16 match and 8 do not
  (finding m1).
* Sources re-read by E6 (text layer with PyMuPDF 1.28.2 where usable; page images rendered at 110-300
  dpi and read visually where not): Heacock et al. arXiv:2103.05428v3 (PDF pp. 3, 6, 25, 31-33);
  Hajek and Rusz arXiv:2608.24679v1 (pp. 2, 3, 5, 6, 10); Dr. Probe preprint (pp. 9-11) and `celslc`
  page; muSTEM v5.3 manual (pp. 5, 15, 16); Thomas, Cleverley, Beanland 2024 (XML text; Eqs. (1)-(2) as
  printed images); Mendis 2024 (XML sec. 3); Ni, Busch, Zuo 2026 (Tables 1-3); Voss, Lehmpfuhl, Smith
  1980 (pp. 973-975, 981-983); Moon 1972 (pp. 393-394); Horio et al. 2014 (pp. 380-386); Horio et al.
  2022 (abstract, pp. 79, 82); Minami et al. 2008 (Eq. (1), Table I); Ramstad, Brocks, Kelly 1995
  (Tables III and IV entry by entry on rendered images, Figs. 16 and 18, pp. 14506, 14516-14518, 14520);
  Zandvliet 2000 (pp. 594-597, 600-601, Tables I-II); Morita et al. 1990 (p. 1273, rendered);
  Uzuhashi and Ohkubo 2024 AM (pp. 3-5, 7); Pastewka et al. 2009 preprint (abstract, sec. 6); Korobtsov
  et al. 2007 (pp. 46, 48); Yagi, Tanishiro, Takayanagi 1986 (p. 1048); Tanishiro 2003 (pp. 166, 167,
  170, 171, rendered at 170-300 dpi); JPS abstracts J-a (pp. 451-452), J-b (p. 439), J-e (p. 852).
* Independent searches (anonymous, no personal data): 8 Crossref `query.bibliographic` queries on
  reflection electron holography with Si(001), silicon, step and phase, 7 answered and 1 returned an
  empty body (JSON cached in `scratchpad/e6/cr_*.json`, `cr2_*.json`); arXiv full-text search for the exact phrase "reflection
  electron holography" (0 results); OpenAlex search refused ("Anonymous search is paused",
  2026-09-24).
* Script: `venv/bin/python tools/review/e6_recompute.py <scratchpad>/l6/calc/main_scattering_function.py`
  (sha256 8c70fa91...), output `tools/review/e6_recompute_output.txt` (sha256 97063fea..., 192 lines).
  Quoted numbers below are lines of that output (label REPRODUCED).

## 1. SECTION_READ claims re-read by E6 (sample)

| claim (report, locator) | E6 reading of the source | verdict |
|---|---|---|
| Heacock: B = 0.4761(17) A^2 at 295.5 K (L6 2.2, arXiv v3 p. 6) | PDF p. 6: "our results are B = 0.4761(17) A2 and <r_n^2> = -0.1101(89) fm2 with a correlation coefficient of -0.94"; B_BvK = 0.4725(17) A^2 "when scaled to 295.5 K" | CONFIRMED |
| Heacock: dB/dT = 0.0014 A^2/K (PDF p. 25) | "scaled to 295.5 K using the BvK model predicted slope of B at room temperature dB/dT = 0.0014 A2 K-1 at 295.5 K" | CONFIRMED |
| Heacock: 0.4767(6) (p. 33), 0.4714(57) (p. 31), <u^2> = B/(8 pi^2), W = BQ^2/(16 pi^2) (p. 3) | all as quoted | CONFIRMED |
| Hajek and Rusz p. 2: no imaginary part in FPM; absorption after averaging; Eqs. (4)-(6); both FPM (Einstein) and CAP need B [15] | verbatim as quoted; [15] = Peng, Ren, Dudarev, Whelan, Acta Cryst. A 52, 257 (1996) | CONFIRMED |
| Hajek and Rusz pp. 5-6, 10: ~1e-3 I0 at the central beam (diamond), 10^-4.5 I0 with a 110 mrad kernel, validity "light-element systems, moderate specimen thickness, and large detector collection angles" | as quoted | CONFIRMED (and see m10: p. 3 and the Fig. 3 caption on p. 6 say more) |
| Dr. Probe preprint p. 9 (absorptive factors with DW damping; TDS "without Debye-Waller factors in a different approach"); p. 11 (<u_s^2> = U = B/(8 pi^2), per axis) | verbatim; p. 9 also defines <u_s^2> = <u_x^2> = <u_y^2> = <u_z^2> | CONFIRMED |
| Dr. Probe celslc page: "Typical values are on the range from 0.01 to 0.20"; Hall and Hirsch printed with "(1957)" | verbatim; the 1957 typo is on the page, as L6 says | CONFIRMED |
| muSTEM manual sec. 1 (p. 5) "one of two models"; sec. 3.8.2 (p. 16) "numerically equivalent", "not thermally smeared out ... quite sharp" | verbatim | CONFIRMED (p. 16 also: "More than 100 passes may be required for the elastic contribution to reach convergence", not carried by L6; m10) |
| Thomas et al. Eq. (1), Eq. (2), "gamma f + i gamma f'", negative beta f' set to zero, 13 B values, "100 kV electrons" statement about Peng 1996a,b, alpha ~ 0.1 statement | Eq. (2) as printed: f'(s,B) = (2h/(beta m0 c)) Int d^2s' f(abs(s/2+s')) f(abs(s/2-s')) {1 - exp[-2B(s'^2 - s^2/4)]}; the rest verbatim | CONFIRMED |
| Mendis 2024 sec. 3: ion-beam polished Si [110], 200 kV JEOL 2100F; ~1990 A for ~830 A (Malis); 1050 A plasmon MFP (Mendis 2019); 7724 A; 0.078 A and B = 0.12 A^2; theta_E = 0.04 mrad; theta_c = 19.1 mrad | verbatim | CONFIRMED (1050 A remains a statement about Mendis 2019: UNVERIFIED, as L6 labels it) |
| Ni et al. 2026 Tables 1-3 (U_111, U'_111, U_222) | 0.04731/0.00086/0.00093 (Extal), 0.04735/0.00079/0.00092 (PyExtal), 200 kV; Table 2 and Table 3 values as L6 | CONFIRMED |
| Voss 1980: 100 keV (p. 975); Eq. (3) "due to Humphreys and Hirsch" (p. 974); B = 0.004, C = 0.0003, "V_000^im = 0.61 Volt" (p. 981); Table 5 (p. 983); Table 1 (p. 982); B = 0.4613 at 293.2 K | all as L6 transcribes, including the Kreutle-Meyer-Ehmsen (500 K) and Radi columns | CONFIRMED |
| Moon 1972: 40 keV, V0 = 12 V "to provide best agreement with the 555 peak", V_imag = V_real/8.0; Debye parameter 0.5 A^2 | verbatim (p. 393 caption, p. 394) | CONFIRMED |
| Horio 2014: alpha = 18.1 deg, a_z - b_z = 0.71 A, Table I rows, 10 % imaginary potential, 0.07 A at RT (Debye temperature 580 K, Radi), V0 = 12 eV, 004/006/008 at 1.66/3.34/4.79 deg, 880 K 0.43 A 10.9 deg, 1031 K 0.29 A 7.4 deg, intensities summed incoherently | all verbatim (Table I on p. 383; sec. V on p. 385); asin(0.71/2.28) = 18.14 deg (REPRODUCED) | CONFIRMED |
| Horio 2022 Eq. (1) and beta = 0.66, 0.71 ("~70 % of Lucas' theoretical value"); V000 = 13.9 eV corrected to 12 eV; 10 % imaginary; interaction thickness 3.6 A | verbatim; the 3.6 A is derived there with beta = 0.7 and an IMFP of 180 A at 10 keV (p. 82) | CONFIRMED (for 10 keV; see M1 for 200 keV) |
| Minami 2008 Eq. (1) and Table I (U_TDS 0.37 V, B 0.38 A^2, U_el 0.01/1.28 V; adatoms 0.80 V, 3.00 A^2, 0.01/1.60 V) | verbatim | CONFIRMED |
| Ramstad, Brocks, Kelly 1995 Tables III and IV as transcribed in L7 1.4 | all 40 Table III and 120 Table IV entries checked on the rendered pages 14516-14517: no transcription error; caption R_klm = (k sqrt2, l sqrt2, m) a/4, a = 5.431 A; y displacements "only of order 10^-5 A"; bond lengths and angles of Fig. 18 and text (2.23, 2.26, 2.28, 2.29 A; 18.3, 18.9/19.3, 18.7/18.9 deg); Fig. 16 energies; "should only be compared with geometries determined experimentally at low temperature" (p. 14518) | CONFIRMED |
| Zandvliet 2000: SA/SB (p. 594); "L = d/tan(theta)" (p. 595); 1.5 deg onset, ~100 % at 5-6 deg (p. 594); 0.03 deg, 0.03-0.1 deg, 0.1 to 1.5-2 deg regimes (p. 600); ~2 deg model; single below 1 deg, double above 4 deg, coexistence 1-4 deg (p. 601); freeze-in 750-875 K (p. 596); Tables I and II | all verbatim | CONFIRMED |
| Morita 1990 p. 1273: 23.7 deg C, 42 %, 1.2 % H2O; 5.4 -> 7.6 A; initial 4.4/1.9/2.3 A; Table I 6.7, 1.7, 1.9 A; thermal-oxide-equivalent convention | verbatim (rendered page) | CONFIRMED (a caveat on the same page is missing in L7; m7) |
| Uzuhashi 2024: ~22/~7/~4/~1 nm at 30/8/5/2 keV; 89.5 deg in SRIM; ~22 to ~29 nm distortion; ~75 % (Si); "irrespective of the beam current" | verbatim (pp. 3-5, 7) | CONFIRMED |
| Pastewka 2009 preprint: 20-30 nm at 30 keV; linear in energy; "at 80 deg a variation of +-5 deg can lead to a change in thickness of +-50 %" | verbatim | CONFIRMED (its transfer to D2 is m9) |
| Korobtsov 2007: ~0.8 nm chemical oxide; "intense background from amorphous structure of SiO2 layer and weak reflections from 1x1 structure" | verbatim (p. 46) | CONFIRMED (the 710 deg C context is m8) |
| Yagi et al. 1986 p. 1048 (ion irradiation, REM image lost, recovery from steps) | as L7 quotes | CONFIRMED |
| Shirasawa, Mizuno, Tochihara 2006 JPS (R4, p. 865): apparent p(2x1) at RT from frequent buckling reversal; LEED I-V at 80 K to 8 layers; transition 205 +- 3 K (Si), 276 +- 6 K (Ge), 2-D Ising | verbatim (rendered page) | CONFIRMED |
| Tanishiro 2003: 200 kV, 10^-9 Pa, Si(111)7x7 at 750 deg C, 0.8 deg, (444) (p. 167); R2 arrangement and 7 pi (p. 170); 60/80/30-40 nm; visibilities 0.4/0.3/0.1/<0.1; theta_E = 3e-5 rad (pp. 170-171) | all present; the azimuth is printed [1-10], not [110] (m2) | CONFIRMED except the azimuth transcription |
| J-a (Osakabe 1990 JPS, pp. 451-452): arrangement (reference set on a defect-free region), Mach-Zehnder reconstruction, coherence 3 um/1 um, Delta_phi = 2 K_perp Delta_z, sqrt((2 pi n)^2 - (2kd)^2 V0/E), Pt(111) 2.3 A step ~0.5 lambda, 10^-6 rad, integer part not observed, refs [2] = P01, [4] = Banzhof EUREM 1988 p. 263 | all verbatim | CONFIRMED |
| J-b (p. 439): Delta_phi = 2K Delta_z sin(theta); reference from a defect-free region; b = a/2[101]; one fringe = 0.5 A | verbatim | CONFIRMED |
| J-e (p. 852): 200 kV omega-filter FEG; Si surface 11.3 eV; 10 eV window; one-plasmon interference distance ~45 nm | verbatim; item [2] also states that holograms formed with electrons that excited one or two surface plasmons show fringes and that these electrons are spatially coherent (not carried by L6; M2) | CONFIRMED |

## 2. Recomputation (tools/review/e6_recompute_output.txt; label REPRODUCED)

| quantity (report) | report value | E6 value | status |
|---|---|---|---|
| sigma(200 keV) (L6 1.5) | 7.288401e-4 rad/(V A) | 7.2884010e-4 | agrees |
| K = h^2/(2 pi m0 e) (L6 1.5) | 47.87765 V A^2 | 47.87765 | agrees |
| u from B = 0.4761 A^2 (L6 2.3) | 0.07765 A (+-0.00014) | 0.07765 (+-0.00014) | agrees |
| A7 0.076 A low in B (L6 2.3, 7.1) | 4.2 % in B, 2.1 % in u | 4.21 %, 2.13 % | agrees |
| A7 vs BvK in u (L6 2.3) | 1.5 % | 1.40 % (293 K) or 1.76 % (295.5 K) | NIT n1 |
| 8 pi^2 x 0.005941 + 2.5 K x 0.0014 (L6 2.2) | 0.4691 -> 0.4726 A^2 | 0.46908 -> 0.47258 | agrees |
| (008) DW amplitude A7 / BvK / Heacock (L6 7.1) | 0.7808 / 0.7739 / 0.7724 | 0.7808 / 0.7739 / 0.7724 (-1.08 %) | agrees |
| 10 K at 0.0014 A^2/K (L6 7.1) | 3 % | 2.94 % | agrees |
| Mendis convention (L6 1.3b) | 0.120 vs 0.480 A^2 | 0.1201 vs 0.4804 | agrees |
| V'(el) = 1/(2 sigma Lambda) (L6 1.5, 7.2) | 0.653 V (1050 A), 0.827 V (830 A) | 0.6534, 0.8265 V | agrees |
| equivalent proportional ratio (L6 7.2) | 0.047 | 0.0470 | agrees |
| TDS attenuation length (L6 1.5) | about 7700 A | 7650 A (B = 0.4761), 7685 A (B = 0.4725) with the published code; 7637 A independent | agrees |
| TDS f'/f and V0'(TDS) (L6 1.5) | see section 3 | see section 3 | agrees |
| 0.089 V scaled to 10 keV (L6 1.6) | 0.32 V | 0.317 V | agrees |
| TDS (111) at 100 keV; ratio to Voss (L6 1.7) | 0.0139; 2.3 | 0.0140; 2.30 | agrees |
| Voss V'_g/abs(V_g) 111, 220, 311, 004 (L6 1.7) | 0.0061, 0.0089, 0.0100, 0.0104 | same | agrees |
| Voss 0.61 V / scaled TDS (L6 1.7) | 5.4 | 5.40 | agrees |
| Ni U'/U ratios (L6 1.3c) | 0.0167, 0.0182; 0.0082, 0.0168, 0.0123 | same | agrees |
| "scatters by a factor of about 3 once scaled to a common energy" (L6 1.7, 7.2.4) | about 3 | 2.76-3.00 unscaled; 3.49-3.81 scaled by the 1/beta TDS law | MINOR m5 |
| Lucas prefactor, n at 16.13 mrad (L6 1.6) | 0.01649; 0.67-0.73; exp(-0.7) = 0.50; amplitude 0.70 | 0.01649; 0.674-0.725; 0.48-0.51; 0.70-0.71 | arithmetic agrees; the input is superseded (M1) |
| IAM minus bonded/measured MIP (L6 3.2) | 1.2-1.9 V | 1.17-1.96 V (against 12.0-12.53 V); up to 2.46 V against 11.5 V | NIT n2 |
| Kirkland minus 12.53 / 12.0 V (L6 7.3) | 1.4-1.9 V | 1.373 / 1.903 V | agrees |
| B1 sensitivity for 0.5 V; 0.48 V x 1.07 %/V (L6 7.3) | -0.17 rad; about 0.5 % | -0.170 rad; 0.51 % | agrees |
| overlayer phase per A per V (L7 5, 6.2) | 0.0903 rad A^-1 V^-1 | 0.09035 | agrees |
| ... at V_ov = 10 V, projected / refracted (L7 6.2) | about 0.9 / 0.86 rad per A | 0.9035 / 0.8580 | agrees (formula scope: M4) |
| path factor 2/sin(theta) (L7 2.5) | 124 | 123.96 | agrees |
| geometric step phases a/4, a/2 at 16.13 mrad (L7 6.2) | 10.98, 21.95 rad | 10.976, 21.952 | agrees |
| Tanishiro check (L7 4.1) | 6.98 pi at 0.8 deg; 13.64 mrad; 6.82 pi; 8 pi | 6.983 pi; 13.641 mrad; 6.822 pi (0.75-0.85 deg gives 6.55-7.42 pi) | agrees |
| GaAs d_880 (L7 3.3) | 0.4997 A | 0.4997 | agrees |
| R1 dimers (L7 1.3) | c(4x2) 2.287 A, 18.7 deg; 2.288 A, 18.9 deg; p(2x1)s 2.230 A; p(2x1)a 2.258 A, 18.3 deg | 2.287/18.72; 2.288/18.95; 2.230; 2.258/18.27 (p(2x2): 2.283/18.86 and 2.283/19.26) | agrees |
| terrace widths L = d/tan(theta) (L7 1.3) | 1555.9, 777.9, 311.2, 155.6, 77.8 A; 38.8 A (a/2 at 4 deg) | same; 38.83 | agrees |
| a/4 (L7 table 5) | 1.3575 A | 1.35775 A (a = 5.431), 1.35773 A (B2) | NIT n3 |
| densities (L7 2.4, 5) | 2.329; 2.28-2.31; 2.285-2.287 g/cm^3 | 2.3291; 2.2825-2.3058; 2.2852 (4.90e22) to 2.2871 (1.8 %) | agrees |

## 3. TDS absorptive potential of Si at 200 keV (task item 3)

Two independent routes (output section D):

1. **Black box**: the unmodified supplementary module of Thomas et al. (`l6/calc/main_scattering_function.py`,
   sha256 bb1cf9f5..., module `V = 200000`) imported and called as `main(s, B, 14)`. It reproduces every
   entry of L6's table 1.5 to the last printed digit, e.g. B = 0.4761 A^2: f'/f = 0.00643, 0.01103,
   0.01816, 0.02740, 0.03977, 0.05352 at 000, 111, 022, 004, 044, 008; V0'(TDS) = 0.0897 V;
   1/(2 sigma V0') = 7650 A. REPRODUCED.
2. **Independent E6 quadrature** of Eq. (2) as printed (2-D Gauss-Legendre in polar coordinates to
   s' = 60 A^-1), with abTEM 1.0.10's Lobato and Kirkland Si scattering factors, not Thomas's
   parameterisation: B = 0.4761 A^2, Lobato: 0.00644, 0.01104, 0.01818, 0.02745, 0.03983, 0.05358;
   V0'(TDS) = 0.0898 V; 7637 A. Kirkland: 0.00646, 0.01103, 0.01821, 0.02745, 0.03987, 0.05352; 0.0898 V.
   Agreement with route 1 within 0.2 % (the size of the parameterisation's interpolation error that L6
   itself reports). The bookkeeping (gamma, the 2h/(beta m0 c) prefactor, V' = K F'/Omega) was checked
   against the optical theorem: 1/(N sigma_TDS) = 7637 A equals 1/(2 sigma V0') = 7637 A. REPRODUCED.

Verdict: L6's "0.089 V mean, f'/f 0.0064 at g = 0 to 0.053 at (0,0,8)" is CONFIRMED (0.0874-0.0903 V
over B = 0.456-0.480 A^2). L6 quotes these at B = 0.4725 (the BvK value) while recommending B = 0.4761;
at the recommended B the numbers are 0.0897 V, 0.0535 at (008), 7650 A (m4).

## 4. Findings

### MAJOR

**M1. Surface-plasmon loss at 200 keV: L6's "unsourced" extrapolation is contradicted by a 200 kV
measurement in Tanishiro 2003, a source L7 read (L6 1.6, 5, 7.2.5; L7 4.1).**
Quoted (L6 1.6): "At theta = 16.13 mrad that is n_s = 1.02 x beta_corr, i.e. 0.67-0.73 excitations per
reflection ... If it holds at 200 keV, only exp(-0.7) = 0.50 of the specularly reflected electrons
leave without a surface-plasmon loss. The loss happens mostly in the vacuum selvedge (interaction
thickness about 3.6 A at 10 keV, Horio 2022 p. 7) ... it is unsourced at 200 keV." (7.2.5): "about 0.7
excitations per reflection ... reduce the coherent amplitude by about exp(-0.35) = 0.70". L6 1.5 item 5:
"No source on REM/RHEED loss at 200 keV was read here".
Evidence: Tanishiro, Hyomen Kagaku 24, 166 (2003), p. 167, sec. 2 (rendered, read by E6): at 200 kV,
Si(111)7x7 at 750 deg C, [1-10] azimuth, 0.8 deg, (444) nearly specular, EELS of the imaging electrons:
"表面プラズモンの平均励起個数は1.44であった" (the mean number of surface-plasmon excitations was
1.44). Pp. 166-167 (introduction, citing its refs. 4-6): the mean number at the specular spot is nearly
inversely proportional to the vacuum glancing angle and close to the Lucas-Sunjic value; most
excitations occur outside the crystal. P. 170: the decay distance is about v/2 omega, "about 6 nm"
under these conditions, over which the exiting electron (exit angle 1.4e-2 rad) travels 0.4 um; about
90 % of the exit-side excitation happens within about 1 um after exit. Horio 2022 abstract: surface
plasmon excitation shows "a moderate increase under Bragg reflection conditions".
E6 recomputation (output F): Lucas value at 0.8 deg = 1.181, so Tanishiro's 200 kV measurement is 1.22
times Lucas, not 0.66-0.71 times; scaled by 1/sin(theta) to the repository's 16.1347 mrad it is n =
1.25, zero-loss fraction 0.29, elastic amplitude factor 0.54 per reflected wave, and a sideband factor
exp(-n) = 0.29 when both waves are reflected (R2). v/(2 omega_s) = 6.07 nm at 200 keV (1.70 nm at 10
keV); Horio's 3.6 A is a 10 keV quantity.
Consequence: L6's numbers understate the loss by a factor of about 1.8 in n, and "unsourced at 200 keV"
is false for the project's own reading set. The locality argument must also change: with a 6 nm decay
length and a 0.4-1 um path along the surface, an atomic step (1.36-3.14 A) does not change the selvedge
appreciably, whereas nm-scale patterned features within about 1 um along the beam do.
Required correction (proposed wording for 7.2.5): "Surface-plasmon loss, measured at 200 kV: mean 1.44
excitations per specular reflection on Si(111)7x7 at 0.8 deg, (444) (Tanishiro 2003 p. 167,
SECTION_READ), close to the Lucas-Sunjic value and inversely proportional to the vacuum glancing angle
(pp. 166-167). Transferred to Si(001) at 16.13 mrad by 1/sin(theta) (ASSUMPTION: surface, temperature
and Bragg condition differ): about 1.25 excitations, zero-loss fraction about 0.29, elastic amplitude
about 0.54 per reflected wave. Decay distance about 6 nm (p. 170)."

**M2. "A plasmon-loss electron is lost (no longer coherent with the reference wave)" is contradicted
by J-e and Tanishiro 2003 (L6 1.4, basis of 7.2.2).**
Quoted (L6 1.4): "For the hologram sideband a plasmon-loss electron is lost (no longer coherent with the
reference wave) even though it stays inside the 3 mrad aperture ... So for holography the electronic
absorption acts on the object wave as true absorption."
Evidence: J-e (Tanishiro et al., JPS 56(1-4), 852, 2001), item [2]: holograms formed with electrons
that excited one or two surface plasmons show fringes; these inelastic electrons are spatially
coherent; one-plasmon interference distance about 45 nm. Tanishiro 2003, English abstract (p. 166):
"electrons that lost a small amount of energy due to surface plasmon excitation etc. are found to be
still coherent"; p. 170: carrier fringes in the single-plasmon-loss hologram (Fig. 4(c)), "実証している"
(demonstrates) spatial coherence; p. 171: visibility 0.4, 0.3, 0.1 and below 0.1 at 0, 5.6, 11.4 and
12.6 eV loss; maximum hologram width 25 nm at 11.4 eV and 45 nm at 6.4 eV. J-e also notes that in
reflection holography both the object and the reference wave contain loss electrons.
Required correction: "The imaginary potential depletes the ELASTIC wave in either case. Whether the
removed plasmon-loss electrons also leave the sideband depends on the hologram width and on the
object-reference separation: beyond about 25-45 nm they add only background (Tanishiro 2003 p. 171;
J-e), below that they add weak fringes (visibility 0.1 or less for one surface plasmon). PROJECT_INPUT
item 16 decides; the loss-electron contribution is an optics term, not part of item 21." The same
correction applies to docs/02 line 58 context (see section 6).

**M3. The uniform bulk electronic absorption of 0.65 V is an upper bound for the specular beam, not
a value; and L6 is internally inconsistent on its g-dependence (L6 1.5 items 3-4, 7.2.2).**
Quoted (7.2.2): "Add only the electronic (plasmon plus single-electron) absorption, as a spatially
uniform imaginary potential inside the crystal ... Candidate value: V0'(el) = 0.65 V ... Upper variant:
0.83 V". (1.5 item 3): the measured-minus-TDS excess at (111), 0.006-0.007, "falls in" Radi's electronic
range C(el)/V_g = 0.005-0.012.
Evidence: (a) Tanishiro 2003 p. 166: for the specular spot the main inelastic process is surface-plasmon
excitation; the fraction of bulk-plasmon excitation increases away from the diffraction spots and
Kikuchi lines. Horio 2022 abstract: "the main surface plasmon and weak bulk plasmon"; bulk-plasmon
excitation "showed an inverse behavior to the intensity of the specular reflection" (weak at Bragg
peaks). (b) DERIVED_HERE: the bulk-plasmon interaction length v/omega_p is 8.1-8.2 nm at 200 keV (output
H), larger than the amplitude extinction depth at the centre of the (0,0,8) band (24.47 A, report P2
line 146) and comparable to the upper end of the 2-10 nm penetration depths of docs/05:144, so the bulk
excitation rate of the specular beam is reduced below the transmission value that defines Lambda = 1050 A; adding the full bulk term AND a
separate surface-plasmon factor (M1) counts part of the same loss twice. (c) The 1050 A value was
measured in transmission (Mendis 2019 via Mendis 2024 sec. 3, UNVERIFIED). (d) The "upper variant"
(830 A, all inelastic channels) includes localised single-electron and core losses, to which the
delocalisation argument for uniformity does not apply, and 1.5 item 3 uses exactly such a g-dependent
electronic term to explain the (111) data.
Required correction: adopt the uniform term only as a bracket for the in-crystal electronic loss, 0 V
and 0.65 V (ASSUMPTION; 0.65 V stated as an upper bound for the specular beam); keep the surface-plasmon
factor of M1 as the principal electronic loss of the reflected waves; state that electronic V'_g at
g != 0 is neglected. L6's own advice to "run the working condition at two absorption settings" then
becomes the bracket 0 / 0.65 V.

**M4. L7's overlayer formula is right, but its S3 consequences are incomplete and one statement
overstates (L7 5 last row, 6.2 S3, 8).**
Quoted (6.2): "a NON-conformal overlayer ... adds Delta_phi ~ 2 C_E V_ov Delta_t / sin theta = 0.090 rad
per A per volt ... about 0.9 rad per A of thickness change (0.86 rad with the refraction formula) ... An
overlayer that is non-uniform at the angstrom level therefore produces phase changes comparable to the
step phase itself".
Derivation (DERIVED_HERE, output H): for specular reflection the phase at a fixed plane above the
surface is 2 [k_perp (vacuum path) + k'_perp (overlayer path)] + phi_crystal, with k'_perp =
sqrt(k_perp^2 + 2 k sigma V_ov) (parallel wavevector conserved; entrance and exit both counted). A
thickness change Delta_t at the vacuum side over a fixed crystal gives 2 (k'_perp - k_perp) Delta_t =
0.858 rad/A at V_ov = 10 V (1.020 rad/A at 12 V); the projected form 2 sigma V_ov Delta_t / sin(theta)
(0.9035 rad/A) is its small-V_ov limit. So the formula, the in-and-out doubling and the refraction form
are right, under the premise that Delta_t is uniform over the entrance-to-exit distance along the beam
(near a riser the overlayer term is spread along the beam).
What is missing: a crystal step BURIED under a flat-topped (planarising) overlayer is a thickness
change of exactly h, so its phase is 2 k'_perp h, not 2 k_perp h. For the a/4 step at 16.1347 mrad:
10.976 rad (conformal overlayer, or none) -> 12.141 rad (planarising, V_ov = 10 V) -> 12.566 rad = 4.000
pi (planarising, V_ov = 13.903 V, the engine's V0: the internal kinematic value). The spread is 1.59 rad,
0.197 A of apparent height (14 %). Under S3 the phase-to-height conversion therefore depends on the
overlayer's shape and mean inner potential.
What overstates: 0.86-1.02 rad per A of top-surface variation against 8.08 rad per A of crystal
topography (2 k_perp): an angstrom-level top-surface variation mimics 0.11-0.13 A of height; it is
"comparable to the step phase" only after wrapping (the wrap period is 0.777 A), not in magnitude.
Required correction: add the conformal/planarising dichotomy to S3 and to the paper's list; replace
"comparable to the step phase itself" by "each angstrom of overlayer thickness variation at the vacuum
side is read as 0.11-0.13 A of height (V_ov = 10-12 V, placeholder); a planarising overlayer raises the
a/4 phase by up to 1.6 rad (up to 14 %)".

**M5. "Si(001) step phases have not been reported" is an absence claim stated as fact (L7 4.2 answer,
8 fact 5).**
Quoted: "A paper on Si(001) ... must state that Si(001) step phases have not been reported." (8, under
"Facts"): "No Si(001) step phase has been published in any source found."
Evidence: L7 searched J-STAGE, CiNii, Crossref, OpenAlex, Semantic Scholar and L4's graph. Not read:
the bodies of P01, P02, P03, P08, Osakabe 1993 (Ultramicroscopy 48, 483; Surf. Sci. 298, 345), Banzhof
EUREM 1988 p. 263, Suzuki et al. JJAP 40, 2527 (2001), the Osakabe (1995) and Takeguchi (1993) theses,
Herring 1995, and the holography book chapters that E6's Crossref queries return (for example a 1995
workshop volume with chapters by Lichte, Tanji and others, and "Applications of Electron Holography"
by Gajdardziska-Josifovska in a 1999 volume; cached in `scratchpad/e6/cr2_*.json`, identity not
verified). E6's own 7 answered Crossref queries and the arXiv phrase search also found no Si(001) reflection
step phase, so the search result is consistent, but the repository's own standard is "an absence in
the sources searched, not proof of absence" (docs/00_executive_summary.md:85-88).
Required wording: "No reflection-holography step phase on Si(001) was found in the sources searched
(J-STAGE, CiNii, Crossref, OpenAlex, Semantic Scholar, the citation graph of the REH papers; 2026-09);
the closest published measurement is 7 pi across a step on Si(111)7x7 at 200 kV, (444), 0.8 deg
(Tanishiro 2003 p. 170)." Move the sentence from "Facts" to "Inferences".

### MINOR

**m1. Eight abbreviated SHA-256 values in L7 do not match the files (L7 3.2, 1.1, 2.1, 2.3).** Actual
values (`scratchpad/e6_allhash.txt`): J-b `osakabe1989jps.pdf` 280fa380...22085330 (L7: ...5c257); J-c
`osakabe1990jps_b.pdf` d1fb9531...42059093 (L7: ...9053); R6 `hayashi2006.pdf` cb465cb7...9014a1bc
(L7: ...14bc); R7 `ogino1997.pdf` 6ff4a1db...e5b04570 (L7: ...0570); D5 `yasaka1991.pdf`
8fc37611...1a3275cf (L7: ...75cb); D6 `azuma2007.pdf` d660f7d3...c17f0e4b (L7: ...7e0f); D8
`korobtsov2007.pdf` 724b801d...6eb2a685 (L7: 724b8010...a2685); D9 `yagi1986oubutsu.pdf`
ffea7c27...24f6c37f (L7: ...6f73). The files are the right documents by content (E6 read J-b, D8, D9);
the printed values were hand-abbreviated wrongly. Correction: print full hashes generated by script.

**m2. Tanishiro 2003 azimuth transcribed as [110] (L7 4.1).** P. 167 prints "電子線を［1 1̄ 0］方向から"
(rendered at 300 dpi). [110] is not in the (111) plane, so it cannot be a beam azimuth on Si(111);
correct to [1-10].

**m3. L6 7.1 asks to change A7; A7 is the inspected repository's inert row (L6 7.1, 5).** A7 is in
section 1 of `docs/model_assumptions.md` ("Assumptions inherited from the inspected repository",
line 19: "Inert: thermal effects are never enabled"). H5 m5 already proposed a new row B35 for the
engine's frozen-phonon u. Correction: leave A7 unchanged; add B35 "u = 0.0777 A per axis (B = 0.4761(17)
A^2 at 295.5 K; Heacock et al. 2021, arXiv:2103.05428v3 PDF p. 6, SECTION_READ; per-axis convention p.
3), at a specimen temperature that is an ASSUMPTION (295.5 K) until supplied"; the sizing tool's
stand-in (`tools/hpc/supercell_sizing.py:89-96`, `U_RMS_ASSUMED_A = 0.076` with a label that already
says "no model_assumptions row yet (H5 m5)") then cites B35; H5's archival rerun script
(`tools/hpc/review_h5_recompute.py:429, 579, 812`, label "ASSUMPTION A7") is a record and need not
change. Use one rounding (0.0777 A, or 0.07765 A with +-0.00014 A) everywhere; L6 uses both.

**m4. The TDS numbers are quoted at B = 0.4725 A^2 while B = 0.4761 A^2 is recommended (L6 5 row "Si
TDS absorptive factor", 7.2.3).** At the recommended B: V0'(TDS) = 0.0897 V (not 0.089), (008) ratio
0.0535 (not 0.0533), attenuation 7650 A. Same quantity, same value: quote the adopted B's numbers.

**m5. "Scatters by a factor of about 3 once scaled to a common energy" (L6 1.7, 7.2.4).** Unscaled,
Ni (200 kV)/Voss (100 keV) = 2.76-3.00; scaled to one energy with the 1/beta TDS law it is 3.49-3.81
(output E), and 7.2.4 lists the three values at two different energies. Correction: "a factor of about
3 between Voss (100 keV) and Ni (200 kV), 3.5-3.8 if scaled with the TDS 1/beta law".

**m6. Page locators of the J-STAGE papers are PDF pages in L6 and journal pages in L7.** L6 cites Horio
2014 "p. 4", "p. 5" (= pp. 383, 384), Horio 2022 "p. 4", "p. 7" (= pp. 79, 82) and Minami 2008 "p. 1-3"
(= pp. 87-89); L7 cites the same Horio 2014 (R3) by printed pages. Correction: printed pages everywhere.

**m7. S4's "2-4 A of regrown oxide at loading" omits Morita's caveat (L7 6.1 S4).** Morita 1990 p. 1273:
the initial values "include Si atoms terminated with hydrogen at Si surface. Therefore, the actual
oxide thicknesses ... are estimated to be thinner than above thickness values at the initial stage."
Add it.

**m8. D8's 710 deg C is not a clean-surface oxide desorption temperature (L7 2.4).** Korobtsov 2007
p. 48 and Fig. 4(c): the (2x1) streaks appear after Fe deposition at 470 deg C and annealing at 710 deg C
of the Fe/SiO2/Si(001) system, with desorption "preferentially" at oxide defects. State the context.

**m9. "x(1 +- 0.5) for +-5 deg of grazing angle (D3)" is applied to D2's values (L7 2.5).** D3's +-50 %
is for 80 deg incidence (10 deg grazing, 1-5 keV MD; preprint sec. 6); D2's thicknesses are FIB
sidewalls (SRIM at 89.5 deg). Label the transfer ASSUMPTION or drop it.

**m10. Finite frozen-phonon ensembles and the R2 factorisation (L6 1.2 inference 1, 7.2.1).** L6's
conclusion (no TDS absorptive potential on top of explicit frozen phonons) is right in expectation
(Hajek and Rusz p. 2, Eq. (4)), but two statements L6 read are not carried: Hajek and Rusz p. 3 ("by
adding more snapshots ... the residual TDS noise in the elastic channel gradually disappears") and the
Fig. 3 caption (p. 6: "residual TDS noise (caused by the finite coherent averaging)"); muSTEM p. 16
("More than 100 passes may be required for the elastic contribution to reach convergence"). For this
project the effect is small: with H2's measured rho^2 = 9.37e-4 in the 3 mrad aperture, the coherent
intensity is biased by rho^2/N = 1.2e-4 and the sideband phase scatters by sqrt(rho^2/2N) = 0.008 rad
per resolution element at N = 8 (output C). Also, "the sideband ... is the coherent average of the
object wave" holds for a vacuum reference; for R2 the sideband is the ensemble mean of psi_r* psi_o,
which factorises into two coherent averages only if the two partial waves depend on disjoint atoms
(Einstein model), i.e. if the object-reference shift exceeds the along-beam footprint. The averaging
after squaring (SM13) is the correct procedure either way. Correction: add a convergence criterion on
the coherent (sideband) average and the R2 proviso.

**m11. "Fact: P01-era Hitachi REH used a surface self-reference" (L7 3.3).** J-a p. 451 describes the
method "realised by our group [2]" ([2] = P01) in the present tense in 1990; attributing the arrangement
to the 1988 P01 experiment is an inference. Label the P01 link DERIVED_HERE; the R2 description itself is
SECTION_READ (J-a p. 451 sec. 2-2; J-b p. 439).

**m12. The uniform electronic term must follow each terrace's surface, not a planar profile (L6 7.2.2).**
Quoted: "A uniform term needs a new model, for example a step profile like `absorber_profile_V`
applied inside the crystal region". `absorber_profile_V` is a function of the surface-normal coordinate
x only. On a stepped cell a planar mask puts an absorbing slab of thickness h on one terrace (or leaves
one un-absorbed): for a/4 at 16.1347 mrad the slab is crossed over 2h/sin(theta) = 168.3 A, an amplitude
factor of 0.923 at V' = 0.6534 V (output H), which breaks the terrace equivalence on which B4's
cancellation rests. Correction: build the mask from the structure builder's local surface height per
terrace (the proportional model avoids this because the imaginary part rides on the atoms), and test it
with the fixed-beam translation null test of docs/05 section 4.

### NIT

* n1. L6 2.3: "1.5 % below in u against the BvK value" -> 1.40 % (BvK at 293 K) or 1.76 % (at 295.5 K).
* n2. L6 3.2: "exceeds every bonded or measured value by 1.2-1.9 V" -> 1.2-2.0 V (against 12.0-12.53 V).
* n3. L7 5: "a/4 = 1.3575 A" -> 1.35775 A (a = 5.431 A, R1) or 1.35773 A (B2's 5.4309 A); L7 uses R1's
  a = 5.431 A throughout while the repository uses 5.4309 A (relative 2e-5; state which).
* n4. L6 1.4 and 7.2.2: theta_E = 0.04 mrad is Mendis's non-relativistic dE/2E (0.0425 mrad); the
  relativistic dE/(pv) is 0.0495 mrad. No consequence.
* n5. Horio 2022 Eq. (1) evaluates 5.79e-2 at 10 keV with the non-relativistic velocity (E6: 0.0579
  non-relativistic, 0.0588 relativistic), so beta = 0.66-0.71 refers to that form (1.5 %). Moot after M1.
* n6. J-a p. 452 says "第1図" for the Pt(111) micrograph, which is 第2図 on that page (the abstract's own
  misnumbering); anyone quoting J-a should cite Fig. 2.
* n7. DOIs printed in the report texts but not in `docs/references.bib` after B4: six in L6, all
  deliberately not merged ("lead", "not added", "not accepted": 10.1016/0039-6028(92)90564-m,
  10.1016/0039-6028(96)00042-8, 10.1016/j.ultramic.2017.01.011, 10.1017/cbo9780511525254.004,
  10.1107/s0108767397016899, 10.15302/frontphys.2026.114201) and one in L7 (Abukawa et al., PRB 62, 16069,
  10.1103/physrevb.62.16069; a Crossref record is in L7's cache, and it is Horio 2014's ref. [4], the
  "CTDS" row of Table I). L7's closed-source list also names four works without DOI that have no bib entry
  (Pehlke and Tersoff PRL 67, 465; Wierenga et al. PRL 59, 2169; Swartzentruber et al. PRL 65, 1913;
  Shirasawa et al. PRL 94, 195502). Do not copy these into docs/ without a verified bib entry.

## 5. Logic of the recommendations (task item 4)

1. **Frozen phonons plus uniform electronic absorption for item 21.** The TDS part: "no TDS absorptive
   potential with explicit frozen phonons" is right (Hajek and Rusz p. 2; Dr. Probe p. 9; muSTEM sec.
   3.8), in expectation; finite N leaves residual TDS noise in the coherent average (m10), negligible
   here at N = 8 by H2's rho^2. The Einstein model gives the correct single-site Debye-Waller factor with
   a sourced u and misses correlations (Hajek and Rusz: about 1e-3 I0 for 50 nm diamond in
   transmission); that is not a reason to add a CAP. The electronic part: a uniform V' is the standard
   local approximation for delocalised valence losses in the bulk, but for the specular reflected wave
   it is an upper bound (M3), the surface-plasmon loss is the larger term and is measured at 200 kV (M1),
   and loss electrons are partly coherent below 25-45 nm (M2). Adopt: frozen phonons + electronic
   bracket 0 / 0.65 V (ASSUMPTION) + surface-plasmon elastic fraction from Tanishiro 2003 (ASSUMPTION for
   the transfer). Do not adopt 0.65 V as "the" value.
2. **u = 0.0777 A at 295.5 K and the new "specimen temperature" input.** Value, convention and locator
   are right (section 1); the neutron (nuclear) B is the appropriate quantity for the thermal smearing
   of the electrostatic potential in the rigid-atom picture. Adopt as B35, not A7 (m3). The temperature
   input is justified (0.0014 A^2/K; 10 K = 2.9 % in B); the slope is the BvK slope at 295.5 K and must not
   be extrapolated far from room temperature (Tanishiro's 750 deg C or any in-situ anneal is outside it).
3. **B1 = 12.0 V until Wu and Spiecker is read.** Agreed. 12.48 +- 0.22 V is abstract-level; the
   measurement is a transmission wedge-refraction value, and the step at an ion-milled, oxidised surface
   is set by the overlayer (S3, M4), so the rocking-curve calibration (item 9) stays decisive. The (0,0,8)
   external angle moves by -0.085 mrad between 12.0 and 12.48 V (16.4743 -> 16.3893 mrad), inside B19's
   0.1 mrad calibration uncertainty.
4. **Surface scenarios S1-S4.** The set is sound and sourced; S0 is a reference limit only. For a sample
   observed in a conventional microscope after ion milling and air exposure (the most likely reading of
   PROJECT_INPUT item 12 as supplied), S3 applies unless in-situ heating is documented. The paper must
   state (a) the preparation and the microscope vacuum; (b) that REM step images disappear after ion
   irradiation until annealing (Yagi et al. 1986 p. 1048, re-read by E6; recovery after amorphisation is
   difficult per the Claverie et al. abstract as read by L7, not re-read by E6), so step visibility under
   S3 is itself to be demonstrated; (c) that under S3 the measured phase refers to the buried
   crystal steps, converted with 2 k_perp h (conformal overlayer) or up to 2 k'_perp h (planarising), a
   14 % range (M4); (d) that S1 (UHV flash to about 1200 deg C) erases the milled topography and leaves
   the miscut's equilibrium steps with 2x1/1x2 domains (Zandvliet pp. 594, 600-601); and (e) that a/2
   steps on a low-miscut annealed surface are not the equilibrium step (single-layer below 1 deg).
5. **"No Si(001) step phase has been published".** Consistent with E6's own Crossref and arXiv checks,
   but the search excluded closed REH papers, theses and book chapters (M5). Scope the sentence.

## 6. Repository statements that must change if L6/L7 are adopted (file:line; proposed content)

| file:line | current statement (abridged) | change |
|---|---|---|
| docs/model_assumptions.md:19 (A7) | "0.076 A per axis is applied ... Inert" | leave unchanged (inspected repository); add B35 (m3) |
| docs/model_assumptions.md (new B35) | - | u = 0.0777 A per axis, B = 0.4761(17) A^2 at 295.5 K (Heacock et al. 2021, arXiv v3 PDF p. 6, SECTION_READ; convention p. 3); specimen temperature ASSUMPTION 295.5 K; dB/dT = 0.0014 A^2/K (PDF p. 25) |
| docs/model_assumptions.md:26 (B1) | 12.0 V ASSUMPTION; Kruse 2006 candidate; DFT 12.53 V | add Wu and Spiecker 12.48 +- 0.22 V (METADATA_VERIFIED +ABSTRACT(PubMed), body unread); RHEED practice 12 V (Horio 2014 p. 384; Horio 2022 p. 79; Moon 1972 p. 394 best fit at 40 keV); keep 12.0 V |
| docs/model_assumptions.md:28 (B3) | Si(001) unreconstructed | add: sourced 2x1/c(4x2) coordinates now read (R1 Tables III-IV, transcription verified by E6); not implemented |
| docs/model_assumptions.md:31 (B6) | "absorptive potential and a loss of coherence" | TDS by frozen phonons (production) or Bird-King on a DW-smeared static lattice, never both; electronic bracket 0 / 0.65 V; surface-plasmon elastic fraction (M1); partial coherence of loss electrons (M2) |
| docs/model_assumptions.md:32 (B7) | 1 nm crossed over about 100 nm at 20 mrad | add the S3 phase-to-height dichotomy (M4) |
| docs/model_assumptions.md:55 (B30) | "No sourced absorptive-potential parameterisation exists here" | outdated: Thomas et al. 2024 (open code) and a sourced electronic MFP statement exist; B30 can stay as the demo stand-in with a new justification |
| docs/06_project_inputs_required.md:44-45 (items 20, 21) | item 21 "from a named parameterisation" | item 21: as B6 above; request an energy-filtered EELS of the specular beam at the working angle (zero-loss fraction), which replaces both M1's transfer and M3's bracket; item 20: add the 12.48 V candidate |
| docs/06_project_inputs_required.md:27 (item 12) | preparation details list | add L7 6.3 checklist; new item 23: specimen temperature during holography |
| docs/02_literature_position.md:54-63 | 200 kV "inferred ... UNVERIFIED"; "not height measurement" | 200 kV SECTION_READ (Tanishiro 2003 p. 167; J-e p. 852); a 7 pi step phase on Si(111)7x7 is reported (p. 170); loss-electron coherence (pp. 170-171) |
| docs/02_literature_position.md:66-71 | Japanese databases "most likely place" | searched by L7 (section 3); scope as in M5 |
| docs/00_executive_summary.md:85-88 | "the Japanese databases were not searched" | now searched (L7); keep "absence in the sources searched" |
| docs/05_final_repository_specification.md:155-157 | "Absorption via a sourced optical potential; frozen phonons optional" | "TDS from frozen phonons or from a Bird-King absorptive factor on a DW-smeared static lattice, never both; electronic losses as in B6" |
| docs/05_final_repository_specification.md:347-348 | "2x1 reconstruction raises NotImplementedError (no source read)" | "(source read: R1 Tables III-IV; not implemented)" |
| docs/03_physics_summary.md:217 | "absorption from a sourced optical potential" | as docs/05:155 |
| docs/source_map.tsv SM22 (line 26) | R2 reading DERIVED_HERE; phase relation UNVERIFIED | R2 description and Delta_phi = 2 K_perp Delta_z SECTION_READ in J-a p. 451 / J-b p. 439 for the Hitachi group; P01 body still unread |
| docs/source_map.tsv SM13 (line 17) | ensemble average after squaring | add the finite-N convergence criterion on the coherent average (m10) |
| docs/07_reading_plan.md:99-128 | upload list | add Mendis 2019 (+ corrigendum), Wu and Spiecker 2017, Osakabe 1995 thesis ch. 4 (NDL remote copy); Tanishiro 2003 body now read |
| physics_conventions.md | - | no change needed (sigma, k, lambda agree with both reports) |

## 7. Verdict table

| item | verdict |
|---|---|
| L6 1.1-1.4 (double counting; sources) | CONFIRMED; amend 1.4's coherence sentence (M2) and add m10 |
| L6 1.5 (TDS numbers) | CONFIRMED, REPRODUCED twice (section 3); quote at the adopted B (m4) |
| L6 1.5 items 4-5, 7.2.2 (uniform electronic 0.65 V) | ADOPT ONLY AS A BRACKET 0 / 0.65 V (M3); surface-following mask (m12) |
| L6 1.6 surface plasmons, 7.2.5 | REJECT the numbers (0.67-0.73, 0.50, 0.70, "unsourced", 3.6 A); replace with M1 |
| L6 1.7 Voss 1980 | CONFIRMED |
| L6 2 (Heacock B, BvK, dB/dT) | CONFIRMED |
| L6 3 (MIP), 7.3 (keep B1) | CONFIRMED; n2 |
| L6 4 (benchmarks) | CONFIRMED |
| L6 7.1 (u = 0.0777 A) | ADOPT as B35, not A7 (m3) |
| L6 7.2.1, 7.2.3 | ADOPT (m10 proviso) |
| L6 7.2.4 | ADOPT with the corrected factor (m5) |
| L7 1 (R1-R7; Tables III-IV) | CONFIRMED (every table entry checked) |
| L7 2 (damage, oxide, densities) | CONFIRMED with m7, m8, m9 |
| L7 3 (Japanese sources) | CONFIRMED with m1, m2, m11 |
| L7 4.1 (Tanishiro 7 pi) | CONFIRMED (m2) |
| L7 4.2 answer, 8 fact 5 | REWORD (M5) |
| L7 6.1-6.3 (scenarios, checklist) | ADOPT with M4 added to S3 |
| L7 6.2 overlayer estimate | formula CONFIRMED; consequences incomplete (M4) |

## 8. Values E6 CONFIRMS (quotable with the locator)

* Si B = 0.4761(17) A^2 at 295.5 K, neutron Pendellosung (Heacock et al. 2021, arXiv:2103.05428v3 PDF
  p. 6); u = 0.07765(14) A per axis (DERIVED_HERE); constrained 0.4767(6) A^2 (p. 33); B_BvK = 0.4725(17)
  A^2 at 295.5 K (p. 6, p. 32); dB/dT = 0.0014 A^2/K at 295.5 K (p. 25); <u^2> = B/(8 pi^2) (p. 3).
* Voss et al. 1980 (100 keV CBED): V'_000 = 0.61 V (p. 981); V'_111, V'_220, V'_311, V'_004 = 0.031,
  0.039, 0.025, 0.027 V (Table 5, p. 983); B = 0.4613 A^2 at 293.2 K used (Table 3 caption, p. 982).
* Si TDS absorptive factor at 200 keV (Thomas et al. 2024 Eq. (2) and code; DERIVED_HERE, REPRODUCED by
  E6 twice): at B = 0.4761 A^2, f'/f = 0.0064 (000), 0.0110 (111), 0.0182 (022), 0.0274 (004), 0.0398
  (044), 0.0535 (008); V0'(TDS) = 0.090 V; intensity attenuation length 7650 A.
* sigma(200 keV) = 7.2884e-4 rad/(V A); V' = 1/(2 sigma Lambda): 0.653 V for Lambda = 1050 A, 0.827 V
  for 830 A (Mendis 2024 sec. 3; the 1050 A measurement itself UNVERIFIED).
* Ni et al. 2026, 200 kV energy-filtered CBED: U'_111/U_111 = 0.0167 (PyExtal), 0.0182 (Extal)
  (Table 1).
* Horio et al. 2014 (10 kV RHEED, Si(001)2x1 at RT): alpha = 18.1 deg, a_z - b_z = 0.71 A with r_AB fixed
  at 2.28 A (Table I, p. 383; sec. V, p. 385).
* Ramstad et al. 1995: Tables III and IV exactly as transcribed in L7 1.4; c(4x2) dimer 2.29 A,
  buckling 18.7 and 18.9 deg (text p. 14517; E6 recomputes 2.287 A, 18.72 deg from Table IV).
* Zandvliet 2000: L = d/tan(theta) (p. 595); single-layer steps below 1 deg, coexistence 1-4 deg,
  double-layer above 4 deg on annealed surfaces (p. 601); freeze-in 750-875 K (p. 596).
* Morita et al. 1990 (HF-last Si(100), clean-room air): 5.4 -> 7.6 A layer-by-layer; 6.7 A after 7 d at
  1.2 % H2O; 1.7-1.9 A in dry gas (p. 1273, Table I), thermal-oxide-equivalent thickness.
* Uzuhashi and Ohkubo 2024: Ga+ FIB amorphous Si ~22, ~7, ~4, ~1 nm at 30, 8, 5, 2 keV (pp. 4-5).
* Tanishiro 2003: 200 kV, Si(111)7x7, 0.8 deg, (444) (p. 167); step phase 7 pi (p. 170); mean
  surface-plasmon excitation number 1.44 (p. 167); decay distance about 6 nm (p. 170); one-plasmon-loss
  fringes with visibility about 0.1 (p. 171).
* Osakabe 1990 JPS (J-a): reference set on a defect-free region (p. 451); Delta_phi = 2 K_perp Delta_z
  (p. 451); Pt(111) 2.3 A step, about 0.5 lambda (p. 452).
* Geometry at the repository's (0,0,8) condition (16.1347 mrad, DERIVED_HERE): step phases 10.976 rad
  (a/4) and 21.952 rad (a/2); path factor 2/sin(theta) = 124; overlayer top-surface term 0.0903 rad
  A^-1 V^-1 (projected), 0.858 rad/A at V_ov = 10 V (refracted).

## 9. The orchestrator must NOT adopt yet

1. L6's surface-plasmon numbers (0.67-0.73 per reflection, zero-loss 0.50, amplitude 0.70), the
   sentence "unsourced at 200 keV" and the 3.6 A interaction thickness as a 200 keV value (M1).
2. L6's "a plasmon-loss electron is lost (no longer coherent with the reference wave)" (M2).
3. V0'(el) = 0.65 V (or 0.83 V) as the item-21 value; only the bracket 0 / 0.65 V (M3).
4. The relabelling of A7; use a new row B35 (m3).
5. L7's "must state that Si(001) step phases have not been reported" and fact 5 of section 8 (M5).
6. L7's S3 text without the planarising-overlayer consequence and with "comparable to the step phase
   itself" (M4).
7. L7's hash list (m1), the [110] azimuth (m2), S4's 2-4 A oxide (m7), the 710 deg C statement (m8)
   and the x(1 +- 0.5) transfer (m9) until corrected.
8. Wu and Spiecker 12.48 V as a replacement of B1 (L6 agrees: body unread).
9. Mendis's 1050 A as a measured value (it is a statement about Mendis 2019; UNVERIFIED until upload 1).
10. A planar (x-only) mask for the uniform electronic term in stepped cells (m12).
