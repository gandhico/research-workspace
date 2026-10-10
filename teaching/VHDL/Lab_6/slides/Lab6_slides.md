# Lab 6 — Slide Content
### Register File · 9 slides · 12 minutes

Lighter week than the ALU. Say so at Open — after Lab 5, "32 registers" sounds
worse than it is.

---

## Slide 1 — Title
> **EE 362 — Laboratory 6**
> **Register File**

---

## Slide 2 — Today's one idea
> ### Thirty-two copies of your Lab 2 register, plus address decoding.

*Say:* This looks bigger than Lab 5 and is considerably smaller. Nothing new is
being invented.

---

## Slide 3 — Three things you already own
> | | from | answers |
> |---|---|---|
> | address **decoder** | Lab 0 | which register does this address mean? |
> | array of **registers** | Lab 2 | each cell is your `RegN` |
> | two **multiplexers** | Lab 3 | which register reaches each read port? |
>
> Write the three equations. The rest is assembly.

*Say:* If you find yourself inventing something, stop — you have gone off the path.
Every part of this you have already built.

---

## Slide 4 — Write is clocked, reads are not
> ```vhdl
> process (clk)                     -- write: needs an edge
>     if rising_edge(clk) then ...
>
> Aout <= regs(index);              -- read: no clock at all
> ```
> The CPU needs **both operands during a cycle**,
> and stores the result **at the end of it**.

*Say:* That asymmetry is deliberate and it is exactly what Lab 12 needs. If you put
the reads inside the clocked process it still simulates, still looks fine here, and
your CPU cannot get its operands. That failure is very hard to see in Lab 12, so get
it right now.

---

## Slide 5 — Register zero
> $$We_k = \text{Strb} \cdot m_k(\text{Dsel}) \cdot \underbrace{[k \neq 0]}_{\text{this}}$$
>
> ### "Hardwired to zero" is not a convention.
> It is one extra AND term — a missing wire.

*Say:* In MIPS, `$0` always reads zero. Not because software politely agrees not to
write it — because the hardware physically refuses. One condition on the write
enable. Block the write *and* force the read: either alone works, but with both, a
mistake in one place still cannot produce a non-zero `$0`.

---

## Slide 6 — Why spend an address on a constant?
> `move rd, rs` is `ADD rd, rs, $0`
> `clear rd` is `ADD rd, $0, $0`
>
> Your Lab 12 program: `SW r2, 0(r0)` → address = `r0 + 0` = **0**
>
> A permanent zero makes the **instruction set** smaller.

*Say:* You are spending one of only 32 register addresses on something that holds
nothing. It buys you several instructions for free, and it is why the store in your
Lab 12 program needs no special "absolute address" form.

---

## Slide 7 — Read ports are cheap, write ports are not
> **Read port:** one more mux over storage that already exists. Any number of
> readers, no conflict.
>
> **Write port:** two writers might target the same register in the same cycle.
> Needs arbitration, priority, and a decision about what "both wrote" means.
>
> `ADD rd, rs, rt` → **two reads, one write.**

*Say:* The register file's shape is dictated by the instruction format. The ISA and
the register file were designed against each other — that is a real
hardware/software interface point, not a coincidence.

---

## Slide 8 — Read-during-write: your decision
> Read port addresses the register being written, same edge. Old value or new?
>
> **READ-OLD** — what you get naturally
> **READ-NEW** — needs a comparator + mux per port (a bypass)
>
> ### Both are correct designs. You must know which one you built.

*Say:* "I don't know" is not an acceptable answer about your own design. Your
testbench has to check it before *and* after the edge, and your report has to name
it.

---

## Slide 9 — Assignment, evidence, tonight
> **`RegFile`** 32×32. **Port names are fixed** — Lab 12 connects by these names.
>
> Testbench must include: **write to R0 then prove it's still zero**, read-during-write
> checked both sides of the edge, an edge with `Strb='0'`, a read with no clock, and R31.
>
> **E4: about 1024 registers.** First design that *should* have any.
>
> **Discussion:** why is a permanently-zero register worth one of only 32 addresses?

*Say:* Far fewer than 1024 usually means the Fitter inferred block memory instead of
flip-flops. Say which happened and how you can tell.

---

## Production notes
- 9 slides, ~12 minutes. This is a light week; give the time to the build phase and
  to catching read-port placement errors at the bench.
- Slide 4's warning is the one that costs the most if missed — repeat it at check-off.
- Example 3 run live covers slides 5 and 8 together.
