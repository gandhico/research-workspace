"""A1 limit case: load threshold 0.001 (the declared 0.0 is rejected by the sealed runner)."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import run_campaign as rc
c = rc.Case(protocol="development_only", campaign="hardstep_variant_screen_a1", platform="x2", mission="hardstep",
            label="cmg_pes_gate", controller="nengo-nef-pes", beta=rc.BETA_CANONICAL, output_gate=rc.GATE_OUTPUT,
            gate_load_threshold=0.001)
r = rc.run_case(c, rc.DEFAULT_RESULTS, 45.0, 5e-4, False)
print(r["status"], c.case_id)
