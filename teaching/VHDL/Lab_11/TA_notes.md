# Lab 11 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## Before anything else: check for Lab 10 latches

Anyone who carried an inferred latch out of Lab 10 must fix it **before** adding
four more rows. Merging into a latched design makes it strictly worse, and Lab 12
is next week.

Your Lab 10 TA notes should list the names. Catch them in the first ten minutes.

## The two signals to hunt: SW

`RF_strb = HOLD` and `RF_oe = DRIVE`.

Both fail **silently**:

- `RF_strb` left at STROBE → every store also corrupts a register, and because the
  store itself still works, the program fails somewhere else entirely.
- `RF_oe` left at HiZ → the store writes `'Z'`, which the RAM happily stores.

Ask for both at every bench. They are the difference between storing and corrupting.

## The signal to hunt: BLEZ

`IR_Xlsft = TWO`. It is the only instruction in this CPU that scales its immediate,
and it passes every decoder test that does not specifically look at that field —
then puts every Lab 12 branch a quarter of the way to its target.

This is Lab 7's "off by a factor", arriving through the decoder instead of the
adder. Worth naming that connection out loud.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~3:55 | Lab 10 decoder not pasted in, or still latched | Step 1. Fix latches first. |
| ~4:15 | `SW` with `RF_strb` still STROBE | Ask what a store writes. |
| ~4:20 | `SW` with `RF_oe` still HiZ | Ask who drives the bus during a store. |
| ~4:30 | `BLEZ` without the ×2 | Connect it to Lab 7's "off by a factor". |
| ~4:40 | `"Bit string literal found where non-array type was expected"` | The single-element table aggregate. The shipped one uses `0 =>` for this reason; once they add a second row they can drop it. |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | Expectation table written by reading their own decoder | Then it agrees with the bug. Ask where the table came from. |
| ~5:15 | Finished early | `SYSCALL` decoding raising an exception signal — connects to the Lab 8 stretch. |

## The idea worth slowing down for

Run Example 2 live. Two implementations of `IR_Xsel` that **disagree on exactly ADD,
SLL and J** — the three instructions that never read the extender — and agree on all
five that do. The transcript prints it row by row.

Then say it:

> *"Both of these are correct. The minimised one is cheaper. This is what
> minimisation means in a real control unit — the same operation as a K-map in Lab 3,
> except the don't cares now come from the architecture: which instructions read
> which signals."*

And the corollary, which is the more useful half:

> *"A testbench that pinned IR_Xsel down for ADD would be testing an accident of your
> implementation, not a requirement. Over-specifying a test is its own kind of bug."*

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:52 | Open + check who is carrying Lab 10 latches |
| 3:52–4:15 | Examples 1, 2, 3 — **Example 2 live and unhurried** |
| 4:15–4:25 | Spec walk: the four rows and the four traps |
| 4:25–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off — ask for `SW`'s two signals |
| 5:40–5:45 | Close — **print your control table** |

Examples 1 and 3 can be compressed; Example 2 should not be.

## Say this at Close, and mean it

> *"Print your completed control table and bring it next week. Step three of the
> Lab 12 debugging method is: do the control signals match the table for this
> opcode? Without the table you cannot do step three, and you will lose the
> session."*

---

## After Monday — fill this in

**How many carried a latch in from Lab 10?**


**How many had SW's RF_strb or RF_oe wrong?**


**How many missed BLEZ's ×2?**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Who does NOT have a working decoder?** (they need the reference version handed
to them on day one of Lab 12 — integration must never be gated on an earlier miss)


**Who has not printed the control table?**


**Carry into Lab 12:**
Lab 12 is wiring and debugging, not new VHDL. Twelve components. Everyone needs:
a working decoder (or the reference), the printed control table, and the timing
contract. Expect it to be emotionally hard and technically shallow.
