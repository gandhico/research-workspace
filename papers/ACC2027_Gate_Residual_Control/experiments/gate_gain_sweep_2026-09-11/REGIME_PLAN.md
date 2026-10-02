# Exploratory mechanism extension

Added following the user's request to find whether conductance matters in another regime, before inspecting new closed-loop regime results. The first canonical anchor showed raw gates >0.9 for 97.7% of unit-samples; total conductance is not negligible.

Hypothesis: gamma=2 introduces positive membrane-gate threshold feedback that supports a high-gate branch; activity saturation can hide conductance-dependent voltage differences. A readout-gain sweep alone need not remove raw-gate saturation. Test gamma=0 (remove threshold feedback) and gamma=0.5 (weaken it), G=1 or 3, chi=0 or 1, on X2 Full3 and Hardstep (16 development runs). All other nominal protocol parameters remain unchanged. Gamma=0 is a structural ablation, not the original full coupled architecture. Gamma=0.5 retains both states and threshold feedback.

Before these closed-loop tests, apply an identical 16-s triangular current ramp from .75 to 2 and back to .75 to gamma={0,.5,1,2}, chi={0,1}, without resetting at the peak. This identifies state sensitivity under matched input, separately from feedback-induced trajectory changes. It is not a UAV performance test.

Report all development cases, including degradation. Any configuration selected after this test requires separately labelled confirmation; do not retrofit it into the frozen nominal table. No claim that changing gamma or G preserves the original experimental architecture numerically.
