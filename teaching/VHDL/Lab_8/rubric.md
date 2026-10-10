# Lab 8 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors; `NIAG` reports **32 registers** and no others |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Walk me through your scripted sequence. Point at the taken branch and the not-taken one — what differs between them in the control signals?*
   - **Full:** same `Sel` code (`REL`), different `Taken`; not-taken falls back to NSA; can name which condition and which flag values produced each.
   - **Partial:** finds both in the waveform, cannot say what differs in control.
   - **None:** has no not-taken case.

2. *Why can `J` not reach every address in memory — and what would you use instead?*
   - **Full:** the top 4 bits are inherited from PC+4, not encoded; 26 bits plus 2 implied zeros reaches 256 MB; `JR` takes a full 32-bit address from a register.
   - **Partial:** knows there is a limit, cannot explain where it comes from.
   - **None:** neither.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted at 3:45; the six equations written | Q1(c) blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, named association throughout, register count explained | Positional `port map` used (−6) | Does not compile |
| **Testbench + vectors** | 20 | Full scripted sequence, all eight required cases | Taken/not-taken pair missing (**−10**); no backward branch (−6) | Stimulus without checks |
| **Simulation results** | 20 | Scripted-sequence waveform, every transition annotated with its source | Waveform present but unannotated (**−8**) | Fails or not run |
| **Report chapter** | 15 | 7 sections; `Sel` table; **all six condition equations** with complement pairs; the 256 MB trade-off | Equations incomplete (−5); trade-off not explained (−4) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| **`GTZ` implemented as N-bar alone** | **−10** — that is `GEZ`. Zero is not greater than zero. |
| Jump paths gated by `Taken` | **−10** — only the relative path is conditional |
| Not-taken producing something other than NSA | **−8** |
| `Abslt` uses the wrong slice of NSA | −8 |
| Positional association in any `port map` | −6 and fix on the spot; Lab 12 has twelve components |
| Missing `when others` in `NIAG_Cond` or `NIAG_MUX` | −6 |
| Scripted-sequence waveform not annotated | −8 — an unannotated 30-signal waveform proves nothing |
| Code pasted into the report | −5 |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: the scripted-sequence waveform is a single annotated figure where every PC
transition is labelled with the source it came from; all six condition equations
appear in the report with the complement pairs identified; and the 256 MB jump limit
is explained as a consequence of the encoding rather than quoted as a fact.

## What to watch for

- **`GTZ` written as N-bar alone.** The single most common error of the lab, and it
  passes every test where the result is non-zero. Ask specifically for `GTZ` with
  `Zero` high.
- **Gating everything with `Taken`.** Produces a CPU that cannot jump whenever the
  last ALU result happened to be positive — a spectacularly confusing Lab 12 bug,
  because it is intermittent by data.
- **Positional port maps.** Six components is where it starts to hurt. Fix it here
  or watch it cost an hour in Lab 12.
- **Reading an `out` port.** Will not compile; the fix is an internal signal. Some
  students try to work around it by adding an extra output instead.
- **Not copying their Lab 7 files in.** Step 1. The shipped copies are skeletons.
- **Finished early.** Have them add the exception vector: on an `Exc` input, force
  the PC to a fixed handler address and save the old PC. Small change, and it
  previews the interrupts lecture on 11/9.
