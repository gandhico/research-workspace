# Lab 5 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## This is the pivot lab

Labs 1–4 taught VHDL. From Lab 5 the language is assumed and the difficulty is in
the specification. Two consequences for you:

- **The deck shrinks.** Aim for 12 minutes, not 15. The build phase needs the time.
- **The check-off lengthens.** The questions are now about *why*, not *does it run*.

Say this to the room at Open. Students who think Lab 5 is "more of the same but
bigger" will manage their time badly.

## Before the session

- [ ] Load Example 3 (`shift_demo`) ready to run. The `SRA`/`SRL` divergence on a
      negative number is the single most valuable thing you show all session.
- [ ] Print pre-labs. This one is worth collecting properly — students who arrive
      with Q1 filled in finish the lab.
- [ ] Have `ALU_Pkg.vhd` open to show. The named-constant argument lands better
      when they can see the file.

## The time-management warning — say it at the spec walk

> *"Ten of these sixteen operations are one line each. Do those first, in five
> minutes, and get the thing compiling. Then slow down and spend the rest of the
> session on four things: SRA, SOLS, SOLU, and the flags. That is where all the
> marks are and all the difficulty is."*

Without this, a predictable number of students write all sixteen carefully in
alphabetical order, run out of time at 5:20, and never reach the parts that
matter. It costs you one sentence.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~4:05 | `Ain < Bin` on raw vectors | Compiles, compares bit patterns lexicographically, not numbers. Cast to `signed`/`unsigned` first. |
| ~4:15 | Shifting by `Shft` directly | You cannot shift by a vector. `to_integer(unsigned(Shft))`, once, into a signal. |
| ~4:25 | Sixteen inline `to_integer` calls | Works. Unreadable. Push the single `amount` signal. |
| ~4:40 | Flags assigned inside every case branch | Can be correct, but it is sixteen chances to be wrong. Point at Example 2 and move them to the after-the-case version. |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | All SRA tests pass on the first try | Check their vectors. If every SRA test uses a positive value, they have tested nothing — an SRA written as SRL passes all of them. |
| ~5:10 | SOLS and SOLU return the same answer | One of them is wrong. `0xFFFFFFFF` vs `0x00000001` must give 1 and 0. |
| ~5:15 | `"01001"` typed instead of `ALU_FUNC_SOLS` | The operation silently does nothing. This is the argument for the package, made concrete. |

## Two things worth saying twice

1. **The flags feed Lab 8.** `Zero` and `Neg` are the entire input to every
   conditional branch three weeks from now. A student who takes the adder's flags
   instead of the selected result's will not notice this week and will spend Lab 8
   hunting a control-flow bug. Catch it at the bench.

2. **Test where the implementations disagree.** Same rule as Lab 4, now applied to
   `SRA` (needs a negative operand) and `SOLS`/`SOLU` (needs the one pair where
   signed and unsigned differ). Students recognise the rule from last week — name
   it explicitly so it consolidates as a general habit rather than a Lab 4 fact.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:55 | Open: "an ALU is a mux", and the pivot warning |
| 3:55–4:15 | Examples 1, 2, 3 — **Example 3 live and unhurried** |
| 4:15–4:30 | Spec walk + the five-minute time-management warning |
| 4:30–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off |
| 5:40–5:45 | Close |

Example 1 can be compressed — the file is heavily commented and they can read it.
Example 3 must not be.

---

## After Monday — fill this in

**Did the five-minute warning work? How many still ran out of time?**


**How many implemented SRA with `unsigned()` on the first attempt?**


**What confused people (their exact words):**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Anyone whose flags come from a single operation rather than the result?**
(These are the Lab 8 casualties — note names and follow up.)


**Carry into Lab 6:**
Lab 6 (register file) is much lighter than this one and reuses Lab 2's `RegN`,
Lab 0's decoder idea and Lab 3's mux. Tell them that at Close — after the ALU,
Lab 6 reads as intimidating ("32 registers!") and is not.
