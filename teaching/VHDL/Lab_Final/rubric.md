# Final Lab — Grading Rubric
### 100 points · TA use

## Structure

| | Weight | |
|---|---|---|
| Demonstration | 30 | the CPU runs, and they can explain it |
| Extension — the work | 30 | the build itself |
| Extension — the write-up | 20 | the analysis |
| Final report completeness | 20 | summary, tables, reflection, appendix |

**For Track C, the 30 points of "the work" are the hazard analysis, not a
functioning pipeline.** Say this when you offer the track and again when you grade.

---

## Demonstration (30)

~4 minutes each. Two questions from the fixed bank — **the same two for everyone in
the section**, chosen before the session starts so it is fair.

1. Point at any cycle in your waveform and tell me what is executing.
2. Which component gave you the most trouble, and how did you find the bug?
3. If I asked you to add one instruction, what would you change and in what order?
4. Where is your critical path, and what would you do to make this run faster?

| | Points |
|---|---|
| CPU runs the program correctly, and they can navigate the waveform | 30 |
| Runs, but can only answer one question fully | 22 |
| Runs on reference components, explanation solid | 24 |
| Does not run; explains their own design and where it fails | 15 |
| Cannot explain their own design | 0 |

**Using the reference CPU is not a demonstration failure.** Lab 12's grade already
stands; do not charge them twice. A student who takes the reference and explains it
well beats one whose own CPU runs but who cannot say why.

---

## Extension — the work (30)

### Track A — new instruction

| | Points |
|---|---|
| Row correct, decoder test passes, **and the CPU runs the program** | 30 |
| Decoder row correct, not verified in the CPU | 20 |
| Row present but wrong extension (sign vs zero) | 18 |
| Cloned the LUI row without adapting it | 12 |

**Watch for:** an `ORI` implemented as "copy the immediate". The supplied program
uses two `ORI`s in a row precisely to catch it — the second must OR *into* the
first result. If a student's test only uses one, ask them to add the second.

**If they attempted SUB:** full credit for discovering that their CPU computes
`rt - rs` rather than `rs - rt`, and documenting why. That discovery is the
assignment. A student who "fixed" it by silently swapping the register-file reads
has broken `SLL` and `SW` — check those still work.

### Track B — performance

| | Points |
|---|---|
| Mix measured, identity holds, both hypotheticals computed | 30 |
| Mix measured, only CPI-as-built reported | 20 |
| Classification has a hole (classes don't sum to cycles) | 15 |
| Counters present but not exercised on the program | 10 |

**The order-of-tests trap:** control flow must be tested **first**. A branch also
has `RF_strb` low and `DM_en` disabled, so testing `RF_strb` first miscounts every
branch. If their numbers are 23/0/1/21 the classification is right; if control flow
comes out low, this is why.

### Track C — pipeline and hazards

| | Points |
|---|---|
| All four hazard categories named, present/absent decided, concrete instruction pairs, fixes and costs | 30 |
| Three of four categories, with concrete pairs | 24 |
| Hazards listed generically, no instruction pairs from this program | 15 |
| A "working" pipeline on a program with no branches and no adjacent dependencies, presented as working | 10 |

**The last row matters.** That is not a working pipeline, it is an untested one, and
the student should be told so plainly. It is also the most common way this track
goes wrong.

**Full credit does not require the loop to run.** Check the straight-line program
executes and the analysis is real.

---

## Extension — the write-up (20)

| | |
|---|---|
| Analysis answers the *required* question for the track, in their own words | 12 |
| Evidence included (test output, mix table, or the failing case) | 5 |
| Honest statement of what does not work | 3 |

The required questions: **A** — why that extension choice, and what the alternative
would have done. **B** — which hypothetical hurts more, argued from the measured
mix. **C** — why the control hazard is the reason MIPS has a branch delay slot.

---

## Final report completeness (20)

| | |
|---|---|
| Executive summary, one page, written for someone who has not read the rest | 5 |
| Resource and timing table across all labs, with the two required sentences | 5 |
| Reflection: two or three **named decisions**, each with trade-off and a position | 6 |
| Response to Checkpoint 4 feedback | 2 |
| Complete code appendix, with reference components identified | 2 |

**The reflection is where this is won or lost.** "I would add more instructions" is
not an answer. They must name a decision that was made *for* them — the
eight-instruction subset, big-endian, `Asel = rt`, two-phase timing, `LUI` as a
plain load, the read-old register file — say what it bought and cost, and take a
position.

---

## What good looks like

Above 90: the executive summary reads as though written for a stranger; the resource
table produces an actual observation (usually that the register file dominates area
and that the CPU's Fmax is close to the ALU's, because the ALU *is* the critical
path); the extension analysis answers the required question with the student's own
measurements; and the reflection names decisions rather than wishes.

## Before anyone leaves

Remind them: **keep the Overleaf project.** A processor designed from gates up,
verified at every stage, with the evidence to prove it, is a genuine portfolio piece
— and it is the most convincing thing they can show someone who asks whether they
can actually design hardware. Students who hear that write noticeably better final
chapters.
