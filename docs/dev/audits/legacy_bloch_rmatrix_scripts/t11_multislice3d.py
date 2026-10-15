import numpy as np, time
import simulation.multislice_3d as MS
import simulation.supercell as SC
import simulation.constants as C
# 1. atomic potential normalisation
V0si, sig = 24.0, 0.3
integral = V0si * 2*np.pi*sig**2     # V A^3 per atom (2-D Gaussian integral of V_proj)
FE2V = 47.87764
true = FE2V * 5.82
print("supercell.compute_projected_potential: per-atom integral = %.2f V A^3 ; neutral Si (h^2/2pi m e) f_e(0) = %.1f V A^3 ; ratio %.1f" % (integral, true, true/integral))
print("  implied mean inner potential of the multislice crystal = %.3f V (neutral-atom value 13.9 V)" % (8*integral/C.SI_LATTICE_PARAM**3))
# numerical check on an actual slice
sc = SC.generate_supercell(n_cells_x=4, n_cells_z=4, crystal_depth_A=50.0, vacuum_thickness_A=50.0)
V = SC.compute_projected_potential(sc["atoms_pc"], sc["cell_x"], sc["cell_y"], sc["y_min"], sc["dz"], 0, sc["dz"], nx_grid=256, ny_grid=256)
y = np.linspace(sc["y_min"], sc["y_min"]+sc["cell_y"], 256, endpoint=False)
inner = (y < -5) & (y > -40)
print("  numerical: mean V_proj/dz over crystal rows = %.3f V ; atoms in slice %d" % (V[inner].mean()/sc["dz"], np.sum((sc["atoms_pc"][:,2]>=0)&(sc["atoms_pc"][:,2]<sc["dz"]))))
exp_atoms = sc["cell_x"]*50*sc["cell_z"]*8/C.SI_LATTICE_PARAM**3
print("  atoms in supercell %d, expected from density %.0f" % (sc["n_atoms"], exp_atoms))
print("  interaction_parameter() = %.5e (independent 7.28840e-04)" % MS.interaction_parameter())
# 2. band limit vs specular deviation at defaults
cell_y = 100.0; ny = 256; dy = cell_y/ny
kmax = (2/3)/(2*dy)
print("defaults: dy=%.4f A ; 2/3-band radius %.3f 1/A = %.1f mrad ; incident tilt 28 mrad -> specular deviation 2*theta = 56 mrad = %.3f 1/A" % (dy, kmax, kmax*C.LAMBDA_200KV*1e3, 56e-3/C.LAMBDA_200KV))
# 3. direction of travel of the tilted propagator
nx, nyy = 8, 512; cy = 200.0
P = MS.make_propagator(nx, nyy, 10.0, cy, 3.84, ky_tilt_mrad=28.0)
yy = np.linspace(-100, 100, nyy, endpoint=False)
psi = np.exp(-(yy/5.0)**2)[:,None]*np.ones((1,nx))
for i in range(100):
    psi = np.fft.ifft2(np.fft.fft2(psi)*P)
cen = np.sum(yy[:,None]*abs(psi)**2)/np.sum(abs(psi)**2)
print("tilted propagator: Gaussian centred at y=0 moves to y=%.2f A after 100 slices (384 A); theta*L = %.2f A ; crystal is at y<0 (supercell), so the beam moves %s" % (cen, 28e-3*384, "AWAY from the crystal" if cen>0 else "toward the crystal"))
