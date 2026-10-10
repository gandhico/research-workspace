# Final Lab — TA Notes

Last session of the semester. Fill in after Monday, before Tuesday.

---

## Settle this BEFORE the session

**Nobody should arrive without a working machine to demonstrate.**

From your Lab 12 notes, you have the list of students whose CPU never ran. Contact
them in the week between. Two options, both fine:

1. finish it in office hours, or
2. take the reference CPU and demonstrate that.

Say explicitly: **using the reference CPU costs nothing on the Final Lab.** Lab 12's
grade already stands; they are not charged twice. Some students will otherwise turn
up with nothing rather than accept what they read as a penalty, and that is a bad
way for the semester to end.

## Pick the two demonstration questions before the session

Choose two from the bank and use the **same two for everyone in that section**. It
is fair, and it lets you compare answers. Different pairs for Monday and Tuesday is
fine; different pairs within a section is not.

The bank:
1. Point at any cycle in your waveform and tell me what is executing.
2. Which component gave you the most trouble, and how did you find the bug?
3. If I asked you to add one instruction, what would you change and in what order?
4. Where is your critical path, and what would you do to make this run faster?

Questions 1 and 2 are the most discriminating. Question 4 rewards students who did
the Lab 5 and Lab 12 timing work properly.

## Say the Track C rule out loud, twice

> *"For Track C, a working pipelined CPU is not required. Breaking it correctly and
> explaining precisely why is full credit."*

If you do not say this — clearly, before they choose — nobody picks it, and the
students who would get the most from it are exactly the ones who will not gamble
their last grade on making a pipeline work in seventy minutes.

Say it when you introduce the tracks, and again to anyone who hovers over C.

## Timing

| Clock | Phase |
|---|---|
| 3:45–3:50 | Open. The closing line (below). Announce the two questions. |
| 3:50–4:20 | **Demonstrations**, ~4 min each. Run these in parallel with people starting their track if the room allows. |
| 4:20–5:25 | Extension work |
| 5:25–5:40 | Submission, and confirm everyone knows the report deadline |
| 5:40–5:45 | Close |

Demonstrations will overrun if you let them. Four minutes each, timed. Students not
being demonstrated should already be working on their track.

## Track-specific things to watch

**Track A.** The supplied program uses two `ORI`s in a row on purpose — one alone
passes even if the instruction was implemented as "copy the immediate", which is
what happens when someone clones the `LUI` row without thinking. If a student's own
test uses one, ask for the second.

Anyone attempting `SUB` will discover their CPU computes `rt - rs`, not `rs - rt`.
**That discovery is the assignment** — full credit for documenting it. But check
they did not "fix" it by swapping the register-file reads, which silently breaks
`SLL` and `SW`.

**Track B.** The classification order matters: control flow must be tested *first*,
because a branch also has `RF_strb` low and `DM_en` disabled. Expected mix for the
program is **23 ALU / 0 loads / 1 store / 21 control flow = 45**. If control flow
comes out low, this is why.

**Track C.** The straight-line test program must execute correctly before the
hazards are anyone's problem. If it does not, the pipeline register itself is wrong.
Push them to fix that first rather than starting the analysis.

## The thing to say at Close

> *"Three months ago you wrote a four-row truth table for a latch. Every week since,
> the same loop: specification, truth table, equations, VHDL, simulation, check.
> Nothing was ever added to the method — you did the same thing thirteen times at
> increasing scale, and at the end of it there is a processor that computes two to
> the tenth."*
>
> *"Keep the Overleaf project. A processor designed from gates up, verified at every
> stage, with the evidence to prove it, is a genuine portfolio piece — and it is the
> most convincing thing you can put in front of someone who asks whether you can
> actually design hardware."*

The second half is not sentiment. Students who hear it write noticeably better final
chapters, and the reflection section is worth 6 points.

---

## After Monday — fill this in

**Who demonstrated on reference components? (not a mark against them — just track it)**


**Track distribution: A __ B __ C __**


**Did anyone pick C? If not, was the grading rule stated clearly enough?**


**What to say differently on Tuesday:**


---

## After the semester

**What to change for next year:**


**Which labs ran long / short:**


**Which examples landed and which did not:**


**Anything in the reference material that was wrong or unclear:**
