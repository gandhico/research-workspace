# EHEKATL Controller Work Rules

Before analyzing, editing, proposing a flight command, or changing controller
gains in this directory, read `docs/CONTROL_DEVELOPMENT_PROCESS.md` completely.

That file is the authoritative project memory. Update it whenever new evidence,
commands, conclusions, failures, or stage-gate results are produced.

Mandatory rules:

1. Work only on the stage marked `CURRENT` in the process document.
2. Do not begin the next stage until every acceptance criterion for the current
   stage has objective evidence and its gate is explicitly marked `PASS`.
3. A simulation run, successful program exit, fitted model, controllability
   rank, or stable calculated eigenvalue is not by itself flight validation.
4. Preserve the original backstepping controller as the recovery-capable
   baseline. Identification excitation must eventually be superimposed on that
   stabilizing controller, not substituted for it.
5. Never recommend a higher control limit, gain, or wider safety envelope to
   overcome divergence.
6. Commands must include the correct project directory, environment activation,
   complete script path, and a real timestamp expansion. Never present a
   placeholder such as `YYYYMMDD_HHMMSS` as a runnable command.
7. Record assumptions, units, routing, actuator signs, trim conditions, X-Plane
   state, and exact input log filenames.
8. Safety stops must be treated as failed validation evidence. Automatic
   re-engagement is not proof of recovery.
