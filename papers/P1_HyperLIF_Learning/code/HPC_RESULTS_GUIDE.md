# Paper 2 HPC cube — what to expect & how to consult it any time

The dense-net × 7-variant roster run writes to `$HLL_RESULTS` (=`results_roster60`). One row per
finished config; **3360 rows when complete** (112 bundles × 30). Always `source hpc/paths.sh` and
`export HLL_RESULTS=$HLL_SCRATCH/results_roster60` first.

## The registry schema
`_registry.csv` columns (1-indexed for awk):
```
1 dataset  2 arch  3 neuron  4 readout  5 seed  6 accuracy  7 macro_f1
8 events_per_sample  9 gate_mean  10 stable  11 nan_batches  12 n_classes  13 T  14 provenance  15 wall_s
```

## The results to expect (the story the cube tells)
1. **Architecture transfer (§6.4 headline):** HyperLIF ≥ LIF across arch × dataset. Best-config
   accuracy per (dataset, arch, neuron). Prior §6.4 saw +0.01…+0.15 in all 13 cells.
2. **Does the gain survive in the dense net?** `convres` (14M) HyperLIF vs LIF — the SOTA-class test.
3. **Which variant wins:** among `lif / hyperlif / hyperlif_t0.95 / adaptive / adaptive_t0.95 /
   adaptive_origin / adaptive_dreset`, per arch/dataset. (θ_event densifies; origin is a temporal asset.)
4. **Efficiency dial:** `events_per_sample` — HyperLIF ~15–200× sparser than LIF in conv; convres
   mid-range.
5. **Structural blindness:** `lif.gate` / `lif.hybrid_*` collapse to chance; `hyperlif.gate` is strong.
6. **Readout tracks firing regime:** membrane on spatial, spike_count on motion, hybrid on audio.

## Consult any time — copy-paste queries
```bash
source hpc/paths.sh; export HLL_RESULTS=$HLL_SCRATCH/results_roster60; R=$HLL_RESULTS/_registry.csv

# progress + health
awk -F, 'END{print NR-1" / 3360 configs done"}' $R
awk -F, 'NR>1{t++; if($10=="True")s++} END{print s"/"t" stable, "t-s" unstable"}' $R

# is the submitter still alive / queue state
squeue -u $USER | tail; tail -3 $HLL_SCRATCH/roster_submit.log

# convres canary — the head-drive + spike-prop fixes on real data (want events>0, gate>0)
grep ',convres,.*,hyperlif,' $R | head

# best accuracy per (dataset, arch, neuron)  — the transfer table
awk -F, 'NR>1{k=$1","$2","$3; if($6>m[k]){m[k]=$6}} END{for(k in m) print k, m[k]}' $R | sort

# HyperLIF vs LIF gap per (dataset, arch): best hyperlif - best lif
awk -F, 'NR>1{k=$1","$2; if($3=="lif"&&$6>l[k])l[k]=$6; if($3=="hyperlif"&&$6>h[k])h[k]=$6}
         END{for(k in h) printf "%-28s LIF %.3f  HyperLIF %.3f  gap %+.3f\n",k,l[k],h[k],h[k]-l[k]}' $R | sort

# efficiency: events/sample per (arch, neuron), best-accuracy row's events
awk -F, 'NR>1{k=$2","$3; if($6>m[k]){m[k]=$6; e[k]=$8}} END{for(k in m) printf "%-22s acc %.3f  events %.1f\n",k,m[k],e[k]}' $R | sort

# per-readout winner for a given arch (e.g. convres)
awk -F, 'NR>1 && $2=="convres"{k=$3","$4; if($6>m[k])m[k]=$6} END{for(k in m) print k, m[k]}' $R | sort
```

## When you want the full analysis / figures / paper text
```bash
python hpc/aggregate_hpc.py --results-root $HLL_RESULTS   # tidy _registry.csv + summary
```
Then **send me `results_roster60/_registry.csv`** (scp/OnDemand it down) and I'll: rank the winners,
regenerate the §6.4 transfer heatmap + efficiency Pareto (`hpc/make_arch_figures.py`), and write the
numbers into `08/paper/paper2_manuscript.md`. I can also build a live progress dashboard from a partial
registry any time — just paste the `awk` progress line or send the CSV.

## Expected timeline & success signals
- ~2–3 days total; convres (batch 16) is the long pole. Light archs finish first.
- Healthy convres bundle = **~1 h elapsed** (not 2.5 min) and non-zero `events`/`gate` in the canary.
- The nohup submitter (`hpc/submit_loop.sh`, logs to `$HLL_SCRATCH/roster_submit.log`) survives
  disconnect; if it ever dies, just re-run it — `--skip-existing` resumes with nothing lost.
