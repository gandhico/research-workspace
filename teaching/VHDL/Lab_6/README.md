# Lab 6 — Register File

**Runs:** Mon 10/12 · Tue 10/13 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck written as content, not built as `.pptx`.
**Note:** Checkpoint 2 (Labs 4–6) due Sunday 18 October — first one requiring the *Response to feedback* section.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab6_spec.pdf` | **students** | Specification, 4 pages |
| `handout/Lab6_prelab.pdf` | **students** | Pre-lab, 3 pages, due 3:45 |
| `Lab6_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | `regfile_small` — 4×8, one port, watchable in a waveform |
| `examples/exe_2` | students | `regfile_two_ports` — the second read port, two lines |
| `examples/exe_3` | students | `read_during_write` — **register 0 and the RDW decision** |
| `assignment/` | **students** | Flat project: `RegFile.vhd`, testbench |
| `slides/Lab6_slides.md` | you | 9 slides + what to say |
| `solution/` | **TA only** | Reference + 18-check testbench. **Never publish.** |
| `overleaf/lab06.tex` | students | Report chapter |
| `rubric.md`, `TA_notes.md` | you | Grading, friction table |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 `regfile_small` | write/read, combinational reads, `Strb` low | ✅ `PASS`, 0 errors |
| exe_2 `regfile_two_ports` | both ports independent, same register OK | ✅ `PASS`, 0 errors |
| exe_3 `read_during_write` | R0 hardwired; READ-OLD both sides of the edge | ✅ `PASS`, 0 errors |
| `assignment/` as shipped | compiles clean, fails on the first vector | ✅ as designed |
| `solution/` | all pass | ✅ `PASS — all 18 checks passed`, 0 errors |
| Overleaf template with `lab06` | builds | ✅ 33 pages, 0 warnings |

---

## A fix worth knowing about

Example 3's read-during-write check was originally labelled "3b" with no "3a" — I
had dropped the check that actually demonstrates the behaviour. It now checks
`Aout` **before** the rising edge (old value, with the new data already sitting on
`Din`) and **after** it (new value). Without the before-check, the example named a
design decision it never showed.

---

## The pedagogical spine

**One idea:** thirty-two copies of the Lab 2 register, plus address decoding. After
Lab 5 this reads as intimidating and is genuinely lighter — say so at Open, because
students who believe it spend the spare time on the report.

**Two things that must not leave the room wrong:**

1. **Reads inside the clocked process.** Simulates plausibly, passes a careless
   testbench, and breaks Lab 12 in a way that is very hard to diagnose six weeks
   later. Check visually at every bench — `Aout <=` must be *outside* `process (clk)`.
2. **Register 0 writable.** The defining feature of the lab. Protect it on both the
   write side and the read side: either alone works, but with both, a mistake in one
   place still cannot produce a non-zero `$0`.

**Read-during-write is a decision, not a detail.** Both READ-OLD and READ-NEW are
correct designs. The failure is not choosing wrong — it is not knowing which one you
built. That is check-off question 2, and the testbench must check both sides of the
edge.

**Example → assignment linkage.** exe_1's array type and index conversion → the
32×32 storage. exe_2's second read port → `Aout`/`Bout` and the read-port cost
argument in the report. exe_3's R0 protection and RDW → the two mandatory testbench
cases.

**New this week in the evidence:** E4 finally has a *non-zero* expected register
count (~1024). For Labs 3–5 the check was "must be zero"; here it flips, and the
number becomes a positive correctness check.

---

## Canvas module

```
Module: Lab 6 — Register File
  ├── Lab6_spec.pdf
  ├── Lab6_prelab.pdf              → due at 3:45
  ├── Lab6_student_files.zip
  ├── Lab 6 slides (PDF)           ← pending deck build
  ├── Reading: H&H Ch. 5.5 (memory arrays / register files); COD Ch. 4.2
  └── ⚠ Checkpoint 2 due Sun 18 Oct — Labs 4–6, whole report PDF,
        opening with the Response to feedback section
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
