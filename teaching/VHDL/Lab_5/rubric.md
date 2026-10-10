# Lab 5 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors; no latch warning; `ALU` reports **0 registers** |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Run `SRA` on a negative number. What comes in at the top, and why is it not zero?*
   - **Full:** the sign bit is replicated; explains that filling with zero destroys the sign so `−8 >> 1` would read as +2 billion instead of −4; knows the VHDL type (`signed` vs `unsigned`) is what selects the behaviour.
   - **Partial:** knows the sign is preserved, cannot say what controls it in VHDL.
   - **None:** cannot produce a negative SRA case.

2. *Your Fmax is ___ MHz. Which operation is on the critical path, and why is that unsurprising?*
   - **Full:** names the adder/subtractor carry chain (or the comparison, which contains a subtract); explains that logic ops are one gate deep while a 32-bit carry propagates.
   - **Partial:** reports Fmax, has not looked at the path.
   - **None:** did not run timing analysis.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted at 3:45 | Q3 blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, no latch warning, 0 registers | Latch warning (**−10**) | Does not compile |
| **Testbench + vectors** | 20 | ≥3 vectors per operation; all five required vectors present; boundary coverage argument | Missing the SOLS/SOLU pair (**−8**); no coverage argument (−7) | Stimulus without checks |
| **Simulation results** | 20 | All implemented ops verified; `SRA`/`SRL` shown side by side | SRA tested only on positives (**−10** — the vectors prove nothing) | Fails or not run |
| **Report chapter** | 15 | 7 sections; function table; `case`-is-a-mux explained; SOLS equation explained; E4 + E6 with interpretation | E6 reported without a critical-path sentence (−4); SOLS equation absent (−4) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| **`SRA` implemented with `unsigned()`** | **−12** — it is the headline bug of the lab |
| `SRA` tested only on positive values | **−10** — the test set cannot detect the above |
| `SOLS` and `SOLU` give the same answer on `0xFFFFFFFF`/`0x00000001` | **−10** — one of them is wrong |
| Flags taken from one operation instead of the selected result | **−8** — this becomes a Lab 8 branch bug |
| Raw bit patterns instead of `ALU_FUNC_*` constants | −5 |
| Missing `when others` | −6 |
| `to_integer` called inline in every branch instead of once into a signal | −2 and a note; it works but it is noise |
| Code pasted into the report | −5 |
| Figure with no interpreting sentence | −4 each |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: the report states plainly that the `case` is the multiplexer and shows the
RTL Viewer mux as evidence; the `SRA`/`SRL` waveform pair is a single annotated
figure with the two answers on the same negative input; the SOLS discussion explains
*why* the sign bit lies on overflow rather than just quoting `R₃₁ ⊕ V`; and the
critical path was predicted before it was measured.

## What to watch for

- **The five-minute trap.** Ten operations are one-liners. Students who write all
  sixteen carefully in order run out of time before `SRA` and `SOLS` — the only
  parts that carry the marks. Say at the spec walk: *get the easy ten done in five
  minutes, then slow down.*
- **`to_integer` inline everywhere.** Works, but produces sixteen conversions and an
  unreadable case. Push the single `amount` signal.
- **Comparing `std_logic_vector` directly.** `Ain < Bin` on raw vectors compares bit
  patterns lexicographically, not numbers. It compiles. Cast first.
- **Package constants ignored.** Someone will type `"01001"`. When their SOLS
  mysteriously does nothing, this is why.
- **Flags inside the case.** Some students assign `Zero` and `Neg` in every branch.
  It can be made correct but it is sixteen chances to get it wrong; push the
  after-the-case version and cite Example 2.
- **Finished early.** Rare this week. If it happens: have them find the critical path
  and try to predict how Fmax would change if `SOLS`/`SOLU` were removed, then test
  the prediction.
