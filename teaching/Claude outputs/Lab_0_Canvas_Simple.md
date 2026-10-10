Lab 0 — VHDL Fundamentals

OVERVIEW

Learn VHDL basics: entity (interface) + architecture (implementation). Verify four circuits by simulation.

All four circuits reappear later in the course. Two end up in your processor. Keep your files.

THE WORKFLOW (All labs follow this)

Specification → Truth Table → Boolean Equations → VHDL → Simulation → Verify

---

THE FOUR CIRCUITS

Exercise 1 — Majority of Three
Y = 1 when at least two of A, B, C are 1
DELIVERABLES: Truth table | Derivation (with law named) | VHDL (2 architectures: behavioral + structural) | Testbench (asserts both agree) | Waveform | RTL Schematic

Exercise 2 — 2-to-1 Multiplexer
Y = D₀ when S = 0; Y = D₁ when S = 1
DELIVERABLES: 8-row truth table + 2-row truth table (source form) | Derivation | VHDL | Testbench | Waveform | RTL Schematic

Exercise 3 — 2-to-4 Decoder with Enable
Exactly one output high when E = 1; all low when E = 0
DELIVERABLES: Truth table | Equations (one per output) | VHDL | Testbench (find the bug in the example!) | Waveform | RTL Schematic

Exercise 4 — Full Adder
A + B + Cᵢₙ → Sum + Cₒᵤₜ
DELIVERABLES: Truth table | Derivations (2 equations; one doesn't K-map simplify—why?) | VHDL (2 architectures: behavioral + structural) | Testbench (asserts both agree) | Waveform | RTL Schematic

---

WHAT TO BUILD FOR EACH CIRCUIT

For all four exercises:
✓ Truth table (numbered rows)
✓ Three-line derivation (canonical form → simplified form → VHDL code)
✓ VHDL entity and architecture
✓ Testbench with assert statements (no eyeballing waveforms)
✓ Simulation waveform (screenshot from ModelSim/Questa)
✓ RTL schematic (Tools → Netlist Viewers → RTL Viewer)

For Exercises 1 & 4 ONLY:
✓ TWO architectures (behavioral + structural)
✓ ONE testbench that verifies both agree on every vector

---

QUARTUS SETUP

1. File → New Project Wizard
2. Working directory: C:\ee362\lab00 (short path, no spaces, not OneDrive)
3. Project name = top-level entity name (must match exactly)
4. Family: Cyclone V | Device: 5CSEMA4U23C6
5. EDA Tool Settings → Simulation: Questa Intel FPGA (VHDL), format VHDL
6. Project → Add/Remove Files (add your .vhd files)
7. Assignments → Settings → EDA Tool Settings → Simulation → Compile test bench → Test Benches → New

---

THE SIMULATION WORKFLOW

| Step | What | Why |
|------|------|-----|
| 1 | Processing → Start → Analysis & Elaboration | Fast syntax check |
| 2 | Tools → Netlist Viewers → RTL Viewer | Did I describe what I meant? |
| 3 | Processing → Start Compilation (Ctrl+L) | Full build |
| 4 | Check Compilation Report | Errors, warnings, resources |
| 5 | Tools → Run Simulation Tool → RTL Simulation | Does it behave? |

**Do step 2 every time.** It costs ten seconds and catches design mistakes before you spend a full compile.

---

THE REPORT — lab00.tex

Overleaf template: Canvas Files → Labs → Resources → Overleaf_template

The template is a REFERENCE for formatting. Your design, analysis, and bug story are YOUR OWN.

Sections (all four circuits):
1. Introduction
2. Exercise 1 (truth table, derivation, code, testbench, waveform, schematic)
3. Exercise 2 (both truth tables, derivation, code, testbench, waveform, schematic)
4. Exercise 3 (truth table, equations, code, testbench, waveform, schematic, bug analysis)
5. Exercise 4 (truth tables, derivations, code, testbench, waveform, schematic)
6. Discussion: Describe ONE real bug you hit, how you found it, how you fixed it
7. Conclusion

Report checklist:
☐ Code included via \lstinputlisting (never pasted)
☐ Truth table rows numbered
☐ Every simplification law named
☐ Testbench coverage explained
☐ Waveforms and transcripts included (all asserts passed)
☐ RTL schematics for all four circuits
☐ Statement of Original Work (signed, dated)

---

GRADING RUBRIC

| Component | Points | Criteria |
|-----------|--------|----------|
| **Exercise 1: Majority (Behavioral)** | 10 | Truth table (2) + Derivation (2) + VHDL (3) + Testbench (2) + Waveform (1) |
| **Exercise 1: Majority (Structural)** | 10 | Architecture (5) + Testbench cross-check (3) + RTL Schematic (2) |
| **Exercise 2: Multiplexer** | 10 | Both truth tables (3) + Derivation (2) + VHDL (3) + Testbench (1) + Waveform (1) |
| **Exercise 3: Decoder** | 12 | Truth table (2) + Equations (3) + VHDL (3) + Testbench (2) + Bug analysis (1) + RTL Schematic (1) |
| **Exercise 4: Adder (Behavioral)** | 10 | Truth table (2) + Derivations (2) + VHDL (3) + Testbench (2) + Waveform (1) |
| **Exercise 4: Adder (Structural)** | 10 | Architecture (5) + Testbench cross-check (3) + RTL Schematic (2) |
| **Report Quality** | 14 | Organization (3) + Clarity (3) + Code formatting (2) + Waveforms/Schematics (3) + Discussion/Bug (3) |
| **Statement of Work & Professionalism** | 4 | Signed statement (2) + Professional presentation (2) |
| | **TOTAL: 80** | |

Grading notes:
- All assert statements must pass (shown in transcript)
- Every simplification must name the law (K-map, absorption, etc.)
- Waveforms and schematics must be clear (screenshots OK)
- Discussion bug must be real—describe the symptom, root cause, and fix
- Deductions for pasted code, missing row numbers, or unsigned statement of work

---

DUE DATE

Submit lab00.pdf to Canvas with all sections and all four circuits.

QUESTIONS?

See Lab0_assignment.pdf in Canvas Files → Labs.
