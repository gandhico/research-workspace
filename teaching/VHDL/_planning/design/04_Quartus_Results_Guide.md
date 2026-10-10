# Reading Your Results
### EE 362 Lab — student handout · Quartus Prime Lite + Questa

We do not have FPGA boards this semester. That changes nothing important: synthesis, fitting, and timing analysis all still run, and they still tell you the truth about your design. We simply never program a chip at the end.

There are **seven** places your design reports on itself. Each lab tells you which ones to include. **A figure with no sentence interpreting it earns zero marks** — the sentence is the work; the screenshot is just evidence for it.

---

## E1 · Flow Summary and Messages
**Where:** the Compilation Report tab opens automatically · Messages panel at the bottom.

**What it answers:** did it build, and what is it worried about?

Read the Flow Summary top block: device, total logic elements, total registers, total pins.

**Warnings are not noise.** Sort them into three piles, and say which pile each one is in:

| Pile | Example | What to do |
|---|---|---|
| **Fix** | "inferred latch for signal X" · "output never driven" · "signal has no driver" | Fix it. These are bugs. |
| **Explain** | "design contains N pins that do not drive any logic" · unconnected port | Say in one sentence why it is expected |
| **Ignore** | timing model / license / file-path informational notes | Say you reviewed and dismissed them |

> **In your report:** *"Compilation completed with 0 errors and 7 warnings. Six are Quartus informational notes about the timing model. One reports N unused pins, expected because the testbench drives the design directly rather than through I/O."*

**The one warning that must never survive:** *inferred latch*. It means you left an input combination undefined. Go back to your truth table and find the missing row.

---

## E2 · RTL Viewer
**Where:** `Tools → Netlist Viewers → RTL Viewer`

**What it answers:** did I describe the circuit I meant?

This is the highest-value habit in the course, and it costs ten seconds. Run **Analysis & Elaboration** and look at the picture *before* you ever run a full compile.

Check three things:
1. **Element count.** Two multiplexers where you expected one means you wrote something twice.
2. **Unexpected storage.** A latch or flip-flop symbol in a design that should be pure combinational logic is an inferred latch — you have a missing `else` or `when others`.
3. **Missing logic.** A signal that goes nowhere means you assigned it and never used it, or used it and never assigned it.

The RTL Viewer shows your design *before* the fitter optimises it, so it maps almost one-to-one onto your VHDL. That is exactly what makes it good for checking intent.

> **In your report:** *"The RTL Viewer shows one 32-bit 3:1 multiplexer with no storage elements, confirming the design is purely combinational as specified."*

---

## E3 · Technology Map Viewer
**Where:** `Tools → Netlist Viewers → Technology Map Viewer (Post-Fitting)`

**What it answers:** what did my design actually become inside this chip?

The RTL Viewer shows what you described. This shows what the fitter built out of the parts the Cyclone V actually has: look-up tables, registers, and routing. The two pictures rarely match, and the difference is the interesting part.

Typical surprises, all normal:
- Your carefully structured gates collapsed into a handful of LUTs. A 6-input LUT implements *any* 6-input function, so gate-level structure mostly disappears.
- Logic you wrote once appears twice — the fitter duplicated it to shorten a path.
- Logic you wrote disappeared entirely, because its output was constant or unused.

> **In your report:** *"The eight gates of the structural full adder mapped to two LUTs. The Cyclone V LUT implements any function of up to six inputs, so gate-level structure is not preserved."*

---

## E4 · Resource Utilisation
**Where:** `Compilation Report → Fitter → Resource Utilisation by Entity`

**What it answers:** what did it cost?

Report these four, per entity, in a small table:

| Column | Meaning |
|---|---|
| ALMs / logic cells | combinational hardware used |
| Dedicated logic registers | flip-flops — **should equal the number of bits you meant to store** |
| Block memory bits | inferred RAM/ROM |
| Pins | I/O signals |

**The register count is a correctness check, not just a cost.** A 32-bit register should report 32 registers. If your "combinational" multiplexer reports any registers at all, you have inferred a latch — go back to E2.

Rough expectations, so you know when to be suspicious:

| Design | Registers | Notes |
|---|---|---|
| `TransLatch` | 1 latch | not a flip-flop — the report distinguishes them |
| `RegN` (N=32) | 32 | |
| `Mux3x32` | **0** | any register here is a bug |
| `RegFile` 32×32 | ~1024 | or inferred as block memory instead |
| `ALU` | 0 | plus HI/LO registers if you included them |

> **In your report:** *"The register file used N dedicated logic registers."* Expect roughly 1024 (32 × 32). A slightly lower count usually means register 0 was optimised away because it is hardwired to zero; a far lower count means the fitter inferred block memory instead of flip-flops. Say which happened to you, and how you can tell.

---

## E5 · Pin-Out and I/O
**Where:** `Compilation Report → Fitter → Pin-Out File`, or `Resource Section → Input Pins / Output Pins`

**What it answers:** how many signals leave this block, and does that make sense?

We are not assigning pins to a board this semester, so Quartus places them automatically. That is fine — the *count* is what matters.

Two things to notice:

1. **The count.** A 32-bit ALU with two data inputs, a result, a function code, a shift amount and two flags needs 32+32+32+5+5+2 = 108 pins. Every one of those is a wire that would have to physically leave the chip. Real designs do not do that — they keep wide blocks *inside* and bring only narrow interfaces out. Compare: your finished CPU in Lab 12 has exactly **one** pin, `SysClk`, because the ROM, RAM and registers all live inside it.
2. **"Design contains N pins that do not drive any logic."** Expected for a component tested by a testbench rather than wired to a board. Say so once; do not treat it as an error.

> **In your report:** *"As a top-level entity the ALU requires 108 I/O pins. This is not a design fault — the ALU is an internal block, and in Lab 12 only the clock crosses the chip boundary."*

That contrast — 108 pins for a component, 1 pin for the whole processor — is worth a sentence in your final report.

---

## E6 · Timing Analyzer
**Where:** `Tools → Timing Analyzer` → `Reports → Slow 1100mV 85C Model → Fmax Summary`, and `Setup Summary`

**What it answers:** how fast can this run, and what is stopping it going faster?

**Always read the Slow 1100mV 85C model.** It is the worst case: slowest silicon, lowest voltage, highest temperature. A design that meets timing there works everywhere. Quoting the fast model is the timing equivalent of quoting your best-ever exam score.

Three numbers:

| Number | Meaning |
|---|---|
| **Fmax** | the highest clock frequency this design can be clocked at |
| **Setup slack** | margin before data arrives too late. Negative = fails |
| **Hold slack** | margin before data arrives too early. Negative = fails |

**If your design is purely combinational there is no clock, so there is no Fmax** — the Timing Analyzer will say so. That is a correct result, not a missing one. Report the worst-case propagation delay instead, or state plainly that timing analysis does not apply.

To find the critical path: `Reports → Custom Reports → Report Timing`, worst-case setup path. It names the start point, the end point, and every element in between.

> **In your report:** *"Fmax is 78.6 MHz on the Slow 1100mV 85C model. The critical path runs from the register file A output through the ALU adder carry chain to the result bus, which is expected: the 32-bit carry chain is the longest combinational path in the design."*

---

## E7 · Questa Waveform and Transcript
**Where:** `Tools → Run Simulation Tool → RTL Simulation`

**What it answers:** does it actually behave, and did the checks pass?

**The transcript is the proof. The waveform is the illustration.** Your testbench `assert` statements are what verify correctness — if the transcript is clean, every assertion passed. Include one line of it.

> *"# Simulation completed: 0 assertion failures."*

**Waveform screenshots — how to not lose marks:**

| Do | Don't |
|---|---|
| Crop to the signals that matter | Capture the whole screen with the file browser in it |
| Set radix per signal: hex for 32-bit buses, binary for control | Leave 32-bit buses in decimal or unsigned |
| Group and order signals: inputs, then internals, then outputs | Leave them in whatever order they were added |
| Zoom to the interesting interval | Show 10 ms in which everything happens in the first 200 ns |
| Save as PNG at full resolution | Screenshot the screenshot, or paste a JPEG |
| Annotate: an arrow and a label on the moment that proves the spec | Leave the reader to find it |

**Reading `std_logic` values:**

| Value | Means | Usually caused by |
|---|---|---|
| `0` `1` | normal | — |
| `U` | uninitialised, never driven | signal declared but never assigned; a `port map` you forgot |
| `X` | **two drivers disagreed** | two processes driving one signal, or two tri-states enabled at once |
| `Z` | high impedance, nothing driving | correct for a disabled tri-state; a bug anywhere else |
| `-` | don't care | rare in simulation |

`U` and `X` are the two you will actually meet. `U` means *nobody* drove it; `X` means *too many people* drove it. They are opposite problems, and knowing which one you are looking at saves an hour.

---

## The five-minute pre-submission check

Before you screenshot anything:

1. **0 errors.** Every warning sorted into fix / explain / ignore.
2. **RTL Viewer** shows the circuit you meant — and no unexpected storage.
3. **Register count** matches the number of bits you intended to store.
4. **Transcript** shows zero assertion failures.
5. **Waveform** cropped, radix set, and the proving moment annotated.
6. Every figure has **one sentence** saying what it proves.

Point 6 is where most marks are lost, and it is the cheapest to fix.

---

## Quick error decoder

| Symptom | Actual cause |
|---|---|
| "Can't find entity/architecture" | File not added to the project, or entity name ≠ what you instantiated |
| Everything is `U` in simulation | Signal never driven — check your `port map` |
| Signal stuck at `X` | Two drivers on one net |
| "Inferred latch for signal X" | Incomplete `if`/`case`; add defaults before the `case` |
| Waveform is empty | Wrong simulation top level, or no `wait` in the stimulus process |
| Simulation never ends | Clock process without a `wait`, or no `wait;` at the end of stimulus |
| "Object cannot be updated" | Assigning to an `in` port, or a signal/variable confusion |
| Width mismatch | `std_logic` vs 1-element vector, or a wrong `generic map` |
| Edits seem to have no effect | Stale libraries — rerun Analysis & Elaboration |
| Inexplicable breakage | Project path contains spaces or non-ASCII characters, or sits in a cloud-synced folder |

That last row is not a joke. Keep your projects in a short local path such as `C:\ee362\lab05`.
