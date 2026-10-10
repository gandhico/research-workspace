# Lab 8 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## This is a rehearsal for Lab 12

Six components, no new logic. Say that at Open, then say the second half:
*if wiring six blocks is uncomfortable, wiring twelve will be much worse — so treat
the integration seriously, not as bookkeeping.*

Three habits, all of which transfer directly:

1. **Named association in every port map.** No exceptions.
2. **One internal signal per wire between components.**
3. **Read the wiring back against the block diagram once, before simulating.**

## Before the session

- [ ] Load Example 3 ready to run — the same `Sel` code with `Taken` high and low is
      much clearer demonstrated than described.
- [ ] Have the CPU block diagram up. At the assignment slide, point at the NIAG box:
      *after today, that whole box is yours.*
- [ ] Print pre-labs.

## The error to hunt for: GTZ

`GTZ` is *not-negative AND not-zero*, not just *not-negative*. Not-negative alone is
`GEZ`.

This is the single most common mistake of the lab and it passes every test where the
result is non-zero — which is most casual test vectors. **Ask every student for
`GTZ` with the Zero flag high at check-off.** It must not be taken: zero is not
greater than zero.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~3:55 | Lab 7 files not copied in | Step 1. The shipped copies are empty skeletons. |
| ~4:20 | `Abslt` slice wrong | It is `NSA(31 downto 28)` — the *top* four bits. |
| ~4:30 | `GTZ` written as not-negative only | See above. Ask for the zero case. |
| ~4:40 | Everything gated by `Taken` | Only the relative path is conditional. Point at Example 3. |
| ~4:45 | "Cannot read output PC" | You cannot read an `out` port. Internal signal, then drive the port from it. |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | Six components wired positionally | Fix it now. Lab 12 has twelve. |
| ~5:15 | Finished early | The exception-vector stretch (see rubric) — previews the interrupts lecture. |

## Two things worth saying twice

1. **Only the relative path is conditional.** Jumps are unconditional by
   construction. A student who gates `ABS` and `REG` with `Taken` builds a CPU that
   cannot jump whenever the last ALU result was positive. That is a genuinely
   horrible bug to find in Lab 12 because it depends on the data.

2. **The complement pairs.** `GTZ`/`LEZ`, `GEZ`/`LTZ`, `EQ`/`NEQ`. Point out that
   the hardware is smaller than the instruction list, and that this is why the
   control table is the document you read rather than the manual. It is the same
   idea they will meet at full scale in Labs 10–11.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:55 | Open + "this is a rehearsal for Lab 12" |
| 3:55–4:15 | Examples 1, 2, 3 — **Example 3 live** |
| 4:15–4:25 | Spec walk + the integration rules |
| 4:25–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off — ask for `GTZ` with Zero high |
| 5:40–5:45 | Close + preview Lab 9 |

Example 2 can be compressed — it is exhaustive and self-explanatory. Examples 1 and
3 should not be.

---

## After Monday — fill this in

**How many wrote GTZ as not-negative only?**


**How many gated the jump paths with Taken?**


**How did the six-component integration go? Where did people get stuck?**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Who struggled with the integration?** (these are the Lab 12 risk cases — note
names, and consider how to pair people differently that week)


**Carry into Lab 9:**
Lab 9 is memory: ROM, RAM, byte addressing, and the actual program the CPU runs.
It reuses Lab 4's `TriBuffer` for the shared data bus. Note anyone whose
`TriBuffer` never worked.
