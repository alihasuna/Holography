import sys, math, numpy as np
import os; _HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, _HERE)  # see README.md: rename pyprismatic_stub.py -> pyprismatic.py only when the real engine is absent
import prismatique, embeam

XYZ = os.path.join(_HERE, "slab.xyz")
a = 5.4309
# repo slab-generator defaults: n_x_si=9 (along [1,-1,1]), n_y=12 (along [1,-1,-2]),
# n_z_si=36 (along [110]); x_vac=10 A, z_vac=30 A  -> cleave-frame box
Lx = 9*(a*math.sqrt(3)) + 2*10.0        # surface-normal direction
Ly = 12*(a*math.sqrt(6)/2)              # in-plane step-normal
Lz = 36*(a/math.sqrt(2)) + 2*30.0       # beam direction
with open(XYZ,"w") as f:
    f.write("synthetic slab matching repo generator default box\n")
    f.write(f"{Lx:.10f} {Ly:.10f} {Lz:.10f}\n")
    f.write(f"14 {Lx/2:.6f} {Ly/2:.6f} {Lz/2:.6f} 1.000 0.076\n")
    f.write("-1")
print(f"box: Lx={Lx:.3f}  Ly={Ly:.3f}  Lz={Lz:.3f} (A)")

E = 200.0; lam = embeam.wavelength(E)
def build(px):
    # exactly what multislice_forward_model.derive_grid_from_meta + _reduced_dim do
    def fftf(n):
        def ok(x):
            y=x
            for p in (2,3,5):
                while y%p==0 and y>1: y//=p
            return y==1
        for span in (0.05,0.1,0.2):
            lo=max(128,int((1-span)*n)); hi=max(lo,int((1+span)*n)); best=None
            for k in range(lo,hi+1):
                if k%4 or not ok(k): continue
                if best is None or abs(k-n)<abs(best-n) or (abs(k-n)==abs(best-n) and k>best): best=k
            if best: return best
        return ((max(128,n)+3)//4)*4
    gx = fftf(max(128,int(math.ceil(Lx/px)))); gy = fftf(max(128,int(math.ceil(Ly/px))))
    disc = prismatique.discretization.Params(
        sample_supercell_reduced_xy_dims_in_pixels=(gx//4, gy//4),
        num_slices=int(math.ceil(Lz/1.0)), z_supersampling=4, interpolation_factors=(1,1))
    sm = prismatique.sample.ModelParams(atomic_coords_filename=XYZ, unit_cell_tiling=(1,1,1),
                                        discretization_params=disc, atomic_potential_extent=8.0)
    return gx, gy, sm

for px in (0.5, 0.13):
    gx, gy, sm = build(px)
    Nx, Ny = prismatique.sample._supercell_xy_dims_in_pixels(sm)
    dx, dy = prismatique.sample._supercell_lateral_pixel_size(sm)
    step = prismatique.tilt.step_size(sm, mean_beam_energy=E)
    maxXtilt = lam/(4*dx)*1000; maxYtilt = lam/(4*dy)*1000
    print(f"\n=== advisory px = {px} A ===")
    print(f"  grid (gx,gy) from repo = ({gx},{gy}); prismatique N_x,N_y = ({Nx},{Ny})  -> match={gx==Nx and gy==Ny}")
    print(f"  potential pixel dx,dy = {dx:.4f},{dy:.4f} A ; HRTEM image pixel = {2*dx:.4f},{2*dy:.4f} A ; image dims = ({Nx//2},{Ny//2})")
    print(f"  tilt.step_size = ({step[0]:.4f}, {step[1]:.4f}) mrad")
    print(f"  Prismatic anti-alias tilt ceiling lam/(4*dx) = {maxXtilt:.3f} mrad (x), {maxYtilt:.3f} mrad (y)")
    rx = prismatique.sample._supercell_dims(sm)
    # repo runner default sweep 0 -> 11 mrad step 0.15, azimuth 0
    for (lo,hi) in [(0.0,11.0), (23.997,23.997)]:
        c = (lo+hi)/2.0; span = hi-lo
        tp = prismatique.tilt.Params(offset=(c,0.0), window=(0.0, span/2.0+0.1))
        try:
            ts = np.array(prismatique.tilt._series(sm, E, tp))
            print(f"  sweep [{lo},{hi}] mrad -> offset=({c:.3f},0), window=(0,{span/2+0.1:.2f}):")
            print(f"     requested angles = {int(round(span/0.15))+1 if span>0 else 1}; SIMULATED tilts = {len(ts)}")
            print(f"     tilt_series[0]   = {ts[0]}   <-- what specular_filter.py [0,0,0,:,:] reads")
            i_c = int(np.argmin(np.linalg.norm(ts-np.array([c,0.0]),axis=1)))
            print(f"     nearest to offset= {ts[i_c]} at index {i_c}")
            print(f"     x-range {ts[:,0].min():.3f}..{ts[:,0].max():.3f}  y-range {ts[:,1].min():.3f}..{ts[:,1].max():.3f} mrad")
        except Exception as e:
            print(f"  sweep [{lo},{hi}] -> offset=({c:.3f},0), window=(0,{span/2+0.1:.2f}): {type(e).__name__}: {e}")
