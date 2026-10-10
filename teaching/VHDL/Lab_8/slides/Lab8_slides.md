# Lab 8 — Slide Content
### Next Instruction Address Generation II · 9 slides · 12 minutes

---

## Slide 1 — Title
> **EE 362 — Laboratory 8**
> **Next Instruction Address Generation II**

---

## Slide 2 — Today's one idea
> ### Branch conditions are Boolean equations over the ALU flags.

*Say:* After today the entire address side of the processor is finished. And this
is your first integration exercise — six components, no new logic. Treat it as a
rehearsal for Lab 12, because that is exactly what it is.

---

## Slide 3 — Absolute jumps: four bits you don't get to choose
> $$\text{Abslt} = \underbrace{\text{NSA}(31..28)}_{\text{inherited}} \,\&\, \underbrace{\text{Index}(25..0)}_{\text{encoded}} \,\&\, \underbrace{\text{"00"}}_{\text{always 0}}$$
>
> 4 + 26 + 2 = 32. **Pure wiring — no adder.**

---

## Slide 4 — The real jump
> | | | |
> |---|---|---|
> | `0x14` | `0x08000002` | `J 0x08` |
>
> NSA = `0x18` → top 4 bits = `0x0`
> Abslt = `0x0` & `0x0000002` & `00` = **`0x00000008`**
>
> `0x08` is the `ADDI` at the top of the loop.
> ### This jump is what makes the loop a loop.

*Say:* Again, not a made-up example. Your CPU executes this ten times in Lab 12.

---

## Slide 5 — The consequence
> The top four bits are **inherited, not encoded**.
>
> → a jump **cannot leave its 256 MB region**.
>
> Not a bug. It is what you get for spending 26 bits instead of 32.
> To go further you need `JR` — a full 32-bit address from a register.

*Say:* Example 1 shows this directly: the same index from two different regions
gives two different targets. That is a real architectural trade-off and it is worth
a sentence in your report.

---

## Slide 6 — Every conditional branch, in six equations
> | code | meaning | Taken = |
> |---|---|---|
> | `NONE` | always | 1 |
> | `EQ` | = 0 | Z |
> | `NEQ` | ≠ 0 | Z̄ |
> | `GTZ` | > 0 | **N̄ · Z̄** |
> | `GEZ` | ≥ 0 | N̄ |
> | `LTZ` | < 0 | N |
> | `LEZ` | ≤ 0 | N + Z |
>
> **Complements:** GTZ/LEZ · GEZ/LTZ · EQ/NEQ

*Say:* This is the payoff for the flags you built in Lab 5. Two bits from the ALU,
and out of them comes every conditional branch the machine has.

Look at the complement pairs — the hardware is *smaller* than the instruction list
makes it look. That is generally true, and it is why you read the control table
rather than the manual. The manual lists what a programmer may write; the table
shows what the hardware does.

**Watch `GTZ`.** It is not `N̄`. That would be `GEZ`. Zero is not greater than zero.

---

## Slide 7 — Two decisions, not one
> **`Sel`** — *which* address is the candidate?
> **`Cond`** — is a *relative* branch actually used?
>
> | Sel | NextPC | |
> |---|---|---|
> | `NSA` | NSA | unconditional |
> | `REL` | **Taken ? Rel : NSA** | conditional |
> | `REG` | RegAddr | unconditional |
> | `ABS` | Abslt | unconditional |

*Say:* Students try to merge these every year and it does not work. Only the
relative path is conditional. Not-taken falls back to NSA because "not taken" is
not a special state — it means carry on to the next instruction, which is NSA.

And there is no conditional `J`. Conditional control flow uses relative addressing
because conditions are usually local. A design decision, not a limitation.

---

## Slide 8 — Your assignment: six blocks, no new logic
> **Step 1: copy your Lab 4 and Lab 7 files in.**
>
> `NIAG_Abslt` · `NIAG_Cond` · `NIAG_MUX` · **`NIAG`** (top level)
>
> **Named association in every port map. Always.**
> One internal signal per wire. You cannot read an `out` port.
>
> `Rtn` is `NSA` — a wire with a better name.

*Say:* Six components is where positional port maps start costing real time. Lab 12
has twelve. Build the habit now, and read your wiring back against the diagram once
before you simulate.

---

## Slide 9 — The scripted sequence, and tonight
> **Required:** one continuous run through — sequential, branch not taken,
> branch taken, `J`, `JR`, a `J` from the new region, a stall, a backward branch.
>
> That waveform is your report's centrepiece figure. **Annotate every transition
> with which source the PC took.**
>
> **E4: 32 registers** (the PC) and no others.

---

## Production notes
- 9 slides, ~12 min. Slides 3–5 are one story; slides 6–7 are the other.
- Run Example 3 live before slide 7 — the same Sel code with Taken high and low is
  much clearer demonstrated than described.
- Have the CPU block diagram up at slide 8 and point at the NIAG box: *after today,
  that whole box is yours.*
