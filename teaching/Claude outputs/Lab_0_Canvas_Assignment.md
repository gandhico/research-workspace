# Lab 0 — VHDL Fundamentals

## Overview

Welcome to EE 362! In this lab, you will learn the foundation of VHDL design—the **entity** that declares an interface and the **architecture** that implements it. You'll verify four small combinational circuits by simulation, not by inspection.

**Why these circuits?** Every one of these four circuits will reappear later in the course. Two of them will end up inside your processor. Keep your files.

---

## The Method (This does NOT change all semester)

All your labs follow the same workflow:

```
Specification → Truth Table → Boolean Equations → VHDL → Simulation → Verify against Table
```

Today it's a four-row table and one equation. By week twelve, it will be an eight-row table with sixteen output columns—but nothing else will have changed.

---

## The Four Circuits

### Exercise 1 — Majority of Three
- **Spec:** Y = 1 when at least two of A, B, C are 1
- **Requirement:** Write two architectures (behavioral and structural) of the same entity
- **Testbench:** Have one testbench verify both architectures agree on every vector

### Exercise 2 — 2-to-1 Multiplexer  
- **Spec:** Y = D₀ when S = 0; Y = D₁ when S = 1
- **Requirement:** Write it TWO ways:
  - The exhaustive 8-row truth table
  - The 2-row table that names a **source** rather than a value
- **Note:** You'll use the second form for the rest of the course (Lab 3 explains why)

### Exercise 3 — 2-to-4 Decoder with Enable
- **Spec:** Exactly one output is high when E = 1; all outputs low when E = 0
- **Requirement:** Write one equation per output
- **Finding:** Notice what all equations have in common—that pattern has a name, and you'll meet it again in Lab 6
- **Real lesson:** The behavioral example from class has a bug. Find it. That's Exercise 3's actual learning goal.

### Exercise 4 — Full Adder
- **Spec:** A + B + Cᵢₙ, producing Sum and Cₒᵤₜ
- **Requirement:** Write two architectures (behavioral and structural) of the same entity
- **Key insight:** One equation does NOT simplify by K-map. Work out why and say what operator it needs instead. The other you've already derived in Exercise 1—say which one.
- **Testbench:** Have one testbench verify both architectures agree on every vector

---

## What to Build

For **each of the four circuits**, deliver:

1. **Truth table** — rows numbered (never paragraph descriptions like "row 5")
2. **Three-line derivation** — with law named:
   - Line 1: Canonical sum of minterms (straight from the table)
   - Line 2: Simplified form (and name the law or K-map grouping used)
   - Line 3: VHDL code that implements it
   - *Note: "It simplified" is not line 2. Name what you did.*
3. **VHDL entity and architecture**
4. **Self-checking testbench** — Use `assert` statements, never eyeballing waveforms
5. **Waveform** and **transcript line** showing checks passed

**For Exercises 1 and 4 only:** Provide two architectures (behavioral and structural) of the same entity, with one testbench that exercises both and asserts they agree on every test vector.

---

## Quartus Setup (Step by Step)

You will build this project by hand. **This is the only time you will**—from Lab 1 onward, the `.qpf` file is supplied. Doing it once is why you need to do it now.

1. **File → New Project Wizard**
2. **Working directory:** Use a short local path with no spaces, NOT inside OneDrive
   - Example: `C:\ee362\lab00` ✓
3. **Project name and top-level entity name:** These must match your VHDL entity name exactly
4. **Family:** Cyclone V  |  **Device:** 5CSEMA4U23C6
5. **EDA Tool Settings → Simulation:**  
   - Tool: **Questa Intel FPGA (VHDL)**  
   - Format: **VHDL**
6. **Project → Add/Remove Files** — Add your `.vhd` files
7. **Assignments → Settings → EDA Tool Settings → Simulation → Compile test bench → Test Benches → New**  
   - Test bench name: your testbench entity name
   - Top-level module: your testbench entity name

---

## The Simulation Workflow

| Step | What | Why |
|------|------|-----|
| 1 | Processing → Start → **Analysis & Elaboration** | Fast syntax check |
| 2 | Tools → Netlist Viewers → **RTL Viewer** | Did I describe what I meant? |
| 3 | Processing → Start **Compilation** (Ctrl+L) | Full build |
| 4 | Check **Compilation Report** | Errors, warnings, resource usage |
| 5 | Tools → Run Simulation Tool → **RTL Simulation** | Does it behave? |

**Do step 2 every time.** It costs ten seconds and catches most design mistakes before you spend a full compile on them.

---

## The Report — `lab00.tex`

You'll use an Overleaf template for your lab reports. **The template is a reference—not a strict format to follow.** Every student's design and analysis will be different; your report should reflect your work.

### Report Structure (All seven sections, for all four circuits)

1. **Introduction** — Overview of the lab goals and method
2. **Exercise 1: Majority of Three** — Truth table, derivation, VHDL code, testbench coverage, waveforms
3. **Exercise 2: 2-to-1 Multiplexer** — Both table forms, derivation, code, testbench, waveforms
4. **Exercise 3: 2-to-4 Decoder** — Truth table, equations, code, testbench, waveforms, bug analysis
5. **Exercise 4: Full Adder** — Both architectures, derivations, code, testbench, waveforms
6. **Discussion** — Describe ONE real bug you encountered, how you found it, and how you fixed it
7. **Conclusion** — Reflection on the lab

### Report Requirements

- **Include code using `\lstinputlisting`** — Never paste code; reference the actual files
- **Number every truth table row** — Use row numbers in text, never prose descriptions
- **Name every simplification law** — K-map groupings, Boolean algebra rules, etc.
- **Include testbench coverage argument** — Explain why your testbench vectors cover the behavior
- **Include waveforms** from simulation
- **Include the transcript** showing all `assert` checks passed
- **Add a Statement of Original Work** (in frontmatter):
  - Sign and date it
  - Note any references or classmates you discussed approaches with

---

## Overleaf Template & Reference Files

The Overleaf template is in **Canvas Files → Labs → Resources → Overleaf_template**

**What the template shows:**
- Professional lab report structure
- How to organize sections and figures
- How to include code listings and waveforms
- Title page and statement of original work format

**What to do:**
1. Review the template as a reference for professional formatting
2. Adapt the structure to YOUR design and analysis
3. Each circuit may have different details, insights, and bugs you found
4. Your discussion of the bug you hit should be unique to your experience

---

## Due Date

Submit your compiled PDF to Canvas: **Full lab report (lab00.pdf)** with all seven sections and all four circuits.

---

## Key Reminders

✓ **Do step 2 (RTL Viewer) before every compile** — Catches mistakes early  
✓ **Use assert statements** in testbenches—never just eyeball waveforms  
✓ **Name every simplification** — "It simplified" is not an answer  
✓ **Exercises 1 & 4 need TWO architectures** with cross-verification  
✓ **Keep your files** — You'll use these circuits again in your processor  
✓ **Your report is YOUR work** — Use the template as a guide, not a formula  

---

## Questions?

See the full assignment details in **Lab0_assignment.pdf** in Canvas Files. Ask during lab hours or post in the discussion forum.

Good luck! 🎯
