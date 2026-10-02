# ACC 2027 - CSV results and provenance

This is the compact evidence companion to `ACC2027_CODE.zip`. CSV files are
copied byte-for-byte; no rounding, cropping, resampling, or selective deletion
of unfavorable rows is applied. Compression is lossless ZIP/Deflate.

## Contents

| Directory | Evidence |
|---|---|
| `project/experiments/nengo_nef_replication_2026-08-29/results/matched_45s` | 24 canonical PD/Nengo runs: two drones, five primary missions plus equilibrium Hover |
| `.../results/compiled` | Canonical paired tables and direct/Nengo equivalence results |
| `.../results/neuron_family_matched_45s` | Full 110-cell supplementary PD/fixed/PES neuron-family CSV campaign, including regressions |
| `.../results/neuron_family_compiled` | Family comparisons, correction-effort and activity summaries |
| `project/results/plots_data` | 24 direct-Python PD/CMG trace/summary sources, including equilibrium |
| `project/results/validation` | Saved X2/CF2 fixed, conductance, and online-PES validation cases |
| `hover3dof/.../results/hardware_armed_roll_n3_2026-09-01` | Repeated physical Roll aggregate and paired-trial CSV |
| `hover3dof/.../results/hardware` | All six raw physical runs referenced by that Roll aggregate |
| `hover3dof/.../results/DIRECT_NENGO_FINAL_2026-09-01` | Later physical campaign including unfavorable Full3/Yaw results and saved interrupted yaw attempts |
| `hover3dof/.../results/FROZEN_AUDIT_2026-09-02` | Complete campaign inventory and approval/validity context |
| `legacy` | Three traceable precursor JSONs and a faithful tabular CSV export of their scalar summaries |

The inventory documents other historical runs whose raw data are not included;
it is not a claim that this ZIP contains the entire research-drive backup.

## Units, timing, and interpretation

- Main MuJoCo metric: mean shortest quaternion-angle error, radians. Plot
  displays may convert to degrees; do not mix units.
- Full-rate summaries use 90,000 samples over 45 seconds at 0.5 ms. Most
  canonical CSVs log every tenth sample; X2 Hard45 retains all samples.
  Do not silently replace a full-rate summary mean by a decimated trace mean.
- `saturation_fraction` is a fraction, not a percentage. Hardstep has small
  nonzero bound occupancy. Multiplying by 100 gives the paper's percentages.
- Hover selected values use mean norm of wrapped yaw/pitch/roll error in
  degrees; separate quaternion fields must not be mislabeled as that metric.
- CF2 rotor design has 1.5x declared thrust authority. It is not stock hardware.
- Legacy annealing uses a different blend/wrench architecture. Only three
  comparisons are traceable; seven v4 table cells remain unverified and are
  deliberately not reconstructed or invented. The legacy runner saved summary
  JSON, not corresponding raw trace CSVs; `precursor_summaries.csv` is explicitly
  a summary export, not newly recovered time-series data.

## Size reduction without altering CSV evidence

Excluded: plot PNG/PDF files, binary full-rate NPZ neuron/probe archives,
GUI-session duplicates, pilot/smoke runs, redundant frozen ZIPs, `.venv`,
cache files, and historical platforms outside the audited manuscript scope.
Full-rate binary neural records remain in the research workspace; the code
bundle can generate new ones using `--full-neural-data`.

Small JSON summaries, configurations, schemas, and manifests are retained
because CSV traces alone cannot specify gains, models, software versions,
arming/completion status, or logging stride. References to omitted NPZs in
original JSON/CSV files are preserved as historical metadata; those NPZs are
not silently represented as present in this archive.

`FILES.csv` is the authoritative map from archived paths to original paths,
byte sizes, and SHA-256 checksums. Original metadata contains absolute lab
paths; use this map to locate the corresponding delivered file. Original
upstream frozen manifests may enumerate files intentionally omitted here;
the new `FILES.csv`, not those upstream inventories, defines ZIP completeness.

## Verify and use

Extract alongside the code bundle. Use its `verify_archive.py` to verify every
payload checksum directly against the ZIP. Open the `compiled/matched_results.csv`
table first. Consult `documentation/ACC2027_V4_TO_V5_AUDIT_2026-09-04.md` before
combining tables across architectures or reporting claims.

No physical hardware or new experiment was run while assembling these saved
results. Package qualification tests are recorded separately in the code ZIP;
they are not appended to the historical result CSVs.
