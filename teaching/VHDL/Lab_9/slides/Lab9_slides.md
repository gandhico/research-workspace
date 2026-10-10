# Lab 9 — Slide Content
### Memory: ROM and RAM · 9 slides · 12 minutes

---

## Slide 1 — Title
> **EE 362 — Laboratory 9**
> **Memory: ROM and RAM**

---

## Slide 2 — The program
> | addr | bytes | instruction |
> |---|---|---|
> | `0x00` | `3C 01 00 0B` | `LUI  r1, 11` |
> | `0x04` | `3C 02 00 01` | `LUI  r2, 1` |
> | `0x08` | `20 21 FF FF` | `ADDI r1, r1, -1` |
> | `0x0C` | `18 20 00 02` | `BLEZ r1, +2` |
> | `0x10` | `00 02 10 40` | `SLL  r2, r2, 1` |
> | `0x14` | `08 00 00 02` | `J    0x08` |
> | `0x18` | `AC 02 00 00` | `SW   r2, 0(r0)` |
>
> ### Seven instructions. This is what your CPU runs.

*Say:* Start here, before any VHDL. Every component you have built since Lab 1
exists to make these seven instructions execute. Ten passes through the loop,
doubling each time. **Your CPU computes 2¹⁰ = 1024**, and stores it at address 0.

That is the sentence at the end of Lab 12, and today you build the memory it lives in.

---

## Slide 3 — Today's one idea
> ### Memory is an array with an address decoder and a bus discipline.

---

## Slide 4 — Bytes into words
> Memory is **byte-addressed**. Instructions are **32 bits**.
>
> ```
> Data(31..24) = M[A]     Data(23..16) = M[A+1]
> Data(15.. 8) = M[A+2]   Data( 7.. 0) = M[A+3]
> ```
> Most significant byte at the **lowest** address → **big-endian**.

---

## Slide 5 — Endianness is a decision
> Bytes `20 21 FF FF`:
>
> **big-endian** → `0x2021FFFF` → opcode `001000` = `ADDI r1,r1,-1` ✓
> **little-endian** → `0xFFFF2120` → opcode `111111` = **not an instruction**
>
> ### Same memory. Different machine.

*Say:* Neither convention is more correct, but they are not compatible. This is
exactly why a binary compiled for one crashes on the other, and why every processor
manual states its byte order on about page three.

This CPU is big-endian. Write that in your report — a memory whose byte order is
undocumented is a memory nobody can use, including you at midnight in six weeks.

---

## Slide 6 — ROM: combinational, and read-only for a reason
> Present an address, the data appears. **No clock.**
>
> Contents are a `constant` — fixed at synthesis time.
>
> That is what read-only *means*: a running program cannot overwrite itself.

---

## Slide 7 — RAM: the bus discipline
> | # | en | rw | Strb | Data bus | memory at ↓ |
> |---|---|---|---|---|---|
> | 0 | 0 | – | – | `Z` | hold |
> | 1 | 1 | **1** | – | M[A] | hold *(read)* |
> | 2 | 1 | 0 | 0 | `Z` | hold |
> | 3 | 1 | 0 | 1 | `Z` *(driven in)* | **write** |
>
> $$\text{DataDrive} = en \cdot rw \qquad \text{Write} = en \cdot \overline{rw} \cdot Strb$$
>
> ⚠ **`rw = '1'` is READ.** Check twice.

*Say:* This is Lab 4 for real. The bus is shared: on a read the RAM drives it, on a
write the register file drives it through the TriBuffer you built. Exactly one driver.

When the RAM is not driving it must **release to `Z`**, not hold `0`. Driving `0`
fights the other driver and the whole bus goes red.

---

## Slide 8 — Why writes happen on the falling edge
> Lab 12 CPU timing:
>
> **↑ rising** — the instruction register loads
> **↓ falling** — the PC updates, and memory writes
>
> Address and data get **half a clock period to settle** before anything commits.

*Say:* Two-phase timing, and it is the reason the whole machine works. Get this edge
wrong and Lab 12 stores the right value at the wrong moment — which looks like random
corruption and is miserable to find.

---

## Slide 9 — Your assignment, and the new number
> **`ROM`** 512 bytes, combinational, preloaded (program given — do not change it)
> **`RAM`** 512 bytes, the table above, shared `inout` bus
>
> **Guard the address range.** 32-bit address, 512-byte memory. Reading `base+3`
> near the top stops the simulation dead.
>
> **E4 this week: block memory bits, not registers.** 512 bytes = 4096 bits.
> Did the Fitter use block RAM or logic? Say which, and why that is sensible.

*Say:* In your report, disassemble all seven ROM words by hand. That is the exercise —
the VHDL is short.

---

## Production notes
- 9 slides, ~12 min. **Slide 2 is the one that matters** — put the program up before
  anything else and let it sit. It reframes the whole remaining term.
- Run Example 3 live between slides 4 and 5.
- Slide 8's timing point should be repeated at check-off; it is the one that costs
  the most in Lab 12.
