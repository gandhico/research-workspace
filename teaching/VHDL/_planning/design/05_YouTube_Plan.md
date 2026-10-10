# VHDL From Zero to a CPU — YouTube Series Plan
### Future work. This document exists so the lab material is built in a shape that makes it cheap later.

---

## 0. Before anything is published — three permissions

Flag these now, because they are cheap to resolve in September and expensive in December.

| # | Issue | Who decides |
|---|---|---|
| 1 | The CPU spine is **A.K. Petersen's NMSU EE362 material** (`Libraries/`, `Documentation/`, the ISA and block diagrams). Publishing derived material publicly needs his or the department's clearance. | Dr. Tang / department |
| 2 | Course handouts, slides and the ISA documents are **course material**, not yours alone. | Dr. Tang |
| 3 | **No student work, names, voices or screens** may appear, ever. | You — absolute rule |

**The safe path:** publish only material *you* authored — your examples, your testbenches, your explanations, your own generic components — and either get clearance for the CPU labs or rebuild that arc on a clean-room RISC-V or minimal-ISA design for the channel. Seasons 1 and 2 below are almost entirely your own work already.

---

## 1. Positioning — why this channel would be different

Most VHDL videos are either 90-minute lectures or 3-minute syntax clips with no verification. The gap in the market is exactly what this course already does:

> **Specification → truth table → Boolean equation → VHDL → simulation → back to the table.**
> Every episode. Same six beats. Nothing hand-waved, nothing "trust me".

Two things almost nobody else shows, and both are free to you because the labs already do them:

- **The deliberate bug.** Every lab has one — the incomplete sensitivity list, the inferred latch, the per-bit contention. Showing a thing *break* and then diagnosing it is far more watchable and far more useful than showing something work first time.
- **Self-checking testbenches.** Most tutorials eyeball a waveform. Yours assert. "The transcript says `PASS — all 16 checks passed`" is a satisfying, honest ending beat.

**Channel promise, one line:** *Short, complete, reproducible hardware design. Every file shown in full. Every result verified.*

---

## 2. Episode format — strict, so production gets cheap

**Length: 6–9 minutes. Never over 10.** One component per episode. If it does not fit, it is two episodes.

### The beat sheet

| Time | Beat | On screen |
|---|---|---|
| 0:00–0:15 | **Cold open: the result first** | The finished waveform, or the transcript printing `PASS`. No intro, no logo, no "hey guys". |
| 0:15–0:45 | **The specification** | The truth table, full screen, static |
| 0:45–1:30 | **The equation** | Canonical → simplified, with the law named |
| 1:30–4:00 | **The code** | Full file, revealed in chunks; equation stays visible in a corner |
| 4:00–5:30 | **Simulate** | Run, read the transcript, read the waveform against the table |
| 5:30–6:30 | **Synthesise** | RTL Viewer, and exactly one report number |
| 6:30–7:15 | **The trap** | Break it deliberately, show the symptom, diagnose it |
| 7:15–7:45 | **Your turn** | The extension problem + repo link |

The cold open matters most. Fifteen seconds showing the finished waveform answers "why am I watching this" before anyone can leave.

### Rules that make it pausable — this is the whole design goal

The stated goal is that viewers *pause and reproduce*. That imposes hard constraints:

1. **Every file appears in full, static, for at least 4 seconds.** No scrolling while talking over it. Scroll first, then stop and hold.
2. **No jump cuts inside code.** A cut mid-file makes reproduction impossible.
3. **Code at 22 pt minimum**, dark theme, 100-column max. Assume a phone screen.
4. **An on-screen `⏸ PAUSE AND TYPE THIS` badge** before each reproduce point. Say it out loud too.
5. **Show every click that matters.** If a menu path is needed, show the menu. Never "and then I set up the simulation".
6. **Persistent corner card** with the current file name and the equation being implemented.
7. **No background music under code or explanation.** Music only under the cold open and the outro.

### Fixed layout

```
┌──────────────────────────────┬───────────────────┐
│                              │  spec / equation  │
│   CODE or WAVEFORM (2/3)     │  (1/3, static)    │
│                              ├───────────────────┤
│                              │  file name        │
└──────────────────────────────┴───────────────────┘
```

Keeping the specification visible while the code is on screen is the single highest-value framing decision: it is the whole thesis of the course, made visual.

---

## 3. Series map

Three seasons, mapped onto lab material that already exists.

### Season 1 — VHDL From Zero (Labs 0–4) · ~16 episodes
Entirely your own material. **Start here.**

| # | Episode | From |
|---|---|---|
| 1 | What an entity and an architecture actually are | Lab 0 |
| 2 | Your first circuit: majority-of-three | Lab 0 |
| 3 | Truth table → Boolean equation → VHDL, the whole loop | Lab 0 |
| 4 | The Quartus flow, end to end, nothing skipped | Lab 1 e1 |
| 5 | Writing a testbench that actually checks | Lab 1 |
| 6 | The transparent latch: where memory comes from | Lab 1 |
| 7 | **The sensitivity list bug that passes synthesis** | Lab 1 e3 |
| 8 | Two latches make an edge: the master–slave flip-flop | Lab 2 e1 |
| 9 | The same flip-flop, behaviourally — and why you'd ship that one | Lab 2 e2 |
| 10 | Generics: one entity, every width | Lab 2 e3 |
| 11 | Multiplexers three ways, and how to choose | Lab 3 e1 |
| 12 | **The inferred latch: your combinational circuit has memory** | Lab 3 e3 |
| 13 | `'Z'` is not a Boolean value | Lab 4 e1 |
| 14 | Sign vs zero extension, and why `ADDI` cares | Lab 4 e2 |
| 15 | `numeric_std`: the conversion chain you'll type 100 times | Lab 4 e3 |
| 16 | Season 1 recap: the six-beat loop | — |

### Season 2 — Building a Datapath (Labs 5–9) · ~14 episodes
ALU, register file, address generation, memory. Mostly your own components; check permission on the ISA specifics.

### Season 3 — Building a CPU (Labs 10–12 + Final) · ~10 episodes
Decoder, integration, running a real program. **Needs clearance (§0)** or a clean-room rebuild.

**Flagship episode:** *"My CPU computes 2¹⁰"* — the Lab 12 trace, 45 cycles, register 2 ending at `0x400`. That is the video that justifies the whole series, and it should be the one you cut most carefully.

---

## 4. Production toolchain — all free, all Windows

| Job | Tool | Setup notes |
|---|---|---|
| **Screen recording** | **OBS Studio** | Record at **2560×1440**, deliver 1080p. Recording above delivery gives you room to punch in on small text without it going soft. |
| **Audio** | Any USB cardioid mic + OBS noise suppression | Audio quality matters more than video quality. A phone mic in a quiet room beats a good mic in a echoey one. |
| **Editing** | **DaVinci Resolve** (free) | Cuts, zoom-ins, the corner card, captions. Overkill but free and it will not run out of headroom. |
| **Code display** | **VS Code**, dark theme, 22 pt, minimap off | Quartus's editor is not legible on a phone. Show code in VS Code, then switch to Quartus for the flow. |
| **Simulation demos** | **Questa CLI + a `.do` script** | See below — this is the biggest production win available to you. |
| **Waveform** | Questa GUI, radix set per signal, cursor annotations | Crop tight. Never show 40 signals. |
| **Diagrams** | draw.io or Excalidraw, exported SVG | Consistent style; reuse across slides, handouts and video |
| **Thumbnails** | Canva template | One template, swap the component name and one image |
| **Captions** | YouTube auto, then correct | Non-native speakers are a large share of this audience — corrected captions materially widen reach |

### The scripted-simulation trick

Do not click through the Questa GUI on camera for the pass/fail beat. Put a `run.do` next to each episode's files:

```tcl
# run.do — one command, three seconds, clean transcript
vlib work
vcom -quiet -2008 TransLatch.vhd TransLatch8.vhd tb_TransLatch.vhd
vsim -c -quiet work.tb_TransLatch -do "run -all; quit -f"
```

```bash
vsim -c -do run.do
```

This is already exactly how every lab in this repo was verified, so the scripts exist. On camera it gives you a three-second, deterministic, repeatable beat that ends with `PASS — all 20 checks passed`. Reproducible for viewers too: one command, no GUI state, no version drift.

**Use the GUI only for what the GUI is uniquely good at:** the waveform and the RTL Viewer.

### Legibility check before every upload

Watch the cut **on your phone, at arm's length**. If any code line is not comfortably readable, the font was too small. This one habit prevents the most common failure of engineering-tutorial channels.

---

## 5. The reproducibility kit

A public repo is what converts a viewer into someone who actually builds it.

```
vhdl-from-zero/
├── README.md                  # what this is, tool versions, how to run
├── ep01_entity_architecture/
│   ├── src/*.vhd              # every file shown, complete
│   ├── run.do                 # the exact command from the video
│   ├── expected_output.txt    # what a correct run prints
│   └── README.md              # spec table, equation, the extension problem
├── ep02_.../
└── TOOLS.md                   # Quartus Lite + Questa install, versions pinned
```

Two rules:
- **`expected_output.txt` in every episode.** A viewer who runs it and gets different text knows immediately that something is wrong — that is worth more than any amount of narration.
- **Pin tool versions** in `TOOLS.md` (Quartus Prime Lite 25.1std, Questa Intel FPGA Starter). Tutorials rot when versions drift silently.

The lab folders are already in almost exactly this shape. Exporting an episode is close to a copy.

---

## 6. Cadence and metadata

- **One episode per week**, same day. Consistency beats volume for a channel this technical.
- **Record in batches of four.** Setting up lighting, audio levels and OBS scenes is most of the overhead; amortise it.
- **Titles:** state the thing, not the hype. *"The VHDL sensitivity list bug that passes synthesis"* beats *"VHDL MISTAKE everyone makes!!"* — and it attracts the viewers who will stay.
- **Chapters in every description**, matching the beat sheet. People re-watch one beat.
- **Pinned comment** on every video: repo link + the extension problem restated.
- **Description ends with the next episode's question**, so the series pulls forward.

---

## 7. What to build first — the pilot

Do **not** start at episode 1. Start at **episode 7, the sensitivity-list bug.**

Reasons: it is self-contained, it needs no prior episode, it has a genuine surprise, the material and both testbenches already exist and are verified, and it is the single most useful five minutes in Season 1. If the format works there, it works everywhere.

**Pilot checklist:**
- [ ] Record ep 7 twice — once to find the pacing, once to keep. Discard the first.
- [ ] Cut it, watch it on a phone, note every unreadable frame.
- [ ] Show it to two students who have done Lab 1 and ask one question: *"could you reproduce this without pausing more than twice?"*
- [ ] Only then build the OBS scene collection, the Resolve template, and the thumbnail template.

Everything above is future work. Nothing in the lab material needs to change to enable it — the six-beat structure, the deliberate bugs, the self-checking testbenches and the `run.do` scripts are already there because the labs were built that way.
