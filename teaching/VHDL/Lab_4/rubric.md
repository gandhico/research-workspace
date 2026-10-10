# Lab 4 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors; no latch warning; `ImmedXtnd` reports **0 registers** |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Show me `0x8000` through your extender both ways. Why do the top sixteen bits differ, and which instruction wants which answer?*
   - **Full:** zero-extend gives `0x00008000`, sign-extend `0xFFFF8000`; names `ADDI`/`LW`/`SW` as sign and `LUI` as zero, and explains it as what the bits *mean*.
   - **Partial:** gets the two values, cannot connect them to instructions.
   - **None:** cannot produce both.

2. *You enabled both tri-states and got `X`. In a real chip, what is physically happening — and why isn't the whole bus `X`?*
   - **Full:** two output drivers fighting (a short from supply to ground through two transistors); and resolution is per bit, so only disagreeing bits go `X`.
   - **Partial:** gets contention, misses the per-bit point.
   - **None:** neither.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted at 3:45 | Q1(c) or Q3 blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors, no latch warning, 0 registers | Latch warning present (**−10**) | Does not compile |
| **Testbench + vectors** | 20 | ≥ 6 vectors incl. `x"8000"` both ways, rows 2 and 3, bus `Z` and `X` | Tested only values where extensions agree (**−8**); row 3 untested (**−6**) | Stimulus without checks |
| **Simulation results** | 20 | Bus shown at `Z`, at a value, and at `X`, annotated | Bus `X` case missing (−6) | Fails or not run |
| **Report chapter** | 15 | 7 sections; Type C table; resolution table; `TriBuffer` identified as non-Boolean | Non-Boolean point missing (−4); reuse decision unjustified (−3) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| Discussion does not answer *why `ADDI` sign-extends but `LUI` zero-extends* | **−8** — it is the named required question |
| Row 3 unimplemented (latch inferred) | **−10** |
| Only tested immediates where the two extensions agree | **−8** — the vectors prove nothing |
| Used `std_logic_arith` or `std_logic_unsigned` | **−6** and fix it on the spot; it will break Lab 5 |
| `'Z'` compared against `'0'` in the testbench | −4 |
| `ALUsftMUX` reuse decision stated with no reasoning | −3 |
| Code pasted into the report | −5 |
| Figure with no interpreting sentence | −4 each |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: the report states plainly that `TriBuffer` is not a Boolean function and
says why (output range `{0,1,Z}`, algebra has `{0,1}`); the waveform figure shows
the bus in all three states with the `X` interval annotated *and attributed to two
enabled drivers*; and the student either reused `Mux2` for `ALUsftMUX` and said why
reuse beats rewriting, or wrote it directly and defended that.

## What to watch for

- **`'Z'` vs `'0'`.** Students write `if Dout = '0'` to test a released bus. It
  fails and they blame the buffer. `'Z'` is not `'0'`.
- **Expecting all-`X`.** Contention with `0xAAAAAAAA`/`0xBBBBBBBB` gives `101X`
  repeated, not all `X`. This caught the reference testbench during development —
  it is a real trap, and slide 8 exists because of it.
- **Sign bit index.** They extend `Immed16(0)` or `(31)`. It is `(15)`.
- **One giant expression.** Students who try to do extend-and-shift in a single
  concurrent assignment produce something unreadable and usually wrong. Push the
  two-signal version; the RTL Viewer then shows two clean stages.
- **`std_logic_arith`.** Someone will find it on the internet. Stop it now — Lab 5
  is entirely `numeric_std` and mixing the two produces incomprehensible errors.
- **Finished early.** Have them reuse `Mux2` for `ALUsftMUX` if they wrote it
  directly (or vice versa) and compare the RTL Viewer output of both.
