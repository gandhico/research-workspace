# Lab 7 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## The whiteboard moment

Slide 4's arithmetic must be worked **on the whiteboard, with the room**, not shown
as a finished slide. Write:

```
0x0C   0x18200002   BLEZ r1, +2

  NSA    = 0x0C + 4                =  ?
  offset = SignExt(0x0002) << 2    =  ?
  target = NSA + offset            =  ?
```

and let them fill it in. Then say: *this is instruction four of the program your CPU
runs in Lab 12, and 0x18 is the store that ends the loop.* That connection —
"this is real, and you will run it" — is what makes the lab land.

## Before the session

- [ ] Load Example 3 ready to run. Its two failing asserts are the best five minutes
      of the session.
- [ ] Print pre-labs. This one is arithmetic; expect hex errors and do not penalise
      them — the derivation is the point.
- [ ] Have the CPU block diagram up. Point at the NIAG box: *by next week this whole
      box is yours.*

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~3:55 | They did not copy their Lab 4 `ImmedXtnd` | Step 1 of the assignment. The shipped copy is the empty skeleton. |
| ~4:20 | Sign extension re-implemented inside `NIAG_Rel` | Works. Point out the CPU has ONE shared extender feeding the ALU and this adder. |
| ~4:35 | Target is not a multiple of 4 | Forgot the `<< 2`. Off by a factor. |
| ~4:40 | Target is 4 too low, consistently | Used PC as the base. Off by a constant. |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | Everything passes on the first run | Check for a negative offset. If every vector is positive, sign extension is untested. |
| ~5:15 | Finished early | Predict then measure a third error: extending the offset unsigned rather than signed. |

## The thing to say twice

**Hand-compute before you simulate.**

This is the first lab where the student can genuinely predict the hardware's answer
in advance, and it is the habit Lab 12 depends on entirely. A student who only ever
reads targets off a waveform has no way to tell a wrong target from a right one.

Say it at the spec walk, and make check-off question 1 a whiteboard derivation
rather than a waveform reading.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:55 | Open + the whiteboard arithmetic |
| 3:55–4:15 | Examples 1, 2, 3 — **Example 3 live** |
| 4:15–4:25 | Spec walk + "hand-compute first" |
| 4:25–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off — Q1 is a whiteboard derivation |
| 5:40–5:45 | Close + preview Lab 8 |

Example 1 can be compressed; Example 2 and 3 should not be.

---

## After Monday — fill this in

**Did the whiteboard derivation work? How many got it unaided?**


**How many had all-positive offsets at check-off?**


**What confused people (their exact words):**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Carry into Lab 8:**
Lab 8 completes the NIAG: absolute jumps, register jumps, the return address, the
five-way PC multiplexer, and the six branch-condition equations over the ALU flags
from Lab 5. It needs Lab 7's three components working AND Lab 3's `Mux3`. Note
anyone missing either.
