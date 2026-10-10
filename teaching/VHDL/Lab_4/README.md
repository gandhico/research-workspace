# Lab 4 — Datapath Support Components

**Runs:** Mon 9/28 · Tue 9/29 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck is written as content, not built as `.pptx`.
**Note:** Checkpoint 1 feedback is due back Wed 30 Sep — hand it back at 3:45 and explain the *Response to feedback* rule for CP2.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab4_spec.pdf` | **students** | Assignment specification, 4 pages |
| `handout/Lab4_prelab.pdf` | **students** | Pre-lab, 3 questions, due 3:45 |
| `Lab4_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | Tri-state buffers and a shared bus — **run live** |
| `examples/exe_2` | students | Sign vs zero extension, side by side |
| `examples/exe_3` | students | The `numeric_std` conversion chain |
| `assignment/` | **students** | Flat Quartus project |
| `slides/Lab4_slides.md` | you | 10 slides + what to say |
| `solution/` | **TA only** | Reference + 16-check testbench. **Never publish.** |
| `overleaf/lab04.tex` | students | Report chapter (also in the template) |
| `rubric.md`, `TA_notes.md` | you | Grading, friction table |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 tri-state bus | Z / A / B / X / agreement all correct | ✅ `PASS`, 0 errors |
| exe_2 the two extensions | differ exactly where the top bit is 1 | ✅ `PASS`, 0 errors |
| exe_3 conversion chain | bits → number → index works | ✅ `PASS`, 0 errors |
| `assignment/` as shipped | compiles, runs, reports failures | ✅ compiles clean, fails as designed |
| `solution/` | all pass | ✅ `PASS — all 16 checks passed`, 0 errors |
| Overleaf template with `lab04` | builds | ✅ 24 pages, 0 warnings |

---

## A bug in my own testbench, kept as a lesson

The reference testbench originally asserted that enabling both drivers with
`0xAAAAAAAA` and `0xBBBBBBBB` gives an all-`X` bus. **It does not.** `0xA` is
`1010` and `0xB` is `1011` — they agree on three bits of every nibble, so the bus
resolves to `101X` repeated.

Resolution is **per bit**, not per bus. The corrected testbench now checks both
cases explicitly (total contention → all `X`; partial contention → `101X`), the
student template warns about it, and slide 8 exists solely because of it. It is a
genuine trap and students will hit it.

---

## The pedagogical spine

**One idea:** `'Z'` is not a Boolean value — some hardware lives outside Boolean
algebra. `TriBuffer`'s output range is `{0,1,Z}` and the algebra has `{0,1}`, so it
cannot be written in AND/OR/NOT. The report must say so.

**The transferable rule, said twice:** *test where the implementations disagree,
not where they agree.* An immediate of `0x0001` extends identically both ways and
proves nothing; `0x8000` separates them. This is the same reasoning as Lab 1's hold
vector and Lab 2's edge vector — point that out.

**Example → assignment linkage.** Example 1's bus → the assignment's two
`TriBuffer` instances on one wire and the mandatory `Z`/`X` checks. Example 2's
extension pair → `ImmedXtnd` and the `x"8000"` requirement. Example 3's conversion
chain → prerequisite for Lab 5, which is entirely `numeric_std`.

**Reuse is now explicit.** `ALUsftMUX` *is* a `Mux2` with `W = 5`. Students may
instantiate their Lab 3 component or write it fresh, but the report must say which
and why. Recognising that a "new" block is one you already own is the skill that
makes Lab 12 tractable.

---

## Canvas module

```
Module: Lab 4 — Datapath Support Components
  ├── Lab4_spec.pdf
  ├── Lab4_prelab.pdf              → due at 3:45
  ├── Lab4_student_files.zip
  ├── Lab 4 slides (PDF)           ← pending deck build
  ├── Reading: COD Ch. 2.5–2.6 (representing instructions; sign extension)
  └── Reference: Lab 3 Mux2.vhd    (publish after Lab 3's late deadline)
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
