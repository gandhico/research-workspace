# Lab 1 — TA Notes

Fill this in **after the Monday section**, before Tuesday. Monday is the dress
rehearsal; Tuesday is the performance. Change your delivery, never the assignment.

---

## Before the session — 15 minute setup

- [ ] Log into the bench PC and open `assignment/Lab1.qpf` once, cold, to confirm the
      project opens and Questa launches on **this semester's lab image**. Do not
      discover a licensing problem in front of twenty people.
- [ ] Have `Documentation/CPU Diagram.pdf` open on the side screen. It stays there
      all semester.
- [ ] Whiteboard ready: you write Table T by hand at 3:50, not from the slide.
- [ ] Print: pre-lab sheets (collect at 3:45), and the rubric for yourself.
- [ ] Have the Example 3 waveform pre-loaded in a second Questa window, in case
      the live run goes sideways.

## Known friction points, in the order they will happen

| Time | What happens | What to do |
|---|---|---|
| 3:45 | Two or three students have no working Quartus | Pair them at a bench PC immediately. Do not debug installs during class — point them at the NMSU install guide and the VPN/license note (`1801@chaos`), and fix it in office hours. |
| ~4:00 | Someone's project will not compile: "Can't find entity" | Top-level entity name ≠ file entity name, or the file was never added |
| ~4:35 | Waveform is all `U` | Expected — the architecture body is still empty. Announce this before it becomes a queue. |
| ~4:40 | NativeLink error on simulation | Simulation top level not set, or they renamed a file the `.qsf` lists |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* Go to those hands first. |
| ~5:10 | "My body looks right but half the checks fail" | The sensitivity list. See the diagnostic table below — do not give the answer, give them the signature and let them find it. |

## Diagnostic table — sensitivity list failures

**Measured, not guessed.** A correct architecture body left with the supplied
`process (En)` produces this exact signature against the reference testbench:

| Failing check | Missing signal | Why |
|---|---|---|
| "clear forces Q low" (`'U'` at the very first check) | `Clr` | The process never wakes when `Clr` rises, so nothing is ever assigned |
| "transparent, Q tracks a change of D" | `D` | `En` is already high, so a change in `D` wakes nothing |
| "clear works while holding" / "releasing clear does not restore" / "clear beats transparency" | `Clr` | Same cause as row 1, seen later |

Re-measured 2026-09-15, 1-bit latch: checks **1, 3, 6, 7, 9** fail. The 8-bit latch
additionally fails **4 and 5** (its data changed while `En` stayed high, so it holds a
stale value). For comparison, a body that wrongly adds `else Q <= '0'` fails **only 4
and 5**, on both widths.

Two things worth knowing before you walk the room:

1. **It fails at check 1, not at the hold vector.** The output sits at `'U'` because
   the process has not run since initialisation. Students will report "it's all U
   again" and assume they have not written any code yet.
2. **The hold check still passes** with a broken list — the value is stuck, which
   looks like holding. That is a good thing to point out afterwards: *a test can
   pass for the wrong reason.*

The rule to hand them: **which signal is missing is named by which checks fail.**
Clear tests failing means `Clr`; the transparency-tracking test failing means `D`.
That is a real debugging method and it is worth 60 seconds at the board.

## Timing reality check

| Planned | Phase |
|---|---|
| 3:45–3:55 | Open + Table T on the board |
| 3:55–4:20 | Examples 1, 2, 3 |
| 4:20–4:30 | Spec walk |
| 4:30–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off |
| 5:40–5:45 | Close |

Example 1 is the one that overruns, because it is where install and project-setup
problems surface. If you are behind at 4:10, **cut Example 2's live typing** and
just run the prepared file — Example 3 is the one that must not be cut.

---

## After Monday — fill this in

**What took longer than planned:**


**What confused people (exact wording of the confusion):**


**What to say differently on Tuesday:**


**Students who need follow-up (install, missed, struggling):**


**Anything to change in the material for next year:**


---

## After Tuesday

**Did the two sections end in the same place?**


**Check-off answer quality — question 1 / question 2:**


**Carry into Lab 2:**
Lab 2 opens with *"two of these latches, wired with opposite enables"* — so note
here anyone whose Lab 1 latch does not work, because they will need the reference
`TransLatch.vhd` on day one of Lab 2.
