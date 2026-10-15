#!/usr/bin/env python3
"""
export_structure.py
===================
Export the Si[110] reflection supercell as CIF, XYZ, and VESTA files.

Generates the crystal slab in the Peng-Cowley frame:
    x = [-1,1,2]/sqrt(6)   in-surface
    y = [1,-1,1]/sqrt(3)    surface normal (crystal below, vacuum above)
    z = [1,1,0]/sqrt(2)     beam direction

Usage:
    python -m simulation.export_structure
    python -m simulation.export_structure --depth 50 --vacuum 50 --ncx 6 --ncz 20
"""

import argparse
import numpy as np
from pathlib import Path
from datetime import date

from simulation.supercell import (
    generate_supercell, ROT_TO_CUBIC, PC_X, PC_Y, PC_Z,
    PERIOD_X, PERIOD_Z,
)
from simulation.constants import SI_LATTICE_PARAM


def export_xyz(atoms_pc, cell_x, cell_y, cell_z, outpath,
               comment=""):
    """Export atom positions as .xyz file.

    Standard XYZ format readable by VESTA, Ovito, ASE, Jmol, etc.
    """
    n = len(atoms_pc)
    with open(outpath, "w") as f:
        f.write(f"{n}\n")
        f.write(f"{comment}\n")
        for pos in atoms_pc:
            f.write(f"Si  {pos[0]:12.6f}  {pos[1]:12.6f}  {pos[2]:12.6f}\n")
    print(f"  XYZ: {outpath} ({n} atoms)")


def export_cif(atoms_pc, cell_x, cell_y, cell_z, outpath,
               y_min=0, y_max=None):
    """Export as CIF (Crystallographic Information File).

    Uses P1 symmetry with the full atom list (no symmetry reduction).
    The unit cell is the supercell in the Peng-Cowley frame.
    """
    if y_max is None:
        y_max = cell_y

    # CIF cell parameters: a=cell_x, b=cell_y_total, c=cell_z, all angles 90
    # (the PC frame is orthogonal)
    a = cell_x
    b = cell_y
    c = cell_z

    n = len(atoms_pc)

    with open(outpath, "w") as f:
        f.write("data_Si110_reflection_supercell\n")
        f.write(f"_audit_creation_date   {date.today().isoformat()}\n")
        f.write("_audit_creation_method  'simulation/export_structure.py'\n")
        f.write("\n")
        f.write(f"_cell_length_a    {a:.4f}\n")
        f.write(f"_cell_length_b    {b:.4f}\n")
        f.write(f"_cell_length_c    {c:.4f}\n")
        f.write("_cell_angle_alpha  90.0000\n")
        f.write("_cell_angle_beta   90.0000\n")
        f.write("_cell_angle_gamma  90.0000\n")
        f.write("\n")
        f.write("_symmetry_space_group_name_H-M  'P 1'\n")
        f.write("_symmetry_Int_Tables_number     1\n")
        f.write("\n")
        f.write("# Peng-Cowley frame for reflection multislice:\n")
        f.write("#   a (x) = [-1,1,2]/sqrt(6)  in-surface\n")
        f.write("#   b (y) = [1,-1,1]/sqrt(3)   surface outward normal\n")
        f.write("#   c (z) = [1,1,0]/sqrt(2)    beam direction\n")
        f.write(f"# Surface at y = 0 (fractional b = {-y_min/b:.4f})\n")
        f.write(f"# Crystal: y < 0, Vacuum: y > 0\n")
        f.write("\n")
        f.write("loop_\n")
        f.write("_atom_site_label\n")
        f.write("_atom_site_type_symbol\n")
        f.write("_atom_site_fract_x\n")
        f.write("_atom_site_fract_y\n")
        f.write("_atom_site_fract_z\n")

        for i, pos in enumerate(atoms_pc):
            fx = pos[0] / a
            fy = (pos[1] - y_min) / b  # shift so y_min maps to 0
            fz = pos[2] / c
            f.write(f"  Si{i+1:04d}  Si  {fx:.6f}  {fy:.6f}  {fz:.6f}\n")

    print(f"  CIF: {outpath} ({n} atoms, P1)")


def export_vesta_header(atoms_pc, cell_x, cell_y, cell_z, outpath,
                        y_min=0):
    """Export a minimal VESTA-readable file (.vesta format).

    VESTA can also open .cif and .xyz directly, but this provides
    pre-configured visualization settings.
    """
    a, b, c = cell_x, cell_y, cell_z
    n = len(atoms_pc)

    with open(outpath, "w") as f:
        f.write("#VESTA_FORMAT_VERSION 3.5.0\n\n")
        f.write("CRYSTAL\n\n")
        f.write("TITLE\n")
        f.write("Si[110] reflection supercell (Peng-Cowley frame)\n\n")
        f.write("GROUP\n")
        f.write("1 1 P 1\n\n")
        f.write("CELLP\n")
        f.write(f"  {a:.4f}  {b:.4f}  {c:.4f}  90.0000  90.0000  90.0000\n\n")
        f.write("STRUC\n")
        for i, pos in enumerate(atoms_pc):
            fx = pos[0] / a
            fy = (pos[1] - y_min) / b
            fz = pos[2] / c
            f.write(f"  {i+1:4d} Si   Si{i+1:04d}  1.0  {fx:.6f}  {fy:.6f}  {fz:.6f}\n")
        f.write("  0 0 0 0 0 0 0\n\n")
        f.write("THERI 0\n")
        for i in range(n):
            f.write(f"  {i+1:4d}  Si{i+1:04d}  1.0\n")
        f.write("  0 0 0\n\n")

    print(f"  VESTA: {outpath} ({n} atoms)")


def export_cubic_xyz(atoms_pc, outpath, comment=""):
    """Export atom positions converted back to cubic coordinates."""
    atoms_cubic = (ROT_TO_CUBIC @ atoms_pc.T).T
    n = len(atoms_cubic)
    with open(outpath, "w") as f:
        f.write(f"{n}\n")
        f.write(f"{comment} (cubic coordinates)\n")
        for pos in atoms_cubic:
            f.write(f"Si  {pos[0]:12.6f}  {pos[1]:12.6f}  {pos[2]:12.6f}\n")
    print(f"  XYZ (cubic): {outpath} ({n} atoms)")


def main():
    parser = argparse.ArgumentParser(
        description="Export Si[110] reflection supercell as CIF/XYZ/VESTA")
    parser.add_argument("--ncx", type=int, default=4,
                        help="Unit cells along x (in-surface)")
    parser.add_argument("--ncz", type=int, default=10,
                        help="Unit cells along z (beam direction)")
    parser.add_argument("--depth", type=float, default=30.0,
                        help="Crystal depth below surface (A)")
    parser.add_argument("--vacuum", type=float, default=30.0,
                        help="Vacuum above surface (A)")
    parser.add_argument("--outdir", type=str, default=None)
    args = parser.parse_args()

    outdir = (Path(args.outdir) if args.outdir
              else Path(__file__).resolve().parent.parent / "simulation_results")
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Generating supercell: {args.ncx}x cells, {args.ncz}z cells, "
          f"depth={args.depth} A, vacuum={args.vacuum} A")

    sc = generate_supercell(
        n_cells_x=args.ncx, n_cells_z=args.ncz,
        crystal_depth_A=args.depth,
        vacuum_thickness_A=args.vacuum)

    atoms = sc["atoms_pc"]
    cx, cy, cz = sc["cell_x"], sc["cell_y"], sc["cell_z"]

    print(f"Supercell: {cx:.2f} x {cy:.2f} x {cz:.2f} A, {sc['n_atoms']} atoms")
    print(f"Surface at y=0, crystal y<0, vacuum y>0")
    print()

    comment = (f"Si[110] reflection supercell, {cx:.1f}x{cy:.1f}x{cz:.1f} A, "
               f"surface at y=0, a={SI_LATTICE_PARAM} A")

    # XYZ in Peng-Cowley frame
    export_xyz(atoms, cx, cy, cz,
               outdir / "si110_supercell_pc.xyz", comment=comment)

    # XYZ in cubic frame
    export_cubic_xyz(atoms,
                     outdir / "si110_supercell_cubic.xyz", comment=comment)

    # CIF
    export_cif(atoms, cx, cy, cz,
               outdir / "si110_supercell.cif",
               y_min=sc["y_min"])

    # VESTA
    export_vesta_header(atoms, cx, cy, cz,
                        outdir / "si110_supercell.vesta",
                        y_min=sc["y_min"])

    print(f"\nAll files saved to {outdir}/")
    print(f"Open si110_supercell.cif in VESTA, or .xyz in Ovito/ASE.")


if __name__ == "__main__":
    main()
