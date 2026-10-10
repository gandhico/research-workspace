# Lab 10 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors, **no inferred-latch warning**, `Decoder` reports **zero registers** |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Feed it an opcode you did not implement. What do the control signals do, and why is that the safe answer?*
   - **Full:** no register write, no memory write, memory disabled, bus not driven, PC still advances; explains that a decoder doing something arbitrary with unrecognised data is a CPU that corrupts memory.
   - **Partial:** knows it does nothing, cannot say why that matters.
   - **None:** has not tested it.

2. *Which signals differ between `ADD` and `ADDI`? Why exactly those?*
   - **Full:** `ALU_Asel` (register vs immediate), `IR_Xsel`/`IR_Xlsft` (the extender is now used), and `RF_Wsel` (rd vs rt); explains that R-type and I-type put the destination in different fields.
   - **Partial:** names some, cannot justify.
   - **None:** neither.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted at 3:45 | Q3 blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, no latch warning, zero registers | Latch warning present (**−12**) | Does not compile |
| **Testbench + vectors** | 20 | ≥1 vector per instruction, unknown opcode, unknown func, **order-dependence test** | Order test missing (**−8**); unknown-func case missing (−5) | Stimulus without checks |
| **Simulation results** | 20 | Every control signal asserted for each instruction | Only a few signals checked (−6) | Fails or not run |
| **Report chapter** | 15 | 7 sections; the four table rows; why the default comes first; why `SPECIAL` needs `func` | Default explanation missing (−5) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| **No default assignment (latches inferred)** | **−12** — the headline bug of the lab |
| **`SPECIAL` decoded on opcode alone** | **−10** — every R-type becomes `ADD` |
| **`RF_Wsel` backwards (rd/rt swapped)** | **−10** — writes the wrong register, silently |
| `ADDI` and `LUI` given the same `IR_Xsel` | **−8** — they differ on exactly that signal |
| Order-dependence test absent | −8 |
| Raw bit patterns instead of `CPU_Pkg` constants | −5 |
| Code pasted into the report | −5 |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: the report explains the default assignment as a *safety property* rather
than a coding convention; the order-dependence test is present with a sentence
saying what class of bug it detects and why a one-instruction-at-a-time testbench
cannot; and the student can point at the two places earlier in the course where the
same "no assignment means hold" rule appeared.

## What to watch for

- **The latch.** Expect several. The Messages panel says so and the register count
  will not be zero — check both at the bench, because students who compile with a
  warning and move on will carry it into Lab 12.
- **Scope panic.** Some students will go looking for the full MIPS instruction list
  and try to decode all of it. Repeat slide 2: eight instructions, four this week.
- **`SPECIAL` on opcode alone.** Passes an `ADD` test and fails `SLL`. Ask them to
  feed both.
- **Copying the table into code without reading it.** Ask why `ADD` leaves
  `IR_Xsel` alone. The answer — it never reads the extender, so it is a don't-care —
  sets up next week's minimisation discussion.
- **Finished early.** Have them restructure the decoder as a ROM-based (microcoded)
  control unit: control bits stored in a lookup table indexed by opcode. Compare the
  resource usage and discuss hardwired versus microcoded — it is a lecture topic they
  will recognise.
