# Lab 1 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

Three boxes. Tick or don't. Do not negotiate at the bench.

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | Quartus full compilation, 0 errors |
| ☐ | **Testbench passes** | Questa transcript shows `PASS` and 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — ask the same two of everyone in the section:**

1. *Point at the waveform: why does Q not change here, when D clearly changed?*
   - **Full:** identifies `En = '0'`, connects it to row 1 of the table, and says the value is held.
   - **Partial:** identifies `En = '0'` but cannot connect it to the specification.
   - **None:** "because that's what a latch does."

2. *If I deleted `Clr` from your sensitivity list, would the simulation change? Would the hardware?*
   - **Full:** simulation yes, hardware no — and names it as a sim/synthesis mismatch.
   - **Partial:** knows something breaks, cannot say which side.
   - **None:** no idea, or thinks both change.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 questions attempted, submitted at 3:45 | Q3 missing or blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, warnings sorted into fix/explain/ignore | Compiles, warnings unexamined (−8) | Does not compile |
| **Testbench + vectors** | 20 | ≥ 6 checked vectors **including the hold vector**; coverage argument present | Vectors present, no coverage argument (−7); hold vector missing (**−12**) | Applies stimulus but checks nothing |
| **Simulation results** | 20 | Waveform matches Table T on all four rows; transcript clean | Passes but waveform not annotated (−5) | Fails, or no simulation run |
| **Report chapter** | 15 | 7 sections; table with numbered rows; 3-line derivation with the law named | Derivation present but law unnamed (−4); figures without interpreting sentences (−4 each) | Chapter absent |
| **Demo + explanation** | 15 | Both questions Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** accepted one week, −20.

---

## Automatic deductions

| | |
|---|---|
| Hold vector missing from testbench | **−12** — they did not test that it is memory |
| Code pasted into the report instead of `\lstinputlisting` | −5 |
| Figure with no interpreting sentence | −4 each |
| "Everything worked first try" in Discussion | −8 — the section is required and this is not it |
| Sensitivity list still incomplete but design "works" | −6 — flag it verbally, it will bite them in Lab 12 |

---

## What good looks like

A student who scores above 90 will have: the hold vector as their *first* test, not
their last; a Discussion section describing the incomplete sensitivity list biting
them and how the RTL Viewer or the waveform revealed it; and a waveform screenshot
cropped to the hold interval with an annotation on it, not a full-screen capture.

## What to watch for

- **The `'U'` panic.** Their first simulation shows `U` everywhere because they have
  not filled in the architecture body. This is expected and the template is designed
  to produce it. Say so before it causes a queue.
- **Deleting the verdict block.** Some students remove the `if errors = 0` block at
  the end of the testbench. That block is what you read at check-off — tell them it
  stays.
- **Copying between the two skeletons.** `TransLatch8` is legitimately almost
  identical to `TransLatch` — that is the lesson, not cheating. Copying from
  *another student* is different; the Discussion section is where it shows.
