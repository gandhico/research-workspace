# Lab 9 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## Open with the program, before any VHDL

Put the seven instructions on the screen and leave them there for a minute.

```
0x00  LUI  r1, 11        0x0C  BLEZ r1, +2
0x04  LUI  r2, 1         0x10  SLL  r2, r2, 1
0x08  ADDI r1, r1, -1    0x14  J    0x08
                         0x18  SW   r2, 0(r0)
```

Then say it:

> *"Every component you have built since Lab 1 exists to make these seven
> instructions run. Ten passes, doubling each time. Your CPU computes two to the
> tenth, and stores 1024 at address zero. Today you build the memory it lives in."*

This is the single most motivating minute available in the whole course. Students
have spent eight weeks on components without seeing the destination. Show it.

## Before the session

- [ ] Load Example 3 ready to run. The bytes `20 21 FF FF` decoding two different
      ways is the demonstration that makes endianness stick.
- [ ] Print pre-labs. Tell them to bring the instruction-format sheet — Q1 is a
      disassembly.
- [ ] **Checkpoint 3 (Labs 7–9) is due Sunday 8 November.** Announce at Open and Close.

## Three errors that pass this lab and break Lab 12

All three simulate plausibly in isolation. Catch them at the bench.

| Error | Why it passes here | What it does in Lab 12 |
|---|---|---|
| **`rw` polarity backwards** | Their own testbench uses their own convention consistently | Every load returns nothing |
| **Drives `'0'` instead of `'Z'`** | Passes with a single driver | Whole data bus goes `'X'` on every store |
| **Writes on the rising edge** | Storage works fine on its own | Stores commit before the address settles — looks like random corruption |

Ask for the `en='0'` case at every bench. That one check catches the second error,
which is the worst of the three.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~4:05 | `rw` used as write-enable | `'1'` is READ. It is fixed by the CPU library. Say it twice. |
| ~4:20 | Out-of-range index aborts the simulation | `base+3` near 511. The error points at the array, not the address — students read it as "my memory is broken". |
| ~4:35 | Bus at `'0'` when idle | Ask what the TriBuffer would be doing at that moment. |
| ~4:45 | Byte order reversed | The ROM reads back as nonsense. Point at Example 3. |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | Disassembly copied from the comment block | Ask them to decode a word you pick. |
| ~5:15 | Finished early | The cache stretch — see rubric. Only place the cache lectures touch hardware. |

## The thing to say twice

**`rw = '1'` is READ.**

It is genuinely counter-intuitive; most people expect `'1'` to mean write. It is
fixed by the original CPU library and cannot be changed without breaking Lab 12.
Say it at the spec walk and again at check-off.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:57 | Open: **the program**, then the one idea |
| 3:57–4:15 | Examples 1, 2, 3 — **Example 3 live** |
| 4:15–4:25 | Spec walk + the `rw` warning |
| 4:25–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off — ask for the `en='0'` case |
| 5:40–5:45 | Close + Checkpoint 3 reminder + preview Lab 10 |

Example 1 can be compressed. Example 3 should not be.

---

## After Monday — fill this in

**Did the program-first opening land? What did people say?**


**How many got the `rw` polarity backwards?**


**How many drove `'0'` instead of `'Z'`?**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Names to re-check before Lab 12** (rw polarity, bus release, write edge):


**Carry into Lab 10:**
Labs 10 and 11 are the control unit — one truth table with sixteen output columns,
split over two weeks. Scope is **eight instructions only**, the ones this program
uses. Tell them that at Close: the fear in those two labs is scope, and the scope is
small.
