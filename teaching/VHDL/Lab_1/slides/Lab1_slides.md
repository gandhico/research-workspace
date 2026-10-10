# Lab 1 — Slide Content
### Design Flow and the Transparent Latch · 12 slides · 15 minutes

Slide text is what goes **on** the slide. *Say* is what you say over it and does not
go on the slide. Keep the slides this sparse — the talking is the lesson, the slide
is the anchor.

---

## Slide 1 — Title

> **EE 362 — Laboratory 1**
> **Design Flow and the Transparent Latch**
> Fall 2026 · Gandhi Torres

*Say:* Nothing. Let it sit while people settle.

---

## Slide 2 — Where this is going

> *(full-slide CPU block diagram, from `Documentation/CPU Diagram.pdf`)*
>
> **By 23 November you will have built all of this.**

*Say:* This diagram stays on the side screen every week for the rest of the
semester. Today you build the smallest box on it. In thirteen weeks you run a
program on the whole thing.

---

## Slide 3 — The loop

> **specification → truth table → Boolean equations → VHDL → simulation → back to the table**

*Say:* This is the entire method of the course. It does not change. Today it is a
four-row table and one equation. In week twelve it is an eight-row table with
sixteen outputs, and that is the only difference. If you learn nothing else here,
learn this loop.

---

## Slide 4 — Today's one idea

> ### An equation whose output appears on its own right-hand side is memory.

*Say:* Read it now, because you are going to prove it in about forty minutes.

---

## Slide 5 — The flow

> | | Step | Answers |
> |---|---|---|
> | 1 | Analysis & Elaboration | does it parse? |
> | 2 | **RTL Viewer** | **did I describe what I meant?** |
> | 3 | Full compilation | does it build? |
> | 4 | Flow Summary & Messages | what is it worried about? |
> | 5 | RTL Simulation (Questa) | does it behave? |
> | 6 | Waveform + transcript | can I prove it? |

*Say:* Step 2 is the one nobody does and everybody should. It takes ten seconds
and it catches the majority of design mistakes before you have wasted a compile on
them. Make it a reflex this week.

---

## Slide 6 — Lab 0 had no memory

> Lab 0, majority-of-three:
> $$Y = AB + AC + BC$$
>
> Today:
> $$Q^{+} = \overline{Clr}\cdot(En\cdot D + \overline{En}\cdot Q)$$
>
> **Find the difference.**

*Say:* Take ten seconds. What is on the right of the second equation that is not on
the right of the first? *(wait for it)* Q. Its own output. That is the whole thing.
A circuit that depends on its own output has to remember what that output was.

---

## Slide 7 — Table T

> | # | Clr | En | D ‖ Q⁺ | note |
> |---|---|---|---|---|
> | 0 | 1 | – | – ‖ **0** | async clear, dominates |
> | 1 | 0 | 0 | – ‖ **Q** | hold ← *the memory row* |
> | 2 | 0 | 1 | 0 ‖ **0** | transparent |
> | 3 | 0 | 1 | 1 ‖ **1** | transparent |
>
> `–` don't care · `Q⁺` next value · **Q** hold

*Say:* Three conventions you will use every week: dash is don't care, Q-plus is the
next value, and a Q in the output column means hold. Row 1 is the only row that
distinguishes this from a wire. Also, number your rows — in your report you will
write "row 1", not a paragraph describing row 1.

**Write this table on the whiteboard as well.** Projected tables get copied;
written tables get watched.

---

## Slide 8 — The derivation

> **(1) canonical**  $Q^{+} = \overline{Clr}\,En\,D + \overline{Clr}\,\overline{En}\,Q$
>
> **(2) factored**  $Q^{+} = \overline{Clr}(En\,D + \overline{En}\,Q)$  **[distributive law]**
>
> **(3) VHDL**  *next slide*
>
> Three lines. Every lab. Line (2) **names its law.**

*Say:* This three-line shape is required in every report chapter this semester.
Line 2 must name the law or the K-map grouping. "It simplified" is not an answer,
because it is not a derivation, it is an assertion.

---

## Slide 9 — The VHDL, and the missing else

> ```vhdl
> process (Clr, En, D)
> begin
>     if Clr = '1' then
>         Q <= '0';          -- row 0
>     elsif En = '1' then
>         Q <= D;            -- rows 2, 3
>     end if;
>     -- row 1 is the missing else
> end process;
> ```

*Say:* There is no else. When Clr is low and En is low, nothing is assigned, so Q
keeps its old value — and that is row 1. **In VHDL, memory is what you get when you
leave a case undefined.** Today we want it. Every other week we will not, and that
is the single most common bug in this course. You are seeing it deliberately on day
one so that you recognise it in week ten.

---

## Slide 10 — The trap: sensitivity lists

> ```vhdl
> process (En)        -- D is missing
> begin
>     if En = '1' then Q <= D; end if;
> end process;
> ```
>
> **Simulation:** Q changes only when `En` rises — a flip-flop, not a latch
> **Synthesis:** Quartus builds that flip-flop — **1 register, no warning**
>
> Add a `Clr` branch (your starter) → **Warning 10492**, a correct latch in
> hardware, broken simulation.
>
> ### One missing name. Two different failures.

*Say:* Here the tool is silent and builds the wrong storage element — the correct
latch actually prints *more* warnings than this one. In your starter, the clear
branch changes the outcome: Quartus warns and builds the right latch, so what you
simulate is not what you build. Either way the testbench catches it, and the Flow
Summary catches this one before you simulate: you expect 0 registers, it says 1.
(Measured on Quartus 25.1 — the old "synthesis always fixes it" story is not true
here.)

---

## Slide 11 — Your assignment

> 1. **`TransLatch`** — 1 bit, with asynchronous clear. Complete the skeleton.
> 2. **`TransLatch8`** — 8 bits. `Clr` and `En` stay **one bit**, shared.
> 3. **Testbench** — ≥ 6 checked vectors, and it **must** include:
>    - the **hold vector** (En = 0, change D, prove Q does not follow)
>    - clear while transparent · clear while holding
>    - one 8-bit pattern that is not all-0s or all-1s
>
> ⚠ The sensitivity lists in the skeletons are **incomplete on purpose.**

*Say:* Without the hold vector you have not tested that your design is memory at
all — a plain piece of wire passes every other test you could write. That vector is
the assignment. Everything else is bookkeeping.

---

## Slide 12 — Evidence, and tonight

> **Collect: E1** Flow Summary · **E2** RTL Viewer · **E7** waveform + transcript
>
> Every figure needs **one sentence saying what it proves.**
> A figure with no sentence earns zero.
>
> **Tonight, 10 minutes:** paste the table and the derivation into `lab01.tex`,
> drop in the waveform, write the one sentence.
>
> **Checkpoint 1 — Sunday 27 September** — Labs 0 through 3.

*Say:* Ten minutes tonight while you still remember what you did. The chapter is
due at the checkpoint; the memory is due tonight.

---

## Production notes

- Total 12 slides. If it runs past 15 minutes, cut slides 5 and 6 — the flow is in
  the workflow card and the Lab 0 contrast can be made verbally.
- Slide 2 needs the CPU block diagram exported from
  `C:\Teaching\VHDL\Documentation\CPU Diagram.pdf`.
- Slides 9 and 10 should use the same code font and colours as the Overleaf
  listings, so students see one visual language across slides, handout and report.
- Keep the deck in the same template as `Lab_0/0_Intro.pptx` for continuity.
