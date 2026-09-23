#!/bin/bash
# Pack the small outputs of finished kit runs into one tarball with a checksum list, to bring the
# results back to the repository (run on a login node of the cluster; then scp the tarball home).
#
#   bash scripts/hpc/alliance/collect_results.sh --max-array-mb N [--run-root DIR]
#        [--jobs ID[,ID...]] [--out DIR]
#
# --max-array-mb N  REQUIRED (no default): array files (*.npz, *.npy, *.h5, *.hdf5; e.g. exit waves)
#                   are included only if at most N MB (1 MB = 10^6 bytes); 0 = no arrays. Larger
#                   ones are listed with their size in SKIPPED_ARRAYS.tsv.
# --run-root DIR    default $SCRATCH/reflholo (where submit.sh puts everything)
# --jobs IDS        only the runs, logs and submission records of these Slurm job ids (array: the
#                   array job id); default: every run under the run root
# --out DIR         where the tarball goes (default <run root>/collect)
#
# Always included from the selected runs: *.json (summaries, manifests, results, job records),
# *.csv, *.tsv, *.txt, *.log, *.png, *.yaml/*.yml, *.md; the Slurm logs (logs/), the submission
# records (submissions/) and the gpu-check PASS records. Inside the tarball: MANIFEST.sha256
# (verify after unpacking with `sha256sum -c MANIFEST.sha256`), SKIPPED_ARRAYS.tsv and
# COLLECT_INFO.txt. Next to it: <tarball>.sha256.
set -euo pipefail

die() { local st=$1; shift; echo "ERROR: $*" >&2; exit "$st"; }

CAP=""
ROOT="${SCRATCH:+$SCRATCH/reflholo}"
JOBS=""
OUTD=""
while [ $# -gt 0 ]; do
  case "$1" in
    --max-array-mb) [ $# -ge 2 ] || die 2 "$1 needs a value"; CAP="$2"; shift 2 ;;
    --run-root) [ $# -ge 2 ] || die 2 "$1 needs a value"; ROOT="$2"; shift 2 ;;
    --jobs) [ $# -ge 2 ] || die 2 "$1 needs a value"; JOBS="$2"; shift 2 ;;
    --out) [ $# -ge 2 ] || die 2 "$1 needs a value"; OUTD="$2"; shift 2 ;;
    -h|--help) sed -n '2,23p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) die 2 "unknown option $1" ;;
  esac
done
[ -n "$CAP" ] || die 2 "--max-array-mb is required (no default; 0 = no arrays)"
case "$CAP" in *[!0-9.]*|"") die 2 "--max-array-mb must be a number, got $CAP" ;; esac
[ -n "$ROOT" ] || die 2 "\$SCRATCH is not set: pass --run-root <scratch>/reflholo"
[ -d "$ROOT" ] || die 2 "run root $ROOT does not exist"
ROOT="$(cd "$ROOT" && pwd -P)"
CAP_BYTES="$(awk -v c="$CAP" 'BEGIN { printf "%.0f", c * 1000000 }')"
OUTD="${OUTD:-$ROOT/collect}"
mkdir -p "$OUTD"
OUTD="$(cd "$OUTD" && pwd -P)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NAME="reflholo_results_$(hostname -s)_${STAMP}"
TMPD="$(mktemp -d)"
trap 'rm -rf "$TMPD"' EXIT

# selected job ids -> path patterns
IDS=()
if [ -n "$JOBS" ]; then
  IFS=',' read -r -a IDS <<< "$JOBS"
  for id in ${IDS[@]+"${IDS[@]}"}; do
    case "$id" in *[!0-9]*|"") die 2 "--jobs takes numeric Slurm job ids, got '$id'" ;; esac
  done
fi
selected() {   # $1 = path relative to the run root
  [ "${#IDS[@]}" -eq 0 ] && return 0
  local id
  for id in "${IDS[@]}"; do
    case "$1" in
      *_"$id"_*|*_"$id"/*|*_"$id".log|*_"$id"_*.log|*_"$id".json) return 0 ;;
    esac
  done
  return 1
}

sub_selected() {   # a submission record belongs to the job id written in its .sbatch_output
  [ "${#IDS[@]}" -eq 0 ] && return 0
  local out="${1%.sbatch_output}.sbatch_output" jid id
  [ -f "$out" ] || return 1
  jid="$(sed -n 's/^Submitted batch job \([0-9][0-9]*\).*/\1/p' "$out")"
  for id in "${IDS[@]}"; do [ "$jid" = "$id" ] && return 0; done
  return 1
}

LIST="$TMPD/files"
: > "$LIST"
: > "$TMPD/SKIPPED_ARRAYS.tsv"
printf 'path\tbytes\n' > "$TMPD/SKIPPED_ARRAYS.tsv"
n=0
while IFS= read -r -d '' f; do
  rel="${f#"$ROOT"/}"
  case "$rel" in collect/*|cache/*) continue ;; esac
  case "$rel" in
    runs/*|logs/*|gpu_check/PASS_*.json) selected "$rel" || continue ;;
    submissions/*) sub_selected "$f" || continue ;;
    *) continue ;;
  esac
  case "$rel" in
    *.npz|*.npy|*.h5|*.hdf5)
      sz="$(stat -c %s "$f")"
      if [ "$sz" -le "$CAP_BYTES" ]; then printf '%s\0' "$rel" >> "$LIST"; n=$((n + 1))
      else printf '%s\t%s\n' "$rel" "$sz" >> "$TMPD/SKIPPED_ARRAYS.tsv"; fi ;;
    *.json|*.csv|*.tsv|*.txt|*.log|*.png|*.yaml|*.yml|*.md|*.sbatch_output)
      printf '%s\0' "$rel" >> "$LIST"; n=$((n + 1)) ;;
  esac
done < <(find "$ROOT" -type f -print0 | sort -z)
[ "$n" -gt 0 ] || die 2 "nothing to collect under $ROOT${JOBS:+ for jobs $JOBS}"

( cd "$ROOT" && while IFS= read -r -d '' rel; do sha256sum -- "$rel"; done < "$LIST" ) > "$TMPD/MANIFEST.sha256"
{
  echo "collected_utc $STAMP"
  echo "host $(hostname)"
  echo "run_root $ROOT"
  echo "jobs ${JOBS:-all}"
  echo "max_array_mb $CAP"
  echo "files $n"
  echo "skipped_arrays $(( $(wc -l < "$TMPD/SKIPPED_ARRAYS.tsv") - 1 ))"
} > "$TMPD/COLLECT_INFO.txt"
TAR="$OUTD/$NAME.tar.gz"
tar -czf "$TAR" -C "$TMPD" MANIFEST.sha256 SKIPPED_ARRAYS.tsv COLLECT_INFO.txt \
    -C "$ROOT" --null -T "$LIST"
( cd "$OUTD" && sha256sum -- "$NAME.tar.gz" > "$NAME.tar.gz.sha256" )
echo "packed $n files into $TAR ($(stat -c %s "$TAR") bytes)"
echo "checksum: $TAR.sha256; skipped arrays: $(( $(wc -l < "$TMPD/SKIPPED_ARRAYS.tsv") - 1 ))"
echo "bring it home, e.g.:  scp <cluster>:$TAR <cluster>:$TAR.sha256 ."
