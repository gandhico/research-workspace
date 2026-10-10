# EE 362 Lab — Resource Plan, Fall 2026

What to give students, when to give it, and why. Companion to `00_Program_Design.md`, `01_Lab_Program.md`, `03_Session_Scripts.md`, `04_Quartus_Results_Guide.md`.

**No FPGA hardware this semester.** Everything below is simulation and synthesis-report based.

Guiding rule: **release resources per lab, not all at once.** A Canvas module with 40 links in week 1 is read by nobody. Three links attached to the lab that needs them get used.

---

## 1. Resources you already own (local)

`C:\Teaching\VHDL\Books\`

| Book | Role in this course | How to use it |
|---|---|---|
| **Harris & Harris — *Digital Design and Computer Architecture*, 4th ed.** | **Primary lab reference.** Best match to this lab sequence: it teaches HDL and microarchitecture in the same book. | Ch. 1–3 for Labs 0–2, Ch. 4 (HDL) throughout, Ch. 5 (building blocks) for Labs 3–6, Ch. 6 (architecture) for Labs 7–11, Ch. 7 (microarchitecture) for Labs 10–12 |
| **Patterson & Hennessy — *Computer Organization and Design*, 5th ed.** | **Dr. Tang's lecture spine.** MIPS ISA and the single-cycle datapath. | Ch. 2 (instructions) for Labs 7–11, Ch. 3 (arithmetic) for Lab 5, Ch. 4 (the processor) for Labs 10–12, Ch. 5 (memory hierarchy) for Lab 9, Appendix B (logic design) for Labs 1–4 |
| **Pedroni — *Circuit Design and Simulation with VHDL*** | Syntax reference at the right level for undergrads. | Point students here for language questions, Labs 1–6 |
| **Pong P. Chu — *RTL Hardware Design Using VHDL*** | **Coding-style authority.** The book that explains why some VHDL synthesizes well and some does not. | Your own reference when writing skeletons; assign excerpts on coding style at Labs 3 and 5 |
| **Ashenden — *The Designer's Guide to VHDL*** | Deep reference. | Keep on the shelf; cite for edge cases. Do not assign to a first course. |
| **Mano — *Digital Design*, 5th ed.** | Prerequisite refresher. | For students who arrive weak on latches/flip-flops (Labs 1–2) |

`C:\Teaching\VHDL\Documentation\`

Twenty PDFs of the ISA and CPU: instruction formats, instruction list, control signals, decode logic table, CPU diagram, pipeline diagram, addressing modes, ALU functions, data types.

**Action item:** these are the single most valuable asset you have, and they are currently in a form students will not read. Condense them into **one 2-page "EE 362 Green Sheet"** — instruction formats, the instruction list with opcodes/func values, register conventions, and the control-signal names — and hand it out at Lab 7. Every student should have it printed by Lab 10. The full PDFs stay available as the authoritative reference.

`C:\Teaching\VHDL\Libraries\` — the seven `EE362*.vhd` packages. Release each package the week its component is built, not earlier: the constants are half the answer.

`C:\Teaching\VHDL\Overleaf_report_example\` — existing Quartus-report example; the base for the report template.

---

## 2. Tool guidance to author (highest priority — Batch A)

### 2.1 The Quartus/Questa Workflow Card (1 page, laminated if possible)

This is the single artifact that saves you the most repeated explanation. Contents:

**Project setup**
1. `File → New Project Wizard`. Project directory with **no spaces and no OneDrive sync** (this causes real, hard-to-diagnose failures).
2. Family **Cyclone V**, device **`5CSEMA4U23C6`**.
3. Top-level entity name **must match** the entity name in the VHDL file.
4. `Assignments → Settings → EDA Tool Settings → Simulation` → Tool: **Questa Intel FPGA (VHDL)**, format VHDL.

**The flow, and what each step is for**
| Step | Where | Use it when |
|---|---|---|
| Analysis & Elaboration | `Processing → Start → Start Analysis & Elaboration` | Fast syntax check. Do this constantly. |
| RTL Viewer | `Tools → Netlist Viewers → RTL Viewer` | *Did I describe the circuit I meant?* Best single debugging habit in the course. |
| Full compilation | `Processing → Start Compilation` (Ctrl+L) | Before every submission |
| Compilation Report | auto | Resource usage, warnings, Fitter results |
| Technology Map Viewer | `Tools → Netlist Viewers` | What the design actually became in the fabric |
| RTL Simulation | `Tools → Run Simulation Tool → RTL Simulation` | Functional verification against the testbench |
| Timing Analyzer | `Tools → Timing Analyzer` | Fmax, for the report's Results section |

**Testbench convention** — testbench entity has no ports; name it `<design>_tb`; set it as the simulation top level under EDA Tool Settings → Simulation → *Compile test bench*.

**Error decoder** — lives in `04_Quartus_Results_Guide.md`, which is the student-facing handout. Do not duplicate it here; one copy, published once, in the Course Resources module.

### 2.2 The recorded flow walkthrough (12–15 min, record once)

Screen recording of exactly the Lab 1 e1 flow: create project → add file → elaborate → RTL Viewer → compile → set up simulation → run → read waveform. Post it in week 1.

You need it for three independent reasons: Labor Day makeup for the Monday section, absent students all semester, and it eliminates the single most repeated live explanation of the term. Highest return per hour of anything in the production plan.

### 2.3 Install guidance (push before Lab 1)

- **NMSU College IT — Quartus Prime Installation for Students at Home:** https://college-it.nmsu.edu/guides/Quartus-Prime-Installation-for-Students-at-Home.pdf
  Includes the NMSU-specific licensing step: connect to the NMSU VPN, then in the license prompt specify the license location `1801@chaos`. **This is the step students fail at every semester** — put it in the announcement text itself, not only in the linked PDF.
- **NMSU College IT guides index:** https://college-it.nmsu.edu/guides/index.html
- Tell them explicitly: install Quartus Prime **Lite** with **Cyclone V** device support and the **Questa Intel FPGA Starter** simulator. Download is large; start it days before Lab 1. Lite edition is free and needs no license, but the NMSU lab-machine configuration does — mention both.

## 3. Online resources, mapped to the lab that needs them

Release each with its lab. Preview any video before posting.

### Tier 1 — recommend by name, repeatedly

| Resource | URL | Attach to |
|---|---|---|
| **Nandland** — tutorials, VHDL examples, and a YouTube channel by Russell Merrick. Best beginner FPGA explanations on the web; strong specifically on **testbenches and simulation**, which is exactly where this class is weakest. | https://nandland.com/ · https://www.youtube.com/c/Nandland/videos | Labs 1, 2, and again at Lab 9 |
| **Nandland — "How to Simulate Your FPGA Designs"** | https://nandland.com/project-6-how-to-simulate-your-fpga-designs/ | Lab 1 |
| **VHDLwhiz — Basic VHDL Course** — clean, structured written tutorials on the exact constructs Labs 1–5 use | https://vhdlwhiz.com/basic-vhdl-tutorials/ | Labs 1–5 |
| **FPGA Tutorial — VHDL series** — short, focused pages per construct | https://fpgatutorial.com/vhdl/ | Labs 2–4 |
| **Merrick, *Getting Started with FPGAs*** (No Starch Press) — the friendliest supplementary book; code in both VHDL and Verilog | https://github.com/nandland/getting-started-with-fpgas | Recommend once, in week 1, to students who want to go further |

### Tier 2 — video series (preview before posting)

Found by search; check the first two videos of each before recommending, since playlists change:

- *FPGA Design using VHDL Lectures* — https://www.youtube.com/playlist?list=PLZv8x7uxq5XY-IQfQFb6mC6OXzz0h8ceF
- *VHDL coding for beginners* — https://www.youtube.com/playlist?list=PLY-KEUOswf8INzQVRnibXYeRymVNh5vOc
- *Master FPGA Design with VHDL* — https://www.youtube.com/playlist?list=PLClhqzBCtzSxqQlV8sH9aO5b0B8rcQ-Ao

Advice on video use, worth saying to the class once: videos are good for *watching a flow* (Lab 1) and bad for *learning a specification* (Labs 10–11). For the decoder, the control table beats any video.

### Tier 3 — reference, not teaching

- Intel/Altera Quartus Prime Lite documentation and the Quartus Prime Handbook (Intel FPGA support site) — for the Timing Analyzer and Signal Tap chapters, at Lab 12 and Final.
- IEEE 1076 / `numeric_std` package reference — for Lab 5, when someone asks what `shift_right` does to a `signed`.
- MIPS instruction reference: use **COD 5th ed.'s reference card** (inside the local PDF) plus your own `Documentation/Instruction Set Summary.pdf`. Do not send students to arbitrary online MIPS references — encodings differ between MIPS revisions and yours is authoritative for this CPU.

---

## 4. Per-lab reading assignment

Short, specific, and actually checkable. One reading per lab, ~10 pages.

| Lab | Assigned reading | Optional |
|---|---|---|
| 0 | H&H Ch. 4.1–4.3 (HDL basics) | Nandland "Your First VHDL Program" |
| 1 | H&H Ch. 3.1–3.2 (latches and flip-flops) | Quartus workflow card + your recording |
| 2 | H&H Ch. 3.2–3.3; COD App. B (sequential elements) | VHDLwhiz on `generic` |
| 3 | H&H Ch. 2.8 + 5.2 (multiplexers) | Chu, on combinational coding style |
| 4 | COD Ch. 2.5–2.6 (representing instructions; sign extension) | fpgatutorial on `numeric_std` |
| 5 | COD Ch. 3.1–3.3; H&H Ch. 5.2 (arithmetic circuits) | H&H Ch. 5.2.4 (prefix adders) for the stretch |
| 6 | H&H Ch. 5.5 (memory arrays / register files) | COD Ch. 4.2 |
| 7 | COD Ch. 2.7 + 4.3 (branch addressing, datapath) | H&H Ch. 7.3 |
| 8 | COD Ch. 2.8–2.10 (jumps, procedures, addressing modes) | — |
| 9 | COD Ch. 5.1–5.2 (memory technology) | H&H Ch. 8.1–8.2 |
| 10 | COD Ch. 4.4 (a simple control implementation); H&H Ch. 7.3 | Your `Decode Logic Table.pdf` |
| 11 | COD Ch. 4.4 continued | `Control Signals.pdf` (authoritative) |
| 12 | COD Ch. 4.4; H&H Ch. 7.3 end to end | COD Ch. 1.6 (performance) for the stretch |
| Final | COD Ch. 4.5–4.6 (pipelining) for track C | H&H Ch. 7.5 |

---

## 5. Overleaf / LaTeX support

Students who have never used LaTeX will lose lab time to it if you do not pre-empt this.

**Provide in week 1:**
- The complete template project, shared as an Overleaf **template link** so each student clicks once and gets their own copy. Do not make them build the structure.
- A 1-page "LaTeX for this report" card: `\lstinputlisting` for VHDL, `\includegraphics` for waveforms, `figure` with `\caption` and `\label`, `\ref`, and the three errors they will hit (missing `$`, unescaped `_`, missing image file).
- A worked `lab00.tex` filled in with one of the Lab 0 examples, as the model chapter.

**Configure for them** (in `preamble.tex`, so nobody debugs it):
- `listings` with a VHDL language definition, line numbers, and a small monospace font.
- Page geometry and a `\vhdlfile{}{}` macro wrapping `\lstinputlisting` with a caption, so a code listing is one line in their `.tex`.
- Figure defaults sized for waveform screenshots (full text width).

**Tell them explicitly:** screenshots must be **PNG at full resolution**, cropped to the signals that matter, with signal names legible. A blurry full-screen Questa capture is the most common way this report loses points, and it is entirely avoidable.

---

## 6. Canvas module structure

Mirror the folder structure so nothing goes missing:

```
Module: Course Resources (pinned, always visible)
  ├── Lab syllabus and policies
  ├── Quartus/Questa Workflow Card  (PDF)
  ├── Quartus install guide + NMSU license note
  ├── Flow walkthrough recording
  ├── Overleaf template link
  ├── LaTeX card
  └── EE 362 Green Sheet (from Lab 7 onward)

Module: Lab N  (published the Wednesday before)
  ├── Slides (PDF)
  ├── Pre-lab sheet  → due at session start
  ├── Assignment specification
  ├── Starter files (.zip: skeletons + testbench template + .qsf)
  ├── Reading (one link, one chapter)
  ├── Reference components from Lab N-1  (published after the late deadline)
  └── Submission: report PDF
```

---

## 7. Resource-related risks

| Risk | Mitigation |
|---|---|
| Install failures dominate week 1 | Push §2.3 before Lab 1; keep two verified lab PCs as fallback; run an install clinic in the first office hour |
| Students never open the books | Assign one specific 10-page reading per lab (§4) and ask one question about it during the check-off |
| Video rabbit-holes replace reading the spec | Say once, plainly: for Labs 10–12 the control table is the source of truth, not a video |
| Links rot mid-semester | Mirror the critical PDFs (install guide, green sheet, results guide) into the Canvas module rather than linking out |
| Overleaf free-tier collaboration limits | Each student owns their own project; no collaboration needed. Add yourself as a viewer only if you want to grade in-place. |

---

*Sources consulted for the online resources above:*
[NMSU College IT guides](https://college-it.nmsu.edu/guides/index.html) ·
[Quartus Prime Installation for Students at Home](https://college-it.nmsu.edu/guides/Quartus-Prime-Installation-for-Students-at-Home.pdf) ·
[Nandland](https://nandland.com/) ·
[Nandland YouTube](https://www.youtube.com/c/Nandland/videos) ·
[Nandland — simulating FPGA designs](https://nandland.com/project-6-how-to-simulate-your-fpga-designs/) ·
[VHDLwhiz Basic VHDL Course](https://vhdlwhiz.com/basic-vhdl-tutorials/) ·
[FPGA Tutorial VHDL](https://fpgatutorial.com/vhdl/) ·
[getting-started-with-fpgas code](https://github.com/nandland/getting-started-with-fpgas)
