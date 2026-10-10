# Final Lab — Demonstration and Extension

**Runs:** Mon 11/30 · Tue 12/1 · 3:45–5:45 PM, ECIII 237
**Full report due:** end of finals week (confirm the date with Dr. Tang)
**Status:** complete. Track A verified end to end; Track B built and compile-clean but **simulation not yet run** (see below).

---

## Settle this the week before

**Nobody should arrive without a working machine to demonstrate.** Your Lab 12 TA
notes list the students whose CPU never ran. Contact them: either finish it in
office hours, or take the reference CPU.

Say explicitly that **using the reference CPU costs nothing on the Final Lab** —
Lab 12's grade already stands and they are not charged twice. Some students will
otherwise turn up with nothing rather than accept what they read as a penalty.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Final_spec.pdf` | **students** | The session, the three tracks, report completion — 3 pages |
| `handout/Final_prep.pdf` | **students** | Demonstration plan + track choice, brought filled in |
| `LabFinal_student_files.zip` | **students** | All components + the three track starters |
| `assignment/components/` | students | The full working CPU and all 17 components |
| `assignment/trackA/` | students | Decoder to extend, plus the `ORI` test program |
| `assignment/trackB/` | students | `PerfCounters` skeleton |
| `assignment/trackC/` | students | `PipeReg` skeleton + straight-line test program |
| `slides/Final_slides.md` | you | 6 slides, 5 minutes — the shortest deck of the term |
| `solution/trackA/` | **TA only** | Working `ORI` decoder row + two-level testbench |
| `solution/trackB/` | **TA only** | `PerfCounters`, instrumented CPU, CPI testbench |
| `solution/trackC/hazard_analysis.md` | **TA only** | The four hazards, and the grading rule |
| `overleaf/labFinal.tex` | students | Final chapter + executive summary, resource table, reflection |
| `rubric.md`, `TA_notes.md` | you | Grading, the Track C rule, per-track traps |

---

## Verification status

| What | Result |
|---|---|
| Track A — `ORI` decoder row **and** CPU execution | ✅ `PASS` — `r1 = 0x000000FF`, stored at address 0 |
| Track A — existing instructions still decode correctly | ✅ checked in the same testbench |
| All track starters and packages compile | ✅ 0 errors |
| Track B — `PerfCounters` + instrumented CPU compile | ✅ 0 errors |
| Track B — **simulation** | ⚠️ **not yet run** |
| Track C — ROM and skeleton compile | ✅ 0 errors |
| Overleaf template with `labFinal` | ✅ 67 pages, 0 errors |

**Why Track B is unverified:** a GUI Questa session is currently holding the
nodelocked licence (`vsim.exe -gui`, running `lab2_e1_run_msim_gate_vhdl.do`), and
only one simulator instance can run at a time. It is your session, so I left it
alone. Close it and run:

```bash
cd C:/Teaching/VHDL/Lab_Final && vsim -c -quiet work.tb_trackB -do "run -all; quit -f"
```

**Expected result** (this is what the testbench asserts): 45 cycles, **23 ALU
operations, 0 loads, 1 store, 21 control flow** — summing to 45 — and CPI 1.000 as
built, ≈1.044 if memory took 3 cycles, ≈1.933 if control flow cost 2 extra cycles.

---

## The three tracks

**A — add an instruction.** `ORI`, end to end. Mirrors `ADDI` except it zero-extends,
because its immediate is a *bit pattern* — the same argument as `LUI` in Lab 4. The
supplied program uses **two `ORI`s in a row on purpose**: one alone passes even if
the instruction was implemented as "copy the immediate", which is exactly what
happens when someone clones the `LUI` row without thinking.

*The harder variant:* `SUB`. Students will discover their CPU computes `rt - rs`
rather than `rs - rt`, because the datapath's operand routing was fixed by
commutative instructions. **That discovery is the assignment** — full credit for
documenting it. Check they did not "fix" it by swapping the register-file reads,
which silently breaks `SLL` and `SW`.

**B — measure it.** CPI is trivially 1, so the *instruction mix* is the interesting
number: it belongs to the program, and it lets them answer questions about hardware
they did not build. This program is roughly half control flow and almost no memory,
so speeding up memory buys nearly nothing — Amdahl's law on a number they measured
themselves. The classification order matters: control flow must be tested **first**,
because a branch also has `RF_strb` low and `DM_en` disabled.

**C — one pipeline stage.** The grading rule is the whole design of this track:

> **A working pipelined CPU is NOT required. Breaking it correctly and explaining
> precisely why is full credit.**

Say it out loud, twice, before they choose. Otherwise nobody picks it. The control
hazard they will find is the reason real MIPS has a branch delay slot — that
connection is worth more than a working pipeline. The analysis must also identify
the structural hazard that is *absent*, and say why: that is the reason Harvard
architectures exist.

---

## Canvas module

```
Module: Final Lab — Demonstration and Extension
  ├── Final_spec.pdf
  ├── Final_prep.pdf               → bring filled in
  ├── LabFinal_student_files.zip
  ├── Final Lab slides (PDF)       ← pending deck build
  ├── Reading: COD Ch. 4.5–4.6 (pipelining) for Track C
  └── Submission: complete report PDF, end of finals week
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
