#!/bin/bash
#SBATCH --job-name=holo-rocking
#SBATCH --account=def-CHANGEME
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
# Flat-surface rocking curves for every reflection (cheap; sets the operating angles).
set -euo pipefail
source hpc/common.sh
for h in "0 0 8" "0 0 12"; do   # (004) sits at 2.1 mrad: a +-3 mrad scan would go negative
  python scripts/rocking_flat.py --surface 001 --hkl $h --span 3 --step 0.1 --backend cupy
done
