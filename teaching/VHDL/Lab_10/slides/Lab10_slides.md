# Lab 10 — Slide Content
### Instruction Decoder I · 8 slides · 12 minutes

The deck is now at its shortest and the check-off at its longest. Almost no new
syntax — the difficulty is entirely systems thinking.

---

## Slide 1 — Title
> **EE 362 — Laboratory 10**
> **Instruction Decoder I**

---

## Slide 2 — Before anything else: the scope
> ### This CPU has **eight** instructions.
> Not forty. The ones its program uses.
>
> **Four this week. Four next week.**
>
> The manual is not your specification. **The control table is** — and it is
> given to you, filled in.

*Say this first, and say it plainly.* The fear in this lab is scope, and the
scope is small. You implement the table; you do not derive it. Deriving it is
Dr Tang's lecture, not fifty-five minutes at a bench.

---

## Slide 3 — Today's one idea
> ### A control unit is one truth table with sixteen output columns.

*Say — slow down here, this is the intellectual close of the course:*

In Lab 1 you took a four-row truth table and wrote one Boolean equation from it.
Today you take an eight-row table and write sixteen.

**That is the entire difference. Nothing new has been introduced since week one.**
The control unit of a processor *is* a truth table — that is not an analogy, it is
literally what you are about to write.

---

## Slide 4 — Fields, and why the opcode sits where it does
> ```
> R  | opcode | rs | rt | rd | sa | func |
> I  | opcode | rs | rt |   immediate    |
> J  | opcode |        index             |
>      31..26
> ```
> The opcode is **always** at 31..26.
>
> Until you decode it you don't know the format —
> so the field you need first must be at a fixed position.

*Say:* And notice `rs` and `rt` are in the same place across R and I types. That
lets the register file start reading *before* decoding finishes. Field placement in
an ISA is a hardware decision, not an aesthetic one.

---

## Slide 5 — One instruction, end to end
> `ADD rd, rs, rt` — read two registers, add, write a third, carry on.
>
> | signal | value |
> |---|---|
> | `ALU_func` | ADD |
> | `ALU_Asel` | AOUT |
> | `RF_Dsel` | ALU |
> | `RF_Wsel` | RD |
> | `RF_strb` | STROBE |
>
> **Five signals. The other eleven keep their defaults.**

*Say:* That is the whole point of having a default — you specify only what is
different. Everything unmentioned is already safe: no memory access, no bus
driving, PC advances.

---

## Slide 6 — Assign the default FIRST
> ```vhdl
> c := CTRL_DEFAULT;     -- <<< every field defined, every path
> case opcode is
>     when OP_ADDI => ...
> ```
> Skip it → the synthesiser keeps unassigned fields unchanged
> → **sixteen latches**
> → control signals that depend on **which instruction ran before**.

*Say:* You have met this twice. Lab 1's missing `else` — there you *wanted* the
latch. Lab 3's missing `when others` — there you did not. Same sentence every time:
**no assignment means hold the previous value.**

In Lab 12 the symptom is the worst kind: every instruction works when tested alone,
the program still fails, and it fails *differently* depending on instruction order.

---

## Slide 7 — Your four rows
> | instr | ALU_func | ALU_Asel | ALU_Ssel | IR_Xsel | RF_Wsel |
> |---|---|---|---|---|---|
> | `ADD` | ADD | AOUT | – | – | **RD** |
> | `SLL` | SLL | AOUT | SA | – | **RD** |
> | `ADDI` | ADD | IMMED | – | **SIGN** | **RT** |
> | `LUI` | ADD | IMMED | – | **ZERO** | **RT** |
>
> R-type writes **rd**. I-type writes **rt**. Different fields.
> `ADDI` sign-extends. `LUI` zero-extends. **One signal apart.**

*Say:* Get `RF_Wsel` backwards and you write the wrong register, silently. Get
`IR_Xsel` backwards on `ADDI` and it adds 65535 instead of subtracting one — your
Lab 12 loop counts the wrong way forever.

And `SPECIAL` is not one instruction, it is a *family*. You must check `func` too,
or every R-type becomes `ADD`.

---

## Slide 8 — The test only a decoder needs, and tonight
> **Required in your testbench: an ORDER-DEPENDENCE test.**
>
> Feed `ADDI`, then `LUI`. Does `LUI` still zero-extend?
> Then the reverse.
>
> A testbench that applies one instruction at a time **cannot detect a latch.**
>
> **E4: zero registers.** Any register or latch = the Example 3 bug.

---

## Production notes
- 8 slides, ~12 min, and the shortest deck of the term. The build phase and the
  check-off both need the time.
- Slide 2 must come first and must be said plainly — the fear here is scope.
- Slide 3 deserves a pause. It is the sentence the whole course has been building
  toward.
- Run Example 3 live between slides 6 and 7; the `'U'` then `'1'` progression on
  `bad_decode` is the demonstration.
