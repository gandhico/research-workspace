# Lab 5 — Slide Content
### Arithmetic Logic Unit · 10 slides · 15 minutes

From here the deck shrinks and the check-off lengthens. Almost no new VHDL — the
difficulty has moved from the language to the specification.

---

## Slide 1 — Title
> **EE 362 — Laboratory 5**
> **Arithmetic Logic Unit**

---

## Slide 2 — Today's one idea
> ### An ALU is a multiplexer over function units.
> You already built the multiplexer.

*Say:* This is the biggest component so far and the least new. There is almost no
new VHDL this week. What changed is that the difficulty moved out of the language
and into the specification — that is true for every remaining lab.

---

## Slide 3 — It does not choose, then compute
> Every unit runs **in parallel, all the time**, on the same inputs.
>
> The function code doesn't say *what to calculate*.
> It says *which already-calculated answer to forward*.

*Say:* This trips people up. There is no "decide, then do". The doing already
happened — all sixteen answers exist simultaneously and the mux picks one. That is
why an ALU costs area rather than time.

---

## Slide 4 — Sixteen is too many to wire by hand
> Example 2: two units + a `Mux2`, structurally. **You can see it.**
>
> Sixteen units + a 16-to-1 mux: pointless typing.
>
> ```vhdl
> case Func is
>     when ALU_FUNC_ADD => result <= ...;
> ```
> ### The `case` IS the multiplexer.

*Say:* Check the RTL Viewer after you build it — the synthesiser draws a mux. A
case statement is simply how you *spell* a multiplexer when there are too many
inputs to wire individually. Your report has to say this.

---

## Slide 5 — Flags go AFTER the mux
> $$\text{Zero} = \overline{R_{31} + R_{30} + \cdots + R_0} \qquad \text{Neg} = R_{31}$$
>
> Take the **adder's** Zero flag, and an `AND` producing zero reports `Zero = 0`.
>
> In Lab 8 that becomes a branch taken when it shouldn't be.

*Say:* `Neg` needs no computation at all — in two's complement the top bit *is* the
sign. And these two signals are the entire input to conditional branching three
weeks from now. Getting them wrong here surfaces as a mysterious control-flow bug
in Lab 8, which is a miserable way to find it.

---

## Slide 6 — The shift everybody gets wrong
> $-8 = $ `0xFFFFFFF8`, shifted right by 1:
>
> | | result | as a number |
> |---|---|---|
> | `SRL` | `0x7FFFFFFC` | +2 147 483 644 |
> | `SRA` | `0xFFFFFFFC` | **−4** |
>
> Shifting right by one should **divide by two**.

*Say:* Filling with zero destroys the sign. Filling with the sign bit preserves it.
Same idea as sign extension last week, applied while shifting.

---

## Slide 7 — And why it's easy to get wrong
> ```vhdl
> shift_right( unsigned(X), n )   -- this is SRL
> shift_right(   signed(X), n )   -- this is SRA
> ```
> Same operator. **The type decides the behaviour.**
>
> An `SRA` written with `unsigned()` compiles, runs,
> and is wrong **only for negative numbers**.

*Say:* Which is exactly the case most people forget to test. If your SRA vectors
are all positive values, you have tested nothing. That is why the spec makes a
negative SRA vector mandatory.

---

## Slide 8 — Set on less than
> Naive: *subtract, look at the sign bit.* **Wrong when the subtraction overflows** — the sign bit lies.
>
> $$\text{SOLS} = R_{31} \oplus V$$
>
> In VHDL: `if signed(Ain) < signed(Bin)` — already overflow-correct.
>
> Same bits, different answers:
> `0xFFFFFFFF` vs `0x00000001` → signed **1**, unsigned **0**

*Say:* Use the operator — `numeric_std` comparisons are correct and the synthesiser
builds exactly that equation. But explain the equation in your report. Knowing why
the naive version fails is the point; retyping it in gates is not.

---

## Slide 9 — Your assignment, and where to spend time
> **Ten are one line each.** Do them in five minutes, get it compiling.
>
> **Then spend the session on four things:** `SRA`, `SOLS`, `SOLU`, the flags.
>
> Use `ALU_FUNC_*` from the package — **never raw bit patterns.**
> A typo in a name is a compile error. A typo in `"01001"` is a 20-minute hunt.
>
> ⚠ The supplied testbench **already has one failing vector** (`SUB`). That's deliberate.

*Say:* A testbench should be red until the design is right, not green until you look
closely. ADD is given to you, so a testbench that only tests ADD passes immediately
and tells you nothing.

---

## Slide 10 — New evidence this week, and tonight
> **E4 Resource** — ALM count; registers must be **0**
> **E6 Timing** — Fmax on the *Slow 1100mV 85C* model, and the critical path
>
> First design big enough for those numbers to mean anything.
>
> **Tonight:** the function table, and the `SRA`/`SRL` waveform pair.
>
> **Discussion:** why does the naive set-on-less-than fail?

*Say:* Find the critical path and say which operation it runs through. It will not
be the logic gates — those are one level deep. Predict it before you look.

---

## Production notes
- 10 slides but a shorter talk — this deck should run 12 minutes, not 15. The extra
  time goes to the build phase, which needs it.
- Slides 6–7 are one story. Run Example 3 live between them.
- Slide 5's point about Lab 8 is worth repeating at check-off.
