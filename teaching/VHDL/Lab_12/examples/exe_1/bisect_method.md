# Lab 12, Example 1 — How to debug a CPU

## The rule

When your CPU does not work — and it will not, the first time — **do not open the
waveform and stare at forty signals.** That is how people lose the whole session.

**Bisect.** Four checks, in this order, every time. Each one either passes or tells
you exactly which quarter of the machine to look at.

---

## The four checks

### 1. Is the PC advancing by 4?

Look at `PC_out` alone. Nothing else.

| What you see | What it means |
|---|---|
| `0, 4, 8, C, 10, …` | fetch is alive. Go to check 2. |
| stuck at 0 | the PC is not being loaded — `NIAG_strb`, or reset never released |
| `'U'` or `'X'` | the PC register has no reset value, or reset is not reaching it |
| advancing by 1 | you wired `NIAG_NSA` to add 1 instead of 4 |
| jumping wildly from the start | `NIAG_sel` is not defaulting to NSA |

**Stop here if this fails.** Nothing downstream can be right if the machine is not
fetching in order.

### 2. Is `IR_out` the instruction the ROM table says?

Compare against the seven-row table in `ROM.vhd`. Just the first two or three.

| What you see | What it means |
|---|---|
| matches the table | fetch is correct. Go to check 3. |
| always zero | `IR_strb` never asserts, or the ROM output is not connected |
| one instruction late | you addressed the ROM with `NSA` instead of `PCreg` |
| garbage | byte order, or the ROM address is not `PCreg` |

### 3. Do the control signals match your printed control table?

**This is why you printed it.** Pick one instruction — `ADDI` is a good one — and
check its row, signal by signal, against what the decoder is producing.

| What you see | What it means |
|---|---|
| matches your table | control is correct. Go to check 4. |
| some signals wrong for one instruction | that row of your decoder |
| signals depend on the *previous* instruction | latches — Lab 10, Example 3 |
| everything inert | the opcode is not being extracted, or `IRreg` is zero |

### 4. Only now, look at the datapath.

If the PC advances, the right instruction is fetched, and the control signals are
right, then the fault is in the wiring between components: an operand from the wrong
register, a mux input swapped, a bus not driven.

---

## Why this order

Each check depends on all the ones before it. Checking the ALU while the PC is stuck
tells you nothing — the ALU is faithfully computing on garbage.

**Four checks, in order, every time.** It is worth doing them in order even when you
are sure you know what is wrong, because you are usually not.

---

## The two bugs in `cpu_broken.vhd`

This example contains a CPU with **two deliberate wiring errors**. Both compile. Both
run. Both produce a machine that looks almost right.

Run `cpu_broken_tb` and work the method. The testbench prints the trace and the final
state; your job is to decide, from the four checks, *which quarter of the machine* is
at fault — before you look at the answer at the bottom of `cpu_broken.vhd`.

Two things worth noticing while you do it:

- **Both bugs produce the same headline symptom**: the stored word is not `0x400`.
  The symptom does not identify the bug. The method does.
- **Both bugs pass checks 1, 2 and 3.** The PC advances, the right instructions are
  fetched, the control signals are correct. That is what makes them datapath bugs,
  and it is exactly the information the first three checks are there to give you.
