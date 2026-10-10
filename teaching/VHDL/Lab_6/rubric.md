# Lab 6 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors; `RegFile` reports **~1024 registers** (or block memory, explained) |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Try to write register 0 in your waveform. Show me it did not take — and tell me what "hardwired to zero" means in hardware.*
   - **Full:** demonstrates the refused write; identifies the `[k ≠ 0]` term on the write enable as the mechanism; knows it is not a software convention.
   - **Partial:** shows R0 reads zero but has only forced it on the read side, not blocked the write.
   - **None:** R0 is writable.

2. *You read a register on the same edge it was written. Which value came out — old or new? Is that what you intended?*
   - **Full:** names READ-OLD (or READ-NEW if they built a bypass), points at the testbench check on both sides of the edge, and knows the other behaviour is also a valid design.
   - **Partial:** knows the answer but has not tested it.
   - **None:** has not considered it.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted at 3:45 | Q3(b) blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, register count explained | Count not commented on (−5) | Does not compile |
| **Testbench + vectors** | 20 | ≥6 vectors; all six required cases present | R0 write attempt missing (**−10**); read-during-write untested (**−8**) | Stimulus without checks |
| **Simulation results** | 20 | R0 refusing a write shown and annotated | R0 case not in the waveform (−6) | Fails or not run |
| **Report chapter** | 15 | 7 sections; Table C + four equations; read-during-write behaviour stated | Behaviour not stated (**−6**); equations missing (−4) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| **Register 0 is writable** | **−12** — the defining feature of the lab, and it silently corrupts Lab 12 |
| **Reads placed inside the clocked process** | **−12** — reads become clocked; the CPU cannot get operands during a cycle. Fix it at the bench, do not let it reach Lab 12. |
| Read-during-write behaviour not stated in the report | −6 |
| R0 forced on the read side only, write not blocked | −5 — works, but half the mechanism |
| Ports renamed | −5 and fix on the spot; Lab 12 will not connect |
| Indexing with a vector instead of `to_integer` | won't compile — help, no deduction |
| Code pasted into the report | −5 |
| Figure with no interpreting sentence | −4 each |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: register 0 is protected on **both** the write and the read side, and the
report says why belt-and-braces is worth it; the read-during-write check appears in
the testbench on both sides of the edge with the behaviour named in the report; and
the E4 register count is quoted with an explanation of what a different number would
have meant.

## What to watch for

- **Reads in the clocked process.** The single most damaging error of this lab. It
  simulates plausibly, passes a careless testbench, and breaks Lab 12 in a way that
  is very hard to diagnose. Check it visually at every bench.
- **R0 half-protected.** Many students force the read and forget the write, or vice
  versa. Both work in isolation — ask which one they did and why they chose it.
- **Off-by-one on the array.** 32 registers is `0 to 31`.
- **"It's too big to test."** No: R0, R31, and one middle register cover the address
  space boundaries. Point at the boundary argument from Lab 5.
- **Finished early.** Common — this is a light week after the ALU. Send them to add a
  third read port and compare the E4 delta with the two-port version, then argue how
  many read ports a two-instruction-per-cycle processor would need and why that
  scales badly. It previews the pipeline discussion.
