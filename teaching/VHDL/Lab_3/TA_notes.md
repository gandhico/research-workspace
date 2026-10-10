# Lab 3 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## Before the session

- [ ] Have the CPU block diagram ready to project **full screen** — slide 10 and
      the report figure both depend on it. Export from
      `C:\Teaching\VHDL\Documentation\CPU Diagram.pdf`.
- [ ] Load Example 3 in Questa ahead of time. Running it live is far more
      effective than describing it, and it is the centre of the lab.
- [ ] Print pre-labs.
- [ ] **Checkpoint 1 is this Sunday (27 Sep), covering Labs 0–3.** Say it at Open
      and again at Close. This is the first checkpoint, so expect questions about
      what "the whole report so far" means: the compiled PDF including every
      chapter, not just Lab 3.

## The two-minute silence on slide 5

Slide 5 asks them to factor $\overline{S_1}$ out themselves. **Actually wait.** The
instinct is to fill the silence after twenty seconds, and if you do, you hand them
the answer and the lesson evaporates. Two minutes of a quiet room feels much longer
than it is. Then reveal slide 6.

This is the highest-value ninety seconds in the lab — it is the first time algebra
visibly produces circuit structure, and it is the intellectual bridge to Labs 10–11
where the same move happens on a control table.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~4:05 | `case` without `when others` is rejected | Not a compiler bug. `std_logic` has nine values. The language is protecting them — say it that way. |
| ~4:10 | "Which style should I use?" | Any of the three. The graded part is *why*, not *which*. Refuse to pick for them. |
| ~4:35 | Width mismatch pointing at the instantiation | Forgotten `generic map`. The error is reported where the size is used, not where it was omitted. |
| ~4:45 | Latch warning present, student moves on | Check the register count on `MUX3x32` at the bench — it must be 0. That is the backstop. |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | Everything passes on the first run | Likely identical data on A, B and C. Ask: *would a mux that always returns A pass your tests?* |
| ~5:10 | Finished early | Send them to the annotated CPU diagram — it takes real thought and carries the lasting value. |

## Two things worth saying out loud

1. **Row 3 is a decision.** Students treat `Sel = "11"` as impossible because the
   CPU never generates it. That is exactly the reasoning that produces latches in
   real designs. The rule: *if the specification does not say what happens, the
   hardware decides for you, and it decides to remember.*

2. **This week's designs are short — the report is where the work is.** Lab 3 is
   the lightest coding week of the semester and the last one before the ALU. Push
   the freed time into the annotated block diagram and the coverage argument, both
   of which pay off from Lab 7 onward.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:55 | Open: the 2⁹⁸ number, then the four-row table on the board |
| 3:55–4:20 | Examples 1, 2, 3 — **Example 3 last and unhurried** |
| 4:20–4:30 | Spec walk + the factoring silence |
| 4:30–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off |
| 5:40–5:45 | Close + Checkpoint 1 reminder |

Example 2 is the one to compress if behind. Example 3 must not be cut.

---

## After Monday — fill this in

**What took longer than planned:**


**Did the two-minute factoring silence work? Did anyone get it unaided?**


**What confused people (their exact words):**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Checkpoint 1 intake — who has not started their Overleaf project?**


**Carry into Lab 4:**
Lab 4 needs nothing from Lab 3 as a component, but it reuses the same
specification discipline (Type C tables) and introduces `'Z'`, which is the first
value that is not Boolean. Note anyone still shaky on `when others`.
