"""Cross-check 2: attribute the 5-12 % reflectivity offset of cross-check 1 to the Debye-Waller factor.

Runs the REPOSITORY engine (scripts/rocking_flat.py at the repository root) with B = 0.5261 A^2 (this
kernel's value: Gao & Peng 1999 polynomial, Peng-Dudarev-Whelan 2004 Table 14.2 p. 462, T = 300 K)
instead of its default B = 0.46 A^2, everything else unchanged, and compares with this kernel's R from
outputs/crosscheck_their_conditions.npz. Runtime about 30 s.
Result (session): R_mine/R_theirs median 0.913 -> 1.006 (range 0.991-1.028), shape correlation 0.9999.
"""
import sys, pathlib
import numpy as np
HERE = pathlib.Path(__file__).resolve().parents[1]; ROOT = HERE.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]     # the repository engine's reflection_holo
from rocking_flat import rocking
from reflection_holo import geometry as geo
B_MINE = 0.5261253                                  # = kernel_validation/reflection_holo/constants.py B_SI_300K
X = np.load(HERE / "outputs" / "crosscheck_their_conditions.npz")
offs, Rm, Rt = X["offsets_mrad"], X["R_mine"], X["R_theirs"]
_, Rb, _ = rocking(geo.SI001_FRAME, (0, 0, 8), offs, B=B_MINE)
for lab, ref in (("B=0.46 (repository default)", Rt), (f"B={B_MINE:.4f} (this kernel)", Rb)):
    r = Rm / ref
    print(f"R_mine/R_repo, repo {lab}: median {np.median(r):.3f}, range {r.min():.3f}-{r.max():.3f}, "
          f"shape corr {np.corrcoef(Rm, ref)[0, 1]:.4f}")
np.savez(HERE / "outputs" / "crosscheck_B_attribution.npz", offsets_mrad=offs, R_mine=Rm, R_theirs_B046=Rt, R_theirs_B0526=Rb)
print("saved outputs/crosscheck_B_attribution.npz")
