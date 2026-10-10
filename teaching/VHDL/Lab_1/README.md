# Lab 1 — Design Flow and the Transparent Latch

**Runs:** Mon 9/7 ⚠ *Labor Day* · Tue 9/8 · 3:45–5:45 PM, ECIII 237
**Status:** complete and verified, ready to publish — except the slide deck (see below).

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab1_spec.pdf` | **students** | Assignment specification, 4 pages |
| `handout/Lab1_prelab.pdf` | **students** | Pre-lab, 3 questions, due 3:45 |
| `handout/Lab1_examples_solution.pdf` | **students, after the session** | The three guided examples fully worked, with measured Quartus/Questa evidence — 9 pages |
| `handout/Lab1_solution.pdf` | **TA; students after the due date** | Assignment solution — 7 pages |
| `Lab1_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/` | **students** | The three guided examples |
| `assignment/` | **students** | Flat Quartus project: `.qpf`, `.qsf`, stubs, testbench |
| `slides/Lab1_slides.md` | you | 12 slides of content, with what to say over each |
| `solution/` | **TA only** | Reference implementation + 20-check testbench. **Never publish.** |
| `overleaf/lab01.tex` | **students** | Report chapter stub (also inside the template) |
| `rubric.md` | you | Points, deductions, the two check-off questions |
| `TA_notes.md` | you | Pre-session checklist, friction table, fill in after Monday |
| `handout/*.tex` | you | LaTeX sources; rebuild with `pdflatex <file>.tex` |

Course-level, one folder up: `C:\Teaching\VHDL\Overleaf_template\` — the semester
report project (`main.pdf` is a built preview).

---

## Everything has been simulation-verified

Run against Questa FSE from the Quartus 25.1std install on this machine.

| What | Expected | Actual |
|---|---|---|
| `examples/exe_1` majority3 | all 8 rows pass | ✅ `PASS — all 8 rows correct`, 0 errors |
| `examples/exe_2` trans_latch | passes | ✅ `PASS — all checks passed`, 0 errors |
| `examples/exe_3` sensitivity compare | **exactly one** deliberate failure | ✅ 1 error, the intended one; good latch passes |
| `assignment/` as shipped to students | compiles, runs, reports `'U'` | ✅ compiles clean, 1 check fails as designed |
| `solution/` | all checks pass | ✅ `PASS — all 20 checks passed`, 0 errors |
| `Overleaf_template/main.tex` | builds | ✅ 8 pages, 0 LaTeX warnings |

**Why the student starter is designed to fail:** it compiles and runs on the first
try and tells them exactly what is missing. A starter that will not compile teaches
nothing except that the TA shipped something broken.

---

## Two deliberate design choices

**1. The sensitivity lists in the skeletons are incomplete on purpose.**
They compile. They simulate wrong. This is the Example 3 lesson, delivered as an
assignment rather than a demonstration. The failure signature is documented in
`TA_notes.md` — it is measured, not guessed, and it fails at the *first* check,
not at the hold vector. Read that table before you walk the room.

**2. The assignment folder is flat, and the testbench is already named
`tb_TransLatch.vhd`.** No subfolders to navigate, no file to rename before the
`.qsf` works. Every rename is a support ticket at the bench on the first lab of the
semester.

---

## Before Tuesday 9/8 — three things

1. **Announce the Labor Day arrangement.** The Monday section has no meeting on 9/7.
   Recommended: they attend Tuesday 9/8 if there are seats; fallback is the recorded
   walkthrough plus check-off at the start of 9/14.
2. **Push the install guide now**, not on the day. The NMSU-specific step is the one
   students fail: connect to the NMSU VPN, then give the license location
   `1801@chaos`. Put that in the announcement text itself, not only in the linked PDF.
3. **Open `assignment/Lab1.qpf` once on a lab bench PC, cold.** Confirm Questa
   launches on this semester's image before twenty people are watching.

---

## Still open

| Item | Note |
|---|---|
| **Slide deck** | `slides/Lab1_slides.md` has all 12 slides written — text, equations, code, and what to say over each. It is not built as a `.pptx`, because your Lab 0 deck has a house style I would rather match than replace. Say the word and I will build it. |
| **`Reading Your Results` handout** | The Lab 1 spec references it. It exists as `_planning/design/04_Quartus_Results_Guide.md` and needs converting to a student-facing PDF before you publish Lab 1. This is a course-level resource, published once. |
| **Recorded flow walkthrough** | 12–15 min. Needed for the Monday makeup, and it removes the most-repeated live explanation of the term. |
| **Overleaf template link** | Publish the template as an Overleaf *template* so each student clicks once and gets their own copy. |

---

## Canvas module for Lab 1

```
Module: Lab 1 — Design Flow and the Transparent Latch
  ├── Lab1_spec.pdf
  ├── Lab1_prelab.pdf              → due at 3:45, start of session
  ├── Lab1_student_files.zip
  ├── Lab 1 slides (PDF)           ← pending deck build
  ├── Reading: H&H Ch. 3.1–3.2 (latches and flip-flops)
  └── Submission: report PDF at Checkpoint 1 (Sun 27 Sep)
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
