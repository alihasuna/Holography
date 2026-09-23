#!/bin/bash
# Pack the small outputs of finished kit runs into one tarball with a checksum list, to bring the
# results back to the repository (run on a login node of the cluster; then scp the tarball home).
#
#   bash scripts/hpc/alliance/collect_results.sh --max-array-mb A --max-file-mb F --max-total-mb T
#        [--run-root DIR] [--jobs ID[,ID...]] [--out DIR]
#
# Caps, all REQUIRED (no default; 1 MB = 10^6 bytes, sizes before compression):
# --max-array-mb A  array files (*.npz, *.npy, *.h5, *.hdf5; e.g. exit waves) above A MB are
#                   dropped; 0 = no arrays
# --max-file-mb F   every other file above F MB is dropped
# --max-total-mb T  the packed files together stay within T MB: files are taken in a fixed order
#                   (non-array files first, then arrays; each group by path) and a file that would
#                   exceed T is dropped
# --run-root DIR    default $SCRATCH/reflholo (where submit.sh puts everything)
# --jobs IDS        only the runs, logs and submission records of these Slurm job ids (array: the
#                   array job id); default: every run under the run root
# --out DIR         where the tarball goes (default <run root>/collect)
#
# Taken from the selected runs: every file of runs/ and logs/, the submission records
# (submissions/) and the gpu-check PASS records, within the caps (cache/ and collect/ are not
# results and are never packed). Inside the tarball: MANIFEST.sha256 (verify after unpacking with
# `sha256sum -c MANIFEST.sha256`; macOS: `shasum -a 256 -c MANIFEST.sha256`), DROPPED_FILES.tsv
# (EVERY selected file that was not packed, with its size and the cap that dropped it),
# SKIPPED_ARRAYS.tsv (the arrays among them dropped by the array cap) and COLLECT_INFO.txt. Next to
# it: <tarball>.sha256.
set -euo pipefail

die() { local st=$1; shift; echo "ERROR: $*" >&2; exit "$st"; }

CAP=""
FCAP=""
TCAP=""
ROOT="${SCRATCH:+$SCRATCH/reflholo}"
JOBS=""
OUTD=""
while [ $# -gt 0 ]; do
  case "$1" in
    --max-array-mb) [ $# -ge 2 ] || die 2 "$1 needs a value"; CAP="$2"; shift 2 ;;
    --max-file-mb) [ $# -ge 2 ] || die 2 "$1 needs a value"; FCAP="$2"; shift 2 ;;
    --max-total-mb) [ $# -ge 2 ] || die 2 "$1 needs a value"; TCAP="$2"; shift 2 ;;
    --run-root) [ $# -ge 2 ] || die 2 "$1 needs a value"; ROOT="$2"; shift 2 ;;
    --jobs) [ $# -ge 2 ] || die 2 "$1 needs a value"; JOBS="$2"; shift 2 ;;
    --out) [ $# -ge 2 ] || die 2 "$1 needs a value"; OUTD="$2"; shift 2 ;;
    -h|--help) sed -n '2,26p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) die 2 "unknown option $1" ;;
  esac
done
[ -n "$CAP" ] || die 2 "--max-array-mb is required (no default; 0 = no arrays)"
[ -n "$FCAP" ] || die 2 "--max-file-mb is required (no default): the cap for every non-array file"
[ -n "$TCAP" ] || die 2 "--max-total-mb is required (no default): the cap for all packed files together"
num_ok() { case "$1" in ""|.|*.*.*|*[!0-9.]*) return 1 ;; esac; return 0; }
num_ok "$CAP" || die 2 "--max-array-mb must be a number, got $CAP"
num_ok "$FCAP" || die 2 "--max-file-mb must be a number, got $FCAP"
num_ok "$TCAP" || die 2 "--max-total-mb must be a number, got $TCAP"
[ -n "$ROOT" ] || die 2 "\$SCRATCH is not set: pass --run-root <scratch>/reflholo"
[ -d "$ROOT" ] || die 2 "run root $ROOT does not exist"
ROOT="$(cd "$ROOT" && pwd -P)"
bytes_of() { awk -v c="$1" 'BEGIN { printf "%.0f", c * 1000000 }'; }
CAP_BYTES="$(bytes_of "$CAP")"
FCAP_BYTES="$(bytes_of "$FCAP")"
TCAP_BYTES="$(bytes_of "$TCAP")"
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

sub_selected() {   # a submission file belongs to the job id written in its record's .sbatch_output
  [ "${#IDS[@]}" -eq 0 ] && return 0
  local f="$1" stem out jid id
  case "$f" in
    *.json.sbatch_output) stem="${f%.json.sbatch_output}" ;;
    *.study.yaml) stem="${f%.study.yaml}" ;;
    *.json) stem="${f%.json}" ;;
    *) return 1 ;;
  esac
  out="$stem.json.sbatch_output"
  [ -f "$out" ] || return 1
  jid="$(sed -n 's/^Submitted batch job \([0-9][0-9]*\).*/\1/p' "$out")"
  for id in "${IDS[@]}"; do [ "$jid" = "$id" ] && return 0; done
  return 1
}

LIST="$TMPD/files"                 # packed (NUL-separated, relative paths)
TXT="$TMPD/cand_text"              # candidates after the per-file caps: non-arrays, then arrays
ARR="$TMPD/cand_arrays"
: > "$LIST"; : > "$TXT"; : > "$ARR"
printf 'path\tbytes\n' > "$TMPD/SKIPPED_ARRAYS.tsv"
printf 'path\tbytes\treason\n' > "$TMPD/DROPPED_FILES.tsv"
n_sel=0
while IFS= read -r -d '' f; do
  rel="${f#"$ROOT"/}"
  case "$rel" in collect/*|cache/*) continue ;; esac
  case "$rel" in
    runs/*|logs/*|gpu_check/PASS_*.json) selected "$rel" || continue ;;
    submissions/*) sub_selected "$f" || continue ;;
    *) continue ;;
  esac
  n_sel=$((n_sel + 1))
  sz="$(stat -c %s "$f")"
  case "$rel" in
    *.npz|*.npy|*.h5|*.hdf5)
      if [ "$sz" -le "$CAP_BYTES" ]; then printf '%s\0' "$rel" >> "$ARR"
      else
        printf '%s\t%s\n' "$rel" "$sz" >> "$TMPD/SKIPPED_ARRAYS.tsv"
        printf '%s\t%s\tarray larger than --max-array-mb %s\n' "$rel" "$sz" "$CAP" >> "$TMPD/DROPPED_FILES.tsv"
      fi ;;
    *)
      if [ "$sz" -le "$FCAP_BYTES" ]; then printf '%s\0' "$rel" >> "$TXT"
      else printf '%s\t%s\tfile larger than --max-file-mb %s\n' "$rel" "$sz" "$FCAP" >> "$TMPD/DROPPED_FILES.tsv"; fi ;;
  esac
done < <(find "$ROOT" -type f -print0 | sort -z)

total=0
n=0
while IFS= read -r -d '' rel; do
  sz="$(stat -c %s "$ROOT/$rel")"
  if [ $((total + sz)) -le "$TCAP_BYTES" ]; then
    printf '%s\0' "$rel" >> "$LIST"; total=$((total + sz)); n=$((n + 1))
  else
    printf '%s\t%s\ttotal would exceed --max-total-mb %s\n' "$rel" "$sz" "$TCAP" >> "$TMPD/DROPPED_FILES.tsv"
  fi
done < <(cat "$TXT" "$ARR")
[ "$n" -gt 0 ] || die 2 "nothing to collect under $ROOT${JOBS:+ for jobs $JOBS} (selected $n_sel file(s); see the caps)"
n_drop=$(( $(wc -l < "$TMPD/DROPPED_FILES.tsv") - 1 ))
n_skip=$(( $(wc -l < "$TMPD/SKIPPED_ARRAYS.tsv") - 1 ))

( cd "$ROOT" && while IFS= read -r -d '' rel; do sha256sum -- "$rel"; done < "$LIST" ) > "$TMPD/MANIFEST.sha256"
{
  echo "collected_utc $STAMP"
  echo "host $(hostname)"
  echo "run_root $ROOT"
  echo "jobs ${JOBS:-all}"
  echo "max_array_mb $CAP"
  echo "max_file_mb $FCAP"
  echo "max_total_mb $TCAP"
  echo "selected_files $n_sel"
  echo "files $n"
  echo "packed_bytes $total"
  echo "dropped_files $n_drop"
  echo "skipped_arrays $n_skip"
} > "$TMPD/COLLECT_INFO.txt"
TAR="$OUTD/$NAME.tar.gz"
tar -czf "$TAR" -C "$TMPD" MANIFEST.sha256 DROPPED_FILES.tsv SKIPPED_ARRAYS.tsv COLLECT_INFO.txt \
    -C "$ROOT" --null -T "$LIST"
( cd "$OUTD" && sha256sum -- "$NAME.tar.gz" > "$NAME.tar.gz.sha256" )
echo "packed $n of $n_sel selected files ($total bytes before compression) into $TAR ($(stat -c %s "$TAR") bytes)"
echo "checksum: $TAR.sha256; dropped files: $n_drop (listed in DROPPED_FILES.tsv inside the tarball); skipped arrays: $n_skip"
if [ "$n_drop" -gt 0 ]; then
  echo "dropped:"
  tail -n +2 "$TMPD/DROPPED_FILES.tsv" | sed 's/^/  /'
fi
echo "bring it home, e.g.:  scp <cluster>:$TAR <cluster>:$TAR.sha256 ."
