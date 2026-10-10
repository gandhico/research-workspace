# Lab 3 — Slide Content
### Multiplexers · 10 slides · 15 minutes

---

## Slide 1 — Title
> **EE 362 — Laboratory 3**
> **Multiplexers**

---

## Slide 2 — Open with the number
> A 32-bit 3-to-1 multiplexer has **98 inputs**.
>
> An exhaustive truth table needs **2⁹⁸ rows.**

*Say:* Before anything else — work this out with me. Four 32-bit inputs, no, three
32-bit inputs plus a 2-bit selector: 98. How many rows does the exhaustive table
need? *(let them get to 2⁹⁸)* That is more rows than you have atoms in your body.
So we are not writing that table. Now watch what we write instead.

---

## Slide 3 — Four rows
> | # | Sel1 | Sel0 ‖ Y | note |
> |---|---|---|---|
> | 0 | 0 | 0 ‖ **A** | |
> | 1 | 0 | 1 ‖ **B** | |
> | 2 | 1 | 0 ‖ **C** | |
> | 3 | 1 | 1 ‖ **0** | *defined default* |
>
> **Type C** — enumerate the control, name the source.

*Say:* Four rows. Complete specification. The rows say "Y equals B" — they name a
*source*, not a value. That is a compressed table, and it is not a shortcut: it is
the only reason datapath design is possible at all. From here on you will use Type
C almost exclusively. Type E survives while you have four inputs or fewer.

Point at row 3: *that is a decision, not an accident. Leave it blank and you get a
latch — we will see it happen in twenty minutes.*

---

## Slide 4 — Today's one idea
> ### A multiplexer is how one control bit steers thirty-two bits of data.

---

## Slide 5 — Factor it yourself
> $$Y_i = \overline{S_1}\overline{S_0}A_i + \overline{S_1}S_0 B_i + S_1\overline{S_0}C_i + S_1S_0\cdot 0$$
>
> **Factor $\overline{S_1}$ out of the first two terms. Two minutes.**

*Say:* Row 3 outputs zero, so it contributes no product term at all — that is the
first simplification, and it is free. Now factor. Take two minutes, I will wait.

---

## Slide 6 — What you just built
> $$Y_i = \overline{S_1}\left(\overline{S_0}A_i + S_0 B_i\right) + S_1\overline{S_0}C_i$$
>
> The bracket is a **2-to-1 mux**.
> The whole expression is a **second 2-to-1 mux**.
>
> ### You factored an equation and a circuit came out.

*Say:* Look at the bracket. That is a 2-to-1 multiplexer choosing A or B. And the
whole expression is a second 2-to-1 multiplexer choosing between that one and C.
You factored algebra and a *structure* appeared. Factoring an expression and
splitting a design into sub-blocks are the same operation. This is the first place
you can see it, and it stays true all the way to the CPU.

---

## Slide 7 — Three ways to say it
> ```vhdl
> Y <= B when Sel = '1' else A;              -- when/else: a priority chain
>
> with Sel select                             -- with/select: a table
>     Y <= A when '0', B when '1', A when others;
>
> case Sel is                                 -- case: a table, sequentially
>     when '0' => Y <= A;
>     when '1' => Y <= B;
>     when others => Y <= A;
> end case;
> ```
> Same hardware. Pick the one that makes the **intent** obvious.

*Say:* All three synthesise identically — Example 1 asserts it vector by vector,
and unlike Lab 2 the RTL Viewer pictures match too. The difference is purely how
the source reads to a human. A multiplexer is a table, so `with/select` or `case`
usually reads best. Whichever you choose, your report has to say why.

---

## Slide 8 — The trap
> ```vhdl
> if    Sel = "00" then Y <= A;
> elsif Sel = "01" then Y <= B;
> elsif Sel = "10" then Y <= C;
> end if;                          -- Sel = "11" assigns NOTHING
> ```
> *"No assignment happens, so the output keeps its previous value."*
>
> ### You have read that sentence before. Lab 1. It was the latch.

*Say:* In Lab 1 that sentence was the feature — we wanted memory. Here it is a bug:
you wanted combinational logic and you described something that remembers. Quartus
builds the latch, warns you, and most people never read the warning.

And note *why* it slipped through: a `case` would not let you do this. VHDL forces
a case to cover every selector value, so a case without `when others` is a compile
error, not a latch. Use `case` and the language protects you.

---

## Slide 9 — Your assignment
> 1. **`Mux2`** — generic width. Any style; **say why you chose it.**
> 2. **`Mux3`** — generic width, **including row 3**. Use `case`.
> 3. **`CPUMuxes`** — four wrappers. `MUX2x5` is done as a worked example.
> 4. **Testbench** — ≥ 6 vectors: every selector value, a **no-latch check**, and one 5-bit check.
>
> Coverage: **exhaustive on the selector, distinct patterns on the data.**

*Say:* Distinct patterns matters. If A, B and C all carry the same value, a
multiplexer that ignores its selector entirely and always returns A passes every
test you wrote. Give each input a value only it has. Then a wrong selection cannot
hide.

---

## Slide 10 — Where these go, and tonight
> | entity | role in your CPU |
> |---|---|
> | `MUX2x5` | `DselMUX` — register write-destination |
> | `MUX2x32` | `ALUinMUX` — register or immediate |
> | `MUX3x32` | `DinMUX` — ALU / memory / return address |
>
> **E1** no latch warning · **E2** RTL Viewer: **zero** storage · **E7** waveform
>
> **Tonight:** table, factored equation, and the **CPU diagram with your four muxes circled.**
>
> **Checkpoint 1 — Sunday 27 September** — Labs 0 through 3.

*Say:* Register count for `MUX3x32` must be zero. Any storage element means you
inferred a latch. And tonight's figure is the annotated block diagram — it is the
first time you see the whole datapath, and from Lab 7 you will be reading it every
week. Checkpoint 1 is this Sunday: the whole report so far, not just this chapter.

---

## Production notes
- 10 slides. Slide 5 must have real silence on it — do not fill the two minutes.
- Slide 8 works far better run live (Example 3) than read off the slide. Use the
  slide as the summary *after* the demo.
- Have the CPU block diagram ready to project full screen at slide 10.
