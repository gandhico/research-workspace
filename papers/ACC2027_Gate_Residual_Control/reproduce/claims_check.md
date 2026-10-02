| # | section | claim | paper | recomputed | status | source |
|---|---|---|---|---|---|---|
| 1 | VI-B primary | x2 gated geo reduction | 37.3 | 37.3 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 2 | VI-B primary | cf2-rotor gated geo reduction | 22.4 | 22.4 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 3 | VI-B primary | x2 geo error PD+ff -> CMG (1e-3 rad) | 4.54->2.85 | 4.54->2.85 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 4 | VI-B primary | cf2-rotor geo error PD+ff -> CMG (1e-3 rad) | 3.77->2.92 | 3.77->2.92 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 5 | VI-B primary | CF2 ungated beta=.05 geo | 6.5 | 6.5 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 6 | VI-B primary | X2 ungated geo | 35.6 | 35.6 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 7 | VI-B primary | Full3/Hard45 reductions X2 | 12.4/13.8 | 12.4/13.8 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 8 | VI-B primary | Full3/Hard45 reductions CF2 | 5.4/7.3 | 5.4/7.3 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 9 | Table II rho=1 | x2 geo reduction on PD+ff rho=1 | 57.8 | 57.8 | OK | `baseline_restatement/master_table.csv  (build_restatement.py over nengo_nef_replication results)` |
| 10 | Table II rho=1 | cf2-rotor geo reduction on PD+ff rho=1 | 57.6 | 57.6 | OK | `baseline_restatement/master_table.csv  (build_restatement.py over nengo_nef_replication results)` |
| 11 | Table II fixed PD | x2 geo reduction on fixed PD | 44.5 | 44.5 | OK | `baseline_restatement/master_table.csv  (build_restatement.py over nengo_nef_replication results)` |
| 12 | Table II fixed PD | cf2-rotor geo reduction on fixed PD | 44.2 | 44.2 | OK | `baseline_restatement/master_table.csv  (build_restatement.py over nengo_nef_replication results)` |
| 13 | VI-B primary | fixed-PD range, all ten cells | 17.3-60.6 | 17.3-60.6 | OK | `baseline_restatement/master_table.csv  (build_restatement.py over nengo_nef_replication results)` |
| 14 | VI-B portability | lqr | 31.1/22.4 | 31.1/22.4 | OK | `final_robustness_gating/results/a5_numbers.json  (run_campaign_a5*.py -> analyze_a5.py)` |
| 15 | VI-B portability | pid | 36.7/22.4 | 36.7/22.4 | OK | `final_robustness_gating/results/a5_numbers.json  (run_campaign_a5*.py -> analyze_a5.py)` |
| 16 | VI-B portability | smc | 43.8/26.6 | 43.8/26.6 | OK | `final_robustness_gating/results/a5_numbers.json  (run_campaign_a5*.py -> analyze_a5.py)` |
| 17 | VI-B portability | mpc | 33.4/22.7 | 33.4/22.7 | OK | `final_robustness_gating/results/a5_numbers.json  (run_campaign_a5*.py -> analyze_a5.py)` |
| 18 | VI-B portability | nmpc | 31.9/21.7 | 31.9/21.7 | OK | `final_robustness_gating/results/a5_numbers.json  (run_campaign_a5*.py -> analyze_a5.py)` |
| 19 | VI-B portability | backstepping | 37.3/22.4 | 37.3/22.4 | OK | `final_robustness_gating/results/a5_numbers.json  (run_campaign_a5*.py -> analyze_a5.py)` |
| 20 | Table II Izhikevich | x2 Delta row (5 missions, geo) | -48.0,5.8,4.5,-1.1,-76.3,-18.9 | -48.0,5.8,4.5,-1.1,-76.3,-18.9 | OK | `neuron_basis_decisive/results/strict_exact/<plat>/<mission>/<basis>  (run_campaign.py)` |
| 21 | Table II Izhikevich | cf2-rotor Delta row (5 missions, geo) | 0.7,1.3,0.8,-0.5,-33.3,-5.4 | 0.7,1.3,0.8,-0.5,-33.3,-5.4 | OK | `neuron_basis_decisive/results/strict_exact/<plat>/<mission>/<basis>  (run_campaign.py)` |
| 22 | Abstract / VI-D | Izhikevich geo increase X2/CF2 | 18.9/5.4 | 18.9/5.4 | OK | `neuron_basis_decisive/results/strict_exact/<plat>/<mission>/<basis>  (run_campaign.py)` |
| 23 | VI-D | Izhikevich geo error ratio X2/CF2 | 1.19/1.05 | 1.19/1.05 | OK | `neuron_basis_decisive/results/strict_exact/<plat>/<mission>/<basis>  (run_campaign.py)` |
| 24 | VI-D | Izhikevich Full3/Hard45 X2 | 5.8/4.5 | 5.8/4.5 | OK | `neuron_basis_decisive/results/strict_exact/<plat>/<mission>/<basis>  (run_campaign.py)` |
| 25 | Table II Izhikevich | x2 effort row | 0.053,0.051,0.053,0.106,0.052,0.063 | 0.053,0.051,0.053,0.106,0.052,0.063 | OK | `final_robustness_gating/results_izh_corrected/table2_full_2026-09-29  (run_izh_corrected.py)` |
| 26 | Table II Izhikevich | cf2-rotor effort row | 0.012,0.021,0.021,0.047,0.012,0.023 | 0.012,0.021,0.021,0.047,0.012,0.023 | OK | `final_robustness_gating/results_izh_corrected/table2_full_2026-09-29  (run_izh_corrected.py)` |
| 27 | Table II Izhikevich | x2 CMG effort row | 0.003,0.023,0.023,0.109,0.001,0.032 | 0.003,0.023,0.023,0.109,0.001,0.032 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 28 | Table II Izhikevich | cf2-rotor CMG effort row | 0.005,0.010,0.012,0.049,<0.001,0.015 | 0.005,0.010,0.012,0.049,<0.001,0.015 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 29 | VI-D | Izhikevich rail fraction range (%) | 0-1.7 | 0-1.7 | OK | `results_izh_corrected/table2_full_2026-09-29/*/trace.csv  (method of rail_fraction_izh.py)` |
| 30 | Table II Izhikevich | x2 Delta row, fixed PD | 39.6,37.5,32.2,6.6,46.6,33.8 | 39.6,37.5,32.2,6.6,46.6,33.8 | OK | `nengo_nef_replication/results/izh_fixed_pd_corrected_2026-09-24  (run_fixed_pd_izh_corrected.py)` |
| 31 | Table II Izhikevich | cf2-rotor Delta row, fixed PD | 33.7,38.9,32.2,diverges,41.5,-- | 33.7,38.9,32.2,diverges,41.5,-- | OK | `nengo_nef_replication/results/izh_fixed_pd_corrected_2026-09-24  (run_fixed_pd_izh_corrected.py)` |
| 32 | VI-D alternatives | paired-current | 11.9/4.8 | 11.9/4.8 | OK | `neuron_basis_decisive/results/strict_exact/<plat>/<mission>/<basis>  (run_campaign.py)` |
| 33 | VI-D alternatives | constant-one | 10.3/4.3 | 10.3/4.3 | OK | `neuron_basis_decisive/results/strict_exact/<plat>/<mission>/<basis>  (run_campaign.py)` |
| 34 | VI-D alternatives | LIFRate threshold-aware, held out | 15.8/11.4 | 15.8/11.4 | OK | `neuron_basis_decisive/results/selected_validate  (select_development.py -> run_selected_validation.py)` |
| 35 | VI-D | LIF/ALIF/LIFRate active unit-samples, mission mean, rho=3 (%) | 3.2-4.4 | 3.2-4.4 | OK | `strict_exact/*/{lif,alif,lifrate}/neural_trace_full_rate.npz` |
| 36 | VI-E noise | seeds moderate/realistic | 5/10 | 5/10 | OK | `final_robustness_gating/results/final_noise.csv  (run_campaign.py --campaign noise, run_campaign_a2.py)` |
| 37 | VI-E noise | realistic Full3/Hard45 X2 | 11.3/10.8 | 11.3/10.8 | OK | `final_robustness_gating/results/final_noise.csv  (run_campaign.py --campaign noise, run_campaign_a2.py)` |
| 38 | VI-E noise | realistic Full3/Hard45 CF2 | 3.9/4.0 | 3.9/4.0 | OK | `final_robustness_gating/results/final_noise.csv  (run_campaign.py --campaign noise, run_campaign_a2.py)` |
| 39 | VI-E noise | Roll/Yaw360 change range | -5.3..2.2 | -5.3..2.2 | OK | `final_robustness_gating/results/final_noise.csv  (run_campaign.py --campaign noise, run_campaign_a2.py)` |
| 40 | VI-E noise | realistic geo X2/CF2 | 2.3/1.0 | 2.3/1.0 | OK | `final_robustness_gating/results/final_noise.csv  (run_campaign.py --campaign noise, run_campaign_a2.py)` |
| 41 | VI-E noise | CF2 beta=.5 Hardstep diverges | 15/15 | 15/15 | OK | `final_robustness_gating/results/final_noise.csv  (run_campaign.py --campaign noise, run_campaign_a2.py)` |
| 42 | VI-E noise | rotor-bound share (%) | 61-79 | 61-79 | OK | `final_robustness_gating/results/final_noise.csv  (run_campaign.py --campaign noise, run_campaign_a2.py)` |
| 43 | VI-E disturbance | x2 burst reduction 1x | 14.4 | 14.4 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 44 | VI-E disturbance | cf2-rotor burst reduction 1x | 5.9 | 5.9 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 45 | VI-E disturbance | x2 burst reduction 0.5x/2x | 24.0/13.3 | 24.0/13.3 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 46 | VI-E disturbance | cf2-rotor burst reduction 0.5x/2x | 6.5/4.7 | 6.5/4.7 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 47 | VI-E disturbance | x2 burst error (deg) | 1.61->1.38 | 1.61->1.38 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 48 | VI-E disturbance | cf2-rotor burst error (deg) | 2.27->2.14 | 2.27->2.14 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 49 | VI-E disturbance | x2 quiet reduction 1x | 14.7 | 14.7 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 50 | VI-E disturbance | cf2-rotor quiet reduction 1x | 19.8 | 19.8 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 51 | VI-E disturbance | X2 quiet 0.5x (deg) | 0.021->0.036 | 0.021->0.036 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 52 | VI-E disturbance | CF2 burst 1x at beta=.5 / beta=.05 | 13.7/1.5 | 13.7/1.5 | OK | `final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)` |
| 53 | VI-F Hardstep | X2 ungated / gated | -17.0/-2.0 | -17.0/-2.0 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 54 | VI-F Hardstep | CF2 beta=.5 gated Hardstep / geo | -1.2/36.5 | -1.2/36.5 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 55 | VI-F Hardstep | CF2 beta=.5 ungated divergence (deg, rotor %) | 136/92 | 136/92 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 56 | VI-F Hardstep | gate blocked share X2/CF2 (%) | 20.5/15.5 | 20.5/15.5 | OK | `final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)` |
| 57 | VI-A | Nengo vs NumPy worst relative error over ten cases | 2.013e-06 (10) | 2.013e-06 (10) | OK | `nengo_nef_replication/results/compiled/archived_equivalence.csv  (verify_archived_equivalence.py)` |
| 58 | VI-C ablation | PES corner (rad/s) | 9.60 | 9.60 | OK | `theory_certificate/certificate_macros.tex  (compute_local_certificate.py)` |
| 59 | Fig. 4 | legend degrees PD/CMG per level | 16.85/7.91,4.07/2.19,0.60/0.52 | 16.85/7.91,4.07/2.19,0.60/0.52 | OK | `final_robustness_gating/figures_out/ladder/x2_hard45_ladder_C.json  (make_ladder_figure.py)` |
