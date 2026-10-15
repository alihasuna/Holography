"""
supercell.py
============
Build a Si supercell for Peng-Cowley reflection multislice simulation.

The coordinate frame is chosen so the surface boundary aligns with a grid axis:

    z = [110]/sqrt(2)       -- beam propagation direction
    y = [1,-1,1]/sqrt(3)    -- outward surface normal (crystal below, vacuum above)
    x = y x z normalized    -- in-surface, perpendicular to beam = [-1,1,2]/sqrt(6)

Lattice periodicity in this frame (FCC Si):
    z-period: a/sqrt(2) = 3.840 A   (from FCC vector a/2*[110])
    x-period: 6.652 A               (from -a1 + 2*a3 = a*[-1/2, 1/2, 1])
    y-period: 9.407 A               (from -a1 + 3*a2 - a3, non-periodic in supercell)

The supercell is periodic in x and z, but NOT in y (crystal + vacuum).
"""

import numpy as np
from simulation.constants import SI_LATTICE_PARAM, SI_ATOM_POSITIONS

# ── Peng-Cowley coordinate frame ─────────────────────────────────────────────
PC_Z = np.array([1, 1, 0], dtype=float) / np.sqrt(2)       # beam direction
PC_Y = np.array([-1, 1, -1], dtype=float) / np.sqrt(3)     # outward surface normal
PC_X = np.cross(PC_Y, PC_Z)
PC_X = PC_X / np.linalg.norm(PC_X)                          # in-surface

# rotation matrix: columns = new frame axes in cubic coords
# R maps new-frame coords -> cubic coords
# R^T maps cubic coords -> new-frame coords
ROT_TO_CUBIC = np.column_stack([PC_X, PC_Y, PC_Z])
ROT_TO_PC = ROT_TO_CUBIC.T

# lattice periods in the PC frame
_A = SI_LATTICE_PARAM
PERIOD_X = np.linalg.norm(ROT_TO_PC @ (_A * np.array([-0.5, 0.5, 1.0])))  # 6.652 A
PERIOD_Z = _A / np.sqrt(2)  # 3.840 A
# y has no useful short period for a rectangular supercell;
# the d-spacing along [1-1 1] is a*sqrt(3)/3 = 3.136 A (Si(111) spacing)
D_111 = _A / np.sqrt(3)  # 3.136 A


def generate_supercell(n_cells_x=4, n_cells_z=200,
                       crystal_depth_A=50.0,
                       vacuum_thickness_A=50.0,
                       a=SI_LATTICE_PARAM):
    """Build the reflection-geometry supercell.

    Parameters
    ----------
    n_cells_x : int
        Repeats along x (in-surface). Period = 6.652 A.
    n_cells_z : int
        Repeats along z (beam). Period = a/sqrt(2) = 3.840 A.
        This is the propagation length.
    crystal_depth_A : float
        Crystal thickness along y (surface normal), in Angstroms.
        Crystal occupies y in [-crystal_depth, 0].
    vacuum_thickness_A : float
        Vacuum thickness above crystal, in Angstroms.
        Vacuum occupies y in [0, vacuum_thickness].
    """
    cell_x = n_cells_x * PERIOD_X
    cell_z = n_cells_z * PERIOD_Z
    cell_y = crystal_depth_A + vacuum_thickness_A

    # y-range: crystal from -crystal_depth to 0, vacuum from 0 to +vacuum_thickness
    # shift so y=0 is at the surface
    y_min = -crystal_depth_A
    y_max = vacuum_thickness_A

    # generate cubic atoms covering the needed volume
    # map PC frame corners to cubic frame to determine required cubic range
    corners = np.array([
        [0, y_min, 0],
        [cell_x, y_min, 0],
        [0, y_max, 0],
        [0, y_min, cell_z],
        [cell_x, y_max, cell_z],
    ])
    corners_cubic = (ROT_TO_CUBIC @ corners.T).T
    c_lo = np.floor(corners_cubic.min(axis=0) / a).astype(int) - 1
    c_hi = np.ceil(corners_cubic.max(axis=0) / a).astype(int) + 2

    # generate all Si atoms in cubic block, then rotate
    atoms_pc = []
    for ix in range(c_lo[0], c_hi[0]):
        for iy in range(c_lo[1], c_hi[1]):
            for iz in range(c_lo[2], c_hi[2]):
                offset = a * np.array([ix, iy, iz], dtype=float)
                for frac in SI_ATOM_POSITIONS:
                    pos_cubic = offset + a * frac
                    pos_pc = ROT_TO_PC @ pos_cubic
                    # check bounds: x periodic, y within range, z periodic
                    if (0 <= pos_pc[0] < cell_x and
                        y_min <= pos_pc[1] < y_max and
                        0 <= pos_pc[2] < cell_z):
                        atoms_pc.append(pos_pc)

    atoms_pc = np.array(atoms_pc) if atoms_pc else np.zeros((0, 3))

    # wrap x and z for periodicity (small numerical tolerance)
    atoms_pc[:, 0] = atoms_pc[:, 0] % cell_x
    atoms_pc[:, 2] = atoms_pc[:, 2] % cell_z

    # remove duplicates
    atoms_pc = _remove_duplicates(atoms_pc, tol=0.2)

    # separate crystal (y < 0) from vacuum (y >= 0)
    crystal_mask = atoms_pc[:, 1] < 0
    n_crystal = np.sum(crystal_mask)

    return {
        "atoms_pc": atoms_pc[crystal_mask],  # only crystal atoms
        "cell_x": cell_x,
        "cell_y": cell_y,
        "cell_z": cell_z,
        "y_min": y_min,
        "y_max": y_max,
        "y_surface": 0.0,  # surface at y=0
        "crystal_depth": crystal_depth_A,
        "vacuum_thickness": vacuum_thickness_A,
        "period_x": PERIOD_X,
        "period_z": PERIOD_Z,
        "n_atoms": n_crystal,
        "n_slices": n_cells_z,
        "dz": PERIOD_Z,
    }


def _remove_duplicates(positions, tol=0.2):
    """Remove duplicate atom positions within tolerance."""
    if len(positions) < 2:
        return positions
    from scipy.spatial import cKDTree
    tree = cKDTree(positions)
    pairs = tree.query_pairs(r=tol)
    to_remove = set()
    for i, j in pairs:
        to_remove.add(max(i, j))
    mask = np.ones(len(positions), dtype=bool)
    mask[list(to_remove)] = False
    return positions[mask]


def compute_projected_potential(atoms_pc, cell_x, cell_y, y_min,
                                dz, z_start, z_end,
                                nx_grid=256, ny_grid=256,
                                sigma_atom=0.3):
    """Compute projected potential for one z-slice.

    The potential is summed over atoms within [z_start, z_end] and
    projected onto the x-y plane. Crystal region has potential,
    vacuum region (y > 0) is zero.

    Parameters
    ----------
    atoms_pc : (N, 3) array
        Atom positions in PC frame (x, y, z) in Angstroms.
    cell_x : float
        x-extent of supercell.
    cell_y : float
        Total y-extent (crystal + vacuum).
    y_min : float
        Minimum y (bottom of crystal, negative).
    dz : float
        Slice thickness.
    z_start, z_end : float
        z-range of this slice.
    nx_grid, ny_grid : int
        Grid dimensions.
    sigma_atom : float
        Gaussian width for atomic potential (Angstroms).

    Returns
    -------
    V_proj : (ny_grid, nx_grid) array
        Projected potential in V*A.
    """
    # select atoms in this z-slice
    mask = (atoms_pc[:, 2] >= z_start) & (atoms_pc[:, 2] < z_end)
    slice_atoms = atoms_pc[mask]

    # grid in x and y
    x = np.linspace(0, cell_x, nx_grid, endpoint=False)
    y = np.linspace(y_min, y_min + cell_y, ny_grid, endpoint=False)
    X, Y = np.meshgrid(x, y)

    V_proj = np.zeros((ny_grid, nx_grid), dtype=float)

    # Si projected atomic potential peak (Kirkland parameterization gives ~24 V*A)
    V0_si = 24.0  # V*A

    for atom in slice_atoms:
        ax, ay = atom[0], atom[1]
        # periodic in x
        dx = X - ax
        dx = dx - cell_x * np.round(dx / cell_x)
        dy = Y - ay
        r_sq = dx**2 + dy**2
        V_proj += V0_si * np.exp(-r_sq / (2 * sigma_atom**2))

    # zero out vacuum region (y > 0)
    V_proj[Y > 0] = 0.0

    return V_proj


if __name__ == "__main__":
    print(f"Peng-Cowley frame:")
    print(f"  x = {PC_X} (in-surface)")
    print(f"  y = {PC_Y} (surface normal)")
    print(f"  z = {PC_Z} (beam [110])")
    print(f"  Periods: x={PERIOD_X:.4f} A, z={PERIOD_Z:.4f} A")
    print()

    sc = generate_supercell(n_cells_x=4, n_cells_z=100,
                            crystal_depth_A=40.0, vacuum_thickness_A=40.0)
    print(f"Supercell: {sc['cell_x']:.2f} x {sc['cell_y']:.2f} x {sc['cell_z']:.2f} A")
    print(f"Crystal: y in [{sc['y_min']:.1f}, 0] A ({sc['crystal_depth']:.0f} A deep)")
    print(f"Vacuum:  y in [0, {sc['y_max']:.1f}] A ({sc['vacuum_thickness']:.0f} A)")
    print(f"Atoms in crystal: {sc['n_atoms']}")
    print(f"Slices: {sc['n_slices']} (dz={sc['dz']:.3f} A)")
    print(f"Propagation length: {sc['cell_z']:.1f} A = {sc['cell_z']/10:.1f} nm")

    expected_atoms = (sc['cell_x'] * sc['crystal_depth'] * sc['cell_z']
                      * 8 / SI_LATTICE_PARAM**3)
    print(f"Expected atoms (bulk density): {expected_atoms:.0f}")
    print(f"Actual/expected ratio: {sc['n_atoms']/expected_atoms:.3f}")

    # test one slice potential
    V = compute_projected_potential(
        sc["atoms_pc"], sc["cell_x"], sc["cell_y"], sc["y_min"],
        sc["dz"], 0, sc["dz"], nx_grid=256, ny_grid=256)
    print(f"\nSlice potential: max={V.max():.2f} V*A, "
          f"crystal fraction={np.mean(V > 0.1):.3f}")
