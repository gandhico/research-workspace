# Lab 11 — Slide Content
### Instruction Decoder II · 8 slides · 12 minutes

---

## Slide 1 — Title
> **EE 362 — Laboratory 11**
> **Instruction Decoder II**

---

## Slide 2 — Today's one idea
> ### Memory access and control flow are just four more rows.
>
> **Step 1: paste in your Lab 10 decoder.**
> If it had latches, **fix that first** — Lab 12 is next week.

---

## Slide 3 — LW and SW share an adder
> ```
> LW   rt, offset(rs)     address = rs + offset
> SW   rt, offset(rs)     address = rs + offset
> ADDI rt, rs, imm        result  = rs + imm
> ```
> Computing `a + b` and computing `base + offset` are the **same operation**.
>
> ### That is why a load costs no more hardware than an add.

*Say:* Look at `ALU_Asel` once your table is complete: it is IMMED for `ADDI`,
`LUI`, `LW` and `SW` — four instructions with nothing obvious in common. When one
control signal is high for a strange-looking set of instructions, **look for the
shared resource.**

---

## Slide 4 — Where LW and SW must differ
> | | LW | SW |
> |---|---|---|
> | `DM_rw` | RD | WR |
> | `RF_Dsel` | MEM | – |
> | **`RF_strb`** | STROBE | **HOLD** |
> | **`RF_oe`** | HiZ | **DRIVE** |
>
> A store writes **memory**, not a register.
> During a store, the **register file** drives the bus — the RAM doesn't.

*Say:* Those two bold signals are the entire difference between "store" and
"corrupt". Leave `RF_strb` at STROBE and every store silently damages a register —
and because the store itself still works, the program fails somewhere else
entirely. Leave `RF_oe` at HiZ and the store writes `'Z'`, which the RAM happily
stores.

---

## Slide 5 — BLEZ and J
> **`BLEZ`** — `NIAG_sel = REL`, `NIAG_cond = LEZ`, **`IR_Xlsft = TWO`**, `RF_strb = HOLD`
>
> The only instruction in this CPU that **scales** its immediate.
> Miss it and every branch lands a quarter of the way to its target.
>
> **`J`** — `NIAG_sel = ABS`, `NIAG_cond = NONE`. **That's all.**
> Two signals changed, fourteen defaults.

*Say:* `BLEZ` runs the ALU even though nobody keeps the result — it does that purely
to produce the flags that decide the branch. `RF_strb` is HOLD: control flow writes
no register.

And notice how sparse `J` is. A control unit is mostly "do nothing" with a few
exceptions per row. That is why default-first is the *natural shape of the problem*,
not a coding convenience.

---

## Slide 6 — Two correct answers
> `IR_Xsel`, two implementations:
>
> **transcribed** SIGN for ADDI, LW, SW, BLEZ
> **minimised** SIGN for everything except LUI
>
> They **disagree** on ADD, SLL and J.
> Those three **never read the extender**.
>
> ### Both are correct. The minimised one is cheaper.

*Say:* This is what minimisation means in a real control unit — the same operation
as a K-map in Lab 3, except the don't cares now come from the *architecture*: which
instructions read which signals.

And it is a warning about testing. A testbench that pinned `IR_Xsel` down for `ADD`
would be testing an accident of your implementation, not a requirement.
**Over-specifying a test is its own kind of bug.**

---

## Slide 7 — Table-driven testing
> The expected control bundle for each instruction lives in an **array**.
> One loop checks every field of every row.
>
> **8 instructions × 14 fields = 112 checks, from one loop.**
>
> If your table and your decoder disagree, **one of them is wrong** —
> and finding out which is the exercise.

*Say:* Write the expectation table from the *specification*, not by reading your own
decoder. A test copied from the implementation agrees with the bug.

---

## Slide 8 — Three latch tests, and print your table
> | sequence | signal | must be |
> |---|---|---|
> | `LUI` after `ADDI` | `IR_Xsel` | ZERO |
> | `SW` after `BLEZ` | `IR_Xlsft` | NONE |
> | `ADD` after `SW` | `RF_oe` | HiZ |
>
> With eight rows there are far more signals that some instructions set
> and others do not.
>
> ### PRINT YOUR COMPLETED CONTROL TABLE. Bring it next week.

*Say:* Step three of the Lab 12 debugging method is *"do the control signals match
the table for this opcode?"*. You will not get through next week without it.

---

## Production notes
- 8 slides, ~12 min. The build phase needs the time: eight rows plus a table-driven
  testbench is genuinely a full session.
- Run Example 2 live at slide 6 — the transcript printing "differ, and it cannot
  matter" for exactly ADD, SLL and J is the demonstration.
- End on slide 8's last line and mean it. Students who arrive at Lab 12 without the
  printed table lose the session.
