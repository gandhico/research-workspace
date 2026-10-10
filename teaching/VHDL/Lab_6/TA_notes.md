# Lab 6 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## Say this at Open

> *"Last week was the biggest lab of the semester. This one looks bigger and is
> not. A register file is three things you already built: a decoder from Lab 0,
> a register from Lab 2, a multiplexer from Lab 3. Write the three equations and
> the rest is assembly."*

After the ALU, "32 registers, 32 bits" reads as intimidating. It is a light week
and students who believe that will use the spare time on the report.

## The one error that must not leave the room

**Reads placed inside the clocked process.**

It simulates plausibly. It passes a careless testbench. And it breaks Lab 12 in a
way that is genuinely hard to diagnose, because the symptom is "the CPU computes
garbage" six weeks later.

Check it *visually* at every bench during the build phase — you are looking for
`Aout <=` outside any `process (clk)`. This costs you ten seconds per student and
saves someone a ruined Lab 12.

## Before the session

- [ ] Load Example 3 ready to run. It covers register 0 and read-during-write
      together, which are the two things worth demonstrating live.
- [ ] Print pre-labs.
- [ ] **Checkpoint 2 (Labs 4–6) is due Sunday 18 October.** Announce it at Open
      and Close. This is the first checkpoint requiring the half-page *Response
      to feedback* section — say explicitly: no response section, no CP grade.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~4:00 | `regs(Asel)` | Cannot index with a vector. `to_integer(unsigned(Asel))`. |
| ~4:10 | Array declared `1 to 32` or `0 to 32` | 32 registers is `0 to 31`. |
| ~4:20 | **Reads inside the clocked process** | See above. Catch it here, not in Lab 12. |
| ~4:35 | R0 protected on one side only | Ask which side and why. Both is the answer. |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | Everything passes, no R0 test written | Their testbench cannot detect the lab's main requirement. Send them back. |
| ~5:10 | Finished early (common) | Third read port + E4 comparison, then the scaling argument. See rubric. |

## Two things worth saying twice

1. **Port names are fixed.** `Asel`, `Bsel`, `Dsel`, `Din`, `Strb`, `clk`,
   `Aout`, `Bout`. They come from the original CPU library and Lab 12
   instantiates this entity by these exact names. A student who renames them for
   tidiness will have to rename them back.

2. **Read-during-write is a decision, not a detail.** Both behaviours are correct
   designs. The failure mode is not choosing wrong — it is not knowing which one
   you built. That is the check-off question.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:55 | Open: "three things you already own" + CP2 announcement |
| 3:55–4:15 | Examples 1, 2, 3 — **Example 3 live** |
| 4:15–4:25 | Spec walk |
| 4:25–5:25 | Build (checkpoint at 4:55) — longer than usual, it is a light week |
| 5:25–5:40 | Check-off |
| 5:40–5:45 | Close + preview Lab 7 |

Example 2 can be compressed to "look, two more lines" — the point is the cost
comparison, not the code.

---

## After Monday — fill this in

**How many put the reads inside the clocked process?**


**How many left register 0 writable?**


**What confused people (their exact words):**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Names to re-check before Lab 12** (reads clocked, or R0 writable):


**Carry into Lab 7:**
Lab 7 starts the address side of the machine — the program counter, PC+4, and
branch target arithmetic. It reuses Lab 2's `RegN` (as the PC) and Lab 4's
`ImmedXtnd` (for the branch offset). Note anyone whose `RegN` or `ImmedXtnd`
still does not work; they will need the reference versions on day one.
