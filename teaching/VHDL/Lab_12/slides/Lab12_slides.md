# Lab 12 — Slide Content
### CPU Integration · 8 slides · 12 minutes

The last technical deck of the term, and the shortest talk. The session is 55 minutes
of wiring and debugging; give it the time.

---

## Slide 1 — Title
> **EE 362 — Laboratory 12**
> **CPU Integration**

---

## Slide 2 — What you are about to run
> | addr | instruction |
> |---|---|
> | `0x00` | `LUI  r1, 11` |
> | `0x04` | `LUI  r2, 1` |
> | `0x08` | `ADDI r1, r1, -1` |
> | `0x0C` | `BLEZ r1, +2` |
> | `0x10` | `SLL  r2, r2, 1` |
> | `0x14` | `J    0x08` |
> | `0x18` | `SW   r2, 0(r0)` |
>
> **45 instructions. CPI = 1. r2 ends at `0x400`.**
> ### Your CPU computes 2¹⁰.

*Say:* Every component you have built since Lab 1 exists to make these seven
instructions run. Today you wire them together.

---

## Slide 3 — Today's one idea
> ### Debugging a system means predicting it first.
>
> Almost no new VHDL. This is **wiring, timing and debugging.**
> Emotionally hard, technically shallow.

---

## Slide 4 — The timing contract
> **↑ rising edge — FETCH.** `IRreg <= ROM[PC]`
> **↓ falling edge — COMMIT.** register file, RAM, PC
>
> One instruction per clock period.
> Captured at the start, everything commits in the middle.
>
> **The register file and NIAG need an INVERTED clock.**

*Say:* Write this on paper before you wire anything. Their architectures use
`rising_edge` and you want them committing on the falling edge with everything
else — inverting at the instantiation is how you retime a component you do not want
to modify.

**Every bug in this lab that is not a mis-wire is an edge mistake.**

---

## Slide 5 — Three wirings that are easy to get wrong
> 1. **`Asel = rt`, `Bsel = rs`.** Swap them and *three of the four instruction
>    types still work.*
> 2. The **store value comes from `Aout`**, through the TriBuffer.
> 3. The **ROM is addressed by `PCreg`**, not `NSA`.

*Say:* Don't trust me on number 1 — work it out. `ADDI`/`LW`/`SW` need the base
register on `Bout` because the ALU's A input is the immediate. `SLL` shifts `rt` on
`Aout`. `SW` stores `rt` from `Aout`. `BLEZ` has `rt = 0`. One assignment satisfies
all eight.

---

## Slide 6 — When it doesn't work: bisect
> | | check | if it fails |
> |---|---|---|
> | 1 | Is the PC advancing by 4? | NIAG, or reset |
> | 2 | Is IR what the ROM table says? | ROM addressing, fetch |
> | 3 | Do control signals match your table? | the decoder |
> | 4 | *Only now*, the datapath. | the wiring |
>
> ### Do not open the waveform and stare at forty signals.

*Say:* Each check depends on the ones before it. Checking the ALU while the PC is
stuck tells you nothing — the ALU is faithfully computing on garbage.

Do them **in order** even when you are sure you know what is wrong. You are usually
not. And this is why you printed the control table.

---

## Slide 7 — Practise on a broken one
> Example 1 is a CPU with **two deliberate wiring errors.**
>
> Both compile. Both run. **Both pass checks 1, 2 and 3.**
>
> Both produce the same headline symptom — the stored word is wrong.
> **The symptom does not identify the bug. The method does.**

*Say:* Establishing that checks 1–3 pass is not wasted effort — it is exactly what
tells you the fault is in the wiring rather than the control. One of the two bugs is
visible on almost every line of the trace; the other on exactly one line. That is why
you read the trace instruction by instruction.

---

## Slide 8 — Hand-compute first, and what to collect
> **Work out the first five trace rows on paper before you simulate.** Graded.
>
> You cannot tell a wrong trace from a right one if you cannot predict it.
>
> **Collect E1 through E7** — the only design all term that reports every one
> meaningfully.
>
> **E5:** the ALU needed 108 pins in Lab 5. The whole CPU needs **one**.

*Say:* That contrast is what "wide blocks live inside the chip" actually means.

---

## Production notes
- 8 slides, 12 minutes maximum. The build phase is the lab.
- Slide 2 should stay up while you talk through slides 3 and 4 if you can manage it.
- Run Example 1 live at slide 7 only if time allows; otherwise point at it and let
  them run it. The method matters more than watching you do it.
- Do not cut slide 6. Students who skip the method lose the session to guessing.
