# EE 362 — Teaching Script: Lab 0 and Lab 1
## VHDL design · testbench · simulation · waveform analysis

**Use:** read it once completely before class. In the lab, follow the headings and the **SAY** blocks.
Sentences are short on purpose, so they are easy to say aloud and easy for students to follow.

| Label | Meaning |
|---|---|
| **SAY** | Say it close to word for word. |
| **DO** | What you do on the projector while you talk. |
| **ASK** | Ask the room and wait 5 seconds. The expected answer follows. |
| **WATCH** | The mistake students usually make at this point. |

All tool results quoted here (warnings, register counts, times) were measured with **Quartus Prime Lite 25.1std** and **Questa**, device **5CSEMA4U23C6**.

---

# Part 0 — Get the definitions right first

Students will repeat your words for the whole semester. Use these definitions every time, with the same wording.

## 0.1 The two parts of every VHDL design

| Word | Definition to say |
|---|---|
| **entity** | *"The outside of the block: its name and its pins."* |
| **architecture** | *"The inside of the block: what it does or how it is built."* |
| **signal** | *"A wire."* |
| **`<=`** outside a process | *"A connection that is always active, not a line that runs once."* |

## 0.2 Three views of one circuit

This is the idea behind Lab 0 Example 1 and Example 3.

| View | Question it answers | In our tools |
|---|---|---|
| **Behavioural** | *What does the circuit do?* | VHDL: an equation, `when/else`, `with/select`, `process` with `if/case` |
| **Structural** | *Which blocks are used, and how are they connected?* | VHDL: components connected with `port map` |
| **Schematic** | *What does the circuit look like as a drawing?* | Quartus Block Editor (`.bdf`), and the **RTL Viewer** |

**SAY**
> *"One circuit can be described in three ways. Behavioural says **what** it does. Structural says **which parts** it uses and **how they are connected**. The schematic is the **drawing** of those parts. All three can describe exactly the same hardware. Your job is to choose the view that explains your design best."*

## 0.3 Four ways to write it in VHDL: be precise here

Students will read textbooks, so the words must match what textbooks say.

| Style | Example | What to call it |
|---|---|---|
| A. Boolean equation | `Y <= (A and B) or (A and C) or (B and C);` | **behavioural (dataflow)** |
| B. Condition or selection | `Y <= D0 when S = '0' else D1;` · `with A select` | **behavioural** |
| C. One signal per gate | `AB_s <= A and B; … Y <= AB_s or AC_s or BC_s;` | **gate-level**: structural *in shape*, written with operators |
| D. Components and port map | `HA1 : entity work.half_adder port map (…);` | **structural**, in the strict sense |

**SAY** (when you show the `_str` files in Lab 0)
> *"This file has one signal for each gate, so it has the same shape as the schematic. That is why we call it the structural version. In the strict sense, structural VHDL means connecting **components** with port map. You will see that in the full adder, and in Lab 2 you build a flip-flop from two copies of your Lab 1 latch."*

**Why this matters:** style C and style D produce the same hardware, but only D is reusable. If a student says "structural means I used `and` and `or`", correct them gently.

## 0.4 Words about verification

| Word | Definition to say |
|---|---|
| **testbench** | *"VHDL that exists only in simulation. It has no pins. It drives inputs and checks outputs."* |
| **stimulus** | *"The inputs we apply."* |
| **assertion** | *"A check that prints an error if the output is wrong."* |
| **waveform** | *"The picture of all signals over time. It is evidence."* |
| **transcript** | *"The text log. The PASS or FAIL line is the proof."* |
| **RTL simulation** | *"Simulating the VHDL we wrote."* |
| **gate-level simulation** | *"Simulating the netlist Quartus built after compilation."* |
| **RTL Viewer** | *"The schematic Quartus drew from our code. It shows what the tool understood."* |

**Sentence to repeat all semester**
> *"A waveform is evidence. An assertion is proof."*

---

# Part 1 — Lab 0: VHDL fundamentals

**Examples:** Ex 1 majority of three (three views) · Ex 2 2-to-1 multiplexer · Ex 3 2-to-4 decoder (four forms) · Ex 4 full adder (true structural, optional)

**Files** (`Lab_0/examples/`):

| Ex | Files |
|---|---|
| 1 | `e1_majority3_beh.vhd` (behavioural), `e1_majority3_str.vhd` (gate-level), `schematic1.bdf` (schematic), `majority3_tb.vhd` (no checks), `tb1_majority3_beh.vhd` / `tb1_majority3_str.vhd` (with asserts), `schematic1_tb.vhd` |
| 2 | `2e_2t1_multiplexer_beh.vhd`, `2e_2t1_multiplexer_str.vhd`, `2e_2t1_multiplexer_tb.vhd` |
| 3 | `decoder_st.vhd` (equations), `decoder.vhd` (`with/select`, **has the enable bug**), `03_decoder_2to4_enable.vhd` (`process if/case`), `decoder_c.vhd` (`process` with default), `decoder_tb.vhd` |
| 4 | `half_adder.vhd`, `full_adder_beh.vhd`, `full_adder_str.vhd`, `full_adder_tb.vhd` |

---

## 1.1 The workflow, before any code (3 min)

**DO:** write this line on the board and leave it there.

```
specification → truth table → Boolean equation → schematic → VHDL
      → testbench → simulation → waveform + transcript → RTL Viewer → back to the table
```

**SAY**
> *"This is the method for the whole semester. We do not start with code. We start with what the circuit must do, and we write the truth table. The code comes in the middle. At the end, we go back to the truth table and check every row."*

**ASK:** *"Why do we go back to the truth table at the end?"*
Expected: *"To check that the circuit does what the specification says."*

---

## 1.2 Quartus project, live (7 min)

**SAY**
> *"Type along with me. Do not copy and paste. If you fall behind, tell me and I will wait."*

**DO**, slowly, saying each step aloud:

1. `File → New Project Wizard`
2. Folder: a short path with **no spaces** and **not in OneDrive**, for example `C:\ee362\lab00_e1`.
3. Project name. Top-level entity: **exactly** the entity name in the VHDL file.
4. Family **Cyclone V**, device **5CSEMA4U23C6**.
5. EDA Tool Settings → Simulation: **Questa Altera FPGA (VHDL)**, format **VHDL**.
6. `File → New → VHDL File`, then save it with the **same name as the entity**.

**WATCH:** the top-level entity name does not match the entity in the file. The error is *"Top-level design entity … is undefined"*. Read it aloud and fix it together.

---

## 1.3 Example 1 — Majority of three: three views of one circuit (35 min)

### Step 1 — Specification and truth table (4 min)

**SAY**
> *"Specification: three inputs A, B and C, one output Y. Y is 1 when two or more inputs are 1. Like a vote with three people."*

**DO:** write the table on the board and **number the rows**.

| # | A | B | C | Y |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 0 | 1 | 0 |
| 2 | 0 | 1 | 0 | 0 |
| 3 | 0 | 1 | 1 | **1** |
| 4 | 1 | 0 | 0 | 0 |
| 5 | 1 | 0 | 1 | **1** |
| 6 | 1 | 1 | 0 | **1** |
| 7 | 1 | 1 | 1 | **1** |

**SAY**
> *"Always number the rows. In your report you will write 'row 5 is correct', not a paragraph."*

### Step 2 — Boolean equation, with the law named (4 min)

**DO:** write the three lines.

```
(1) canonical   Y = Σm(3,5,6,7) = A'BC + AB'C + ABC' + ABC
(2) simplified  add ABC two more times          (idempotent law:  X = X + X)
                = BC(A'+A) + AC(B'+B) + AB(C'+C)  (distributive law)
                = AB + AC + BC                   (complement law: X + X' = 1)
(3) VHDL        Y <= (A and B) or (A and C) or (B and C);
```

**SAY**
> *"Line two must name the law. 'It simplified' is not a derivation."*

**ASK:** *"Does Y appear on the right side of its own equation?"*
Expected: *"No."*
**SAY:** *"Correct. So this circuit has no memory. Remember this question. In Lab 1 the answer becomes yes."*

### Step 3 — View 1: behavioural (5 min)

**DO:** open `e1_majority3_beh.vhd`.

```vhdl
entity majority3 is
  port ( A : in std_logic; B : in std_logic; C : in std_logic;
         Y : out std_logic );
end majority3;

architecture behavioral of majority3 is
begin
  Y <= (A and B) or (A and C) or (B and C);
end architecture behavioral;
```

**SAY** (point at each part)
> *"`library` and `use` make `std_logic` available. The entity is the outside: three input pins and one output pin. The architecture is the inside. This single line is the equation from the board. It is not a program that runs once. It is hardware that is always connected: when A, B or C changes, Y changes."*

**DO:** Analysis & Elaboration, then **Tools → Netlist Viewers → RTL Viewer**.

**SAY**
> *"This is what Quartus understood from our line. Count the gates. Three ANDs and one OR, the same as our equation. This check takes ten seconds. Do it every time."*

### Step 4 — View 2: structural, gate level (5 min)

**DO:** open `e1_majority3_str.vhd`.

```vhdl
architecture structural of majority3_structural is
  signal AB_s, AC_s, BC_s : std_logic;   -- three internal wires
begin
  AB_s <= A and B;                        -- gate 1
  AC_s <= A and C;                        -- gate 2
  BC_s <= B and C;                        -- gate 3
  Y    <= AB_s or AC_s or BC_s;           -- gate 4
end architecture;
```

**SAY**
> *"Same circuit, different view. Now every internal wire has a name, and every line is one gate. If I draw one box per line, I get the schematic. That is the structural idea: the parts, and how they connect. Strictly, structural VHDL uses components, and we will see that in Example 4. This file has the same shape."*

**ASK:** *"Will Quartus build different hardware for these two files?"*
Expected: *"No, the same hardware."*
**DO:** show both RTL Viewers side by side. **SAY:** *"The code is different. The hardware is the same."*

### Step 5 — View 3: schematic in the Block Editor (10 min)

**SAY**
> *"The third view is a drawing. Quartus lets us design by drawing gates. That file is called a Block Diagram File, `.bdf`."*

**DO**, step by step:

1. `File → New → Block Diagram/Schematic File`.
2. Double-click the empty canvas to open **Symbol**. Choose `primitives → logic → and2`. Place three. Then `or3`, and place one.
3. Pins: `primitives → pin → input` three times, `output` once. Double-click each pin to rename it **A, B, C, Y**.
4. Connect with the **Orthogonal Node Tool**. A dot appears where wires really connect.
5. Save as `schematic1.bdf`, then **Project → Set as Top-Level Entity**.
6. Start Compilation.

**SAY**
> *"Look: the drawing is exactly the gate-level file. Same three ANDs, same OR. So we now have three views of one circuit: an equation, a list of gates, and a drawing."*

**WATCH:**
- Wires that look connected but have no dot are **not** connected.
- A pin name that does not match the testbench (`y` versus `Y` is fine in VHDL, but `Y1` is not).

### Step 6 — Which view is best? (2 min)

**SAY**
> *"Which one should you use? Behavioural when the specification is a rule or an equation: it is short and clear. Structural when you connect parts you already built: it is how we will build the processor. Schematic to explain and to check: we draw it, and the RTL Viewer draws it for us. For this circuit, behavioural is best, because the equation is one line. The other two are here so you can see that all three views are the same hardware."*

### Step 7 — Testbench, first without checks (5 min)

**DO:** open `majority3_tb.vhd`, the class version without asserts.

**SAY** (point at each part)
> *"A testbench is VHDL that exists only in simulation. Look: the entity has no ports. It is a closed box. Inside, we declare signals with the same names as the pins. We place the circuit, called the DUT, the design under test, and we connect it with port map. Then one process applies the eight rows. Each row lasts 10 nanoseconds. The last `wait;` with no time stops the process. Without it, the process starts again forever."*

**DO:** configure the testbench (say every click):
`Assignments → Settings → EDA Tool Settings → Simulation → Compile test bench → Test Benches… → New` → test bench name **majority3_tb**, top-level module **majority3_tb**, add the file `majority3_tb.vhd` → OK.
Then `Tools → Run Simulation Tool → RTL Simulation`.

### Step 8 — Waveform analysis (7 min)

Use the same routine for every waveform in the course (see Part 3).

**SAY**
> *"Before we look at any signal, we check the time. Eight rows at 10 nanoseconds each is 80 nanoseconds. Look at 'Now' at the bottom: 80 ns. So all eight rows ran."*

**DO:** `View → Zoom → Zoom Full`. Put the cursor **in the middle** of each 10 ns window, and read the values in the **Msgs** column.

**SAY** (walk through the windows)
> *"Row i lives between 10i and 10i + 10 nanoseconds. From 0 to 30, fewer than two inputs are 1, and Y is low. At 30 to 40, B and C are 1: row 3, and Y is high. At 40 to 50, only A is 1: row 4, and Y is low. From 50 to 80, Y is high: rows 5, 6 and 7. That matches the table exactly."*

**WATCH:** students place the cursor exactly **on** a transition edge and read the old value. Always read in the **middle** of a window.

**ASK:** *"We read the waveform and it looked correct. Is the design verified?"*
Wait for answers, then:

**SAY**
> *"Not really. We checked it with our eyes, and eyes only confirm what we already expect. If this circuit had eight rows, or eighty, we would miss a mistake. So now we add the proof."*

**DO:** open `tb1_majority3_beh.vhd` and point at one check:

```vhdl
A <= '0'; B <= '1'; C <= '1';
wait for 10 ns;
assert Y = '1' report "Error 011" severity error;
```

**SAY**
> *"We change the inputs, we wait so that the circuit can respond, and then we check. If Y is wrong, the transcript prints 'Error 011'. The wait must come **before** the assert. If we check immediately, we read the old value."*

**DO:** run it. Show the final note in the transcript and `Errors: 0`.

**SAY**
> *"A waveform is evidence. An assertion is proof. From today, every testbench you submit checks itself."*

### Step 9 — Simulating the schematic (3 min)

**SAY**
> *"The simulator reads VHDL, not drawings. So for the schematic, we let Quartus compile it first. Quartus then writes the netlist as a VHDL file, and we simulate that netlist. That is called gate-level simulation."*

**DO:**
1. Full compilation with `schematic1` as top level.
2. Test bench: `schematic1_tb`, file `schematic1_tb.vhd`.
3. `Tools → Run Simulation Tool → Gate Level Simulation`.

**SAY** (point at the component declaration in `schematic1_tb.vhd`)
> *"This testbench uses a component declaration. It tells the simulator the pins of `schematic1` before the netlist is compiled. The waveform is the same as the behavioural one: three views, one behaviour."*

Optional: `File → Create/Update → Create HDL Design File from Current File` turns the drawing into a VHDL file, and then RTL simulation works too.

---

## 1.4 Example 2 — 2-to-1 multiplexer (10 min)

**SAY**
> *"A multiplexer is a switch controlled by a signal. S chooses which input goes to the output."*

**DO:** board.

| # | S | Y |
|---|---|---|
| 0 | 0 | D0 |
| 1 | 1 | D1 |

```
Y = S'·D0 + S·D1
```

**SAY**
> *"This table has only two rows, because the output column names a **source**, not a value. When S is 0, Y **is** D0, whatever D0 is. We use this short form for wide circuits. In Lab 3 the multiplexer is 32 bits wide, and a full table would be impossible to write."*

**DO:** show both styles.

```vhdl
Y <= D0 when S = '0' else D1;          -- behavioural: the specification as a condition
```
```vhdl
not_s <= not S;                         -- gate level: the equation as gates
w0 <= D0 and not_s;
w1 <= D1 and S;
Y  <= w0 or w1;
```

**SAY**
> *"The first line reads like the specification: 'D0 when S is 0, else D1'. The second shows the gates. Same hardware. For a choice, behavioural `when/else` is clearer."*

**DO:** run `2e_2t1_multiplexer_tb.vhd`. Waveform, window by window:

| Window | D0 | D1 | S | Y | Reading |
|---|---|---|---|---|---|
| 0–10 ns | 0 | 1 | 0 | 0 | S = 0, so Y = D0 = 0 |
| 10–20 ns | 0 | 1 | 1 | 1 | S = 1, so Y = D1 = 1 |
| 20–30 ns | 1 | 0 | 0 | 1 | S = 0, so Y = D0 = 1 |
| 30–40 ns | 1 | 0 | 1 | 0 | S = 1, so Y = D1 = 0 |

**ASK:** *"In every window D0 and D1 are different. Why did we choose the vectors like that?"*
Expected: *"If they were equal, we could not tell which input was selected."*

**SAY**
> *"Exactly. A good test vector can only pass if the circuit is correct. If D0 and D1 are equal, a broken multiplexer still gives the right answer."*

---

## 1.5 Example 3 — 2-to-4 decoder with enable: four forms (20 min)

### Step 1 — Specification, table and equations (5 min)

**SAY**
> *"A decoder turns a binary number into one active wire. Two address bits give four outputs, and exactly one output is 1. The enable E turns the whole decoder on or off."*

**DO:** board.

| # | E | A1 | A0 | D3 D2 D1 D0 |
|---|---|---|---|---|
| 0 | 0 | – | – | 0 0 0 0 |
| 1 | 1 | 0 | 0 | 0 0 0 1 |
| 2 | 1 | 0 | 1 | 0 0 1 0 |
| 3 | 1 | 1 | 0 | 0 1 0 0 |
| 4 | 1 | 1 | 1 | 1 0 0 0 |

```
D0 = E·A1'·A0'    D1 = E·A1'·A0    D2 = E·A1·A0'    D3 = E·A1·A0
```

**SAY**
> *"The dash means don't care. Row 0 says: when E is 0, the address does not matter, and all outputs are 0. That is a promise, and the testbench must check it. Rows 1 to 4 have exactly one 1. That is called one-hot. Each output is one minterm of the address, multiplied by E."*

### Step 2 — The four forms (8 min)

**DO:** show the files in this order, one or two sentences each.

| Form | File | How E is handled | Correct? |
|---|---|---|---|
| (a) Boolean equations | `decoder_st.vhd` | E is inside every AND term | ✔ |
| (b) Selected assignment `with … select` | `decoder.vhd` | **E is never used** | ✘ |
| (c) `process` with `if` then `case` | `03_decoder_2to4_enable.vhd` | `if en = '0'` checked first | ✔ |
| (d) `process` with default | `decoder_c.vhd` | `D <= "0000";` first, then `if E = '1'` | ✔ |

**SAY for (a)**
> *"Form (a) is the schematic written as text: two inverters and four AND gates with three inputs. E goes into every gate, so when E is 0 every output is 0."*

**SAY for (c)**
> *"Form (c) follows the specification in order: first ask 'is it enabled?', then decode the address. A process with `if` and `case` is **still combinational**, because there is no clock and D gets a value on every path."*

**SAY for (d)**
> *"Form (d) gives D a default value first. Then, only if E is 1, the case overwrites it. Because D always gets a value, this cannot create memory. It is a very safe habit."*

### Step 3 — Find the bug in form (b), live (6 min)

**DO:** open `decoder.vhd`. **Do not say there is a bug.**

```vhdl
A <= A1 & A0;
with A select
  D <= "0001" when "00",
       "0010" when "01",
       "0100" when "10",
       "1000" when "11",
       "0000" when others;
```

**ASK:** *"Look at the entity, then at the architecture. Is anything missing?"*
Wait. Someone will find it: **E is never used.**

**SAY**
> *"E is declared, but the architecture never reads it. So the decoder works even when it is disabled. And `when others` does not save us: it covers values like U and X on the address, which only exist in simulation. It does not cover E."*

**DO:** show the three pieces of evidence, in this order:

1. **Messages** after compilation:
   ```
   Warning (21074): Design contains 1 input pin(s) that do not drive logic
       Warning (15610): No output dependent on input pin "E"
   ```
   **SAY:** *"Quartus told us the bug before any simulation. Read your warnings."*
2. **RTL Viewer:** the pin E is not connected to anything.
3. **Waveform** from `decoder_tb.vhd`: in **0–10 ns**, E = 0 but **D = 1**, that is `0001`. In 10–50 ns, D = 1, 2, 4, 8, which is correct.
   **SAY:** *"Set the radix of D to hexadecimal: right-click, Radix, Hexadecimal. One-hot values in hexadecimal are 1, 2, 4, 8, which are easy to read."*

**ASK:** *"If the testbench had started with E = 1, would we have found this bug?"*
Expected: *"No."*

**SAY**
> *"A testbench can only find a bug in a row it actually applies. Every row of the table becomes a vector, including the boring one."*

### Step 4 — Fix it: two correct ways (1 min)

```vhdl
-- Fix 1: use form (c) or (d)

-- Fix 2: keep 'with select', but include E in the selection
EA <= E & A1 & A0;
with EA select
  D <= "0001" when "100",
       "0010" when "101",
       "0100" when "110",
       "1000" when "111",
       "0000" when others;   -- now 'others' also covers E = '0'
```

**SAY**
> *"Now `others` really means 'disabled or unknown'. Recompile. The warning disappears, and row 0 passes."*

---

## 1.6 Example 4 — Full adder: structural in the strict sense (10 min, optional)

**SAY**
> *"This is structural VHDL in the strict sense. We build a full adder from two half adders that we already have, and we connect them with port map."*

```vhdl
HA1 : entity work.half_adder port map ( A => A,  B => B,   S => S1,  C => C1 );
HA2 : entity work.half_adder port map ( A => S1, B => Cin, S => Sum, C => C2 );
Cout <= C1 or C2;
```

**SAY**
> *"Always use named association: `A => A`. Never positional order. When a component has seven ports, positional port maps create bugs that compile without any error."*

**ASK:** *"Cout is 1 when at least two of A, B and Cin are 1. Where have we seen that today?"*
Expected: *"The majority circuit."*
**SAY:** *"Yes. The first circuit of the course is the carry of an adder."*

---

## 1.7 Close Lab 0 (3 min)

**SAY**
> *"Today you saw one method. Specification, truth table, equation, schematic, VHDL, testbench, waveform, and back to the table. You saw that one circuit has three views, and that one decoder can be written in four forms, and one of them was wrong. Tonight, put the truth table, the derivation with the laws named, and one waveform in your Overleaf chapter. Under every figure, write one sentence that says what it proves."*

---

# Part 2 — Lab 1: design flow and the transparent latch

**Session plan (3:45–5:45):** 10 Open · 25 Guided examples · 10 Spec walk · 55 Build (hard checkpoint at 4:55) · 15 Check-off · 5 Close

**Files:** `Lab_1/examples/exe_1` (majority3 + table-driven testbench) · `exe_2` (trans_latch) · `exe_3` (trans_latch_bad + side-by-side testbench) · `Lab_1/assignment/` (TransLatch, TransLatch8, tb_TransLatch)

**Before class:** open each example project once and check the **top-level entity** and **device**. `exe_2/lab1_e2.qsf` has top level `de0_nano_soc_baseline`, and `exe_1`/`exe_3` use a different device. Set them to `majority3`, `trans_latch`, `trans_latch_bad` and `5CSEMA4U23C6`.

---

## 2.1 Open (10 min)

**DO:** write two equations on the board, one under the other.

```
Lab 0:   Y  = AB + AC + BC
Lab 1:   Q+ = Clr'·(En·D + En'·Q)
```

**ASK:** *"Find the difference."* Wait 10 seconds.
Expected: *"Q appears on the right side."*

**DO:** circle the last `Q`.

**SAY**
> *"That circle is the whole difference between combinational logic and memory. Everything in Lab 0 had no Q on the right. This circuit uses its own output to decide its next output, so it remembers. Today's one idea: an equation whose output appears on its own right-hand side is memory."*

**SAY** (the flow, point at a list on the board)
> *"Same loop as Lab 0, with the tool steps added: Analysis and Elaboration, does it parse. RTL Viewer, did I describe what I meant. Compilation. Messages and Flow Summary, what is Quartus worried about. RTL simulation, does it behave. Waveform and transcript, can I prove it."*

---

## 2.2 Guided examples (25 min)

### Example 1 — The flow on a circuit you already trust (6 min)

**SAY**
> *"We start with the majority circuit from Lab 0. Why an old circuit? Because we never learn a tool and a circuit at the same time. If something fails today, the circuit is already correct, so the problem is in the tool steps. One unknown only."*

**DO:** open `majority3_tb.vhd` in `exe_1`. Point at the table constant.

```vhdl
constant VECTORS : vector_array := (
    ('0','0','0','0'),      -- row 0
    ...
    ('1','1','1','1') );    -- row 7
```

**SAY**
> *"This is new: the truth table is stored as data inside the testbench. One loop applies every row, waits 10 nanoseconds, and compares Y with the table. When something fails, the message says 'row 5', and you look up row 5 on your table. In Lab 11 this table has 8 rows and 14 columns, and the loop is the same."*

**DO:** run it. Show:
```
# ** Note: PASS - majority3: all 8 rows correct.
#    Time: 80 ns
```

**SAY**
> *"Two checks. The PASS line. And the time: 80 nanoseconds, which is 8 rows times 10. If the time is different, the loop did not cover the table."*

**DO:** Flow Summary: **0 registers**. **SAY:** *"Zero registers, because nothing is stored. Remember this number. In ten minutes it becomes important."*

### Example 2 — The transparent latch (10 min)

**DO:** board, then `trans_latch.vhd`.

| # | En | D | Q+ | |
|---|---|---|---|---|
| 0 | 0 | – | **Q** | hold, the memory row |
| 1 | 1 | 0 | 0 | transparent |
| 2 | 1 | 1 | 1 | transparent |

```
Q+ = En·D + En'·Q
```

**SAY**
> *"Q-plus means the next value. A Q in the output column means 'keep the old value'. Now look at the equation. It is the multiplexer from Lab 0: En is the select, D is one input, and the other input is Q, the output itself. A latch is a multiplexer with its output connected back to its input."*

```vhdl
process (En, D)
begin
    if En = '1' then
        Q <= D;
    end if;          -- no else
end process;
```

**SAY**
> *"There is no else. When En is 0, nothing assigns Q, so Q keeps its value. That is row 0. In VHDL, memory is what you get when you leave a case without an assignment. Today we want it. In almost every other lab we will not, and it is the most common bug of the semester. You are seeing it on purpose, on day one."*

**DO:** run `trans_latch_tb.vhd`. **Waveform analysis of memory**: draw this timeline on the board while the waveform is visible.

| Time | En | D | Q expected | What it proves |
|---|---|---|---|---|
| 0–10 | 1 | 0 | 0 | transparent |
| 10–20 | 1 | 1 | 1 | transparent |
| 20–30 | **0** | 1 | 1 | the latch closes |
| 30–40 | 0 | **0** | **1** | **hold: D changed, Q did not** |
| 40–50 | **1** | 0 | 0 | reopened: Q follows D again |

**DO:** place the cursor at **35 ns**. Read the Msgs column: En = 0, D = 0, Q = 1.

**SAY**
> *"This is the most important moment of the waveform. D went down, and Q stayed up. That is memory. A plain wire would follow D. This window is the picture for your report."*

**ASK:** *"Why does the testbench close the latch at 20 and change D at 30, not both at 20?"*
**SAY:** *"If data changes at the same instant the latch closes, real hardware may store either value. Separate the events. Keep that habit when clocks arrive next week."*

**SAY** (the check table, measured)
> *"We tried this testbench on wrong circuits. A plain wire passes three checks and fails only the hold check. An AND gate, which is what you get if you add `else Q <= '0'`, also fails only the hold check. So without the hold vector, a wire passes your testbench."*

**DO:** Quartus evidence:
- Messages: `Warning (10631): … inferring latch(es) for signal or variable "Q" …`
  **SAY:** *"Usually this warning means you forgot a branch. Today it confirms the design is right."*
- Compilation Report → Analysis & Synthesis → **User-Specified and Inferred Latches**: `Q$latch`, enable signal **En**.
- Flow Summary: **0 registers**. **SAY:** *"A latch is not a register."*

### Example 3 — One missing name (9 min)

**DO:** show the one difference.

```
trans_latch      process (En, D)
trans_latch_bad  process (En)
```

**SAY**
> *"The body is identical. Rule: the sensitivity list must contain every signal the process **reads**. This process reads En and D."*

**ASK:** *"Predict: at 10 nanoseconds D changes while En is already 1. What does each latch do?"* Take two or three answers.

**DO:** run `sensitivity_compare_tb.vhd`.

| Time | En | D | Q_good | Q_bad |
|---|---|---|---|---|
| 0 ns | 1 (changes) | 0 | 0 | 0 |
| **10 ns** | 1 | **1 (changes)** | **1** | **0** |
| 20 ns | checks | | | |

Transcript: **exactly one error**, the expected one, at 20 ns.

**SAY**
> *"At 10 nanoseconds only D changed. The good process wakes up. The bad process only listens to En, so it sleeps, and Q_bad stays 0."*

**SAY** (what it really is)
> *"Think about the broken one. It only runs when En changes, and it copies D only if En is now 1. So Q changes only at the moment En goes from 0 to 1. That is not a broken latch. That is a flip-flop, clocked by En."*

**DO:** Flow Summary of `trans_latch_bad`: **Total registers: 1**, and **no warning**.

**SAY**
> *"We measured it. Quartus builds exactly that flip-flop: one register, and no warning at all. The correct latch prints a warning, and the broken one prints nothing. Silence does not mean correct. You expected zero registers, the report says one: you found the bug without running any vector."*

**SAY** (link to the assignment)
> *"Your starter file also has an incomplete list, but it has a Clr branch first. There, Quartus behaves differently. It prints Warning 10492, 'signal is read inside the Process Statement but isn't in the sensitivity list', and it builds the correct latch. So the hardware is right and your simulation is wrong. One missing name, two different failures. In both cases the testbench catches it."*

---

## 2.3 Spec walk (10 min)

**DO:** board.

| # | Clr | En | D | Q+ | |
|---|---|---|---|---|---|
| 0 | 1 | – | – | 0 | clear wins |
| 1 | 0 | 0 | – | Q | hold |
| 2 | 0 | 1 | 0 | 0 | transparent |
| 3 | 0 | 1 | 1 | 1 | transparent |

```
(1) Q+ = Clr'·En·D + Clr'·En'·Q
(2) Q+ = Clr'·(En·D + En'·Q)        [distributive law]
(3) if Clr = '1' then Q <= '0'; elsif En = '1' then Q <= D; end if;
```

**SAY**
> *"Clr is tested first, because row 0 comes first: the first matching row wins. Two parts. TransLatch, one bit. TransLatch8, eight bits. Clr and En stay one bit, and they are shared by all eight bits. Control signals are narrow, data is wide. For the cleared vector, write `(others => '0')`."*

**SAY**
> *"Your testbench must include: the hold vector, where En is 0 and D changes; clear while transparent; clear while holding; and one 8-bit pattern that is not all zeros or all ones. The sensitivity lists in the starter files are incomplete on purpose. Before you type anything, write the table and the equation on paper."*

---

## 2.4 Build (55 min)

**At exactly 4:55, stop the room. SAY:**
> *"Hands up if your design does not compile yet."*

Go to those students first.

**At 5:15, SAY:**
> *"Ten minutes. If it simulates, take your screenshots now. Do not leave without the waveform."*

**Common problems (measured symptoms):**

| Symptom | Cause | Say |
|---|---|---|
| The **first** check fails with Q = `U`; on the 1-bit latch checks 1, 3, 6, 7 and 9 fail (measured) | sensitivity list still `(En)` | *"Which signals does your process read?"* The failing checks name the missing signal: clear checks mean `Clr`, the D-tracking check means `D`. |
| Only the two checks with the latch closed and holding a 1 fail (vectors 4 and 5) | they wrote `else Q <= '0'` | *"Which row of the table is the missing else?"* |
| On the 1-bit latch the hold checks **pass** but the clear checks fail | broken sensitivity list: a stuck value looks like a held value (the 8-bit latch also fails 4 and 5) | *"A test can pass for the wrong reason."* |
| `Q <= '0'` does not compile in TransLatch8 | a bit assigned to a vector | *"Use `(others => '0')`."* |
| No PASS and no FAIL line | the testbench did not run as top level | *"Check the test bench name in the settings."* |
| Q is `U` at the start | nothing assigned yet | *"Normal before the first vector. Read from the first window."* |
| Timing Analyzer shows *Critical Warning 332148* | see 2.5 | *"Not a design error. Read 2.5."* |

---

## 2.5 How to read the evidence (say this while you walk the room)

**Flow Summary: Total registers = 0.**
> *"Correct. A latch is not a register. If you see 8 registers, you built a flip-flop."*

**Inferred latches report:** `Q[0]$latch` to `Q[7]$latch`, enable **En**.
> *"Eight latches for eight bits. Quartus found the enable signal by itself, and it matches your table."*

**RTL Viewer:**
> *"You see a latch symbol, with D on the data pin and En on the enable pin. If you see a plain gate, you wrote the else."*

**Timing Analyzer:**
> *"There is no clock constraint file, so Quartus invents a 1-nanosecond clock on En. There is no Fmax, because no path goes from one storage element to another. It may print 'Timing requirements not met'. That is a check against a clock nobody asked for. It is not a design error. Write that in your report. Real timing starts next week."*

**Waveform screenshot for the report:**
> *"Put the cursor inside the hold window, where En is 0, D changes, and Q stays. Under the figure, write one sentence that says what it proves."*

---

## 2.6 Check-off (15 min): the same two questions for everyone

**Question 1:** point at the hold window. *"Why does Q not change here, when D clearly changed?"*
- Full answer: *"En is 0, so it is row 1 of the table: the latch holds its value."*

**Question 2:** *"If I deleted Clr from your sensitivity list, would the simulation change? Would the hardware?"*
- Full answer: *"The simulation yes: the process would not react to Clr alone. The hardware no: Quartus warns (10492) and still builds the latch. It is a simulation–synthesis mismatch."* (Verified on Quartus 25.1.)

If they cannot answer:
> *"Have a look at that, and come find me before you leave."*

---

## 2.7 Close (5 min)

**SAY**
> *"Tonight, ten minutes: put the table and the three-line derivation in Chapter 1, add the hold waveform with one sentence, and write in the Discussion which bug you hit and which vector caught it. The chapter is due at the checkpoint. The memory is due tonight. Next week we connect two of these latches with opposite enables, and we get an edge."*

---

# Part 3 — Waveform analysis: the routine for every lab

Teach it once in Lab 0, then repeat it every week in the same order.

| Step | Do | Say |
|---|---|---|
| 1 | Read **Now** at the bottom | *"Vectors × step = expected end time. Did everything run?"* |
| 2 | Read the **transcript** | *"PASS or FAIL? How many errors?"* |
| 3 | **Zoom Full**, and set the radix (hexadecimal for vectors) | *"See the whole run, in readable numbers."* |
| 4 | Cursor in the **middle** of each window | *"Never on an edge."* |
| 5 | Read inputs → find the row → compare the output | *"Row i lives between 10i and 10i + 10."* |
| 6 | Explain any `U` or `X` | *"U: not assigned yet. X: two drivers, or unknown."* |
| 7 | Choose **one** window that proves the key idea | *"Hold window, disabled row, select change."* |
| 8 | Screenshot with the cursor there, plus **one sentence** | *"What does this figure prove?"* |

Questa tips to show once:
- Values at the cursor appear in the **Msgs** column.
- Right-click a bus → **Radix → Hexadecimal**.
- `restart -f` then `run -all` re-runs without closing Questa.
- Add a divider or change signal order so the inputs are above the outputs.

---

# Part 4 — Answers to questions students always ask

| Question | Answer |
|---|---|
| *"Is VHDL a programming language?"* | *"It looks like one, but it describes hardware. Ask: what circuit does this line create?"* |
| *"Why does a process not mean sequential logic?"* | *"Sequential means memory. A process with a value on every path and no clock is combinational."* |
| *"Behavioural or structural: which is better?"* | *"Behavioural for a rule or equation. Structural to connect parts you already built. Same hardware."* |
| *"Why `std_logic` and not `bit`?"* | *"`std_logic` has U and X. They show you uninitialized and conflicting signals. `bit` would hide them."* |
| *"The waveform looks right. Why do I need asserts?"* | *"Your eyes confirm what you expect. The assert checks what the table says."* |
| *"Why do I need `when others`?"* | *"A std_logic vector also has values like U and X. `others` covers them. It does not replace a real case, like the enable."* |
| *"What is the difference between RTL and gate-level simulation?"* | *"RTL simulates your code. Gate-level simulates the netlist Quartus built after compilation."* |
| *"Quartus shows critical warnings. Did I fail?"* | *"Read them. No pin location and no .sdc file are expected this semester. Warnings about your own signals are not."* |

**Phrases for difficult moments**

| Situation | Say |
|---|---|
| *"Can you fix my code?"* | *"Read me the error message out loud."* |
| A student is stuck and silent | *"Show me your truth table."* |
| It works, but they cannot explain it | *"Which line implements which term of your equation?"* |
| Time is almost over and nothing works | *"Compile, screenshot the error, and write the Discussion about it. A documented failure is worth more than a blank page."* |

---

# Part 5 — Ten sentences to memorize

1. *"Specification first, code in the middle, back to the truth table at the end."*
2. *"Behavioural says what it does. Structural says which parts and how they connect. The schematic is the drawing."*
3. *"Different code, same hardware: check it in the RTL Viewer."*
4. *"A waveform is evidence. An assertion is proof."*
5. *"Wait, then check. Never check in the same instant you change the input."*
6. *"A testbench can only find a bug in a row it actually applies."*
7. *"Read your warnings: Quartus found the enable bug before the simulation did."*
8. *"An equation whose output appears on its own right-hand side is memory."*
9. *"In VHDL, memory is what you get when you leave a case without an assignment."*
10. *"Silence is not correctness: the broken latch printed no warning."*
