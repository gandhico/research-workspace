# Lab 7 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors; `NIAG_Reg` reports **32 registers**; the adders report none |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Hand-compute your backward-branch target on the whiteboard. Does the simulation agree?*
   - **Full:** produces NSA, the scaled offset (as a negative number) and the target, and the simulation matches.
   - **Partial:** gets the target from the waveform but cannot derive it.
   - **None:** has no backward-branch vector.

2. *What would break if you used PC instead of PC+4 as the branch base?*
   - **Full:** every target lands one instruction early; still word-aligned so it looks plausible; loops run one instruction wrong. Names it as "off by a constant".
   - **Partial:** knows it would be wrong, cannot say how.
   - **None:** neither.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted at 3:45; Q1 arithmetic done | Q1(c) blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, register count explained | Count not commented on (−5) | Does not compile |
| **Testbench + vectors** | 20 | ≥6 vectors; all six required cases | **No backward branch (−10)**; NSA-combinational untested (−5) | Stimulus without checks |
| **Simulation results** | 20 | Forward and backward targets shown and annotated | Only forward shown (−8) | Fails or not run |
| **Report chapter** | 15 | 7 sections; Table T; **hand-computed arithmetic next to the simulated result**; both "why" questions answered | Hand computation missing (**−6**); one "why" unanswered (−4) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| **Forgot the `<< 2`** | **−12** — targets are not even word-aligned |
| **Used PC instead of PC+4 as the base** | **−10** |
| All branch offsets positive | **−10** — sign extension is untested, and every backward branch in Lab 12 will be wrong |
| `NSA` computed inside a clocked process | **−10** — it would arrive a cycle late |
| No reset vector / PC can power up at `'U'` | −8 |
| Hand-computed arithmetic absent from the report | −6 |
| Re-implemented sign extension instead of reusing `ImmedXtnd` | −4 and a note — it works, but the CPU has one shared extender |
| Code pasted into the report | −5 |
| Figure with no interpreting sentence | −4 each |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: the report shows the hand-computed arithmetic for one forward and one
backward branch sitting directly next to the simulated values; both "why" questions
(PC+4, and the shift) are answered as trade-offs rather than rules; and the student
reused their Lab 4 `ImmedXtnd` and can say why the CPU has only one extender.

## What to watch for

- **All-positive offsets.** The most common way to pass this lab without testing it.
  Ask to see a negative offset at every bench.
- **Re-implementing the extender.** Some students will write the sign-extend inside
  `NIAG_Rel`. It works. Point out that the CPU has one shared extender feeding both
  the ALU and this adder, and that duplicating it means two places to fix.
- **`RegN` reuse that silently breaks.** `RegN` resets to zero; `NIAG_Reg` has a
  reset *vector* generic. If they instantiate `RegN` they must check the reset value
  is expressible. For `RESET_VEC = 0` it is, so this usually passes by luck — ask
  whether they checked.
- **Hex arithmetic errors in the pre-lab.** Common and harmless; the point is that
  they attempted the derivation.
- **Finished early.** Send them to Example 3 and have them predict, then measure,
  what a *third* error would do: extending the offset as unsigned instead of signed.
