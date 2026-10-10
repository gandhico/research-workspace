"""Replacement rules for the three files that use multi-line implicit string
concatenation inside Path(...). These need the whole expression replaced, not
just the first fragment.
"""

EXTRA = {
    "hover3dof_hardware/audit_and_freeze_all_2026_09_02.py": ([
        ('ROOT = Path(r"C:\\Research\\hover3dof\\nengo_gui_hil_2026-08-29")',
         "ROOT = HOVER_PROJECT"),
        ('MUJOCO = Path(\n'
         '    r"C:\\Research\\papers\\ACC2027_Gate_Residual_Control\\experiments"\n'
         '    r"\\nengo_nef_replication_2026-08-29\\results"\n'
         ')',
         "MUJOCO = MUJOCO_RESULTS"),
        ('"pd_baseline": Path(r"C:\\Research\\hover3dof\\pd_cmg_focused_final_round_2026-08-28\\src\\pd_baseline.py"),',
         '"pd_baseline": LAB_ROOT / "hover3dof"\n'
         '        / "pd_cmg_focused_final_round_2026-08-28" / "src" / "pd_baseline.py",'),
        ('"nengo_cmg": Path(\n'
         '            r"C:\\Research\\papers\\ACC2027_Gate_Residual_Control\\experiments"\n'
         '            r"\\nengo_nef_replication_2026-08-29\\nengo_cmg.py"\n'
         '        ),',
         '"nengo_cmg": NENGO_NEF / "nengo_cmg.py",'),
        ('"nengo_neuron_family": Path(\n'
         '            r"C:\\Research\\papers\\ACC2027_Gate_Residual_Control\\experiments"\n'
         '            r"\\nengo_nef_replication_2026-08-29\\nengo_neuron_family.py"\n'
         '        ),',
         '"nengo_neuron_family": NENGO_NEF / "nengo_neuron_family.py",'),
        ('"paper_draft": Path(\n'
         '            r"C:\\Research\\papers\\ACC2027_Gate_Residual_Control\\paper"\n'
         '            r"\\acc2027_neuromorphic_gate_residual_draft.tex"\n'
         '        ),',
         '"paper_draft": PAPER / "ACC2027_manuscript.tex",'),
        ('"six_dof_progress": Path(\n'
         '            r"C:\\Research\\papers\\ACC2027_Gate_Residual_Control\\experiments"\n'
         '            r"\\six_dof_expansion_2026-08-31\\PROGRESS_2026-08-31.md"\n'
         '        ),',
         '"six_dof_progress": SIX_DOF / "PROGRESS_2026-08-31.md",'),
    ], ["HOVER_PROJECT", "MUJOCO_RESULTS", "NENGO_NEF", "SIX_DOF", "PAPER",
        "LAB_ROOT"], 1),

    "hover3dof_hardware/make_acc_positive_hardware_figures.py": ([
        ('DIRECT = Path(\n'
         '    r"C:\\Research\\hover3dof\\nengo_gui_hil_2026-08-29\\results"\n'
         '    r"\\DIRECT_NENGO_FINAL_2026-09-01"\n'
         ')',
         "DIRECT = HOVER_FINAL"),
        ('AUDIT = Path(\n'
         '    r"C:\\Research\\hover3dof\\nengo_gui_hil_2026-08-29\\results"\n'
         '    r"\\FROZEN_AUDIT_2026-09-02\\canonical_physical_deep_audit.json"\n'
         ')',
         'AUDIT = (HOVER_RESULTS / "FROZEN_AUDIT_2026-09-02"\n'
         '         / "canonical_physical_deep_audit.json")'),
        ('ROLL_N3 = Path(\n'
         '    r"C:\\Research\\hover3dof\\nengo_gui_hil_2026-08-29\\results"\n'
         '    r"\\hardware_armed_roll_n3_2026-09-01\\armed_roll_n3_summary.json"\n'
         ')',
         'ROLL_N3 = (HOVER_RESULTS / "hardware_armed_roll_n3_2026-09-01"\n'
         '           / "armed_roll_n3_summary.json")'),
        ('OUT = Path(\n'
         '    r"C:\\Research\\papers\\ACC2027_Gate_Residual_Control\\results\\plots"\n'
         '    r"\\hover3dof_positive_only_2026-09-03"\n'
         ')',
         'OUT = out_dir("hover3dof_positive_only")'),
    ], ["HOVER_FINAL", "HOVER_RESULTS", "out_dir"], 1),

    "hover3dof_hardware/hover_nengo_hil_gui.py": ([
        ('HOVER_ROOT = Path(r"C:\\Research\\hover3dof")',
         'HOVER_ROOT = LAB_ROOT / "hover3dof"'),
        ('ACC_ROOT = Path(r"C:\\Research\\papers\\ACC2027_Gate_Residual_Control")',
         "ACC_ROOT = ROOT"),
        ('NENGO_REFERENCE_ROOT = (\n'
         '    ACC_ROOT / "experiments" / "nengo_nef_replication_2026-08-29"\n'
         ')',
         "NENGO_REFERENCE_ROOT = NENGO_NEF"),
    ], ["LAB_ROOT", "ROOT", "NENGO_NEF"], 1),
}
