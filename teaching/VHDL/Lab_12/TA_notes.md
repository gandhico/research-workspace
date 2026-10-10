# Lab 12 — TA Notes

Fill in after the Monday section, before Tuesday.

---

## What this session actually is

Almost no new VHDL. It is **55 minutes of wiring and debugging**, and it will feel
harder to the students than Lab 5 did, despite being technically much shallower.
That gap — hard-feeling, easy-looking — is worth naming at Open so nobody concludes
they have fallen behind.

Your job this session is **not** to explain concepts. It is to keep twenty people
from flailing. The single most valuable thing you do is interrupt random-change
debugging and walk somebody through check 1.

## Before the session — three things

- [ ] **Hand out reference components at the START**, to anyone who needs them.
      Not at 5:15. Say out loud: *using a reference component costs you nothing on
      this lab.* Some students will otherwise struggle in silence rather than take
      what they assume is a penalty.
- [ ] Check who has their **printed control table**. Step 3 needs it. Have a few
      spare printouts.
- [ ] Have Example 1 (`cpu_broken`) loaded and ready.

## The four checks — put them on the whiteboard and leave them there

```
1. Is the PC advancing by 4?           -> no: NIAG or reset
2. Is IR what the ROM table says?      -> no: ROM addressing or fetch
3. Do control signals match the table? -> no: the decoder
4. Only now, the datapath.
```

Point at it every time someone asks for help. Do not diagnose for them — ask *"which
check are you on?"*. If the answer is "I'm just looking at the waveform", that is the
problem, and it is the one worth fixing.

## Known friction points, in order

| Time | What happens | What to do |
|---|---|---|
| ~3:55 | Students missing an earlier component | Reference components, immediately, no penalty |
| ~4:10 | Positional `port map` | Twelve components. Fix it now. |
| ~4:25 | `'U'` everywhere | One undriven signal — usually a missing `port map` connection or an internal signal declared and never assigned |
| ~4:30 | **Random-change debugging begins** | Stop them. Walk check 1. This is the intervention that saves sessions. |
| ~4:40 | `'X'` on the memory bus | `TriBuffer` and `RAM` both driving. Check `RF_oe`. |
| ~4:45 | Clock-edge confusion | The register file and NIAG need the inverted clock |
| ~4:55 | **Hard checkpoint** | *"Hands up if your CPU is not fetching yet."* Note the wording — fetching, not compiling. |
| ~5:05 | `Asel`/`Bsel` swapped | Three instruction types still work. Symptom: `r2` never doubles. |
| ~5:15 | Runs but stores 0 | The store value is coming from `Bout` instead of `Aout` |

## Two things that will surprise you

1. **Metavalue warnings are a diagnostic, not noise.** Several appear in the first
   few cycles and then stop. Warnings that *never* stop mean a signal is never
   driven. Point this out — it is a genuinely useful skill and students read it as
   an error message they should ignore.

2. **The trace sampling point.** The provided testbench samples just *before* the
   falling edge. If a student modifies it to sample after, `ADDI r1,r1,-1` appears to
   compute the next iteration's value, because the combinational logic recomputes
   from the just-written `r1`. The hardware is fine; the observer is lying. Worth
   mentioning at the spec walk — it cost me an hour while building this lab.

## Timing

| Planned | Phase |
|---|---|
| 3:45–3:52 | Open: the program, the one idea, the timing contract on the board |
| 3:52–4:05 | The four checks on the board + Example 1 |
| 4:05–4:15 | Spec walk: the three wiring traps |
| 4:15–5:25 | Build and debug — **longer than usual, and it needs to be** |
| 5:25–5:40 | Check-off |
| 5:40–5:45 | Close |

Cut the examples before you cut the build time. The method on the whiteboard matters
more than watching you demonstrate it.

## The line to end on

> *"Your processor computes two to the tenth. Three months ago you were writing a
> four-row truth table for a latch. Same loop every week — specification, truth
> table, equations, VHDL, simulation, check. Nothing was ever added to the method.
> That is engineering, and it is the actual thing you are taking away from this
> course."*

---

## After Monday — fill this in

**How many got the CPU running by 5:25?**


**How many needed reference components? Did anyone resist taking them?**


**Where did people get stuck longest?**


**Did the four-checks whiteboard work? Who ignored it?**


**What to say differently on Tuesday:**


---

## After Tuesday

**Did both sections end in the same place?**


**Anyone whose CPU never ran** — they need a plan before the Final Lab:


**Carry into the Final Lab:**
Demonstrations plus one extension track. Anyone whose CPU is not running needs to
be settled before then — either finish it in office hours or take the full reference
CPU so they can still demonstrate and do an extension. **Nobody should reach the
final session without a working machine to show.**
