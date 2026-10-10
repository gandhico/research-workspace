# Lab 12 — Grading Rubric
### 100 points · TA use

## Bench check-off (at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors; metavalue warnings settle after the first few cycles |
| ☐ | **Runs the program** | `PASS — the CPU computes 2^10 and stores it` |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Show me your final `r2`. What number is it, and why that number?*
   - **Full:** `0x400` = 1024 = 2¹⁰; explains the loop doubles `r2` once per pass and runs ten full passes before the counter reaches zero.
   - **Partial:** reads the value off the screen, cannot explain where it comes from.
   - **None:** the CPU does not run.

2. *Pick any cycle in your waveform and read the control signals off it. Which instruction is executing?*
   - **Full:** identifies the instruction from the control bundle alone, using their control table.
   - **Partial:** identifies it from the IR value only.
   - **None:** cannot navigate the waveform.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted; **Q1 trace hand-computed** | Q1 blank (−3) | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, named association, warnings explained | Positional `port map` (−6) | Does not compile |
| **Hand-computed trace** | 20 | First five rows derived on paper, matching the simulation | Trace copied from the simulation only (**−12**) | Absent |
| **Simulation** | 20 | The CPU runs, `PASS`, 45 cycles | Runs but with the wrong final value (−10) | Does not run |
| **Report chapter** | 15 | Timing contract; full 45-row trace; E1–E7 each interpreted; real Discussion | Evidence set incomplete (−5); trace truncated (−4) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain |

**Late:** one week, −20.

### On using reference components

**Using a reference component from `components/` costs nothing on this lab.** The
earlier lab's grade stands as it was. Do not deduct, and say so out loud when a
student asks — some will assume it is a penalty and struggle in silence rather than
take one.

---

## Automatic deductions

| | |
|---|---|
| **Trace copied from the simulation with no hand computation** | **−12** — the hand computation is the graded part |
| Positional association in any `port map` | −6 |
| Waveform present but unannotated | −6 |
| Evidence set incomplete (fewer than E1–E7) | −5 |
| "Everything worked first try" in Discussion | −8 — nobody wires twelve components correctly first time |
| Report does not say which of the four checks found each bug | −4 |

---

## What good looks like

Above 90: the hand-computed first five rows sit directly beside the simulated ones;
the Discussion names each integration bug **and which of the four checks found it**;
the waveform is cropped to ~20 cycles with the instruction boundaries marked; and E5
is discussed as the 108-pins-versus-one-pin contrast rather than just reported.

## What to watch for

- **Panic at 4:00.** The CPU does nothing and the student starts changing things at
  random. Stop them and walk check 1. This is the single most valuable intervention
  of the session.
- **Skipping the method.** "I know it's the ALU." It is almost never the ALU. Make
  them do checks 1–3 anyway; it takes two minutes and usually finds it.
- **`'U'` everywhere.** One undriven signal. Almost always a `port map` with a
  missing connection, or an internal signal declared and never assigned.
- **`'X'` on the memory bus.** `TriBuffer` and `RAM` both driving. Check `RF_oe`
  against the control table.
- **Metavalue warnings that never stop.** A signal that is never driven. This is a
  genuinely useful diagnostic — point it out.
- **Students who cannot start** because an earlier lab is missing. Hand them the
  reference components immediately, at the start of the session, not at 5:15.

## The line to end the semester on

> *"Your processor computes two to the tenth. Three months ago you were writing a
> four-row truth table for a latch. Same loop every week — specification, truth
> table, equations, VHDL, simulation, check. Nothing was ever added to the method.
> That is engineering, and it is the actual thing you are taking away from this
> course."*
