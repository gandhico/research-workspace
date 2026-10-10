# GitHub release plan: ACC 2027 project folder (DRAFT, 2026-10-01)

Target: `github.com/gandhico/Neuromorphic-Embodied-AI/online-pes-neuromorphic-residual-control/` (flat project folder,
per the portfolio rule). Nothing here is committed or pushed; drafts live in `C:\Research\github\_drafts\`.

## Principle: ship the verifiable core, archive the bulk

| Layer | Content | Size | Where |
|---|---|---|---|
| Code | `src/gra_control`, the five experiment folders' scripts, `reproduce/` | small | GitHub |
| Compact results | every `summary.json`, `manifest.json`, CSV/JSON table (2,639 runs) | ≈35 MB | GitHub |
| Documents | companion PDF, controller-family PDF, pre-registration, certification/audit reports | few MB | GitHub `docs/` |
| Raw traces | `trace.csv`, `neural_trace_full_rate.npz` | ≈57 GB | Zenodo (DOI), linked from `DATA.md` |

With only the GitHub layer, a reader can (a) recompute all 59 paper numbers in seconds, (b) check that the code they
read is byte-identical to the code that produced the runs (manifests hold the hashes), and (c) re-simulate any run.

## Recommended layout decision: keep the original dated experiment folders

The runners locate shared code by relative path (`parents[1]`, `experiments/nengo_nef_replication_2026-08-29`, `src/`),
and every manifest records the SHA-256 of those files. Keeping `src/gra_control/` and the dated folder names unchanged
means the scripts run unmodified and the hash check still passes. Renaming folders by paper section would read better but
would require editing scripts, changing their hashes and breaking that check. The paper-section view is given instead by
the README and `REPRODUCE.md` tables.

Consequence: the currently pushed folder (library at `gra_control/`, `Readme.md`) moves to `src/gra_control/` and
`README.md`.

## Included / excluded

Included: `nengo_nef_replication_2026-08-29`, `theory_certificate_2026-09-12`, `baseline_restatement_2026-09-16`,
`final_robustness_gating_2026-09-20`, `neuron_basis_decisive_2026-09-24` (scripts + compact results + reports).

Excluded (not used by the paper's numbers, or post-submission): `six_dof_expansion_2026-08-31`,
`gate_gain_sweep_2026-09-11` (check: referenced by any claim?), `neuromorphic_rl_attitude_2026-09-30` (RL pilot),
`backstepping_true_2026-10-01` (post-submission extension), `share/`, `tmp/`, `paper/` drafts, `.venv`, logs, smoke runs.

## Build steps (once the decisions below are made)

1. `tools/build_release.py`: copy the included folders, filter to code + compact results, drop `__pycache__`/logs/traces,
   rewrite nothing; write `RELEASE_MANIFEST.json` (every shipped file with SHA-256).
2. In the release copy: run `verify_acc2027_claims.py` (must print 59/59) and a hash check against the run manifests.
3. Convert `REPRODUCE_ACC2027.md` to `REPRODUCE.md` with repository-relative paths (no `C:\` paths).
4. Zenodo upload of the traces; put the DOI in `DATA.md` and `CITATION.cff`.
5. Commit to the working copy; push only on your go.

## Decisions needed from Gandhi

1. **Timing:** release the full package now (reviewers can use the link) or on acceptance (current convention)?
2. **Layout:** keep dated folder names (recommended, hash-verifiable) or rename by paper section?
3. **Raw data:** Zenodo (needs your account) or traces not released?
4. **Post-submission work** (recursive backstepping, controller-family document): omit until a paper, or add as
   `extensions/` clearly marked "not in the ACC paper"?
5. **Paper PDF:** add the accepted manuscript/preprint (IEEE author-posting policy) or only the companion documents?
6. **Identity:** ORCID 0009-0001-3686-9205 and email for README/CITATION.

## Corrections needed in the currently pushed README

- It lists "backstepping" as a family beyond PD. In the code that family is computed torque, algebraically identical to
  PD+ff with model feedforward off (its row equals the primary result). Call it "PD+ff (computed-torque form)" and count
  five families beyond PD+ff: PID+ff, LQR, SMC, MPC, NMPC.
- It says the library needs only NumPy + MuJoCo; the reported runs also need Nengo 4.1.0.
- `Readme.md` → `README.md`; Contact TODO; "Status: Private (pre-publication)" while the folder is public.
