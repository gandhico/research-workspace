# Lab 2 — Slide Content
### Master–Slave Flip-Flop and the N-Bit Register · 11 slides · 15 minutes

Slide text is what goes on the slide. *Say* is what you say over it.

---

## Slide 1 — Title
> **EE 362 — Laboratory 2**
> **Master–Slave Flip-Flop and the N-Bit Register**

---

## Slide 2 — Last week / this week
> Lab 1: a latch. **Level**-sensitive — a wire while `En` is high.
> Lab 2: a flip-flop. **Edge**-triggered — changes at one instant only.
>
> *Nobody designs an edge. It falls out of two latches.*

*Say:* Last week's latch has a problem for a processor. A value that changes
whenever its input changes cannot hold state across a cycle — it would race around
the datapath uncontrolled. We need something that changes at exactly one instant.

---

## Slide 3 — Today's one idea
> ### Two latches with opposite enables make an edge.

---

## Slide 4 — Walk the clock

> | | master (`En = not Clk`) | slave (`En = Clk`) |
> |---|---|---|
> | `Clk = 0` | **transparent**, follows D | holding |
> | `Clk = 1` | holding | **transparent**, copies master |

*Say:* Walk it with your finger. Clock low — master follows D, slave holds. Clock
rises — master freezes on whatever D was at that instant, slave opens and copies
it. The output can only ever change right there. Nobody built an "edge"; it is a
consequence of two level-sensitive parts wired in opposition. That is how a lot of
digital design works: the useful behaviour is emergent.

---

## Slide 5 — Same equation, twice
> $$Q_m^{+} = \overline{Clr}(\overline{Clk}\,D + Clk\,Q_m)$$
> $$Q^{+} = \overline{Clr}(Clk\,Q_m + \overline{Clk}\,Q)$$
>
> Both are **Lab 1's equation**. Only the enable changed.

*Say:* You are not learning a new circuit. You are wiring two copies of the one you
already own, with opposite enables. Write that in your report — it is the honest
description of what you did.

---

## Slide 6 — Structural vs behavioural
> ```vhdl
> -- what you build today, to see the mechanism
> MASTER : entity work.TransLatch port map (...);
> SLAVE  : entity work.TransLatch port map (...);
>
> -- what you would actually ship
> if rising_edge(Clk) then Q <= D; end if;
> ```
> Same waveform. **Completely different RTL Viewer.**

*Say:* Both descriptions produce identical behaviour — Example 2 asserts it
vector by vector. But the synthesiser recognises `rising_edge` as an idiom and maps
it onto a real flip-flop primitive in the fabric, which is smaller and faster than
two latches. From here on, every clocked design in this course is behavioural. You
built the structural one once, so you know what is underneath.

---

## Slide 7 — The register: Table T
> | # | Rst | Ld | Clk ‖ Q⁺ | note |
> |---|---|---|---|---|
> | 0 | 1 | – | – ‖ **0** | async reset |
> | 1 | 0 | – | not ↑ ‖ **Q** | hold between edges |
> | 2 | 0 | 0 | ↑ ‖ **Q** | edge, not loading |
> | 3 | 0 | 1 | ↑ ‖ **D** | load |
>
> $$Q_i^{+} = \overline{Rst}\,(Ld\cdot D_i + \overline{Ld}\cdot Q_i)$$

*Say:* Compare that equation with last week's latch. `En` became `Ld`, `Clr` became
`Rst`, and the enable is sampled at an edge instead of continuously. It is the same
circuit with new names. Recognising that is worth more than memorising either one.

---

## Slide 8 — The sensitivity list rule changes
> **Lab 1 (combinational / latch):** every signal the process reads.
>
> **Lab 2 (clocked):** the clock, plus **asynchronous** controls. Nothing else.
>
> ```vhdl
> process (Clk, Rst)     -- not Ld, not D
> ```

*Say:* This is the one place where a short sensitivity list is correct, and you
should be able to say why: `D` and `Ld` are only ever read *at the edge*, and the
edge is caused by `Clk`. `Rst` is there because it is asynchronous — it must act
without waiting for a clock. The skeleton ships with this list incomplete; work
out what is missing and justify it in your report.

---

## Slide 9 — Generics
> ```vhdl
> entity RegN is
>     generic (N : positive := 32);
>     port (D : in std_logic_vector(N-1 downto 0); ...);
> ```
> ```vhdl
> R5 : entity work.RegN
>     generic map (N => 5)      -- no semicolon here
>     port map (...);
> ```
> The CPU needs width **5** and width **32**.

*Say:* Write `Reg5` and `Reg32` separately and you fix every bug twice, and they
drift apart. One parameterised entity cannot drift apart from itself. Note the
syntax: `generic map` first, `port map` second, no semicolon between them. That is
the most common syntax error of the week.

---

## Slide 10 — Your assignment
> **Step 1:** overwrite `TransLatch.vhd` with **your own** Lab 1 version.
>
> 1. **`MSFlipFlop`** — structural, two latches, `Clr` to **both**
> 2. **`RegN`** — generic, load enable, async reset, nested `if`
> 3. **Testbench** — ≥ 6 vectors, and it must include:
>    - the **edge vector** (toggle D between edges, Q moves once)
>    - async reset asserted **between** edges
>    - an edge with `Ld = '0'`
>
> Top level is `RegN`. The Fitter must report **32 registers.**

*Say:* Clear both latches, not just the slave — otherwise the master pushes the old
value back at the next edge and your clear undoes itself one cycle later. And the
register count is a correctness check, not just a cost number: if it is not 32, you
inferred something you did not intend.

---

## Slide 11 — Evidence, and tonight
> **E1** Flow Summary · **E2** RTL Viewer — **both** versions · **E7** waveform
>
> The money shot: `D` toggling three times in one clock period, `Q` moving once.
>
> **Tonight, 10 minutes:** table, both equations, that waveform, one sentence.
>
> **Checkpoint 1 — Sunday 27 September** — Labs 0 through 3.

---

## Production notes
- 11 slides. If short on time, cut slide 6 — Example 2 makes the same point live.
- Slides 5 and 7 should show the Lab 1 equation alongside, so the "same circuit,
  new names" claim is visible rather than asserted.
- Keep the CPU block diagram on the side screen; point at the PC and the register
  file when you say where `RegN` ends up.
