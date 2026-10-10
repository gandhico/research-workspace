# Lab 9 — Grading Rubric
### 100 points · TA use

## Bench check-off (60 s per student, at 5:25)

| | Box | Passes if |
|---|---|---|
| ☐ | **Compiles** | 0 errors; `ROM` reports **block memory bits**, zero registers |
| ☐ | **Testbench passes** | `PASS`, 0 assertion failures |
| ☐ | **Can explain** | Answers both questions below |

**The two questions — same two for everyone:**

1. *Read the word at `0x08` out of your ROM. Which instruction is it, and how did you get that from four separate bytes?*
   - **Full:** `0x2021FFFF`, `ADDI r1,r1,-1`; explains big-endian assembly with `M[A]` landing in bits 31..24; can say what the other convention would have given.
   - **Partial:** reads the word off the waveform, cannot explain the assembly.
   - **None:** cannot produce it.

2. *Read your RAM with `en='0'`. What is on the bus, and why is that the right answer rather than zero?*
   - **Full:** `'Z'`, all 32 bits; because the bus is shared and driving `'0'` would fight the other driver and produce `'X'`; names the TriBuffer as the other driver.
   - **Partial:** knows it is `'Z'`, cannot say why it matters.
   - **None:** drives `'0'`.

---

## Points

| Component | Pts | Full credit | Partial | Zero |
|---|---|---|---|---|
| **Pre-lab** | 5 | All 3 attempted at 3:45; Q1 disassembly done | Q1(b) blank | Not submitted |
| **Compiles cleanly** | 25 | 0 errors; block-memory result commented on | Resource result not discussed (−5) | Does not compile |
| **Testbench + vectors** | 20 | All seven ROM words checked; full bus discipline | Fewer than seven ROM words (−6); write-mode `'Z'` case missing (**−8**) | Stimulus without checks |
| **Simulation results** | 20 | Bus shown at `Z`, RAM-driven, and externally driven, annotated | Only two of the three states shown (−6) | Fails or not run |
| **Report chapter** | 15 | 7 sections; **hand disassembly of all seven words**; endianness stated; out-of-range behaviour stated | Disassembly missing (**−6**); endianness not stated (−4) | Chapter absent |
| **Demo + explanation** | 15 | Both Full | One Full one Partial (−5); both Partial (−9) | Cannot explain own code |

**Late:** one week, −20.

---

## Automatic deductions

| | |
|---|---|
| **`rw` polarity backwards** | **−10** — `'1'` is read; this breaks every load in Lab 12 |
| **Drives `'0'` instead of releasing to `'Z'`** | **−10** — the whole bus goes `'X'` in Lab 12 |
| **Writes on the rising edge** | **−10** — works alone, breaks Lab 12's two-phase timing |
| Byte order reversed | −10 — the program decodes as garbage |
| ROM and RAM disagree on endianness | −8 — stores and loads do not round-trip |
| No range guard (simulation can abort) | −6 |
| Endianness not stated in the report | −4 |
| Code pasted into the report | −5 |
| "Everything worked first try" | −8 |

---

## What good looks like

Above 90: all seven ROM words disassembled by hand in the report, against the
instruction formats, not copied from the comment block; the endianness convention
stated explicitly with a sentence on why it matters; the bus waveform annotated with
*who* is driving in each interval; and the E4 result discussed as block memory versus
logic rather than just quoted.

## What to watch for

- **`rw` backwards.** Genuinely counter-intuitive — most people expect `'1'` to mean
  write. It is fixed by the CPU library and cannot be changed. Say it twice.
- **Driving `'0'` when idle.** Passes a single-driver testbench and destroys Lab 12.
  Ask for the `en='0'` case at every bench.
- **Rising-edge writes.** Also passes in isolation. The two-phase timing only matters
  once the CPU exists, which is why it must be caught now.
- **Out-of-range reads.** `base+3` near 511 aborts the simulation with an error that
  points at the array rather than the address. Students read it as "my memory is
  broken".
- **Copying the disassembly from the comment block.** The comment gives the answers;
  the report wants their derivation. Ask them to decode a word you pick.
- **Finished early.** The cache stretch: put a 4-entry direct-mapped cache in front of
  the ROM, run the loop, and report the hit rate. It is the only place the cache
  lectures touch hardware.
