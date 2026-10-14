# G. Independent check of Appendix A of `docs/08_fir_simulation_campaign.md` (items A1 to A11)

Status: in progress (written incrementally), 2026-10-14. Author: derivation-check subagent G.

Scope: independent re-derivation of the eleven derivations in Appendix A of
`docs/08_fir_simulation_campaign.md`, which underpin the grazing-incidence multislice code
`reflection_holo/`, followed by a comparison with the formulas as written in the appendix and as
implemented in `reflection_holo/analysis.py` (`updown`, `vdp_reflectivity`, `vdp_spectrum`),
`reflection_holo/reference1d.py` (`parratt`, `K_profile`), `reflection_holo/simulate.py`
(`delay_allowance_A`, `plan_windows`) and `reflection_holo/aggregate.py` (`image_from_spectrum`,
`terrace_ratio`). No repository file other than this report was modified.

Conventions (from `docs/physics_conventions.md`): `exp(+i(k.r - wt))`; x = outward surface normal
(into vacuum), z = beam azimuth, y completes a right-handed frame; glancing angles to the surface;
`q` in cycles/A, `K = 2 pi q` in rad/A; forward Fourier transform `F(q) = int f exp(-2 pi i q.r) dr`.
Beam energy 200 keV throughout (300 keV never used).

Evidence labels: every result below is DERIVED_HERE (re-derived from the stated premises in this
report) and checked NUMERICALLY by the scripts whose output is pasted. No textbook passage was read
for this check; where the appendix recalls a textbook result (Landau and Lifshitz section 25), it is
marked UNVERIFIED as a citation and treated only as a cross-check.

Procedure: for each item the premises were restated and the result derived before the
implementation was opened; the comparison with the code was made afterwards. All scripts are in the
session scratchpad (paths given per item), were run with `/tmp/claude-0/venv/bin/python`
(numpy 2.5.4, scipy 1.18.1), and contain self-checks with explicit tolerances.

Finding ranks: Blocker (results of the GPU campaign would be wrong or uninterpretable),
Major (a stated result is wrong or a check is missing that could hide a wrong result),
Minor (imprecise statement or number with limited consequence), Nit (wording).

## 0. Constants used (script `s0_constants.py`)

(pending)

