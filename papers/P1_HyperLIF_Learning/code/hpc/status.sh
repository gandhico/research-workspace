#!/bin/bash
# Quick progress glance for the HyperLIF array.  Usage:  bash hpc/status.sh
source "$(cd "$(dirname "$0")" && pwd)/paths.sh"
JOB=hyperlif_ev

echo "caches ($HLL_CACHE):"
ls -1 "$HLL_CACHE"/*.pt 2>/dev/null | sed 's#.*/#  #' || echo "  (none)"
TOT=$(python "$HLL_ROOT/hpc/grid.py" --count 2>/dev/null)
echo "grid: ${TOT:-?} jobs"

echo "queue ($USER / $JOB):"
squeue -u "$USER" -n "$JOB" -h -o "%t" | sort | uniq -c | awk '{printf "  %s=%s\n",$2,$1}'
[ -z "$(squeue -u "$USER" -n "$JOB" -h)" ] && echo "  (nothing queued)"

REG="$HLL_RESULTS/_registry.csv"
if [ -f "$REG" ]; then
  DONE=$(( $(wc -l < "$REG") - 1 ))
  echo "finished: $DONE / ${TOT:-?}"
  echo "by dataset/arch:"
  tail -n +2 "$REG" | awk -F, '{print $1"/"$2}' | sort | uniq -c | awk '{printf "  %-28s %s\n",$2,$1}'
  # find the 'stable' column by header (robust to added columns like arch)
  BAD=$(awk -F, 'NR==1{for(i=1;i<=NF;i++)if($i=="stable")c=i} NR>1 && c && $c!="True"{n++} END{print n+0}' "$REG")
  echo "unstable rows (stable!=True): $BAD"
else
  echo "no registry yet ($REG)"
fi
