"""Extended-XYZ writer records the frame; metadata JSON round trip."""
import hashlib
import json

import numpy as np

from reflection_holo.structure import read_xyz, write_metadata_json, write_xyz


def test_xyz_round_trip_records_frame(mixed_110, tmp_path):
    s = mixed_110
    p = write_xyz(s, tmp_path / "s.xyz", outputs_root=tmp_path / "outputs")
    species, pos, hdr = read_xyz(p)
    assert species.tolist() == ["Si"] * s.n_atoms
    assert np.max(np.abs(pos - s.positions_A)) < 1e-9
    assert np.allclose(np.array(hdr["Lattice"].split(), float).reshape(3, 3), s.cell_A)
    assert hdr["pbc"] == "F T T" and hdr["units"] == "angstrom"
    assert hdr["Properties"] == "species:S:1:pos:R:3"
    for key, v in (("x_hat_crystal", s.frame.x_hat), ("y_hat_crystal", s.frame.y_hat),
                   ("z_hat_crystal", s.frame.z_hat),
                   ("crystal_origin_slab_A", s.crystal_origin_slab_A)):
        assert np.allclose(np.array(hdr[key].split(), float), v, atol=1e-14)
    assert hdr["normal_hkl"] == "0 0 1" and hdr["azimuth_uvw"] == "1 1 0"
    assert hdr["azimuth_label"].startswith("TEST_ONLY")
    assert hdr["termination"] == "bulk (ASSUMPTION B3)"
    assert hdr["overlayer"] == "None (ASSUMPTION B7)"
    sha = hashlib.sha256(np.ascontiguousarray(s.positions_A, dtype="<f8").tobytes()).hexdigest()
    assert hdr["positions_sha256"] == sha == s.metadata["positions_sha256"]


def test_metadata_json_round_trip(mixed_110, tmp_path):
    s = mixed_110
    md = json.loads(write_metadata_json(s, tmp_path / "s.json",
                                        outputs_root=tmp_path / "outputs").read_text())
    assert md["atom_count"] == s.n_atoms
    assert md["azimuth"]["uvw"] == [1, 1, 0]
    assert [x["type"] for x in md["steps"]] == ["translation", "screw", "screw"]
    assert len(md["terrace_map"]) == 3
    assert md["options"]["termination"]["label"] == "ASSUMPTION B3"
    assert md["options"]["overlayer"]["label"] == "ASSUMPTION B7"
