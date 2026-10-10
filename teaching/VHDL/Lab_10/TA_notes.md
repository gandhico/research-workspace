# Lab 10 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## Say the scope first, before anything else

> *"This CPU has eight instructions. Not forty — eight, the ones its program
> actually uses. You do four today and four next week. And the instruction set
> manual is not your specification: the control table is, and I am giving it to
> you filled in. You implement it. You do not have to derive it."*

The fear in this lab is scope, and the scope is small. Students who go looking for
the full MIPS instruction list will drown, and they will do it in the first ten
minutes if you let them.

## Then slow down for the one idea

> *"In Lab 1 you took a four-row truth table and wrote one Boolean equation from
> it. Today you take an eight-row table and write sixteen. That is the entire
> difference. Nothing new has been introduced since week one — the control unit of
> a processor is a truth table. That is not an analogy."*

Pause after it. This is the sentence the whole course has been building toward, and
it is worth five seconds of silence.

## The bug to hunt: the missing default

Expect several. It is the headline error of the lab and it has two tells:

- the Messages panel says **inferred latch**
- the register count is **not zero**

Check both at every bench. A student who compiles with the warning and moves on
carries sixteen latches into Lab 12, where the symptom is: *every instruction works
alone, the program still fails, and it fails differently depending on order.*

Example 3 demonstrates it directly — `bad_decode` shows `'U'` first (never assigned)
and then `'1'` (inherited from the previous ADDI), while `good_decode` gives `'0'`
both times. Run it live.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~3:55 | Student opens the full MIPS manual | Slide 2 again. Eight instructions. Four today. |
| ~4:20 | No default assigned | The headline bug. Messages panel + register count. |
| ~4:30 | `SPECIAL` decoded on opcode alone | Passes `ADD`, fails `SLL`. Ask them to feed both. |
| ~4:40 | `RF_Wsel` rd/rt swapped | Writes the wrong register, silently. Ask which field each format uses. |
| ~4:45 | `ADDI` and `LUI` given the same `IR_Xsel` | They differ on exactly that one signal. |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | Testbench applies one instruction at a time and passes | It cannot detect a latch. Send them to write the order test. |
| ~5:15 | Finished early | The microcoded-ROM restructure — see rubric. |

## A question worth asking at check-off

*"Why does `ADD` leave `IR_Xsel` alone?"*

The answer — `ADD` never reads the extender output, so it is a **don't care** —
sets up next week's discussion, where the same don't-care lets two different
correct equations disagree on rows nobody looks at.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:52 | **Scope first**, then the one idea, with a pause |
| 3:52–4:15 | Examples 1, 2, 3 — **Example 3 live** |
| 4:15–4:25 | Spec walk: read the four table rows aloud |
| 4:25–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off — longest of the term, the questions are about *why* |
| 5:40–5:45 | Close + preview Lab 11 |

Example 1 can be compressed — the file is heavily commented. Examples 2 and 3
should not be.

---

## After Monday — fill this in

**How many inferred latches at check-off?**


**Did anyone go looking for the full instruction set? How did they react to slide 2?**


**How many decoded SPECIAL on the opcode alone?**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Names carrying a latch into Lab 11** (these must be fixed before the merge):


**Carry into Lab 11:**
Lab 11 adds `LW`, `SW`, `BLEZ`, `J` and merges everything into the complete
decoder. It also contains the don't-care discussion — two different correct
equations for `IR_Xlsft` that disagree only on rows nobody reads. Anyone still
carrying a latch must fix it first; the merge will make it worse.
