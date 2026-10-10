# Track C — Pipeline: the hazard analysis
### Reference notes (TA) — and the grading rule students must be told

## The grading rule, stated first

**A working pipelined CPU is NOT required. Breaking it correctly and explaining
precisely why is full credit.**

Say this out loud when you offer the track, and put it in the handout. Otherwise
nobody picks it, and the students who would get the most out of it are exactly the
ones who will not gamble their last grade on "make a pipeline work in 70 minutes".

---

## What the track actually asks

Insert **one** pipeline register between fetch and execute, so that:

```
stage 1 (IF)   PC -> ROM -> IR
                              |
                       [ pipeline register ]
                              |
stage 2 (EX)   decode, register read, ALU, write-back, PC update
```

Then make **arithmetic-only** instructions work — `LUI`, `ADDI`, `ADD`, `SLL` — and
**document every way the pipeline is now wrong.**

## The four hazards, and why each one appears

### 1. Control hazard — the big one

The PC is updated in stage 2, but stage 1 has already fetched the next instruction
by then. So after a taken branch or a jump, **one wrong instruction is already in
the pipe.**

In the Lab 12 program this is fatal: the loop is four instructions and contains both
a `BLEZ` and a `J`. Every pass through the loop mis-executes.

Real fixes: flush the fetched instruction (a bubble), or predict and recover, or
declare a branch delay slot and make the assembler fill it — which is what MIPS
actually did, and why `J` in real MIPS code is followed by an instruction that
executes *anyway*.

**Students should recognise this as the reason the delay slot exists.** That
connection is worth more than a working pipeline.

### 2. Data hazard — read-after-write

`ADDI r1, r1, -1` followed immediately by `BLEZ r1` reads `r1` in stage 2 while the
`ADDI` is still writing it. With one pipeline register the write happens at the end
of the same cycle the next instruction reads, so the read gets the **old** value.

Real fixes: forwarding (bypass the ALU result back), or interlock and stall.

In this program the `ADDI`/`BLEZ` pair is adjacent, so the hazard fires on every
loop iteration.

### 3. Structural hazard — one memory, two stages

Stage 1 reads the ROM every cycle. Stage 2 reads or writes the RAM. In this design
they are separate memories, so **there is no structural hazard** — which is worth
saying explicitly, because it is the reason Harvard architectures exist. A single
unified memory would create one immediately.

Getting a student to notice a hazard that is *absent*, and say why, is a better
outcome than getting them to list three that are present.

### 4. The reset and startup hazard

The pipeline register must come up holding something harmless. All-zeros decodes as
`SLL r0, r0, 0` — a NOP that writes `r0`, which is blocked. That is the same
accident that cost an hour in Lab 12 when the PC advanced before the first fetch,
and it is worth pointing at.

---

## What a full-credit submission looks like

1. The pipeline register exists and arithmetic instructions execute correctly
   through it — demonstrated on a short straight-line program.
2. The hazard analysis names **all four** categories above, says whether each is
   present in this design, and for the present ones gives a concrete instruction
   pair from the Lab 12 program that triggers it.
3. For each present hazard, one named real-world fix and one sentence on its cost.
4. An honest statement of what does **not** work and why.

## What does not earn credit

- A pipeline that "works" because the test program has no branches and no adjacent
  dependencies. That is not a working pipeline; it is an untested one.
- A hazard list copied from the textbook without a concrete instruction pair from
  *this* program.

---

## A short straight-line program for demonstrating stage 2

Four instructions, no branches, no adjacent register dependencies — so it should
execute correctly through a one-stage pipeline. If it does not, the pipeline
register itself is wrong, not the hazards.

```
0x00   3C 01 00 05    LUI  r1, 5        r1 <- 5
0x04   3C 02 00 03    LUI  r2, 3        r2 <- 3
0x08   3C 03 00 07    LUI  r3, 7        r3 <- 7
0x0C   00 22 20 20    ADD  r4, r1, r2   r4 <- 8     (r1 and r2 are old enough)
```

`ADD r4, r1, r2` = opcode `000000`, rs `00001`, rt `00010`, rd `00100`,
sa `00000`, func `100000` = `0x00222020`.

Note the deliberate spacing: `r1` is written three instructions before it is read,
so no forwarding is needed. Ask the student what happens if they move the `ADD` up
to `0x08` — that is the data hazard, made by hand.
