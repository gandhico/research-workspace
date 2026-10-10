# Today's session — Lab 0 recap + Lab 1: Design Flow and the Transparent Latch
### EE 362 · Monday section · 9/14 · a speech to yourself before you open the door

You are folding four things into one block today, in this order: quick Lab 0
examples 1–3, the Lab 0 assignment, the Overleaf template, then Lab 1 —
skipping majority3 since example 1 already covers it, and landing hard on
the Transparent Latch, examples 2 and 3, sensitivity list comparison. That
is a lot for one afternoon. The discipline that makes it fit is the same
discipline you already wrote into the Lab 1 materials: **quick means
quick.** Examples 1–3 are recap, not re-teaching. Spend your slow, careful
minutes where the semester's first real idea lives — the missing else and
the sensitivity list — not on circuits they have already built once.

Say this to yourself before anyone walks in: *the goal of the first hour is
not coverage, it's momentum. The goal of the second half is one sentence
they can defend: an equation whose output appears on its own right-hand
side is memory.* Everything else today serves that sentence.

---

## Part 1 — Lab 0, examples 1, 2, 3 (quick)

You are not re-deriving these. You already did that once. Today you are
reminding them of the shape, so that when Lab 1 introduces the one thing
that's different — memory — they see it as one new idea against a familiar
background, not as everything-is-new again.

**Example 1 — majority3.** $Y = AB + AC + BC$. Put it up, don't derive it.
This is the one you'll point back to in twenty minutes: "Lab 0 had no Q on
the right-hand side. Watch what Lab 1 has." Say the entity/architecture
shape out loud once — port list, then `Y <= (A and B) or (A and C) or (B
and C);` — and move on. This is also why you're skipping majority3 as a
*Lab 1* example: they've already seen it twice, once as Lab 0's exercise
and once as Lab 1's own example 1. A third pass buys you nothing.

**Example 2 — 2-to-1 mux.** Remind them there are two ways to write the
truth table — the exhaustive 4-row version and the 2-row "name a source"
version — and that the second form is the one they'll use for the rest of
the course. You don't need to justify why today; just plant the flag,
Lab 3 collects on it.

**Example 3 — 2-to-4 decoder with enable.** This is the one with a
deliberate bug in the version you showed in class. Do **not** hand them
the fix. Ask the room: "somewhere in this process, one branch doesn't
behave the way the spec says. Find it before I tell you." Let it sit for
thirty seconds of actual silence. The exercise 3 lesson is *finding* the
bug, not watching you find it — if you fix it yourself you've taught them
to wait for you.

Keep this whole section under ten minutes. If you feel yourself
re-deriving the majority-of-three K-map, you've already lost the pacing
for the day — stop, and move to Part 2.

---

## Part 2 — the Lab 0 assignment

Say the method once, because it is the only thing that doesn't change all
semester:

> **specification → truth table → Boolean equations → VHDL → simulation →
> back to the table.**

Four circuits: majority3, 2-to-1 mux, 2-to-4 decoder with enable, full
adder. Tell them plainly what "done" looks like, because this is the
rubric shape for every lab from here on, not just this one:

- every truth table with **numbered rows** — "row 5," never a paragraph
  describing row 5;
- the three-line derivation, and **line 2 has to name the law or the
  K-map grouping**. "It simplified" is not a derivation, it's an
  assertion, and it will be graded as one;
- entity and architecture in VHDL;
- a **self-checking** testbench — `assert` statements, not eyeballing a
  waveform;
- the waveform and the transcript line showing the checks passed.

One thing to flag explicitly, because it's easy to miss reading the
handout alone: exercises 1 and 4 want **two architectures of the same
entity** — behavioral and structural — with **one testbench exercising
both** and asserting they agree on every vector. Say it as a sentence, not
a bullet, so it doesn't get lost: "majority3 and the full adder each need
a second architecture, and your testbench has to prove both versions give
the same answer."

Tell them which two of these four circuits matter beyond this lab, because
it's a good hook for attention: two of the four end up inside their
processor, and a third is the mechanism behind the register file. Don't
say which — let that be a reason to keep their files instead of deleting
the project folder in December.

---

## Part 3 — the Overleaf template

Frame this before you screen-share it: *one report, the whole semester,
one chapter per lab.* Not fourteen separate documents. Open `main.tex` and
show them literally what changes week to week — nothing except uncommenting
one `\input{labs/labNN}` line as each lab is finished. That's the whole
edit to this file, all semester.

Then open a chapter stub — `lab00.tex` or `lab01.tex` — and walk the seven
sections top to bottom once: Objective, Specification, Design,
Implementation, Verification, Results, Discussion. Say plainly: **same
seven sections every week, don't add, remove, or reorder them.** That
consistency is what lets you grade twenty reports in the time it takes to
grade five.

Three habits to demonstrate live, because these are worth more than any
other five minutes of Overleaf instruction you'll give this semester:

1. Code goes in with `\vhdlfile{...}`, pointing at a real `.vhd` file
   uploaded into `code/labNN/`. **Never pasted.** Show them the difference
   once so they can't claim not to have known.
2. Every figure — RTL Viewer screenshot, waveform — needs one sentence
   saying what it *proves*, not what it shows. A figure with no
   interpreting sentence earns zero. Point at the `\figplaceholder` →
   `\resultfig` pattern in the stub so they see exactly where that
   sentence goes.
3. Discussion is required, every week, and "everything worked first try"
   is not an answer — it scores zero, because the section exists to prove
   they debugged something, and something always breaks.

If you have a moment, mention the Overleaf template can be shared as a
*template* link so each of them gets their own copy with one click — worth
setting up once so you're not fielding "how do I get the project" tickets
all semester.

---

## Part 4 — Lab 1: the Transparent Latch

This is where you slow down. Everything before this was recap; this is the
first new idea of the semester, and it's worth protecting the time for it
even if Parts 1–3 ran long.

**Open with the contrast, not the definition.** Put Lab 0's equation next
to today's:

$$Y = AB + AC + BC \qquad\text{vs.}\qquad Q^{+} = \overline{Clr}\cdot(En\cdot D + \overline{En}\cdot Q)$$

Ask them to find the difference themselves — give it real silence — and
then say it: *Q. Its own output, on the right-hand side. A circuit that
depends on its own output has to remember what that output was. That's the
whole idea. Everything else today is detail on top of that one sentence.*

**Table T, on the whiteboard, by hand** — not projected. Projected tables
get copied without being read; a table you write while talking gets
watched.

| # | Clr | En | D | Q⁺ | note |
|---|---|---|---|---|---|
| 0 | 1 | – | – | **0** | async clear, dominates |
| 1 | 0 | 0 | – | **Q** | hold ← the memory row |
| 2 | 0 | 1 | 0 | **0** | transparent |
| 3 | 0 | 1 | 1 | **1** | transparent |

Say the three conventions out loud as you write them, because they'll use
all three every week for the rest of the semester: dash is don't care,
Q-plus is the next value, Q in the output column means hold.

**The derivation, three lines, and name the law on line two:**

$$Q^{+} = \overline{Clr}\,En\,D + \overline{Clr}\,\overline{En}\,Q
\;\longrightarrow\;
Q^{+} = \overline{Clr}\left(En\,D + \overline{En}\,Q\right)\ \text{[distributive law]}$$

**The VHDL, and the missing else** — this is the sentence of the day:

```vhdl
process (Clr, En, D)
begin
    if Clr = '1' then
        Q <= '0';          -- row 0
    elsif En = '1' then
        Q <= D;            -- rows 2, 3
    end if;
    -- row 1 is the missing else
end process;
```

There's no else. When `Clr` is low and `En` is low, nothing gets assigned,
so `Q` keeps its old value — and that's row 1. Say it plainly: *in VHDL,
memory is what you get when you leave a case undefined.* Today they want
it. Most other weeks they won't, and an accidentally-missing branch is the
single most common bug in this course. They're seeing it on purpose in
week two so they recognize it as a bug in week ten.

**Example 2 — `trans_latch`.** The 1-bit latch without the clear input,
plus the testbench shape they'll reuse the rest of the semester. Nothing
tricky here — this is the "it works" baseline you compare against next.

**Example 3 — the sensitivity comparison. Slow down here; this is the
real lesson of the day.** Same latch, one file correct, one file broken —
and the only difference between `trans_latch` and `trans_latch_bad` is a
single missing name in the sensitivity list:

```vhdl
process (En)        -- BUG: D is missing from this list
begin
    if En = '1' then Q <= D; end if;
end process;
```

Run them side by side against the same stimulus and let the waveform make
the point instead of you: at t = 10 ns, `D` changes while `En` is already
high. `Q_good` follows immediately. `Q_bad` does not move — its process
never woke up, because `En` is the only signal that can wake it. Say the
two-part result slowly, because it's the part that surprises them:

- **In simulation**, `Q_bad` only changes when `En` rises. It behaves like
  a flip-flop clocked by `En`, not a latch.
- **In synthesis**, Quartus recognizes that exact shape as a flip-flop
  template and builds one — one register, zero latches, **no warning at
  all**. Simulation and hardware agree with each other and disagree with
  the spec. That's the dangerous case: nothing in the tool tells you
  anything is wrong.

Then say the twist, because it's the part that makes this worth a whole
example instead of one slide: add a `Clr` branch in front — which is
exactly what their assignment starter already has — and the *same* missing
name produces a *different* failure. Quartus now warns (10492) and builds
a correct latch in hardware. So the starter they're about to open
simulates wrong and synthesizes right, while this standalone example
simulates wrong and synthesizes wrong. One missing name, two different
failures depending on what else is in the process. That's not a detail —
that's the reason "it compiled with no warnings" can never be their
definition of done.

**Land the assignment on top of this, don't present it separately.**
`TransLatch` (1 bit, async clear), `TransLatch8` (8 bits, `Clr` and `En`
stay one bit each, shared — control signals are narrow, data paths are
wide, a pattern that holds for the rest of the course), and a testbench
needing at least six checked vectors that **must** include the hold vector
— `En = '0'`, change `D`, prove `Q` does not follow. Say why that vector
matters more than the other five combined: *without it, you have not
tested that your design is memory at all. A plain wire passes every other
test you could write.* Tell them straight that both skeleton sensitivity
lists are incomplete on purpose — the files compile and run as given, and
simulate wrong, exactly like the example they just watched. Fixing that is
part of the assignment, not a bug to report to you.

**Don't give them the fix when they hit it — give them the diagnostic.**
When someone's body looks right but half the checks fail, the rule is:
*which signal is missing is named by which checks fail.* Clear-related
checks failing means `Clr` is missing from the list; the transparency
check failing means `D` is missing. That's a real debugging method, worth
sixty seconds at the board, and it's more valuable to them long-term than
you just telling them to add `Clr, En, D`. Two things to have ready in
your head when you walk the room: it fails at the *first* check, not the
hold vector, because the process hasn't run since initialization — they'll
say "it's all U again" and think they haven't written anything; and the
hold check will still *pass* on a broken list, because a stuck value looks
like holding. That's worth saying out loud once: **a test can pass for the
wrong reason.**

---

## Before you call it

If you're behind schedule by the time you reach Lab 1, cut Example 2's
live typing and just run the prepared file — Example 3, the sensitivity
comparison, is the one that must not be cut. That's the idea the rest of
the semester depends on.

Close with the two questions you'll actually ask at check-off, so today
plants the answer instead of Tuesday springing it on them cold:

1. *Point at the waveform — why doesn't Q change here, when D clearly
   changed?* You want `En = '0'`, tied back to row 1 of the table, stated
   as "the value is held" — not "because that's what a latch does."
2. *If I deleted `Clr` from your sensitivity list, would the simulation
   change? Would the hardware?* You want: simulation yes, hardware no —
   named as a sim/synthesis mismatch, not just "something breaks."

And the sentence to leave them with, because it's the one they should be
able to defend a week from now without their notes:

> **An equation whose output appears on its own right-hand side is
> memory.**

That's the whole session. Go.
