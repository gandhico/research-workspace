# Lab 3 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors; **no inferred-latch warning**; `MUX3x32` reports **0 registers** |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Row 3 outputs zero. What did that let you delete from the canonical equation, and what happens if you leave row 3 out entirely?*
   - **Full:** the `S1S0` product term disappears because it multiplies zero; and omitting row 3 leaves the output unassigned, which infers a latch.
   - **Partial:** knows it becomes a latch, cannot explain the deleted term.
   - **None:** neither.

2. *Point at your four multiplexers on the CPU diagram. What does each one choose between?*
   - **Full:** names all four roles correctly (`DselMUX`, `ALUinMUX`, `DinMUX`, spare) with what each selects.
   - **Partial:** finds them but cannot say what they choose between.
   - **None:** has not annotated the diagram.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted at 3:45 | Q3(a)/(b) blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, no latch warning, 0 registers reported | Compiles but latch warning present (**−10**) | Does not compile |
| **Testbench + vectors** | 20 | ≥ 6 vectors; every selector value **including "11"**; no-latch check; coverage argument | No coverage argument (−7); identical data on all inputs (**−8**) | Stimulus without checks |
| **Simulation results** | 20 | All four rows shown; no-latch behaviour demonstrated | Row 3 untested (**−8**) | Fails or not run |
| **Report chapter** | 15 | 7 sections; Type C table; factored equation with law named; **annotated CPU diagram** | Diagram missing (−6); law unnamed (−4) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| **Row 3 unimplemented** (latch inferred) | **−12** — this is the entire lesson of the lab |
| Identical test data on A, B and C | **−8** — a mux ignoring its selector would pass |
| No no-latch check in the testbench | −6 |
| Annotated CPU block diagram missing from the report | −6 |
| `if/elsif` chain used for `Mux3` instead of `case` | −3 and a verbal note — it works, but they gave up the language's protection |
| Coding style chosen with no justification | −4 — "why this style" is the graded question |
| Code pasted into the report | −5 |
| Figure with no interpreting sentence | −4 each |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: the factored equation is derived rather than copied, and the report says
in the student's own words that the bracket is a 2-to-1 mux and the whole thing is
a mux tree. The annotated CPU diagram is full-page with all four muxes circled and
labelled with what they select. The testbench uses three visibly distinct data
patterns and says explicitly which wrong implementation each vector rules out.

## What to watch for

- **The `exp` / reserved-name trap.** Not a student issue, but if anyone names a
  testbench parameter after a predefined function they get "Illegal target for
  signal assignment", which points nowhere useful. Suggest renaming.
- **`when others` refused.** Students write `case` without `when others`, the
  compiler rejects it, and they think the compiler is wrong. It is not: `std_logic`
  has nine values. This is the language protecting them — say so.
- **Width mismatch that points somewhere else.** Almost always a forgotten
  `generic map`, reported at the instantiation rather than at the omission.
- **Latch warning ignored.** Some students will compile with the warning and move
  on. The register count on `MUX3x32` is the backstop — check it at the bench.
- **Finished early.** Common this week; the designs are short. Send them to
  strengthen the report — the annotated CPU diagram takes real thought and is where
  most of the lasting value is — or have them help a neighbour. Explaining it is how
  they find out whether they know it.
