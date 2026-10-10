# Lab 4 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## Before the session

- [ ] Put the **resolution table on the whiteboard** and leave it there all
      session. Students will copy it, and they will refer back to it in Labs 9
      and 12.
- [ ] Load Example 1 in Questa ahead of time — the bus going red is the moment
      that lands, and it is better seen than described.
- [ ] Print pre-labs.
- [ ] **Checkpoint 1 feedback should be back by now** (returned Wed 30 Sep).
      Bring it, hand it back at 3:45, and say out loud that from Checkpoint 2
      onward every submission opens with a half-page *Response to feedback*
      listing each comment and what changed. No response section, no CP grade.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~4:00 | `'Z'` compared against `'0'` | `'Z'` is not `'0'`. It is the absence of a value. Point at the resolution table. |
| ~4:15 | Someone finds `std_logic_arith` online | Stop it immediately. `numeric_std` only. Mixing them produces errors that read as though the compiler has lost its mind, and Lab 5 is entirely `numeric_std`. |
| ~4:30 | Sign bit index wrong | It is `Immed16(15)`, not `(0)` and not `(31)`. |
| ~4:40 | One enormous concurrent assignment for extend-and-shift | Push the two-step version with an internal signal. The RTL Viewer then shows two clean stages, which is also the report figure. |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | "Contention should give all X but I get 101X" | It should. Resolution is **per bit**. `0xA` and `0xB` agree on three bits of every nibble. This caught the reference testbench during development. |
| ~5:10 | Extension tests all pass immediately | Check their test values. If they only used small positive immediates, both extensions agree and the vectors prove nothing. |

## The one thing to say twice

**Test where the implementations disagree, not where they agree.**

An immediate of `0x0001` sign-extends and zero-extends to the same answer. A
student can write six such vectors, watch them all pass, and have verified
nothing at all. `0x8000` is the value that separates the two.

This is the most transferable idea in the lab and it generalises far beyond
extension — it is the same reasoning behind the hold vector in Lab 1 and the edge
vector in Lab 2. Say it at the spec walk and again at check-off.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:55 | Open + resolution table on the board (+ CP1 feedback handback) |
| 3:55–4:20 | Examples 1, 2, 3 — **Example 1 live** |
| 4:20–4:30 | Spec walk |
| 4:30–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off |
| 5:40–5:45 | Close + preview Lab 5 |

Example 3 (conversion chain) is the one to compress — it is reference material
and the file is heavily commented. But do **not** skip it entirely: Lab 5 opens
with `to_integer(unsigned(...))` and assumes they have seen it.

---

## After Monday — fill this in

**What took longer than planned:**


**Did anyone hit the per-bit contention surprise? How did they react?**


**What confused people (their exact words):**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Anyone still using `std_logic_arith`?** (must be zero before Lab 5)


**Carry into Lab 5:**
Lab 5 is the first big lab and the first with real arithmetic. It assumes:
`numeric_std` fluency (Example 3), and `ALUsftMUX` working, because the ALU's
`Shft` port is fed by it. Note anyone whose Lab 4 is incomplete — the ALU is
2× the size of anything so far and they cannot afford to start behind.
