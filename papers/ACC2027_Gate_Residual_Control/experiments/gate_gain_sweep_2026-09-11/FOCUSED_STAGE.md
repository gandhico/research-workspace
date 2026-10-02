# Resource-driven staged execution

The full 148-case factorial launcher is retained in sweep.py and its original version in sweep_full_plan_v1.py. After the first six-worker batch took approximately 350 seconds per CMG case (other research campaigns are concurrently using this computer), the present analysis was restricted to a focused 28-case stage:

- X2/Full3 and CF2-rotor/Hardstep, selected to contrast smooth multi-axis and abrupt rotor-constrained tracking in the frozen results.
- G={1,1000,100000,1000000}, chi={0,1}: 16 direct-CMG cells.
- Two fresh PD anchors and two paired-linear/PES comparators.
- Eight Nengo checks at the same four gains, chi=1.

The initial X2/Roll cells are retained as additional exploratory observations, including incomplete coverage. They are not discarded or treated as a balanced full factorial.

This is a resource-driven scope change, not selection of gains based on favorable tracking results. No generalization to every mission is claimed. The independent 16-case gamma-regime development plan is unchanged. The 148-case full sweep is available for a later extended run, but is not claimed complete in this revision.

Canonical summary metadata contains a pre-existing suffix bug: `direct-online-pes` is labelled as a Nengo backend because it ends in `-pes`. The new analysis uses the explicit wrapper `backend` field and corrects this descriptive metadata; the control calculations are unaffected. Likewise direct decoder leakage is 1e-6, not zero.
