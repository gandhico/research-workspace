# Lab 2 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors; Fitter reports **32 registers** for `RegN` |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Show me a point in your waveform where D changed and Q did not. Why not?*
   - **Full:** identifies that the change was between edges, and that the master was open but the slave was closed, so nothing reached the output.
   - **Partial:** "because it's edge-triggered" without the mechanism.
   - **None:** cannot find such a point in their own waveform.

2. *Your register is Lab 1's latch equation with two signals renamed. Which became which — and why is the sensitivity list different?*
   - **Full:** `En`→`Ld`, `Clr`→`Rst`; and: a clocked process needs the clock plus asynchronous controls only, because `D` and `Ld` are read only at the edge.
   - **Partial:** gets the renaming, not the sensitivity-list reason.
   - **None:** neither.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted, submitted at 3:45 | Q3 blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors; warnings triaged; 32 registers reported | Compiles, register count not checked (−6) | Does not compile |
| **Testbench + vectors** | 20 | ≥ 6 vectors **including the edge vector**; coverage argument | No coverage argument (−7); async reset tested only on an edge (**−8**) | Stimulus without checks |
| **Simulation results** | 20 | Waveform matches all four rows; toggle-between-edges shown | Passes but waveform not annotated (−5) | Fails or not run |
| **Report chapter** | 15 | 7 sections; Table T; both latch equations; sensitivity-list justification | Sensitivity-list question unanswered (−5) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| **Edge vector missing** (never toggles D between edges) | **−12** — they have not shown it is edge-triggered rather than transparent |
| Async reset only ever asserted at a clock edge | **−8** — that tests a synchronous reset, which is a different circuit |
| `Clr` wired to the slave only | −6 — flag it; ask them to run one more cycle and watch the clear undo itself |
| `MSFlipFlop` written behaviourally instead of structurally | −10 — the structure *is* the assignment this week |
| Code pasted into the report | −5 |
| Figure with no interpreting sentence | −4 each |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: the report shows both RTL Viewer pictures side by side with one sentence
on why two latches and one flip-flop are the same behaviour; the waveform is
cropped to a single clock period with the three D-toggles and the one Q-move
annotated; and the Discussion answers the sensitivity-list question as something
they worked out rather than something they were told.

## What to watch for

- **Simulation appears frozen.** Clock process with no `wait`. It is looping at time
  zero, not hung. Extremely common this week — announce it during the spec walk.
- **`generic map` semicolon.** `generic map (...) port map (...)` — no semicolon
  between. The resulting error message points somewhere unhelpful.
- **Forgetting `generic map` entirely.** They silently get width 32 and then hit a
  width mismatch on the 5-bit instance.
- **Setup-time violations.** Students who change `D` exactly on a rising edge get
  results that vary and conclude the design is broken. Point them at the falling
  edge as the safe place to change stimulus.
- **Register count ≠ 32.** Usually means they wrote the register combinationally or
  left an inferred latch. Good teaching moment: the number is a correctness check.
