# Lab 2 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## Before the session

- [ ] Confirm students have their Lab 1 `TransLatch.vhd`. Anyone whose Lab 1 latch
      never worked needs the reference version handed to them **at 3:45**, not at
      5:00 — Lab 2 is blocked without it. Check your Lab 1 `TA_notes` list.
- [ ] Whiteboard: draw the two-latch diagram by hand and walk the clock with your
      finger. Do not project it.
- [ ] Have Example 1's waveform ready to project — the three-toggles-one-move
      picture is the whole lesson and you want it visible while you talk.
- [ ] Print pre-labs.

## Diagnostic table — sensitivity list failures

**Measured against the reference testbench, not guessed.**

| Signature | Cause |
|---|---|
| **Only** the two "async reset acts immediately" checks fail; everything else passes | `Rst` missing from `RegN`'s sensitivity list. The reset is being sampled at clock edges, so it behaves synchronously. |
| Flip-flop checks fail with `'U'` from the first check | Their `TransLatch` is still the empty skeleton — they did not do Step 1 |
| Everything fails from check 1 | `MSFlipFlop` architecture body still empty, or latches wired to the same enable |

The rule to hand them: **which checks fail names the missing signal.** Reset checks
failing means `Rst`. That is a real debugging method and it is worth 60 seconds.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| 3:45 | Someone has no working Lab 1 latch | Hand over the reference immediately. Do not let it eat their session. |
| ~4:05 | "The simulation is frozen" | Clock process with no `wait` — it is looping at time zero. **Announce this before the build phase**; it will otherwise happen five times. |
| ~4:15 | `generic map (...); port map (...)` | No semicolon between them. Error message points elsewhere. |
| ~4:40 | Width mismatch on the 5-bit instance | They forgot `generic map` and silently got the default 32 |
| ~4:55 | **Hard checkpoint** | *"Hands up if your design does not compile yet."* |
| ~5:05 | "It works but the reset test fails" | The sensitivity list. See the table above — give the signature, not the answer. |
| ~5:15 | Results vary run to run | They are changing `D` on a rising edge. Setup-time violation. Move stimulus to after falling edges. |

## Two things worth saying out loud

1. **The structural flip-flop is a one-time exercise.** Say plainly: *you build it
   structurally once so you know what is underneath, and then you never write it
   that way again.* Otherwise students think structural is the expected style and
   carry it into Lab 5, where it would be miserable.

2. **The register count is a correctness check.** Top level is `RegN`, so the
   Fitter reports the register count for a 32-bit register. It must be 32. Anything
   else means something unintended was inferred. This is the first week E4 carries
   real diagnostic weight, and it sets up Lab 6, where the count must be ~1024.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:55 | Open + two-latch diagram on the board |
| 3:55–4:20 | Examples 1, 2, 3 |
| 4:20–4:30 | Spec walk |
| 4:30–5:25 | Build (checkpoint at 4:55) |
| 5:25–5:40 | Check-off |
| 5:40–5:45 | Close |

Example 3 (generics) is the one to compress if you are behind — the syntax is on
the slide and in the spec, and students can pick it up from `reg_n.vhd` directly.
Example 1 must not be cut; it is the lesson.

---

## After Monday — fill this in

**What took longer than planned:**


**What confused people (their exact words):**


**What to say differently on Tuesday:**


**Students who still owe Lab 1, or who needed a reference component:**


---

## After Tuesday

**Did both sections end in the same place?**


**Check-off answer quality — Q1 / Q2:**


**Carry into Lab 3:**
Lab 3 opens with the 2⁹⁸-rows argument and needs nothing from Lab 2 as a
component. But note anyone whose `RegN` does not work — it is needed again in
Lab 7 (the program counter) and Lab 6 (the register file).
