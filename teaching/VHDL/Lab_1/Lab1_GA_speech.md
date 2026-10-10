# Lab 1 - 2 | Transparent Latch & Flip Flops

A Transparent Latch is commonly named gated D latch, and it is a level-sensitive sequential digital logic circuit that passes its data input directly to its output whenever the enable signal is active. 

It gets the name of transparent because while enabled, changes at the input D instantly propagate through to the output Q, making the lath behave as though it were invisible or transparent. 

(Transparent Latch) When the enable is active, the output Q continuously follows the input D. 
If D changes while E remains high, Q changes immediately. 

Inactive high or opaque, hold state. When enable 0 the latch freezes. The output Q retains the last state D had right before E transitioned to low, ignoring any subsequent changes on D. 

The bridge between Combinational Logic - where outputs are immediate, pure mathematical functions of present inputs- and sequential logic, where a circuit remembers past states. 

The fundamental shift: Output depends on Memory. 
In combinational logic, every circuit is stateless: out = f (in)
If you change the input, the output updates after a short propagation delay (t_PD). 

In sequential logic, we introduce a feedback loop that holds state, along with an enable/clock signal that controls when new data is allowed to enter memory: 

Out_next = f(inputs, current state)

 Gate-Level Schematics for a D LatchA Gated D Latch consists of two stages:An Input Steering Stage: Directs the input $D$ and Enable $E$ into complementary control signals.A Bistable Storage Stage (SR Core): Formed by cross-coupled gates creating positive feedback.

 


The primary distinction between a latch and a flip-flop lies in how they are triggered: 

Transparent Latch is level-sensitive, remains open and continuously sampling D for the entire duration E is active (high or low).

Flip-Flop (edge-triggered). Only captures the data input on a specific instantaneous transition of the clock (rising edge or falling edge). Changes on D before or after the clock edge are ignored. 

Key Benefit: Output $Q$ updates only once per full clock period (on the clock transition edge), preventing feedback loops and timing instability in synchronous digital logic.

To step from basic combinational logic to robust sequential storage, we build memory structures layer-by-layer: first constructing latches using pure NAND/NOR gates, then isolating active windows to create edge-triggered Flip-Flops and Master-Slave configurations.

