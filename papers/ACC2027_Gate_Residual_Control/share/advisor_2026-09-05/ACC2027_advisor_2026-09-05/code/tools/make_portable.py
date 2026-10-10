"""Rewrite absolute paths in the advisor package into acc2027_paths symbols.

Applied to the *package copy* only -- the working research tree at
C:\\Research is never modified.

Each rule is an exact-string replacement plus the symbols it needs imported.
The script refuses to finish if any rule misses, if any absolute path
survives, or if any rewritten file fails to compile.

Run:  python make_portable.py <package_root>
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

BOOTSTRAP_MARK = "# --- portable paths (added for distribution) ---"


def bootstrap(depth: int, symbols: list[str]) -> str:
    """Two-line sys.path bootstrap plus the acc2027_paths import."""
    return (f"{BOOTSTRAP_MARK}\n"
            f"import sys as _sys, pathlib as _pathlib\n"
            f"_sys.path.insert(0, str(_pathlib.Path(__file__).resolve()"
            f".parents[{depth}]))\n"
            f"from acc2027_paths import {', '.join(symbols)}  # noqa: E402\n")


# file -> (list of (old, new) replacements, symbols needed, bootstrap depth)
# depth is how many parents up from the file to reach code/ .
RULES: dict[str, tuple[list[tuple[str, str]], list[str], int]] = {
    # ---------------- eprop_anneal ------------------------------------------
    "eprop_anneal/nengo_eprop_anneal.py": ([
        (r'Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29")',
         "NENGO_NEF"),
    ], ["NENGO_NEF"], 1),

    "eprop_anneal/nengo_run_hard45.py": ([
        (r'Path(r"C:\Research\papers\P3_Gate_Residual\learned\code")', "LEGACY_P3"),
    ], ["LEGACY_P3"], 1),

    "eprop_anneal/reproduce_5missions.py": ([
        (r'Path(r"C:\Research\papers\P3_Gate_Residual\learned\code")  # fully local, no D: dependency',
         "LEGACY_P3  # shipped with this package"),
    ], ["LEGACY_P3"], 1),

    "eprop_anneal/reproduce_traces.py": ([
        (r'Path(r"C:\Research\papers\P3_Gate_Residual\learned\code")  # fully local, no D: dependency',
         "LEGACY_P3  # shipped with this package"),
    ], ["LEGACY_P3"], 1),

    "eprop_anneal/verify_nengo_eprop_equivalence.py": ([
        (r'Path(r"C:\Research\papers\P3_Gate_Residual\learned\code\experiments\controller_benchmarks")',
         'LEGACY_P3 / "experiments" / "controller_benchmarks"'),
    ], ["LEGACY_P3"], 1),

    # ---------------- gra_control -------------------------------------------
    "gra_control/platforms/hardware.py": ([
        (r'Path(r"C:\Research\pendulum\runners\run_online_qube.py")',
         'LAB_ROOT / "pendulum" / "runners" / "run_online_qube.py"'),
        (r'Path(r"C:\Research\qcar\01_Code\hardware\qcar2_unified_lane_control_hardware_v1.py")',
         'LAB_ROOT / "qcar" / "01_Code" / "hardware" / "qcar2_unified_lane_control_hardware_v1.py"'),
        (r'Path(r"C:\Research\hover3dof\3DOF_Hover")',
         'LAB_ROOT / "hover3dof" / "3DOF_Hover"'),
    ], ["LAB_ROOT"], 2),

    # ---------------- hover3dof_hardware ------------------------------------
    "hover3dof_hardware/audit_and_freeze_all_2026_09_02.py": ([
        (r'Path(r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29")', "HOVER_RESULTS"),
        (r'r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments"', "str(CODE)"),
        (r'Path(r"C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28\src\pd_baseline.py")',
         'LAB_ROOT / "hover3dof" / "pd_cmg_focused_final_round_2026-08-28" / "src" / "pd_baseline.py"'),
        (r'r"C:\Research\papers\ACC2027_Gate_Residual_Control\paper"', "str(PAPER)"),
    ], ["HOVER_RESULTS", "CODE", "PAPER", "LAB_ROOT"], 1),

    "hover3dof_hardware/audit_q8_neuron_family_shadow.py": ([
        (r'Path(r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\q8_neuron_family_shadow_2026-09-01")',
         'HOVER_RESULTS / "q8_neuron_family_shadow_2026-09-01"'),
    ], ["HOVER_RESULTS"], 1),

    "hover3dof_hardware/compile_final_hardware_campaign_2026_09_01.py": ([
        (r'Path(r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29")', "HOVER_RESULTS"),
    ], ["HOVER_RESULTS"], 1),

    "hover3dof_hardware/compile_final_hardware_report.py": ([
        (r'Path(r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\DIRECT_NENGO_FINAL_2026-09-01")',
         "HOVER_FINAL"),
        (r'Path(r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\DIRECT_NENGO_FINAL_2026-09-01\plots")',
         'out_dir("hover3dof_hardware_plots")'),
    ], ["HOVER_FINAL", "out_dir"], 1),

    "hover3dof_hardware/hover_nengo_hil_gui.py": ([
        (r'Path(r"C:\Research\hover3dof")', 'LAB_ROOT / "hover3dof"'),
        (r'Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")', "ROOT"),
    ], ["LAB_ROOT", "ROOT"], 1),

    "hover3dof_hardware/make_acc_positive_hardware_figures.py": ([
        (r'r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results"', "str(HOVER_RESULTS)"),
        (r'r"C:\Research\papers\ACC2027_Gate_Residual_Control\results\plots"',
         'str(out_dir("acc_positive_hardware_figures"))'),
    ], ["HOVER_RESULTS", "out_dir"], 1),

    "hover3dof_hardware/verify_nengo_hover_equivalence.py": ([
        (r'Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")', "ROOT"),
    ], ["ROOT"], 1),
}

from rules_extra import EXTRA  # noqa: E402
for _k, _v in EXTRA.items():
    RULES[_k] = _v

ABS_RE = re.compile(r"""["']?[A-Za-z]:[\\/]{1,2}(?:Research|Users)""")


def insert_bootstrap(text: str, depth: int, symbols: list[str]) -> str:
    """Put the bootstrap after the last __future__/stdlib import block."""
    if BOOTSTRAP_MARK in text:
        return text
    lines = text.split("\n")
    # after the module docstring and any __future__ import, before first use
    anchor = 0
    in_doc = False
    for i, ln in enumerate(lines):
        st = ln.strip()
        stripped_prefix = st.lstrip('rRbBuUfF')
        if i == 0 and (stripped_prefix.startswith('"""')
                       or stripped_prefix.startswith("'''")):
            in_doc = (not stripped_prefix.endswith(('"""', "'''"))
                      or len(stripped_prefix) < 6)
            anchor = i + 1
            continue
        if in_doc:
            if st.endswith('"""') or st.endswith("'''"):
                in_doc = False
            anchor = i + 1
            continue
        if st.startswith(("from __future__", "import ", "from ")) or not st \
                or st.startswith("#"):
            anchor = i + 1
            continue
        break
    lines.insert(anchor, "\n" + bootstrap(depth, symbols))
    return "\n".join(lines)


def main(pkg: Path) -> int:
    code = pkg / "code"
    problems: list[str] = []
    changed = 0

    for rel, (repls, symbols, depth) in RULES.items():
        f = code / rel
        if not f.is_file():
            problems.append(f"missing file: {rel}")
            continue
        text = io.open(f, encoding="utf-8").read()
        original = text
        for old, new in repls:
            if old not in text:
                problems.append(f"{rel}: rule did not match:\n      {old}")
                continue
            text = text.replace(old, new)
        if text != original:
            text = insert_bootstrap(text, depth, symbols)
            io.open(f, "w", encoding="utf-8").write(text)
            changed += 1
            print(f"  rewrote  {rel}")

    # --- verify: no absolute paths survive anywhere in code/ ----------------
    survivors = []
    for f in sorted(code.rglob("*.py")):
        for n, ln in enumerate(io.open(f, encoding="utf-8"), 1):
            if ABS_RE.search(ln) and "acc2027_paths" not in ln:
                survivors.append(f"{f.relative_to(code)}:{n}: {ln.strip()[:100]}")

    # --- verify: everything still compiles ----------------------------------
    import py_compile
    broken = []
    for f in sorted(code.rglob("*.py")):
        try:
            py_compile.compile(str(f), doraise=True, cfile=str(f) + "c")
            Path(str(f) + "c").unlink(missing_ok=True)
        except py_compile.PyCompileError as e:
            broken.append(f"{f.relative_to(code)}: {e.msg.splitlines()[-1][:120]}")

    print(f"\n{changed} files rewritten")
    for label, items in (("RULE PROBLEMS", problems),
                         ("ABSOLUTE PATHS REMAINING", survivors),
                         ("SYNTAX ERRORS", broken)):
        print(f"{label}: {len(items)}")
        for it in items:
            print(f"    {it}")
    return 1 if (problems or survivors or broken) else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]).resolve()))
