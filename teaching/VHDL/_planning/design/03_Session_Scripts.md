# EE 362 Lab — Session Scripts
### What to say, 3:45–5:45

Print this. The **recurring script** is the same every week — learn it once and it stops costing you attention. The **per-lab delta** is ~150 words you read beforehand.

Text in *italics* is meant to be said close to verbatim. Everything else is stage direction.

---

## Part 1 — The recurring script (identical every week)

### 3:45 · Open (10 min)

> *"Last week you built \_\_\_\_. Today you build \_\_\_\_, and by the end of the semester it goes inside the processor, right here."* — point at the block diagram, which stays projected on the side screen all semester.
>
> *"Today's one idea is: \_\_\_\_."* — the single sentence from the lab's delta below. Say it once now, once at check-off, and nowhere else.
>
> *"Same loop as always: specification, truth table, Boolean equations, VHDL, simulation, and back to the truth table to check. Let's write the table."*

Put the table on the board yourself. Do not project it — projected tables are copied, written tables are watched.

### 3:55 · Guided example (25 min)

> *"Type along with me. Do not read ahead, do not copy-paste. If you fall behind, say so — I will wait."*

Compile it live. **Break it on purpose once**, every single week: delete a semicolon, or a `when others`, and read the actual error message aloud before fixing it. Students who have seen an error message being read calmly stop panicking at error messages.

### 4:20 · Spec walk (10 min)

Read the assignment aloud. Put the required equations on the board.

> *"Before you type anything: write the table and the equation on paper. If you cannot write the equation, you cannot write the VHDL — you will just be guessing at syntax, and I will be able to tell."*

### 4:30 · Build (55 min) — with a hard checkpoint at 4:55

At exactly 4:55, stop the room:

> *"Hands up if your design does not compile yet."*

This is the highest-leverage 30 seconds of the session. Students who are stuck and silent at 4:55 will not finish, and you will find out at 5:35 when it is too late to help. Go to those hands first.

At 5:15:

> *"Ten minutes. If it compiles and simulates, start your screenshots now — do not leave without the waveform."*

### 5:25 · Check-off (15 min)

Three boxes at the bench, 60 seconds per student: **compiles ✓ · testbench passes ✓ · can explain ✓**. Then two questions from the lab's delta below. Ask the same two questions to everyone, so it is fair and so you can compare answers.

If they cannot answer, do not fail them on the spot:

> *"Have a look at that and come find me before you leave."*

### 5:40 · Close (5 min)

> *"Tonight, before you forget it: paste your truth table and your three-line derivation into Chapter N. Add the waveform with one sentence saying what it proves. Ten minutes of work. The chapter is due at the checkpoint — the memory is due tonight."*
>
> *"Next week: \_\_\_\_."* — one sentence, from the next lab's delta.

### Checkpoint weeks only — add at Open

> *"Checkpoint N is Sunday at midnight. You submit the whole report so far, not just the new chapters. I read the new ones and I check that the previous comments got fixed. If your Discussion sections are empty, that is where you are losing points — write them this week."*

---

## Part 2 — Per-lab deltas

### Lab 1 — Design Flow and the Transparent Latch

**One idea:** *An equation whose output appears on its own right-hand side is memory.*

**Board moment.** Write `Q⁺ = C̄lr·(En·D + Ēn·Q)`, then circle the trailing `Q`.
> *"That circle is the entire difference between combinational logic and memory. Everything you built in Lab 0 had no Q on the right. This one does, so it remembers."*

Then show the VHDL with no `else`:
> *"In VHDL, memory is what you get when you leave a case undefined. Here we want it. Every other week we will not — and that is the bug you will hit all semester. Remember that you saw it on purpose, on day one."*

**Check-off questions**
1. Point at the waveform: *why does Q not change here, when D clearly changed?*
2. *If I deleted `Clr` from your sensitivity list, would the simulation change? Would the hardware?*

**Close:** *"Next week we take two of these latches, wire them with opposite enables, and get an edge."*

---

### Lab 2 — Master–Slave Flip-Flop and the N-Bit Register

**One idea:** *Two latches with opposite enables make an edge.*

**Board moment.** Draw both latches. Walk the clock through one full period with your finger:
> *"Clock is low. Master is transparent, so it follows D. Slave is holding. Clock goes high — master freezes on whatever D was at that instant, and the slave opens and copies it. The output can only ever change right there."* — tap the rising edge.
> *"Nobody designed an 'edge'. It fell out of two level-sensitive devices wired in opposition. That is how most of digital design works: the useful behaviour is emergent."*

**Check-off questions**
1. *Show me a point in your waveform where D changed and Q did not. Why not?*
2. *Your register is the same equation as last week's latch, renamed. Which signal became which?*

**Close:** *"Next week, multiplexers — the thing that lets one control bit steer thirty-two bits of data."*

---

### Lab 3 — Multiplexers

**One idea:** *A multiplexer is how a control signal steers a datapath — and why we need compressed tables.*

**Board moment.** Before anything else:
> *"A 32-bit 3-to-1 multiplexer has 98 inputs. How many rows does its exhaustive truth table have?"* — let them work it out — *"2⁹⁸. That is more rows than you have atoms in your body. Now watch."* — write the four-row compressed table — *"Four rows. Complete specification. This is not a shortcut; it is the reason datapath design is possible at all."*

Later, make them factor `S̄₁` out themselves. Do not hand it over — it is the first real simplification of the semester and it should cost them five minutes. Then show them what they built:
> *"Look at the bracket you just made. That is a 2-to-1 multiplexer. And the whole expression is a second 2-to-1 multiplexer choosing between that one and C. You factored an equation and a circuit came out. Factoring algebra and splitting a design into blocks are the same operation — that is the first time you will see it, and it will keep being true."*

**Check-off questions**
1. *Row 3 outputs zero. What did that let you delete from the canonical equation, and why?*
2. *Point at your four muxes on the CPU diagram. What does each one choose between?*

**Close:** *"Next week: the extender, and the one signal value that is not 0 and not 1."*

---

### Lab 4 — Extender, Tri-State, Shift Select

**One idea:** *`'Z'` is not a Boolean value — some hardware lives outside Boolean algebra.*

**Board moment.** Draw the 3×3 resolution table.
> *"Boolean algebra has two values. This table has four. That is why VHDL needs a resolved type, and it is why `'X'` in your waveform never means the simulator got confused — it means two drivers disagreed. When you see red next week, or in Lab 12, that is what it is telling you."*

**Check-off questions**
1. *Show me `0x8000` through your extender both ways. Why do the top sixteen bits differ?*
2. *You enabled both tri-states and got `'X'`. In a real chip, what would actually be happening?* (a short from supply to ground through two output transistors)

**Close:** *"Next week the ALU. It is large, but it is not hard: it is a multiplexer over function units, and you already built the multiplexer."*

---

### Lab 5 — Arithmetic Logic Unit

**One idea:** *An ALU is a multiplexer over function units. You already built the multiplexer.*

**Board moment.** Derive `SOLS = R₃₁ ⊕ V`:
> *"To find out whether A is less than B, subtract and look at the sign bit. Works every time — except when the subtraction overflows, and then the sign bit lies to you. So we XOR it with the overflow flag, which un-lies it. Two minutes of algebra, and now you know what overflow is actually for."*

Say the scope out loud so nobody panics at the function list:
> *"Fifteen functions sounds like a lot. Twelve of them are one line each. Budget your time for `SRA`, `SOLS`, and the wrapper — that is where the real work is."*

**Check-off questions**
1. *Run `SRA` on a negative number. What comes in at the top, and why is it not zero?*
2. *Your Fmax is \_\_\_ MHz. Which operation do you think is on the critical path?*

**Close:** *"Next week: thirty-two copies of your Lab 2 register, with an address decoder in front."*

---

### Lab 6 — Register File

**One idea:** *Thirty-two copies of your Lab 2 register, plus address decoding.*

**Board moment.** Before they touch anything:
> *"This lab looks big and it is not. Three things you already own: a decoder from Lab 0, a register from Lab 2, a multiplexer from Lab 3. Write the three equations, and then it is assembly."*

Write `We_k = Strb · m_k(Dsel) · [k ≠ 0]`, then:
> *"That last bracket is register zero. In MIPS, `$0` is always zero — not by convention that software politely follows, but because the hardware physically refuses to write it. It is one AND term. That is what 'hardwired' means."*

**Check-off questions**
1. *Try to write register 0 in your waveform. Show me it did not take.*
2. *You read a register in the same cycle you wrote it. Which value came out — old or new? Is that what you intended?*

**Close:** *"Next week we start the address side of the machine: the program counter."*

---

### Lab 7 — Next Instruction Address Generation I

**One idea:** *The PC is a register; everything else is address arithmetic.*

**Board moment.** Work the real `BLEZ` from the ROM program: `0x0C`, offset `+2`, NSA `0x10`, target `0x18`. Then two questions, answered:
> *"Why is the base PC-plus-4 and not PC? Because by the time we compute the branch, the fetch has already happened — the hardware has moved on. And why shift left by two? Because instructions are word-aligned, so the bottom two bits of every instruction address are always zero. Encoding them would waste two bits, so instead we get four times the branch range for free. That is a real architectural trade-off, and it fits in one line of VHDL."*

**Check-off questions**
1. *Hand-compute your backward-branch target. Does the simulation agree?*
2. *What would break if you used PC instead of PC+4 as the base?*

**Close:** *"Next week: jumps, returns, and the six Boolean equations that implement every conditional branch in the machine."*

---

### Lab 8 — Next Instruction Address Generation II

**One idea:** *Branch conditions are Boolean equations over ALU flags.*

**Board moment.** Write all six conditions as equations, then:
> *"Six one-line equations, and between them they implement every conditional branch this machine has. Notice GTZ and LEZ are complements. So are GEZ and LTZ. The hardware is smaller than the instruction list makes it look — that is almost always true, and it is why you read the control table and not the manual."*

On the absolute jump:
> *"The top four bits of a jump target are inherited from the PC, not encoded. So a jump can only reach within a 256-megabyte region. That limitation is not a bug and it is not an accident — it is what you get for spending 26 bits instead of 32. One line of concatenation, one architectural trade-off."*

**Check-off questions**
1. *Walk me through your scripted sequence. Point at the taken branch and the not-taken one.*
2. *Why can `J` not reach every address in memory?*

**Close:** *"Next week: memory, and the program your CPU is going to run."*

---

### Lab 9 — ROM and RAM

**One idea:** *Memory is an array with an address decoder and a bus discipline.*

**Board moment.** Put the seven-instruction ROM program up:
> *"This is the program your processor will run in three weeks. Seven instructions. It computes two to the tenth. From today you are not building components any more — you are building the machine that runs this."*

On endianness:
> *"Big-endian is a decision, not a fact. If I flip it, these same bytes decode as completely different instructions and your CPU executes garbage. That is why a program compiled for one convention crashes on the other — and it is why you write the convention down in your report."*

Flag the `LUI` simplification honestly:
> *"Fair warning: this CPU treats LUI as a plain immediate load, not a shifted upper load. That is not what real MIPS does. It is a deliberate simplification in our decoder, and I am telling you so that when you read the real ISA you know the difference."*

**Check-off questions**
1. *Read the word at `0x08` out of your ROM. Which instruction is it, and how did you get that from four bytes?*
2. *Read your RAM with `en='0'`. What is on the bus, and why is that the right answer?*

**Close:** *"Next two weeks: the control unit. It is one truth table. That is all it is."*

---

### Lab 10 — Instruction Decoder I

**One idea:** *A control unit is one truth table with sixteen output columns.*

**Board moment — this is the intellectual close of the course, so slow down.**
> *"In Lab 1 you took a four-row table and wrote one Boolean equation from it. Today you take an eight-row table and write sixteen. That is the whole difference. Nothing new has been introduced since week one. The control unit of a processor is a truth table — that is not an analogy, it is literally what you are about to write."*

Then set the scope immediately, because the fear here is scope:
> *"This CPU has eight instructions. Not forty. Eight — the ones its program actually uses. You do four today and four next week."*

On defaults:
> *"Assign every control signal a default before the case statement. If you skip this, the synthesiser infers sixteen latches and your CPU will do something different depending on what it did last. This will happen to at least half of you. When it does, you will remember Lab 1."*

**Check-off questions**
1. *Feed it an opcode you did not implement. What do the control signals do, and why is that the safe answer?*
2. *Which signals differ between `ADD` and `ADDI`? Why exactly those?*

**Close:** *"Next week: loads, stores, branches, jumps. Four more rows and the control unit is finished."*

---

### Lab 11 — Instruction Decoder II

**One idea:** *Memory access and control flow are just four more rows.*

**Board moment.** Once the table is complete, read three things off it:
> *"Look at `ALU_Asel`. It is high for `ADDI`, `LUI`, `LW` and `SW` — four instructions with nothing in common. Why? Because the adder is shared. Computing `a + b` and computing `base + offset` are the same operation, so they use the same hardware. That is why a load costs no more than an add."*
>
> *"Look at `RF_strb`. It is low for `SW`, `BLEZ` and `J`. Stores and branches never write a register. If you get this one bit wrong, your CPU quietly corrupts a register and everything downstream is wrong — it is the hardest bug in Lab 12 to find."*
>
> *"And `DM_rw` is determined by exactly one instruction out of eight. Real control units are this sparse. Most of a control table is default."*

**Check-off:** *"Print this table. Bring it in two weeks. You will not debug Lab 12 without it."*

**Check-off questions**
1. *Why is `RF_strb` low for `SW`?*
2. *Why is `IR_Xlsft` set to ×2 only for `BLEZ`?*

**Close:** *"Next week you wire the whole thing together and run the program."*

---

### Lab 12 — CPU Integration

**One idea:** *Debugging a system means predicting it first.*

**Board moment — the timing contract, before anything else.**
> *"Instruction register loads on the rising edge. Program counter and RAM write on the falling edge. One instruction per clock period. Write that down. Every bug in this lab that is not a mis-wire is an edge mistake."*

Then the debugging method, explicitly:
> *"When it does not work — and it will not work the first time — do not open the waveform and stare at forty signals. Bisect. One: is the PC advancing by four? If not, stop, the fault is in NIAG. Two: is the instruction register the value the ROM table says? If not, it is ROM addressing. Three: do the control signals match your printed table for this opcode? If not, it is the decoder. Only then look at the ALU. Four checks, in order, every time."*

And before they simulate:
> *"Hand-compute the first five rows of your trace before you run anything. I am grading the hand-computation, not just whether it matches. You cannot debug a machine you cannot predict."*

**Check-off questions**
1. *Show me your final `r2`. What number is it, and why that number?*
2. *Show me one cycle in the waveform and read the control signals off it. Which instruction is executing?*

**Close:** *"Your processor computes two to the tenth. Three months ago you were writing a four-row truth table for a latch. Same loop, every week — that is how this was always going to end."*

---

### Final Lab — Demonstration and Extension

**Open (this one is different — it is the last thing they hear):**
> *"Fourteen weeks ago, Lab 0: entity, architecture, one output. Today you are demonstrating a processor you built from gates up, and it runs a program. Nothing was ever added to the method — specification, truth table, equations, VHDL, simulation, check. You did the same thing thirteen times at increasing scale. That is engineering, and it is the actual thing you are taking away from this course."*

**Demonstrations**, ~4 min each, two questions from this fixed bank (choose two, same pair for everyone in the section):
1. Point at any cycle in your waveform and tell me what is executing.
2. Which component gave you the most trouble, and how did you find the bug?
3. If I asked you to add one instruction, what would you change and in what order?
4. Where is your critical path, and what would you do to make this run faster?

**Close:**
> *"Finish the report. Keep the Overleaf project — it is a genuine portfolio piece, and it is the most convincing thing you can put in front of someone who asks whether you can actually design hardware."*

---

## Part 3 — Phrases worth reusing

Small, repeatable, and they do real work:

| Situation | Say |
|---|---|
| A student asks you to debug for them | *"Read me the error message out loud."* — solves it about half the time |
| A student is stuck and quiet | *"Show me your truth table."* — if there isn't one, that is the bug |
| Something works but they cannot say why | *"Which line implements which term of your equation?"* |
| A student is copying a neighbour | *"Different question: what does line 12 do?"* — no accusation needed |
| Someone finishes at 5:00 | *"Do the stretch. Or help the person next to you — explaining it is how you find out whether you know it."* |
| Everything is broken and time is short | *"Compile only. Get the compile, screenshot the error, and write the Discussion section about it. A documented failure is worth more marks than a blank page."* |
