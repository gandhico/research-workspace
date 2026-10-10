# Lab 7 — Slide Content
### Next Instruction Address Generation I · 9 slides · 12 minutes

---

## Slide 1 — Title
> **EE 362 — Laboratory 7**
> **Next Instruction Address Generation I**

---

## Slide 2 — Today's one idea
> ### The PC is a register; everything else is address arithmetic.

*Say:* This is where the machine stops being a pile of parts and starts having a
control flow. Everything you have built so far computed values. This decides what
happens next.

---

## Slide 3 — A counter would not be enough
> A counter only **counts**.
>
> A program counter must also **jump** — to a branch target, to a subroutine,
> back from one.
>
> So "advance to the next instruction" is not a special mechanism.
> ### It is just loading PC+4.

*Say:* Next week that single NextPC input becomes a multiplexer over five candidate
addresses, and sequential execution becomes one input of the mux. Nothing special.

---

## Slide 4 — A real instruction
> | address | encoding | instruction |
> |---|---|---|
> | `0x0C` | `0x18200002` | `BLEZ r1, +2` |
>
> $$\text{NSA} = 0x0C + 4 = 0x10$$
> $$\text{offset} = \text{SignExt}(0x0002) \ll 2 = 2 \times 4 = 0x08$$
> $$\text{target} = 0x10 + 0x08 = \mathbf{0x18}$$

*Say:* This is not a made-up example. It is instruction four of the program your CPU
runs in Lab 12, and 0x18 is the store that ends the loop. Work it out with me.

---

## Slide 5 — Why PC+4, not PC?
> By the time the branch is evaluated, **the fetch already happened.**
>
> Using PC would put every target one instruction early —
> so the assembler would have to compensate.
>
> Basing on PC+4 keeps the encoding honest: **"+2" means "skip 2".**

---

## Slide 6 — Why shift left by two?
> Instructions are 4 bytes and word-aligned.
> → the low two bits of every instruction address are **always zero**
>
> Encoding them would waste two bits on information we already have.
>
> ### Shift instead, and get 4× the branch range for free.

*Say:* A genuine architectural trade-off, and it fits in one line of concatenation.
It is also why the offset counts *instructions*, not bytes.

---

## Slide 7 — Two shapes of addressing bug
> | error | shape | tell-tale |
> |---|---|---|
> | forgot `<< 2` | off by a **factor** | target not a multiple of 4 |
> | used PC not PC+4 | off by a **constant** 4 | still aligned, still nearly right |
>
> The second one is harder to see: loops just run one instruction too many.

*Say:* Example 3 builds all three versions side by side and two of its asserts fail
on purpose. "Off by a factor" and "off by a constant" are worth naming — they are
the two shapes almost every addressing bug takes, including the ones you will hit
in Lab 12.

---

## Slide 8 — Your assignment
> **Step 1: copy your Lab 4 `ImmedXtnd.vhd` into the folder.**
>
> 1. **`NIAG_NSA`** — one line. NSA = PC + 4.
> 2. **`NIAG_Rel`** — one line. Rel = NSA + Xtnd32.
> 3. **`NIAG_Reg`** — the PC. *Your Lab 2 `RegN`, renamed.*
>
> $$PC^+ = \overline{Rst}\,(Strb \cdot NextPC + \overline{Strb} \cdot PC)$$
>
> Testbench must include a **backward** branch. All-positive offsets test nothing.

*Say:* You are not writing the extender again. In the real CPU it is a shared block —
its output feeds the ALU *and* this adder. One extender, two consumers. That is why
NIAG_Rel takes an already-extended value.

---

## Slide 9 — Hand-compute first, and tonight
> **Hand-compute every branch target before you simulate.**
> Put the arithmetic in your report.
>
> If you cannot predict the hardware, you cannot debug it —
> and Lab 12 is entirely debugging.
>
> **E4: 32 registers**, one per PC bit. The two adders have none.

---

## Production notes
- 9 slides, ~12 min. Slides 4–6 are one continuous story; do not break them up.
- Work slide 4's arithmetic on the whiteboard with the room, do not just show it.
- Run Example 3 live between slides 6 and 7 — the two failing asserts land better
  than the table does.
