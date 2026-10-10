# EE 362 — Computer Organization Lab (VHDL) · Fall 2026
## Program Design

**TA:** Gandhi Torres · **Instructor:** Dr. Wei Tang
**Lab:** Mon **and** Tue sections, **3:45–5:45 PM (120 min)**, ECIII 237
**Tools:** Quartus Prime Lite + Questa Intel FPGA Starter · Device `5CSEMA4U23C6` (Cyclone V)
**Hardware: none this semester.** Everything is simulation and synthesis-report based. The device is still selected, because synthesis, fitting, and timing results all depend on it — we simply never program a board.

---

## 1. The thesis

Every lab is the same intellectual move, repeated at growing scale:

> **Specification → Truth table → Boolean equations → VHDL → Simulation → back to the truth table.**

Lab 1 does it with a 4-row table and one equation. Labs 10–11 do it with a control table of 8 instructions and 16 output signals. Nothing else changes. If a student internalizes that loop, they can design digital hardware; if they only learn Quartus menus, they have learned nothing transferable.

Say the loop out loud in every session. It is the course.

---

## 2. Calendar

Labs are released the Wednesday before and run the following Mon/Tue.

| Lab | Mon | Tue | Topic | Builds |
|---|---|---|---|---|
| 0 | 8/31 ✅ | 9/1 ✅ | VHDL fundamentals | — |
| 1 | **9/7 ⚠** | 9/8 | Design flow + transparent latch | `TransLatch` |
| 2 | 9/14 | 9/15 | Master–slave FF, N-bit register | `MSFlipFlop`, `RegN` |
| 3 | 9/21 | 9/22 | Multiplexers | `Mux2`, `Mux3` + 4 wrappers |
| 4 | 9/28 | 9/29 | Extender, tri-state, shift mux | `ImmedXtnd`, `TriBuffer`, `ALUsftMUX` |
| 5 | 10/5 | 10/6 | ALU | `ALU` + function units |
| 6 | 10/12 | 10/13 | Register file | `RegFile` |
| 7 | 10/19 | 10/20 | NIAG I — PC, sequential, relative | `NIAG_Reg/NSA/Rel` |
| 8 | 10/26 | 10/27 | NIAG II — absolute, return, select | `NIAG_Abslt/Rtn/MUX`, `NIAG` |
| 9 | 11/2 | 11/3 | ROM and RAM | `ROM`, `RAM` |
| 10 | 11/9 | 11/10 | Decoder I — ADD, SLL, ADDI, LUI | `Decoder` (part) |
| 11 | 11/16 | 11/17 | Decoder II — LW, SW, BLEZ, J | `Decoder` (complete) |
| 12 | 11/23 | 11/24 | CPU integration | `CPU` |
| Final | 11/30 | 12/1 | Demonstration + extension | — |

**⚠ Mon 9/7 is Labor Day.** The Monday section loses Lab 1. Recommended: Monday students attend Tue 9/8; fallback is the recorded walkthrough plus check-off at the start of 9/14.

---

## 3. Session structure — 3:45 to 5:45

| Clock | Min | Phase |
|---|---|---|
| 3:45 | 10 | **Open** — recap, today's one idea, truth table on the board |
| 3:55 | 25 | **Guided example** — you drive, they type along |
| 4:20 | 10 | **Spec walk** — read the assignment aloud; equations on the board |
| 4:30 | 55 | **Build** — they work, you circulate; hard checkpoint call at 4:55 |
| 5:25 | 15 | **Check-off** — demo + two questions each |
| 5:40 | 5 | **Close** — tonight's Overleaf task, next week's preview |

The 4:55 checkpoint is not optional. Call the room: *"If your design does not compile yet, raise your hand now."* Students who are stuck at 4:55 and silent will not finish, and you will discover it at 5:35 when you can no longer help.

Word-for-word scripts: `03_Session_Scripts.md`.

---

## 4. The Spec Ladder — how truth tables and equations are written

One notation, used by you and by them, all semester. This is the part that makes the reports gradeable and the designs debuggable.

### 4.1 Three table types

Students must label which type they are using. Choosing the wrong type is the most common specification error.

| Type | Use when | Form |
|---|---|---|
| **E — Exhaustive** | ≤ 4 binary inputs | All 2ⁿ rows, numbered |
| **C — Compressed** | Wide data paths (a 32-bit mux has 2⁶⁵ rows) | Control inputs enumerated; data inputs symbolic (`Y = A`) |
| **T — Transition** | Storage elements | Condition → `Q⁺` (next state), including the hold row |

### 4.2 Table format (fixed)

```
| # | inputs …        ‖ outputs …   | note        |
|---|-----------------‖-------------|-------------|
| 0 | 0   0   0       ‖ 0    0      | clear       |
```

Rules:
- **Number every row.** Discussion says "row 5", never "the case where En is high and D is low."
- Inputs left, outputs right, separated by a visible double bar.
- `–` = don't care · `Z` = high impedance · `↑` = rising edge · `Q` in an output column = hold.
- Type C rows name a source (`Y = B`), not a value.
- One table per entity. If you need two, you have two entities.

### 4.3 Boolean equations (fixed)

Notation, and its VHDL twin — put this table in Lab 1's slides and never repeat it:

| Algebra | Meaning | VHDL |
|---|---|---|
| `A·B` or `AB` | AND | `A and B` |
| `A + B` | OR | `A or B` |
| `A ⊕ B` | XOR | `A xor B` |
| `Ā` | NOT | `not A` |
| `Q⁺` | next value of Q | left side of an assignment inside a clocked/latched process |
| `Σm(3,5,6,7)` | sum of minterms | the rows where the output is 1 |

**Required derivation, three lines, every time:**

```
(1) canonical   Y = Σm(3,5,6,7) = ĀBC + AB̄C + ABC̄ + ABC
(2) simplified  Y = AB + AC + BC          [absorption / adjacency]
(3) VHDL        Y <= (A and B) or (A and C) or (B and C);
```

Line (2) must name the law or the K-map grouping used. "It simplified" is not an answer.

**Two rules students must be able to state by Lab 2:**

1. *An equation whose output appears on its own right-hand side is memory.* `Q⁺ = En·D + Ēn·Q` is a latch precisely because of that trailing `Q`.
2. *A specification that leaves an input combination undefined becomes a latch in hardware.* This is why every `case` needs `when others` and every process needs default assignments.

### 4.4 Sequential elements

For anything clocked, the spec is a **characteristic equation** plus a **transition table**, never a plain truth table. Example, the Lab 1 latch:

```
Q⁺ = C̄lr · ( En·D + Ēn·Q )
```

---

## 5. Reading Quartus results

Seven evidence sources. Each lab names which subset is required — never all seven, that is how reports become padding. Full student-facing explanations in `04_Quartus_Results_Guide.md`.

| # | Source | Answers |
|---|---|---|
| E1 | Flow Summary + Messages | Did it build, and what did it warn about? |
| E2 | RTL Viewer | Did I describe the circuit I meant? |
| E3 | Technology Map Viewer | What did it become in the fabric? |
| E4 | Fitter → Resource Utilization by Entity | What did it cost? |
| E5 | Fitter → Pin-Out / Input–Output | How many I/O, and why so many? |
| E6 | Timing Analyzer → Fmax and slack | How fast can it run? |
| E7 | Questa waveform + transcript | Does it behave, and do the asserts pass? |

Evidence sets by lab:

| Labs | Required |
|---|---|
| 1–4 | E1, E2, E7 |
| 5–6 | E1, E2, E4, E6, E7 |
| 7–9 | E1, E2, E4, E7 |
| 10–11 | E1, E2, E4, E7 |
| 12 + Final | E1–E7, all |

---

## 6. Reports: one Overleaf project, four checkpoints

### 6.1 The project

One Overleaf project per student for the whole semester. One chapter per lab. Seven fixed sections per chapter:

1. **Objective** — 2–3 sentences
2. **Specification** — the labelled truth table (E/C/T) and the Boolean equations, derived in three lines
3. **Design** — entity interface and why this architecture style
4. **Implementation** — `\lstinputlisting` of the real `.vhd` (never pasted code)
5. **Verification** — test-vector table + coverage argument
6. **Results** — this lab's evidence set (§5), each figure with one sentence of interpretation
7. **Discussion** — one bug, how it was found, what it cost. **Required.**

Section 6's rule matters most: *a figure with no sentence interpreting it scores zero.* A screenshot is not a result.

### 6.2 The four checkpoints

Students submit the **compiled PDF of the whole report so far** four times. Not each lab — four times.

| CP | Covers | Due (Sunday 23:59) | You return comments by |
|---|---|---|---|
| **CP1** | Labs 0–3 | Sun 9/27 | Wed 9/30 |
| **CP2** | Labs 4–6 | Sun 10/18 | Wed 10/21 |
| **CP3** | Labs 7–9 | Sun 11/8 | Wed 11/11 |
| **CP4** | Labs 10–12 | Sun 11/29 | Wed 12/2 |
| **Final** | All + Final Lab + revisions | End of finals week | — |

**The mechanism that makes comments matter:** from CP2 onward, the submission opens with a half-page **"Response to feedback"** listing each CP comment and what changed. No response section, no CP grade. Without this, comments are decoration.

**How to comment (budget ~8 min per student per checkpoint):** Canvas SpeedGrader annotation on the PDF. Three inline notes maximum, plus one summary comment in this shape:

> *Strongest:* … · *Fix before CP\<n+1\>:* … · *One habit to change:* …

Three notes, not thirty. A report covered in red is not read.

### 6.3 How to ask for it — the words

At the end of every lab (Close phase), say the same thing:

> *"Tonight, before you forget it: paste your truth table and your three-line derivation into Chapter N. Add the waveform with one sentence saying what it proves. Ten minutes. The chapter is due at the checkpoint, but the memory is due tonight."*

At the start of each checkpoint week:

> *"Checkpoint N is Sunday. You are submitting the whole report so far, not just the new chapters — I read the new ones and I check that the old comments got fixed. If you have not written the Discussion sections, write them now; that is where most of the lost points are."*

### 6.4 Where lecture homework fits

Dr. Tang's HW 0–3 stay his, submitted his way. Do **not** create a second submission stream. The connection appears in one line inside each chapter's Discussion:

> *"This lab implements the datapath element used in HW 2, problem 3."*

That single sentence is the whole integration. It takes students 30 seconds and makes the lecture–lab link explicit, which is the actual goal.

---

## 7. Grading

| Stream | Weight | Basis |
|---|---|---|
| Weekly check-off (13 labs) | 40% | Per lab: compiles ✓, testbench passes ✓, can explain ✓ |
| Four report checkpoints | 40% | 10% each |
| Final lab + complete report | 20% | Demonstration + final submission |

Weekly check-off is deliberately coarse — 3 boxes, ticked at the bench. It takes you 60 seconds per student and cannot be argued with. Depth of assessment lives in the checkpoints, where you have time to actually read.

Late: one week, −20%. Attendance: >3 missed labs fails the lab. Reference components are published after each lab's late deadline, so no student is ever blocked from Lab 12 by an earlier miss.

---

## 8. Canvas-ready: definition of done

A lab may be published to Canvas when all seven exist. Publish first, then take it to Dr. Tang.

- [ ] Slides (PDF, ≤ 12 slides)
- [ ] Assignment specification (PDF) — including the truth table and required equations
- [ ] Starter `.zip` — a **flat** `assignment/` folder: `.qpf` + `.qsf` preconfigured, stubbed `.vhd`, and the testbench **already named as the `.qsf` expects**. Every rename or subfolder a student has to navigate on the bench costs you support time; Lab 1 proved it.
- [ ] Pre-lab sheet (3 questions)
- [ ] Reference solution (TA-only, not published)
- [ ] `labNN.tex` chapter stub with figure placeholders
- [ ] Rubric line + the two check-off questions

Course-level resources published once, in week 1: workflow card, `04_Quartus_Results_Guide.md`, recorded walkthrough, Overleaf template, LaTeX card.

---

## 9. Production order

Do not build in date order. Build in batches — within a batch, slides and examples share structure.

| Batch | Contents | Why first |
|---|---|---|
| **A — now** | Labs 1–4 · Overleaf template · workflow card · Quartus results guide · recorded walkthrough | The template and recording are reused 13 times. Lab 1 runs Tue 9/8. |
| **B — by 9/28** | Labs 5–9 | Legacy solutions exist; this is skeleton extraction and spec writing, not authoring |
| **C — by 10/26** | Labs 10–12 + Final | The only genuinely new authoring: cutting the 35 KB legacy decoder into two student-sized weeks |

**Immediate:** Lab 1 must be Canvas-ready before Tue 9/8.

---

*Companion files:* `01_Lab_Program.md` (the 12 labs in full) · `02_Resources.md` · `03_Session_Scripts.md` (speeches) · `04_Quartus_Results_Guide.md` (student handout).
