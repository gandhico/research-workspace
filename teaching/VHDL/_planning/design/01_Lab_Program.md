# EE 362 Lab — The Twelve Laboratories

Simulation only. Every lab follows the Spec Ladder from `00_Program_Design.md` §4.
Table types: **E** exhaustive · **C** compressed · **T** transition. Evidence sets **E1–E7** per §5.

Notation: `·` AND · `+` OR · `⊕` XOR · `X̄` NOT · `Q⁺` next value · `‖` concatenation · `–` don't care.

---

## Lab 1 — Design Flow and the Transparent Latch
**Mon 9/7 ⚠ Labor Day · Tue 9/8** · Evidence **E1, E2, E7**
**One idea:** *An equation whose output appears on its own right-hand side is memory.*

### Specification — Table T

| # | Clr | En | D ‖ Q⁺ | note |
|---|---|---|---|---|
| 0 | 1 | – | – ‖ **0** | asynchronous clear, dominates |
| 1 | 0 | 0 | – ‖ **Q** | hold — the memory row |
| 2 | 0 | 1 | 0 ‖ **0** | transparent |
| 3 | 0 | 1 | 1 ‖ **1** | transparent |

### Equations

```
(1) canonical    Q⁺ = C̄lr·En·D  +  C̄lr·Ēn·Q
(2) factored     Q⁺ = C̄lr · ( En·D + Ēn·Q )        [distributive law]
(3) VHDL         process(Clr, En, D)
                   if Clr = '1' then Q <= '0';
                   elsif En = '1' then Q <= D;
                   end if;                          -- no else: the hold row IS the missing else
```

Point at the `Q` in equation (1) and say: *that is the entire difference between combinational logic and memory.* Then point at the missing `else` in (3) and say: *and in VHDL, memory is what you get when you leave a case undefined. Here we want it. Every other week we will not, and that is the bug you will hit all semester.*

### Build

| Entity | Ports |
|---|---|
| `TransLatch` | `D, En, Clr : in std_logic` · `Q : out std_logic` |
| `TransLatch8` | same, `D, Q : std_logic_vector(7 downto 0)` |

### Testbench — 6 vectors minimum
Transparency `En=1` both polarities · hold across a `D` change with `En=0` (**the critical vector**) · clear while transparent · clear while holding · release from clear.

### Overleaf `lab01.tex`
Table T, the 3-line derivation, RTL Viewer figure, waveform with the hold interval annotated.

### Pitfalls
Incomplete sensitivity list · `=` vs `<=` · expecting edge behaviour from a level-sensitive device.

---

## Lab 2 — Master–Slave Flip-Flop and the N-Bit Register
**Mon 9/14 · Tue 9/15** · Evidence **E1, E2, E7**
**One idea:** *Two latches with opposite enables make an edge.*

### Specification — Table T

Master transparent when `Clk=0`, slave transparent when `Clk=1`.

| # | Rst | Ld | Clk ‖ Q⁺ | note |
|---|---|---|---|---|
| 0 | 1 | – | – ‖ **0** | async reset |
| 1 | 0 | – | not ↑ ‖ **Q** | hold between edges |
| 2 | 0 | 0 | ↑ ‖ **Q** | edge, but not loading |
| 3 | 0 | 1 | ↑ ‖ **D** | load |

### Equations

```
master   Qm⁺ = C̄lr·( C̄lk·D  + Clk·Qm )   -- Lab 1's latch, enable = C̄lk
slave    Q⁺  = C̄lr·( Clk·Qm + C̄lk·Q  )   -- Lab 1's latch, enable = Clk
```
While `Clk=0` the master follows `D` and the slave holds. At `Clk: 0→1` the master freezes and the slave copies it. **The output can therefore change only at the rising edge** — that is what "edge-triggered" means, derived rather than asserted.

Register, per bit *i*, evaluated at ↑Clk:
```
(1)  Q_i⁺ = R̄st · ( Ld·D_i + L̄d·Q_i )
(2)  identical to Lab 1 equation (2) with En → Ld and Clr → Rst   [same circuit, new name]
(3)  if Rst = '1' then
         Q <= (others => '0');
     elsif rising_edge(Clk) then
         if Ld = '1' then Q <= D; end if;   -- Ld nested INSIDE the edge test
     end if;
```
Write `Ld` as a **nested** `if`, not as `and Ld='1'` on the `elsif`. Both simulate the same; the nested form is the idiom every synthesiser recognises, and it keeps the edge test as the sole condition on the `elsif`, which is what makes the register inference unambiguous.

### Build

| Entity | Ports |
|---|---|
| `MSFlipFlop` | `D, Clk, Clr : in` · `Q : out` — **structural, from two `TransLatch` instances**, `Clr` wired to *both* |
| `RegN` | `generic N := 32` · `D(N-1..0), Clk, Ld, Rst : in` · `Q(N-1..0) : out` |

`Clr` reaching **both** latches is the point worth making: clear only the slave and the master pushes the stale value back at the very next rising edge, so the clear appears to undo itself one cycle later. Worth demonstrating deliberately.

The generic is proved by the testbench instantiating `RegN` at widths 5 **and** 32, so no separate demo entity is needed. Top-level for synthesis is `RegN` at the default width, which makes the Fitter's register count (must be 32) a correctness check.

### Testbench
Clock process with `wait`. Must show: `D` toggling several times between edges while `Q` stays put; load only at ↑; async reset asserting *between* edges.

### Overleaf `lab02.tex`
Both characteristic equations, and a waveform where `D` toggles 3 times inside one clock period while `Q` moves once.

### Pitfalls
Clock process with no `wait` (simulation hangs) · reset polarity · forgetting `generic map` and silently getting 32 bits.

---

## Lab 3 — Multiplexers
**Mon 9/21 · Tue 9/22** · Evidence **E1, E2, E7**
**One idea:** *A multiplexer is how a control signal steers a datapath — and why we need compressed tables.*

### Specification — Table C

`Mux2`, width *W*:

| # | Sel ‖ Y |
|---|---|
| 0 | 0 ‖ **A** |
| 1 | 1 ‖ **B** |

`Mux3`, width *W*:

| # | Sel₁ | Sel₀ ‖ Y | note |
|---|---|---|---|
| 0 | 0 | 0 ‖ **A** | |
| 1 | 0 | 1 ‖ **B** | |
| 2 | 1 | 0 ‖ **C** | |
| 3 | 1 | 1 ‖ **0** | *defined* default — the reference design drives all zeros |

**Open the lab with this:** a 32-bit 3:1 multiplexer has 98 inputs. An exhaustive table has 2⁹⁸ rows — more rows than there are atoms in your body. The four rows above specify it completely. *That* is what a compressed table buys you, and it is why datapath design is possible at all.

### Equations

Per bit *i*:
```
Mux2   Y_i = S̄·A_i + S·B_i

Mux3
(1) canonical   Y_i = S̄₁S̄₀·A_i + S̄₁S₀·B_i + S₁S̄₀·C_i + S₁S₀·0
                                                          └─ row 3 outputs 0: no product term needed
(2) factored    Y_i = S̄₁·( S̄₀·A_i + S₀·B_i ) + S₁·S̄₀·C_i       [distributive law, factoring S̄₁]
(3) VHDL        case Sel is
                  when "00" => Y <= A;  when "01" => Y <= B;
                  when "10" => Y <= C;  when others => Y <= (others => '0');
                end case;
```
**Make them factor step (2) themselves, then show them what they just built.** The parenthesis is a 2:1 multiplexer choosing A or B; the whole expression is a second 2:1 multiplexer choosing between that and C. Algebraic factoring produced a multiplexer *tree*. That is not a coincidence — factoring a Boolean expression and decomposing a circuit into sub-blocks are the same operation, and this is the first place they can see it.

### Build

| Entity | Role on the CPU diagram |
|---|---|
| `Mux2` (generic W) | base |
| `Mux3` (generic W) | base |
| `MUX2x32`, `MUX3x32` | `DinMUX`, `ALUinMUX` |
| `MUX2x5`, `MUX3x5` | `DselMUX` (register write select) |

### Testbench
Exhaustive on `Sel`; ≥ 2 distinct data patterns per selector value; one vector proving no latch (hold `Sel`, change data, output must follow immediately).

### Overleaf `lab03.tex`
Table C, the factored equation with the law named, the mux-tree observation, and an annotated CPU block diagram with their four muxes circled. **First time they see the whole datapath — make it a full-page figure.**

### Pitfalls
Missing `when others` → inferred latch · width mismatch in `port map` · `std_logic` vs 1-bit vector on `Sel`.

---

## Lab 4 — Extender, Tri-State, Shift Select
**Mon 9/28 · Tue 9/29** · Evidence **E1, E2, E7**
**One idea:** *`'Z'` is not a Boolean value — some hardware lives outside Boolean algebra.*

### Specification — Table C

`ImmedXtnd` (16 → 32), controls named as the CPU decoder will drive them:

| # | IR_Xsel | IR_Xlsft ‖ Y(31..0) | used by |
|---|---|---|---|
| 0 | 0 zero | 0 none ‖ **0¹⁶ ‖ I** | LUI, ANDI-class |
| 1 | 1 sign | 0 none ‖ **I₁₅¹⁶ ‖ I** | ADDI, LW, SW |
| 2 | 1 sign | 1 ×4 ‖ **I₁₅¹⁴ ‖ I ‖ 00** | branch offsets |
| 3 | 0 zero | 1 ×4 ‖ **0¹⁴ ‖ I ‖ 00** | (unused, but defined) |

`TriBuffer`:

| # | Sel ‖ Y |
|---|---|
| 0 | 0 ‖ **Z** |
| 1 | 1 ‖ **A** |

`ALUsftMUX`: `ALU_Ssel = 0` → shift amount from the instruction `sa` field; `= 1` → from register `Bout(4..0)`.

### Equations

```
Extender, no shift:   Y_i = I_i                    for i = 0..15
                      Y_i = IR_Xsel · I₁₅          for i = 16..31
With ×4 shift:        Y_i = E_(i-2), Y₁ = Y₀ = 0   where E is the extended value

Tri-state:            Y = A when Sel='1', else 'Z'    -- NOT a Boolean function
```

**The `'Z'` moment.** Write the `std_logic` resolution table on the board and let them stare at it:

| two drivers | 0 | 1 | Z |
|---|---|---|---|
| **0** | 0 | **X** | 0 |
| **1** | **X** | 1 | 1 |
| **Z** | 0 | 1 | Z |

Boolean algebra has two values. This table has four. That is why VHDL needs a *resolved* type, and why `'X'` in your waveform always means "two drivers disagreed" — never "the simulator is confused."

### Build
`ImmedXtnd` · `TriBuffer` (32-bit) · `ALUsftMUX` · `BusDemo` (two `TriBuffer`s on one net, to produce `'X'` deliberately).

### Testbench
`ImmedXtnd` on `0x8000` — the value where sign and zero extension visibly differ (`0xFFFF8000` vs `0x00008000`). Both tri-states enabled → assert `'X'`.

### Overleaf `lab04.tex`
Resolution table. Discussion must answer: *why does `ADDI` sign-extend but `LUI` zero-extend in this CPU?*

### Pitfalls
Extending the wrong bit · treating `'Z'` as `'0'` · `(others => I(15))` aggregate syntax.

---

## Lab 5 — Arithmetic Logic Unit
**Mon 10/5 · Tue 10/6** · Evidence **E1, E2, E4, E6, E7**
**One idea:** *An ALU is a multiplexer over function units. You already built the multiplexer.*

### Specification — Table C (the function select)

Codes are fixed by `EE362ALU.vhd`; use the constants, never literals.

| # | ALU_func | Operation | Result |
|---|---|---|---|
| 0 | `00000` ADD | add | Ain + Bin |
| 1 | `00001` SUB | subtract | Ain − Bin |
| 6 | `00110` NEG | negate | 0 − Bin |
| 7 | `00111` SLA | shift left arith | Ain ≪ Shft |
| 8 | `01000` SRA | shift right arith | Ain ≫ₐ Shft |
| 9 | `01001` SOLS | set on less, signed | Ain < Bin ? 1 : 0 |
| 10 | `01010` SOLU | set on less, unsigned | Ain < Bin ? 1 : 0 |
| 11–17 | AND … NOT | bitwise | per bit |
| 18 | `10010` SLL | shift left logical | Ain ≪ Shft |
| 19 | `10011` SRL | shift right logical | Ain ≫ Shft |

### Equations

```
Full adder, bit i:   S_i     = A_i ⊕ B_i ⊕ C_i
                     C_(i+1) = A_i·B_i + C_i·(A_i ⊕ B_i)

Subtraction:         A − B = A + B̄ + 1                     [two's complement]

Flags:               N = R₃₁
                     Z = ¬(R₃₁ + R₃₀ + … + R₀)             [32-input NOR]
                     V = C₃₂ ⊕ C₃₁                          [signed overflow]

Set on less:         SOLS = R₃₁ ⊕ V        where R = A − B  (overflow-corrected sign)
                     SOLU = ¬C₃₂           (no carry out means a borrow occurred)

Shifts by k = Shft:  SLL  Y_i = X_(i−k), else 0        (X = Ain)
                     SRL  Y_i = X_(i+k), else 0
                     SRA  Y_i = X_(i+k), else X₃₁            ← the classic bug lives here
```

`SOLS = R₃₁ ⊕ V` is the one equation students will not guess. Derive it: the sign bit of `A − B` tells you the answer *unless* the subtraction overflowed, in which case it lies, and `V` corrects it. Two minutes at the board, and it makes overflow concrete for the first time.

### Build

Port list is fixed by `EE362ALU.vhd`: `Ain`, `Bin` (32), `Func` (5), **`Shft` (5)**, `Rout` (32), `Stat`.
Shifts act on **`Ain`, by the amount on `Shft`** — a separate port, fed in the finished CPU by `ALUsftMUX`. Students who assume the shift amount arrives on `Bin` will pass Lab 5's testbench and fail Lab 12.

Implement: `SUB`, `NEG`, `AND`, `NAND`, `OR`, `NOR`, `XOR`, `XNOR`, `NOT`, `SLL`, `SRL`, `SLA`, `SRA`, `SOLS`, `SOLU`, plus the `ALU` wrapper with `Zero` and `Neg` outputs.
**Given complete:** `ADD` (the template), `MULS`, `MULU`, `DIVS`, `DIVU`, `RDHI/RDLO/WRHI/WRLO`.

### Testbench
≥ 3 vectors per implemented function, each including one boundary case: `SUB` producing a negative · `SRA` on a negative number · `SOLS` vs `SOLU` on `0xFFFFFFFF` and `0x00000001`, where they disagree (−1 < 1 signed; 4294967295 > 1 unsigned).

### Overleaf `lab05.tex`
Function table with one worked example each. **First lab reporting E4 and E6** — resource cost and Fmax. One sentence each: what dominates the area, and where the critical path runs.

### Pitfalls
`SRA` written as `SRL` · shift amount left as a vector instead of `to_integer` · comparing `std_logic_vector` without casting to `signed`/`unsigned` · missing `when others` in the wrapper.

---

## Lab 6 — Register File
**Mon 10/12 · Tue 10/13** · Evidence **E1, E2, E4, E6, E7**
**One idea:** *Thirty-two copies of your Lab 2 register, plus address decoding.*

### Specification — Table C

Port list is fixed by `EE362RegFile.vhd`.

| # | Strb | Dsel ‖ effect at ↑Clk |
|---|---|---|
| 0 | 0 | – ‖ no write |
| 1 | 1 | `00000` ‖ **no write** — R0 is hardwired |
| 2 | 1 | k ≠ 0 ‖ **R_k ← Din** |

Reads are combinational and always valid: `Aout = R[Asel]`, `Bout = R[Bsel]`, with `R[0] ≡ 0`.

### Equations

```
Address minterm      m_k(S) = 1  iff  S = k          (a 5→32 decoder — Lab 0's decoder, widened)

Write enable         We_k = Strb · m_k(Dsel) · [k ≠ 0]

Storage, per reg     R_k⁺ = We_k·Din + W̄e_k·R_k       ← identical to Lab 2, 32 times

Read port A          Aout = Σ(k=1..31) m_k(Asel) · R_k    (a 32:1 mux, one per bit)
                     R₀ ≡ 0, so k=0 contributes nothing
```

Three components they already own: a decoder, a register, a multiplexer. Say that before they start — it converts a scary lab into an assembly job.

### Build
`RegFile` — `Asel, Bsel, Dsel (4..0)`, `Din (31..0)`, `Strb`, `clk`, `Aout, Bout (31..0)`.

### Testbench
Write R5, read on both ports · attempt to write R0, confirm it still reads 0 · read a register in the same cycle it is written (**state in the report which behaviour your design has, and why**) · simultaneous distinct reads on A and B.

### Overleaf `lab06.tex`
The three equations above, and E4 with a comment on how much of the device 1024 flip-flops actually costs.

### Pitfalls
Writing R0 · reading combinationally from a signal only assigned inside the clocked process · strobe polarity.

---

## Lab 7 — Next Instruction Address Generation I
**Mon 10/19 · Tue 10/20** · Evidence **E1, E2, E4, E7**
**One idea:** *The PC is a register; everything else is address arithmetic.*

### Specification — Table T / C

| # | Rst | NIAG_strb ‖ PC⁺ |
|---|---|---|
| 0 | 1 | – ‖ **RESET_VEC** (`0x00000000`) |
| 1 | 0 | 0 ‖ **PC** |
| 2 | 0 | 1 ‖ **NIAGout** at ↓Clk |

### Equations

```
Next sequential      NSA = PC + 4
Relative target      Rel = NSA + ( SignExt₃₂(imm₁₆) ≪ 2 )
```

**Worked example, taken from the real ROM program** — put it on the board, they hand-verify it in the report:

```
0x0C:  BLEZ r1, +2        encoding 0x18200002
       NSA  = 0x0C + 4                       = 0x10
       off  = SignExt(0x0002) ≪ 2 = 2 × 4    = 0x08
       Rel  = 0x10 + 0x08                    = 0x18   ✓ the SW instruction
```

Two questions worth asking aloud: *why is the base `PC+4` and not `PC`?* (the fetch already happened) and *why shift by 2?* (instructions are word-aligned, so the low two bits are always zero — free range).

### Build
`NIAG_Reg` (the PC, reusing `RegN`) · `NIAG_NSA` · `NIAG_Rel` (reusing `ImmedXtnd`).

### Testbench
Forward branch · **backward branch with a negative offset** · plain sequential. Hand-compute each target in the report before simulating.

### Overleaf `lab07.tex`
The worked example above, done for a *different* offset, with the arithmetic shown.

### Pitfalls
Forgetting `≪ 2` · using PC instead of PC+4 as base · sign extension of a negative offset · resetting the PC to something other than `RESET_VEC`.

---

## Lab 8 — Next Instruction Address Generation II
**Mon 10/26 · Tue 10/27** · Evidence **E1, E2, E4, E7**
**One idea:** *Branch conditions are Boolean equations over ALU flags.*

### Specification — Table C, PC source select

| # | NIAG_sel ‖ PC⁺ source |
|---|---|
| 0 | `00` NSA ‖ **PC + 4** |
| 1 | `01` REL ‖ **Rel**, if the condition holds; else NSA |
| 2 | `10` REG ‖ **Bout** (jump register) |
| 3 | `11` ABS ‖ **Abslt** |

### Specification — Table E, branch conditions (`NIAG_cond`, from ALU flags)

This is a proper exhaustive table over `{N, Z}`, and the payoff of Lab 5's flags.

| # | NIAG_cond | Meaning ‖ Taken = |
|---|---|---|
| 0 | `000` NONE | unconditional ‖ **1** |
| 1 | `001` EQ | rs = rt ‖ **Z** |
| 2 | `010` NEQ | rs ≠ rt ‖ **Z̄** |
| 3 | `011` GTZ | rs > 0 ‖ **N̄ · Z̄** |
| 4 | `100` GEZ | rs ≥ 0 ‖ **N̄** |
| 5 | `101` LTZ | rs < 0 ‖ **N** |
| 6 | `110` LEZ | rs ≤ 0 ‖ **N + Z** |

Six one-line Boolean equations that between them implement every conditional branch in the machine. Show that `GTZ` and `LEZ` are complements, and `GEZ`/`LTZ` are complements — the hardware is smaller than the instruction list suggests.

### Equations

```
Absolute target      Abslt = NSA(31..28) ‖ index(25..0) ‖ "00"
Return address       Rtn   = NSA = PC + 4
PC next              PC⁺   = sel=00 → NSA
                             sel=01 → Taken·Rel + T̄aken·NSA
                             sel=10 → Bout
                             sel=11 → Abslt
```

**Worked example from the ROM program:**
```
0x14:  J 0x02            encoding 0x08000002
       NSA   = 0x18 → top 4 bits = 0x0
       Abslt = 0x0 ‖ 0x0000002 ‖ 00 = 0x00000008   ✓ back to the loop top
```
Ask: *why can a jump only reach 2²⁸ bytes?* Because the top 4 bits are inherited, not encoded. That is a real architectural trade-off, visible in one line of concatenation.

### Build
`NIAG_Abslt` · `NIAG_Rtn` · `NIAG_MUX` (reusing `Mux3`/`Mux2`) · top-level `NIAG`.

### Testbench — one scripted sequence, and it becomes the report's centrepiece figure
sequential → taken branch → not-taken branch → `J` → jump-register → return.

### Overleaf `lab08.tex`
Both tables, the six branch equations, and the annotated waveform of the scripted sequence.

### Pitfalls
Mux priority when two selects assert · treating the jump index as a byte address · forgetting `Taken` gates `Rel` but not `Abslt`.

---

## Lab 9 — ROM and RAM
**Mon 11/2 · Tue 11/3** · Evidence **E1, E2, E4, E7**
**One idea:** *Memory is an array with an address decoder and a bus discipline.*

### Specification — Table C, RAM

Polarities are fixed by the reference design: **`rw='1'` reads, `rw='0'` writes, and writes land on the falling edge.**

| # | en | rw | Strb ‖ Data bus ‖ memory at ↓Clk |
|---|---|---|---|
| 0 | 0 | – | – ‖ **Z** ‖ hold |
| 1 | 1 | 1 | – ‖ **M[A] word** ‖ hold |
| 2 | 1 | 0 | 0 ‖ **Z** ‖ hold |
| 3 | 1 | 0 | 1 ‖ **Z** (driven externally) ‖ **M[A..A+3] ← Data** |

### Equations

```
Drive the bus        DataDrive = en · rw
Perform a write      Write     = en · r̄w · Strb        sampled at ↓Clk

Word assembly, big-endian:
   Data(31..24) = M[A]     Data(23..16) = M[A+1]
   Data(15.. 8) = M[A+2]   Data( 7.. 0) = M[A+3]
```

Endianness is a *decision*, not a fact. State it, then show that a little-endian ROM would make the same bytes decode as a different instruction — which is exactly why a program compiled for one convention crashes on the other.

### Build
`ROM` — 512 × 8, combinational read, initialised with the supplied program image (you provide it).
`RAM` — 512 × 8, `Addr, Strb, rw, en, clk`, `Data : inout`.

### The supplied ROM program (they will run it in Lab 12 — show it now)

| Addr | Bytes | Instruction | Meaning |
|---|---|---|---|
| `0x00` | `3C 01 00 0B` | `LUI r1, 11` | r1 ← 11 (loop counter) |
| `0x04` | `3C 02 00 01` | `LUI r2, 1` | r2 ← 1 |
| `0x08` | `20 21 FF FF` | `ADDI r1, r1, -1` | loop top |
| `0x0C` | `18 20 00 02` | `BLEZ r1, +2` | exit when r1 ≤ 0 |
| `0x10` | `00 02 10 40` | `SLL r2, r2, 1` | r2 ← r2 × 2 |
| `0x14` | `08 00 00 02` | `J 0x08` | loop |
| `0x18` | `AC 02 00 00` | `SW r2, 0(r0)` | store the result |

*Note: this CPU treats `LUI` as a plain zero-extended immediate load, not a shifted upper load. It is a documented simplification — say so, or a sharp student will correctly tell you the ISA is wrong.*

### Testbench
Read the first 7 words from ROM and assert they match the table above, word by word. RAM: write-then-read at three addresses, and one read with `en='0'` asserting `'Z'`.

### Overleaf `lab09.tex`
The ROM contents table with their own disassembly worked out, and a statement of the endianness convention.

### Pitfalls
Endianness · misaligned word reads · driving `Data` when not enabled · writing on the wrong clock edge.

### Stretch ⭐ (the cache hook)
Put a 4-entry direct-mapped cache in front of the ROM, run the loop, and report the hit rate. This is the only place the cache lectures touch hardware.

---

## Lab 10 — Instruction Decoder I
**Mon 11/9 · Tue 11/10** · Evidence **E1, E2, E4, E7**
**One idea:** *A control unit is one truth table with 16 output columns.*

**Scope decision:** this CPU implements exactly **eight instructions** — the ones its program uses. Do not present the 40-instruction ISA as the target; it is not, and pretending otherwise is what makes this lab traumatic.

### Specification — the control table

Sixteen control signals, defaults first. **A row shows only what differs from the default** — which is exactly how the reference implementation is written, and how they should write it.

**Defaults (every instruction, before decoding):**

| Signal | Default | Signal | Default |
|---|---|---|---|
| `ALU_Asel` | `0` AOUT | `NIAG_sel` | `00` NSA |
| `IR_Xsel` | `0` ZERO | `NIAG_cond` | `000` NONE |
| `IR_Xlsft` | `1` ×2 | `NIAG_strb` | `1` |
| `IR_strb` | `1` | `RF_Dsel` | `00` ALU |
| `DM_en` | `0` | `RF_strb` | `0` HOLD |
| `DM_rw` | `1` READ | `RF_Wsel` | `00` RD |
| `DM_strb` | `0` | `RF_oe` | HiZ |

**This lab's four rows:**

| Instr | opcode / func | ALU_func | ALU_Asel | ALU_Ssel | IR_Xsel | IR_Xlsft | RF_Dsel | RF_strb | RF_Wsel |
|---|---|---|---|---|---|---|---|---|---|
| `ADD` | `000000` / `100000` | ADD | AOUT | – | – | – | ALU | **1** | RD |
| `SLL` | `000000` / `000000` | SLL | AOUT | **RS** | – | – | ALU | **1** | RD |
| `ADDI` | `001000` | ADD | **IMMED** | – | **SIGN** | **NONE** | ALU | **1** | **RT** |
| `LUI` | `001111` | ADD | **IMMED** | – | ZERO | **NONE** | ALU | **1** | **RT** |

### Equations — instruction recognition, then control

```
Recognisers (minterms over the opcode/func fields):
   R_ADD  = (op = 000000)·(func = 100000)
   R_SLL  = (op = 000000)·(func = 000000)
   I_ADDI = (op = 001000)
   I_LUI  = (op = 001111)

Control signals as sums of recognisers:
   RF_strb  = R_ADD + R_SLL + I_ADDI + I_LUI
   ALU_Asel = I_ADDI + I_LUI                       (1 = immediate)
   RF_Wsel  = RD·(R_ADD + R_SLL) + RT·(I_ADDI + I_LUI)
   IR_Xsel  = I_ADDI                               (1 = sign extend)
   IR_Xlsft = ¬(I_ADDI + I_LUI)                    (default is ×2; ADDI and LUI force NONE)
```

**This is the moment the whole course closes.** Say it plainly: *In Lab 1 you wrote one Boolean equation from a four-row table. This is the same operation on a table with eight rows and sixteen output columns. Nothing new has been introduced. The control unit of a processor is a truth table.*

### Build
`Decoder` (partial) — `Instruction : in std_logic_vector(31 downto 0)` · `CtrlSgnls : out CTRL_SIGNL_REC`.
Structure: assign all defaults into a variable, then override per instruction. **The default assignment is what stops the synthesiser inferring sixteen latches.**

### Testbench
One encoded instruction per row (hex constants given), asserting the full control bundle. Plus one *unimplemented* opcode, asserting the safe default: no register write, no memory write, sequential PC.

### Overleaf `lab10.tex`
Their four rows of the table, the recogniser equations, and the safe-default statement.

### Pitfalls
Missing defaults → sixteen inferred latches (this *will* happen; budget for it) · confusing `rt` and `rd` as destination · forgetting that opcode `000000` needs the `func` field.

---

## Lab 11 — Instruction Decoder II
**Mon 11/16 · Tue 11/17** · Evidence **E1, E2, E4, E7**
**One idea:** *Memory access and control flow are just four more rows.*

### Specification — the remaining four rows

| Instr | opcode | ALU_func | ALU_Asel | IR_Xsel | IR_Xlsft | RF_Dsel | RF_strb | RF_Wsel | RF_oe | DM_en | DM_rw | DM_strb | NIAG_sel | NIAG_cond |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `LW` | `100011` | ADD | IMMED | SIGN | NONE | **MEM** | **1** | **RT** | – | **1** | READ | – | – | – |
| `SW` | `101011` | ADD | IMMED | SIGN | NONE | – | 0 | – | **DRIVE** | **1** | **WRITE** | **1** | – | – |
| `BLEZ` | `000110` | ADD | AOUT | SIGN | **×2** | – | 0 | – | – | – | – | – | **REL** | **LEZ** |
| `J` | `000010` | – | – | – | – | – | 0 | – | – | – | – | – | **ABS** | NONE |

### Equations — the complete control unit

```
   I_LW = (op = 100011)   I_SW = (op = 101011)
   I_BLEZ = (op = 000110)  J_J = (op = 000010)

   RF_strb   = R_ADD + R_SLL + I_ADDI + I_LUI + I_LW
   ALU_Asel  = I_ADDI + I_LUI + I_LW + I_SW
   DM_en     = I_LW + I_SW
   DM_rw     = ¬I_SW                          (1 = read)
   DM_strb   = I_SW
   RF_oe     = I_SW
   IR_Xsel   = I_ADDI + I_LW + I_SW + I_BLEZ  (1 = sign extend)
   IR_Xlsft  = I_BLEZ                          (minimised — see the don't-care note below)
   NIAG_sel  = ABS·J_J + REL·I_BLEZ + NSA·(everything else)
   NIAG_cond = LEZ·I_BLEZ
```

**A don't-care worth stopping on.** The reference decoder defaults `IR_Xlsft` to ×2 and overrides it to NONE for `ADDI`, `LUI`, `LW` and `SW`. That leaves `ADD`, `SLL` and `J` sitting at ×2 — which looks wrong, until you notice those three never read the extender output at all. The value is a **don't-care**, so both of these are correct:

```
as implemented   IR_Xlsft = ¬(I_ADDI + I_LUI + I_LW + I_SW)
minimised        IR_Xlsft = I_BLEZ
```

They disagree on exactly the rows nobody looks at. Ask the class which one they would ship, and let them argue: the minimised form is smaller, the implemented form reads more directly as a table. Both are defensible, and understanding why the question is even open is the point.

Three further observations, because each is a lecture concept made physical:

1. `ALU_Asel` is high for four unrelated instructions — **the adder is shared** between arithmetic and address computation. That is the whole reason a load and an add cost the same hardware.
2. `RF_strb` is low for `SW`, `BLEZ` and `J` — **stores and branches never write a register.** Getting this wrong corrupts registers silently and is the single hardest Lab 12 bug to find.
3. `DM_rw = ¬I_SW`: one instruction out of eight determines a whole control line. Real control units are this sparse.

### Build
Merge Labs 10 and 11 into one `Decoder`. Produce the **complete 8-row control table as a standalone artifact** — it is their Lab 12 debugging reference, and they should print it.

### Testbench
Table-driven: an array of (instruction, expected control bundle) pairs, looped over. Report the count: *8 instructions, 8 vectors, all pass*, plus the unimplemented-opcode default.

### Overleaf `lab11.tex`
The complete control table, all recogniser and control equations, and the three observations above in their own words.

### Pitfalls
`SW` writing a register · `BLEZ` forgetting `IR_Xlsft = ×2` · `J` leaving `RF_strb` at a stale value · don't-cares written as `'Z'` where a real `'0'` is needed.

---

## Lab 12 — CPU Integration
**Mon 11/23 · Tue 11/24** · Evidence **E1–E7, all**
**One idea:** *Debugging a system means predicting it first.*

Almost no new VHDL. This lab is wiring, timing discipline, and evidence.

### The timing contract — put this on the board before anything else

| Edge | What happens |
|---|---|
| ↑ SysClk | `IRreg ← IMemData` (instruction latched) |
| ↓ SysClk | `PCreg ← NIAGout` when `NIAG_strb` · RAM performs its write |

One instruction per clock period. Reads are combinational and settle during the period; both writes happen on the falling edge, after the control signals are stable. **Every Lab 12 bug that is not a mis-wire is an edge mistake.**

### Build

Fill in `CPU.vhd` (skeleton provided, `TODO`s marked): instantiate `ROM`, `Decoder`, `ImmedXtnd`, `RegFile`, `ALUinMUX`, `ALUsftMUX`, `ALU`, `NIAG`, `DselMUX`, `TriBuffer`, `RAM`, `DinMUX`, and add the two clocked processes. Use **named association** in every `port map`, without exception.

### The expected result — this is what "working" means

Running the Lab 9 ROM program to completion:

| Quantity | Expected |
|---|---|
| Iterations of the loop body | 10 |
| Final `r1` | `0x00000000` |
| Final `r2` | `0x00000400` = 1024 = 2¹⁰ |
| `RAM[0..3]` | `00 00 04 00` |
| Instructions executed | **45** — so 45 clock cycles, CPI = 1. They must derive it, not be told it |

The 45 breaks down as: 2 setup instructions, 10 full loop passes of 4 instructions each, one final pass of 2 (`ADDI`, then a taken `BLEZ`), and the closing `SW`. Have them derive it before simulating — a trace with a different cycle count is a bug, and this is how they will know.

*Your CPU computes 2¹⁰.* That is the sentence to end the semester on.

### Deliverable — the execution trace table

Fixed columns, so it is gradeable at a glance:

| Cyc | PC | Instruction | Disassembly | ALU out | RegWr | Value | Next-PC source |
|---|---|---|---|---|---|---|---|
| 0 | `0x00` | `3C01000B` | `LUI r1,11` | `0000000B` | r1 | `0000000B` | NSA |
| 1 | `0x04` | `3C020001` | `LUI r2,1` | `00000001` | r2 | `00000001` | NSA |
| 2 | `0x08` | `2021FFFF` | `ADDI r1,r1,-1` | `0000000A` | r1 | `0000000A` | NSA |
| 3 | `0x0C` | `18200002` | `BLEZ r1,+2` | `0000000A` | — | — | NSA (not taken) |
| … | | | | | | | |

**First five rows must be hand-computed before simulating.** Grade the hand-computation, not just the match.

### Debugging method — teach it explicitly, do not leave it to chance

The guided example is a pre-wired CPU containing **two deliberate wiring errors**. Walk the method:

1. Is `PCreg` advancing by 4? If not, the fault is in NIAG or the falling-edge process. Stop there.
2. Is `IRreg` the instruction the ROM table says? If not, ROM addressing or the rising-edge process.
3. Do the control signals match the Lab 11 table for this opcode? If not, the decoder. **This is why they printed the table.**
4. Only then look at the ALU or the register file.

Bisect, never guess. A student who opens the waveform and stares at all 40 signals at once will still be staring at 5:40.

### Fallback so nobody is blocked
TA reference components are available for any lab a student did not finish. Using one costs nothing on this lab's grade — the earlier lab's grade simply stands. Integration is never gated on an earlier miss.

### Overleaf `lab12.tex` — the longest chapter
Timing contract · full trace table · hand-computed first five rows · annotated waveform of ~20 cycles · full evidence set E1–E7 · Discussion of the integration bugs. Expect 8–12 pages.

### Pitfalls
Positional `port map` · clock-edge mistakes · `'U'` propagating from one uninitialised signal (almost always the real cause of a dead CPU) · `TriBuffer` and `RAM` both driving the data bus.

---

## Final Lab — Demonstration and Extension
**Mon 11/30 · Tue 12/1** · Full report due end of finals week

**Structure:** 30 min demonstrations (≈ 4 min each, two questions from a fixed bank so it is fair across sections) · 70 min extension work · 20 min submission and close.

### Extension — pick exactly one

| Track | Task | Deliverable | Best for |
|---|---|---|---|
| **A · New instruction** | Add `SUB`, `BEQ`, or `ORI` end to end: recogniser, control row, ALU or NIAG change, testbench, trace | The instruction working in the CPU | A clean, certain finish |
| **B · Performance** | Add cycle and instruction counters; measure CPI over the program; vary the ROM program and compare | A CPI table and one paragraph relating it to Amdahl's law | Students who like measurement |
| **C · Pipeline** | Insert one pipeline register between fetch and execute; make arithmetic instructions work; **document the hazards it breaks** | The hazard analysis — a *working* pipeline is not required | Strong students |

Track C's grading rule must be stated in the handout or nobody will choose it: **breaking it correctly and explaining precisely why is full credit.**

### Final report additions
Executive summary of the CPU · resource and timing summary across all labs · a reflection chapter (*what I would design differently*) · complete code appendix · the CP4 "Response to feedback" section.

Tell them plainly: this is a portfolio piece. Students who hear that write noticeably better final chapters.

---

## Dependency map — what to hand a student who missed a week

```
Lab 1  TransLatch ──> Lab 2  MSFlipFlop, RegN ──┬──> Lab 6  RegFile ────┐
                                                 └──> Lab 7  NIAG_Reg ──┤
Lab 3  Mux2/Mux3 ───────────────────────────────────> Lab 8  NIAG_MUX ──┤
Lab 4  ImmedXtnd ───────────────────────────────────> Lab 7  NIAG_Rel ──┤
Lab 4  TriBuffer ───────────────────────────────────> Lab 9  RAM ───────┼──> Lab 12 CPU ──> Final
Lab 5  ALU ─────────────────────────────────────────────────────────────┤
Lab 10 Decoder I ──> Lab 11 Decoder II ─────────────────────────────────┘
```

**Critical path: 10 → 11 → 12.** A student who misses Lab 10 gets the reference decoder immediately, not at the Lab 12 deadline.
