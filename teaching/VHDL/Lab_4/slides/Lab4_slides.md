# Lab 4 — Slide Content
### Datapath Support Components · 10 slides · 15 minutes

---

## Slide 1 — Title
> **EE 362 — Laboratory 4**
> **Datapath Support Components**
> Extender · Tri-state · Shift select

---

## Slide 2 — Today's one idea
> ### `'Z'` is not a Boolean value.
> Some hardware lives outside Boolean algebra.

---

## Slide 3 — Widening is two operations
> Same 4-bit input `0x8`:
>
> **zero-extend** → `0x08` = 8
> **sign-extend** → `0xF8` = −8
>
> Neither is "more correct". **The instruction decides.**

*Say:* Widening a number is not one operation. Which one you want depends on what
the bits *mean*. And you cannot tell by looking at the bits — the instruction
carries that information, which is why there is a control signal for it.

---

## Slide 4 — Why it matters in your CPU
> `ADDI r1, r1, -1` → immediate is a **signed offset** → **sign**-extend
> Zero-extend it and −1 becomes **+65535**.
>
> `LUI r1, 0x000B` → immediate is a **bit pattern** → **zero**-extend
>
> *Your Lab 12 loop counter depends on getting this right.*

*Say:* This is not hypothetical. The program your CPU runs in Lab 12 starts by
loading 11 into r1 and then subtracting one each time round. Zero-extend that −1
and the loop counts upward forever. One control bit.

---

## Slide 5 — Why branch offsets are shifted by two
> Branch offsets count **instructions**, not bytes.
> Instructions are 4 bytes and word-aligned → low 2 bits are **always zero**.
>
> Encoding them wastes 2 bits. Shifting gives **4× the range for free.**

*Say:* You will meet this again in Lab 7 when you compute a real branch target.
It is a genuine architectural trade-off and it fits in one line of concatenation.

---

## Slide 6 — The third state
> ```vhdl
> Y <= A when Sel = '1' else 'Z';
> ```
> `'Z'` = **high impedance** = *"I am not driving this wire at all."*
>
> That is not a value. It is the **absence** of one.
>
> ### This is not a Boolean function.

*Say:* Its output range is zero, one, or Z. Boolean algebra has two values. You
cannot write this as AND, OR and NOT — and that is worth saying in your report,
because it is the first component all semester that is outside the algebra.

---

## Slide 7 — Resolution
> | | `0` | `1` | `Z` |
> |---|---|---|---|
> | **`0`** | 0 | **X** | 0 |
> | **`1`** | **X** | 1 | 1 |
> | **`Z`** | 0 | 1 | Z |
>
> Two agreeing → that value. One driving, one at `Z` → **that is a bus.**
> Two disagreeing → **X**.

*Say:* Boolean algebra has two values; this table has four. That is why VHDL needs
a *resolved* type — something has to decide what a wire reads when more than one
thing touches it.

And take this away: **`X` in your waveform never means the simulator is confused.**
It means two things drove one wire and disagreed. In Lab 9 and Lab 12 that will be
the fastest diagnosis you own.

---

## Slide 8 — Resolution is per *bit*
> `0xAAAAAAAA` vs `0xBBBBBBBB` driving the same 32-bit bus:
>
> `A = 1010`, `B = 1011` → they agree on three bits per nibble
>
> Result: **`101X` repeated** — not all `X`.

*Say:* Worth knowing before it confuses you. Contention does not make the whole bus
red. It makes exactly the disagreeing bits red. To see an all-X bus you need data
that differs in every bit — zero against all-ones.

---

## Slide 9 — Your assignment
> 1. **`ImmedXtnd`** — all **four** rows. Extend first, then shift. Two steps.
> 2. **`TriBuffer`** — 32 bits, `(others => 'Z')` to release.
> 3. **`ALUsftMUX`** — *this is a `Mux2` with `W = 5`.* Reuse Lab 3, or write it. **Say which and why.**
> 4. **Testbench** — ≥ 6 vectors, and it must include:
>    - `x"8000"` both ways — **the value where the two answers differ**
>    - rows 2 and 3 (both shifted cases)
>    - bus with no driver → `Z`, and both drivers → `X`
>
> Top level `ImmedXtnd`. Register count must be **zero**.

*Say:* An immediate of `0x0001` gives the same answer either way, so it proves
nothing. Test where the implementations disagree, not where they agree. That is a
general rule for choosing vectors and it is the coverage argument for this lab.

Row 3 is the "unused" one. Skip it and you have a latch — the same trap as last
week.

---

## Slide 10 — Where these go, and tonight
> `ImmedXtnd` → `NIAG_Rel` (Lab 7) and every immediate instruction (Lab 12)
> `TriBuffer` → how the register file reaches the memory bus (Lab 9)
> `ALUsftMUX` → feeds the ALU's `Shft` port (Lab 5)
>
> **Tonight:** the two tables, and the waveform showing the bus at `Z`, at a value, and at `X`.
>
> **Discussion must answer:** *why does `ADDI` sign-extend but `LUI` zero-extend?*

---

## Production notes
- 10 slides. Slides 3–5 are one story; do not break them up.
- Slide 7's table should go on the whiteboard as well — students copy it, and they
  will refer back to it in Labs 9 and 12.
- Slide 8 exists because the reference testbench originally got this wrong. It is
  a real trap, worth the slide.
- Run Example 1 live before slide 7, then use the slide as the summary.
