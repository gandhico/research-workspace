# Lab 9 — Memory: ROM and RAM

**Runs:** Mon 11/2 · Tue 11/3 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck written as content, not built as `.pptx`.
**Note:** Checkpoint 3 (Labs 7–9) due Sunday 8 November.

---

## Open with the program

Slide 2 puts the seven instructions up before any VHDL. This is the single most
motivating minute in the course — students have spent eight weeks building
components without seeing the destination.

```
0x00  LUI  r1, 11        0x0C  BLEZ r1, +2
0x04  LUI  r2, 1         0x10  SLL  r2, r2, 1
0x08  ADDI r1, r1, -1    0x14  J    0x08
                         0x18  SW   r2, 0(r0)
```

*Every component you have built since Lab 1 exists to make these seven instructions
run. Ten passes, doubling each time. Your CPU computes 2¹⁰ and stores 1024 at
address zero.*

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab9_spec.pdf` | **students** | Specification, 4 pages |
| `handout/Lab9_prelab.pdf` | **students** | Pre-lab, 2 pages, due 3:45 |
| `Lab9_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | `rom_small` — 16 bytes, four instructions |
| `examples/exe_2` | students | `ram_small` — the full shared-bus discipline |
| `examples/exe_3` | students | `endian_demo` — **the same bytes, two machines** |
| `assignment/` | **students** | Flat project: `ROM` (preloaded), `RAM`, testbench |
| `slides/Lab9_slides.md` | you | 9 slides + what to say |
| `solution/` | **TA only** | Reference + 19-check testbench. **Never publish.** |
| `overleaf/lab09.tex` | students | Report chapter |
| `rubric.md`, `TA_notes.md` | you | Grading, the three Lab-12-breaking errors |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 `rom_small` | four real instructions read correctly | ✅ `PASS`, 0 errors |
| exe_2 `ram_small` | bus discipline + storage | ✅ `PASS`, 0 errors |
| exe_3 `endian_demo` | the two conventions give different programs | ✅ `PASS`, 0 errors |
| `assignment/` as shipped | compiles clean, fails on the first ROM read | ✅ as designed |
| `solution/` | all pass | ✅ `PASS — all 19 checks passed`, 0 errors |
| Overleaf template with `lab09` | builds | ✅ 50 pages, 0 warnings |

---

## Three errors that pass this lab and break Lab 12

All three simulate plausibly in isolation. The TA notes list where to catch each.

| Error | Why it passes here | What it does in Lab 12 |
|---|---|---|
| **`rw` polarity backwards** | Their testbench uses their own convention consistently | Every load returns nothing |
| **Drives `'0'` instead of `'Z'`** | Passes with a single driver | The whole data bus goes `'X'` on every store |
| **Writes on the rising edge** | Storage works fine alone | Stores commit before the address settles — looks like random corruption |

Asking for the `en='0'` case at every bench catches the second, which is the worst.

**`rw = '1'` is READ.** Counter-intuitive, fixed by the CPU library, and worth
saying twice.

---

## The pedagogical spine

**One idea:** memory is an array with an address decoder and a bus discipline.

**Endianness is a decision, not a fact.** Example 3 shows `20 21 FF FF` decoding as
`ADDI r1,r1,-1` big-endian and as opcode `111111` — not an instruction at all —
little-endian. Same memory, different machine. It also includes a *palindromic*
value where both conventions agree, as a warning about test data: the same "test
where the implementations disagree" rule from Labs 4 and 5.

**Lab 4 becomes real.** The `inout` data bus, the `'Z'` release, and the contention
rules were abstract in Lab 4. Here the RAM shares its bus with the register file's
`TriBuffer`, and the testbench itself plays that second driver.

**Two-phase timing is introduced here, not at Lab 12.** RAM writes on the falling
edge because the instruction register loads on the rising edge. Address and data get
half a period to settle. Getting this right now is much cheaper than debugging it
inside a twelve-component CPU.

**E4 flips again.** Labs 3–5 wanted zero registers; Lab 6 wanted ~1024; here the
interesting number is **block memory bits** (512 bytes = 4096 bits). Whether the
Fitter chose block RAM or logic is the report question.

---

## Canvas module

```
Module: Lab 9 — Memory: ROM and RAM
  ├── Lab9_spec.pdf
  ├── Lab9_prelab.pdf              → due at 3:45; bring the instruction-format sheet
  ├── Lab9_student_files.zip
  ├── Lab 9 slides (PDF)           ← pending deck build
  ├── Reading: COD Ch. 5.1–5.2 (memory technology)
  └── ⚠ Checkpoint 3 due Sun 8 Nov — Labs 7–9, whole report PDF
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
