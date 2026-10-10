# Lab 3 — Multiplexers

**Runs:** Mon 9/21 · Tue 9/22 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck is written as content, not built as `.pptx`.
**⚠ Checkpoint 1 (Labs 0–3) is due Sunday 27 September** — announce it at Open and Close.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab3_spec.pdf` | **students** | Assignment specification, 4 pages |
| `handout/Lab3_prelab.pdf` | **students** | Pre-lab, 3 questions, due 3:45 |
| `Lab3_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | One 2:1 mux, three coding styles, all asserted equal |
| `examples/exe_2` | students | `mux4` — 4-to-1, 8 bits, generic |
| `examples/exe_3` | students | **The latch trap** — the centre of the lab |
| `assignment/` | **students** | Flat Quartus project |
| `slides/Lab3_slides.md` | you | 10 slides + what to say |
| `solution/` | **TA only** | Reference + 14-check testbench. **Never publish.** |
| `overleaf/lab03.tex` | students | Report chapter (also in the template) |
| `rubric.md`, `TA_notes.md` | you | Grading, friction table, the two-minute silence |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 three coding styles | all three agree on every vector | ✅ `PASS`, 0 errors |
| exe_2 `mux4` | every selector row correct | ✅ `PASS`, 0 errors |
| exe_3 latch trap | **exactly one** deliberate failure | ✅ 1 error, the intended one |
| `assignment/` as shipped | compiles, runs, reports failures | ✅ compiles clean, fails as designed |
| `solution/` | all pass | ✅ `PASS — all 14 checks passed`, 0 errors |
| Overleaf template with `lab03` | builds | ✅ 19 pages |

---

## The pedagogical spine of this lab

**1. The 2⁹⁸ opening.** A 32-bit 3:1 mux has 98 inputs. Make them compute the
exhaustive row count before showing the four-row table. Type C stops being a
notation convention and becomes obviously necessary.

**2. The two-minute factoring silence (slide 5).** They factor $\overline{S_1}$
out themselves. The bracket turns out to be a 2:1 mux and the whole expression a
mux tree — algebra visibly producing circuit structure. **Actually wait the full
two minutes.** Fill the silence and the lesson evaporates. This is the bridge to
Labs 10–11, where the same move happens on a control table.

**3. Example 3, the latch trap.** *"No assignment happens, so the output keeps its
previous value"* is Lab 1's latch sentence, word for word. In Lab 1 it was the
feature; here it is the bug. Run it live rather than describing it.

**4. Example → assignment linkage.** Example 1's three styles → the assignment
asks which style you chose and *why*. Example 2's generic → the assignment's
`generic map` wrappers. Example 3's latch → the assignment's mandatory row 3 and
the no-latch testbench check. Nothing in the examples is decorative.

---

## Two deliberate design choices

**`case` is recommended over `if/elsif` for `Mux3`, and the spec says why.** VHDL
forces a `case` to cover every selector value, so a `case` without `when others`
is a compile error rather than a latch. The language protects them; an `if/elsif`
chain does not. Students who use `if/elsif` lose 3 points and get a verbal note —
it works, but they gave up the protection.

**Top level is `MUX3x32`, so its register count must be zero.** That is the
backstop for students who compile with the latch warning and move on. Check it at
the bench.

---

## Canvas module

```
Module: Lab 3 — Multiplexers
  ├── Lab3_spec.pdf
  ├── Lab3_prelab.pdf              → due at 3:45
  ├── Lab3_student_files.zip
  ├── Lab 3 slides (PDF)           ← pending deck build
  ├── Reading: H&H Ch. 2.8 and 5.2 (multiplexers)
  └── ⚠ Checkpoint 1 due Sun 27 Sep — Labs 0–3, whole report PDF
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
