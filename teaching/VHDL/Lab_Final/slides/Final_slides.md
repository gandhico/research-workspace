# Final Lab — Slide Content
### Demonstration and Extension · 6 slides · 5 minutes

The shortest deck of the term. The session is demonstrations and building; talk as
little as possible.

---

## Slide 1 — Title
> **EE 362 — Final Laboratory**
> **Demonstration and Extension**

---

## Slide 2 — Open with this, and mean it
> Three months ago: a **four-row truth table** for a latch.
>
> Every week since, the same loop:
> **specification → truth table → equations → VHDL → simulation → check**
>
> Nothing was ever added to the method.
> You did the same thing thirteen times at increasing scale.
>
> ### At the end of it there is a processor.

*Say:* And it computes two to the tenth. That is the whole course, and it is the
actual thing you are taking away — not VHDL syntax, which you will forget, but the
loop, which you will not.

---

## Slide 3 — Today
> **3:50–4:20** demonstrations — 4 minutes each, two questions
> **4:20–5:25** extension work — one track
> **5:25–5:45** submission
>
> **Full report due end of finals week.**

*Say:* Announce the two questions now, and say they are the same two for everyone in
the section. Students not demonstrating should already be starting their track.

---

## Slide 4 — Pick one track
> **A — Add an instruction.** `ORI`, end to end: decoder row, test, running program.
> *A clean, certain finish.*
>
> **B — Measure it.** Instruction mix, then CPI for two machines you did not build.
> *Amdahl's law on numbers you measured yourself.*
>
> **C — One pipeline stage.** Make arithmetic work; document everything it breaks.
> *Extends the pipeline lecture.*

---

## Slide 5 — The Track C rule
> ### A working pipelined CPU is NOT required.
> ### Breaking it correctly and explaining precisely why is FULL CREDIT.
>
> The graded deliverable is the **hazard analysis.**

*Say this out loud, twice.* If you do not, nobody picks it — and the students who
would get the most out of it are exactly the ones who will not gamble their last
grade on making a pipeline work in seventy minutes.

The control hazard you will find is the reason real MIPS has a branch delay slot.
That connection is worth more than a working pipeline.

---

## Slide 6 — Close
> **Keep the Overleaf project.**
>
> A processor designed from gates up, verified at every stage,
> with the evidence to prove it.
>
> It is the most convincing thing you can put in front of someone
> who asks whether you can actually design hardware.

*Say:* This is not sentiment. The reflection chapter is worth six points and students
who believe the project matters write a noticeably better one.

---

## Production notes
- 6 slides, 5 minutes. Do not extend it. The session is demonstrations and building.
- Slides 2 and 6 are the bookends of the whole semester — deliver them properly,
  they are short.
- Slide 5 must not be skipped or softened.
- If a student is demonstrating on reference components, say nothing about it in
  front of the room. Lab 12's grade already stands.
