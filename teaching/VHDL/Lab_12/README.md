# Lab 12 — CPU Integration

**Runs:** Mon 11/23 · Tue 11/24 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. **The CPU runs.**

---

## The result

```
PASS - Lab 12: the CPU computes 2^10 and stores it.
final r1     = 0x00000000
final r2     = 0x00000400   (= 1024 = 2^10)
stored word  = 0x00000400   at address 0
```

**45 instructions, one per clock period, CPI = 1** — exactly the count predicted in
the program design document before any of it was built. The trace shows r1 counting
11→10→…→0 and r2 doubling 1→2→4→…→1024.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab12_spec.pdf` | **students** | Specification, 4 pages |
| `handout/Lab12_prelab.pdf` | **students** | Pre-lab — **hand-computed trace**, due 3:45 |
| `Lab12_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1/bisect_method.md` | **students** | The four-check debugging method |
| `examples/exe_1/cpu_broken.vhd` | students | A CPU with **two deliberate wiring errors** |
| `assignment/CPU.vhd` | **students** | The skeleton, with the traps documented |
| `assignment/components/` | **students** | All 17 reference components |
| `assignment/tb_Lab12.vhd` | students | **Provided complete** — prints the trace, checks the result |
| `slides/Lab12_slides.md` | you | 8 slides + what to say |
| `solution/` | **TA only** | The working CPU. **Never publish.** |
| `overleaf/lab12.tex` | students | Report chapter — the longest of the term |
| `rubric.md`, `TA_notes.md` | you | Grading, the four checks, friction table |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| `solution/` full CPU | runs the program, computes 2¹⁰ | ✅ `PASS`, 0 errors, 7 startup warnings |
| `examples/exe_1` broken CPU | **exactly 2** failures, both intended | ✅ 2 errors: r2 = 0, stored = 0 |
| `assignment/` as shipped | compiles, fails with a *useful* message | ✅ *"no write to r2 was ever observed — start at check 1"* |
| Overleaf template with `lab12` | builds | ✅ 64 pages, **0 errors**, 0 warnings |

---

## Three real bugs found while building this

**1. The first instruction was being lost.** The all-zeros reset value of `IRreg`
decodes as `SLL r0, r0, 0` — a valid NOP — which strobed the PC before the first
fetch ever happened. Fixed by releasing reset *between* clock edges rather than on
one; the testbench now says why in a comment.

**2. The trace was lying.** It sampled 1 ns *after* the falling edge, so for
`ADDI r1, r1, -1` the combinational logic had already recomputed from the
just-written `r1` — the trace showed 9 where the hardware had correctly computed 10.
The hardware was fine; the observer was wrong. Now samples 1 ns *before* the edge,
with a comment explaining that **when you sample is part of the measurement.** This
is documented in the spec because it is a genuinely common way to lose an hour.

**3. Failure messages rendered `'U'` as `0`.** An empty CPU reported *"r1 should end
at 0, got 0x00000000"*. Now guarded with `is_x()` and reports *"no write to r1 was
ever observed"* plus a pointer to check 1.

---

## The pedagogical spine

**One idea:** debugging a system means predicting it first.

**The four checks**, on the whiteboard all session:

```
1. Is the PC advancing by 4?           -> no: NIAG or reset
2. Is IR what the ROM table says?      -> no: ROM addressing or fetch
3. Do control signals match the table? -> no: the decoder
4. Only now, the datapath.
```

Each depends on the ones before it. Checking the ALU while the PC is stuck tells you
nothing — the ALU is faithfully computing on garbage.

**Example 1's two bugs both pass checks 1, 2 and 3.** That is the point: establishing
that is not wasted effort, it is what localises the fault to the wiring. And both
produce the *same headline symptom* — the stored word is wrong. The symptom does not
identify the bug; the method does. One is visible on almost every trace line, the
other on exactly one.

**`Asel = rt`, `Bsel = rs`** is the trap worth the most time. Swap them and *three of
the four instruction types still work* — only `SLL` breaks, because it shifts
whatever arrives on `Aout`.

**Integration is never gated on an earlier miss.** All 17 reference components ship
in `assignment/components/`. Hand them out at the *start* of the session, and say out
loud that using one costs nothing — some students will otherwise struggle in silence
rather than accept what they assume is a penalty.

---

## Canvas module

```
Module: Lab 12 — CPU Integration
  ├── Lab12_spec.pdf
  ├── Lab12_prelab.pdf             → due at 3:45; BRING THE PRINTED CONTROL TABLE
  ├── Lab12_student_files.zip      (skeleton + all 17 reference components)
  ├── Lab 12 slides (PDF)          ← pending deck build
  └── Reading: COD Ch. 4.4; H&H Ch. 7.3 end to end
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
