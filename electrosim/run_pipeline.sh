#!/usr/bin/env bash
# The first ElectroSim test of the holography pipeline, every step recorded by gemicro.
#
# Run from the gemicro project root, after copying this folder's code/ to <project>/code/ and params/ to
# <project>/params/ (see README.md). Each step is one `gemicro run`; the script stops at the first failure.
#
#   bash code/run_pipeline.sh            # everything: slab, GPU exit wave, holograms, reconstruction, controls
#   STEPS="recon validate" bash code/run_pipeline.sh     # only some steps (names below)
#
# Environment paths can be overridden (e.g. for a laptop test): EM_ABTEM=... EM_HOLO=... GEMICRO=...
set -euo pipefail

EM_ABTEM=${EM_ABTEM:-/opt/envs/em-abtem/bin/python}
EM_HOLO=${EM_HOLO:-/opt/envs/em-holography/bin/python}
GEMICRO=${GEMICRO:-gemicro}
STEPS=${STEPS:-"slab exit-wave image-wave hologram recon validate controls check"}

[ -f gemicro.json ] || { echo "run this from the gemicro project root (no gemicro.json here)"; exit 2; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
say() { printf '\n=== %s\n' "$*"; }

if want slab; then
  say "1/8 slab (em-abtem, CPU)"
  "$GEMICRO" run --kind sim --name slab --params params/slab.yaml --output sims/slab -- \
    "$EM_ABTEM" code/si110_cleave_slab_generator.py --params params/slab.yaml --output sims/slab
fi

if want exit-wave; then
  say "2/8 exit wave (em-abtem, GPU): is the GPU slice free?"
  "$GEMICRO" gpu || true
  "$GEMICRO" run --kind sim --name exit-wave --input sims/slab/si110_slab.extxyz --params params/exit_wave.yaml \
    --output sims/exit-wave -- \
    "$EM_ABTEM" code/multislice_forward_model.py --params params/exit_wave.yaml \
    --structure sims/slab/si110_slab.extxyz --output sims/exit-wave
fi

if want image-wave; then
  say "3/8 objective aperture -> image wave (em-holography, CPU)"
  "$GEMICRO" run --kind process --name image-wave --input sims/exit-wave/exit_wave.npy \
    --params params/specular_filter.yaml --output derived/image-wave -- \
    "$EM_HOLO" code/specular_filter.py --params params/specular_filter.yaml --exit-wave sims/exit-wave \
    --output derived/image-wave
fi

if want hologram; then
  say "4/8 object + reference holograms (em-holography, CPU)"
  "$GEMICRO" run --kind process --name hologram --input derived/image-wave/image_wave.npy \
    --params params/hologram.yaml --output derived/hologram -- \
    "$EM_HOLO" code/hologram_formation.py --params params/hologram.yaml --image-wave derived/image-wave \
    --output derived/hologram
fi

if want recon; then
  say "5/8 reconstruction (em-holography, CPU, HoloSpy)"
  "$GEMICRO" run --kind analysis --name holo-recon --input derived/hologram/hologram.npy \
    --input derived/hologram/reference_hologram.npy --params params/holo.yaml --output derived/holo-recon -- \
    "$EM_HOLO" code/holo_recon.py --params params/holo.yaml --hologram derived/hologram --output derived/holo-recon
fi

if want validate; then
  say "6/8 validation against the truth (expected: PASS)"
  "$GEMICRO" run --kind analysis --name holo-validate --input derived/holo-recon/phase_unwrapped.npy \
    --input derived/hologram/image_wave_detector.npy --input sims/exit-wave/ground_truth_phase.npy \
    --params params/validate.yaml --output derived/holo-validate -- \
    "$EM_HOLO" code/holo_validate.py --params params/validate.yaml --recon derived/holo-recon \
    --hologram derived/hologram --exit-wave sims/exit-wave --slab sims/slab --output derived/holo-validate
fi

if want controls; then
  for c in no_reference wrong_sideband; do
    n=${c//_/-}
    say "7/8 control: $c (reconstruction, then validation expected to FAIL)"
    "$GEMICRO" run --kind analysis --name "holo-recon-control-$n" --input derived/hologram/hologram.npy \
      --input derived/hologram/reference_hologram.npy --params "params/holo_control_$c.yaml" \
      --output "derived/holo-recon-control-$n" -- \
      "$EM_HOLO" code/holo_recon.py --params "params/holo_control_$c.yaml" --hologram derived/hologram \
      --output "derived/holo-recon-control-$n"
    "$GEMICRO" run --kind analysis --name "holo-validate-control-$n" \
      --input "derived/holo-recon-control-$n/phase_unwrapped.npy" --params params/validate_control.yaml \
      --output "derived/holo-validate-control-$n" -- \
      "$EM_HOLO" code/holo_validate.py --params params/validate_control.yaml \
      --recon "derived/holo-recon-control-$n" --hologram derived/hologram --exit-wave sims/exit-wave \
      --slab sims/slab --output "derived/holo-validate-control-$n"
  done
fi

if want check; then
  say "8/8 output check and ledger verification"
  "$GEMICRO" run --kind analysis --name check-outputs --params params/output_validator.yaml \
    --output derived/check-outputs -- \
    "$EM_HOLO" code/output_validator.py --params params/output_validator.yaml --stage sims/slab \
    --stage sims/exit-wave --stage derived/image-wave --stage derived/hologram --stage derived/holo-recon \
    --stage derived/holo-validate --output derived/check-outputs
  "$GEMICRO" verify
fi
