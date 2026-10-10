# Lab 5 — Arithmetic Logic Unit

**Runs:** Mon 10/5 · Tue 10/6 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck written as content, not built as `.pptx`.

---

## This is the pivot lab

Labs 1–4 taught VHDL. From here the language is assumed and the difficulty lives in
the specification. Two practical consequences, both in `TA_notes.md`:

- **The deck shrinks** — 12 minutes, not 15. The build phase needs the time.
- **The check-off lengthens** — the questions are now about *why*, not *does it run*.

New evidence sources appear this week: **E4 (resource)** and **E6 (timing)**. The ALU
is the first design big enough for those numbers to mean anything.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab5_spec.pdf` | **students** | Specification, 4 pages |
| `handout/Lab5_prelab.pdf` | **students** | Pre-lab, 3 pages, due 3:45 |
| `Lab5_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | `alu_add` — one complete function unit, the template |
| `examples/exe_2` | students | `alu_mini` — two units + a mux: *what an ALU is* |
| `examples/exe_3` | students | `shift_demo` — **SLL / SRL / SRA on negatives** |
| `assignment/` | **students** | Flat project: `ALU_Pkg.vhd` (given), `ALU.vhd`, testbench |
| `slides/Lab5_slides.md` | you | 10 slides + what to say |
| `solution/` | **TA only** | Reference + 26-check testbench. **Never publish.** |
| `overleaf/lab05.tex` | students | Report chapter |
| `rubric.md`, `TA_notes.md` | you | Grading, friction table, the time-management warning |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 `alu_add` | boundary cases + flags + carry | ✅ `PASS`, 0 errors |
| exe_2 `alu_mini` | flags follow the *selected* result | ✅ `PASS`, 0 errors |
| exe_3 `shift_demo` | SRA preserves sign, SRL does not | ✅ `PASS`, 0 errors |
| `assignment/` as shipped | compiles, runs, **fails on `SUB`** | ✅ compiles clean, 1 failure by design |
| `solution/` | all pass | ✅ `PASS — all 26 checks passed`, 0 errors |
| Overleaf template with `lab05` | builds | ✅ 29 pages, 0 warnings |

---

## A fix worth knowing about

The student testbench template originally **passed** as shipped, because the only
concrete vector exercised `ADD` — which is given. A student could have submitted it
untouched and seen `PASS`.

It now ships with a concrete `SUB` vector that fails until they implement `SUB`,
with a comment explaining why: *a testbench should be red until the design is right,
not green until you look closely.* That restores the Labs 1–4 pattern where the
starter compiles cleanly and fails informatively.

---

## The pedagogical spine

**One idea:** an ALU is a multiplexer over function units — and they built the
multiplexer in Lab 3. Example 2 wires two units and a `Mux2` structurally so the
idea is *visible*; the assignment uses a `case` because sixteen units is pointless
typing. The report must state that **the `case` is still the multiplexer**, with the
RTL Viewer as evidence.

**Three traps, each with an example behind it:**
1. `SRA` written with `unsigned()` — compiles, runs, wrong only for negatives (exe_3).
2. Flags taken from the adder rather than the selected result — silent here, becomes a branch bug in Lab 8 (exe_2, vector 4).
3. Raw bit patterns instead of `ALU_FUNC_*` — a typo becomes a wrong answer instead of a compile error (`ALU_Pkg.vhd`).

**The rule from Lab 4, consolidated:** *test where the implementations disagree.*
Applied here to `SRA` (needs a negative operand) and `SOLS`/`SOLU` (needs the one
operand pair where signed and unsigned differ). Name it explicitly so students see
it as a general habit, not a Lab 4 fact.

**Time management is the hidden difficulty.** Ten of sixteen operations are
one-liners; the marks are all in `SRA`, `SOLS`, `SOLU` and the flags. The spec, the
slides and the TA notes all carry the same warning: *get the easy ten done in five
minutes, then slow down.*

---

## Canvas module

```
Module: Lab 5 — Arithmetic Logic Unit
  ├── Lab5_spec.pdf
  ├── Lab5_prelab.pdf              → due at 3:45
  ├── Lab5_student_files.zip
  ├── Lab 5 slides (PDF)           ← pending deck build
  ├── Reading: COD Ch. 3.1–3.3; H&H Ch. 5.2 (arithmetic circuits)
  └── Reference: Lab 4 ALUsftMUX.vhd  (publish after Lab 4's late deadline)
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
