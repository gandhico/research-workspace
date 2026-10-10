# Lab 11 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors, no latch warning, `Decoder` reports **zero registers** |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures, all 8 rows in the table |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Why is `RF_strb` HOLD for `SW`?*
   - **Full:** a store writes memory, not a register; leaving it STROBE would silently corrupt a register on every store, and because the store itself still works the program would fail somewhere else entirely.
   - **Partial:** knows it should be HOLD, cannot say what goes wrong.
   - **None:** has it STROBE.

2. *Why is `IR_Xlsft` set to ×2 only for `BLEZ`?*
   - **Full:** branch offsets count instructions, not bytes, so the offset is scaled by 4; every other immediate in this CPU is a byte quantity; missing it puts every branch a quarter of the way to its target.
   - **Partial:** knows only BLEZ scales, cannot say why.
   - **None:** neither.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted at 3:45 | Q3 blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, no latch warning, zero registers | Latch warning (**−12**) | Does not compile |
| **Testbench + vectors** | 20 | All 8 rows in the table with full bundles; unknown opcode; unknown func; **three latch tests** | Table incomplete (−2 per missing row); latch tests missing (**−8**) | Stimulus without checks |
| **Simulation results** | 20 | Every field of every row verified | Only some fields checked (−6) | Fails or not run |
| **Report chapter** | 15 | **Complete eight-row control table**; the three observations; the don't-care discussion | Table incomplete (**−6**); observations missing (−4); don't-care discussion missing (−4) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| **`SW` with `RF_strb = STROBE`** | **−12** — silently corrupts a register on every store |
| **`SW` with `RF_oe = HiZ`** | **−12** — stores `'Z'` |
| **`BLEZ` without `IR_Xlsft = TWO`** | **−10** — every branch off by a factor of four |
| `BLEZ` or `J` with `RF_strb = STROBE` | −10 |
| Latches surviving from Lab 10 | **−12** and fix on the spot |
| Expectation table copied from the decoder rather than the specification | **−8** — it agrees with the bug and cannot detect anything |
| Three latch tests absent | −8 |
| Control table in the report incomplete | −6 |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: the complete eight-row table is in the report and legible enough to debug
from; the three observations (shared adder, table sparsity, the `RF_strb` rule) are
stated as insights rather than restatements; the don't-care discussion explains why
*two different implementations are both correct*; and the expectation table was
written from the specification, with a Discussion noting where it and the decoder
disagreed and which turned out to be wrong.

## What to watch for

- **`SW`'s two signals.** `RF_strb = HOLD` and `RF_oe = DRIVE`. Ask for both at every
  bench — they are the difference between storing and corrupting, and both fail
  silently.
- **`BLEZ` without the scale.** Passes every decoder test that does not look at
  `IR_Xlsft`, then puts every Lab 12 branch in the wrong place.
- **Latches from Lab 10.** Anyone who carried one in must fix it before merging.
  Merging four more rows into a latched design makes it strictly worse.
- **Expectation table written by reading their own decoder.** Then it agrees with
  whatever they wrote, including the bugs. Ask where the table came from.
- **The single-element aggregate.** The shipped table has one row and uses `0 =>`
  for that reason; once students add a second row they can drop it. If they get
  "Bit string literal found where non-array type was expected", this is why.
- **Finished early.** Have them add `SYSCALL` decoding that raises an exception
  signal, and connect it to the Lab 8 exception-vector stretch if they did it.

## Before they leave

**Tell every student to print their completed control table and bring it to Lab 12.**
Step three of the debugging method is *"do the control signals match the table for
this opcode?"* — students who arrive without it lose the session.
