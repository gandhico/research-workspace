# EE362 — Computer Organization Laboratory
## Digital Systems Design using VHDL — First-Class Presentation Speech

**Presentation date:** August 31, 2026  
**Instructor/TA:** Gandhi Contreras  
**Course:** EE362 — Introduction to Computer Organization  

> **Practice goal:** Do not try to memorize every sentence. Memorize the transitions, the core definitions, and the complete design workflow. Use the diagrams as visual prompts while speaking.

---

## Slide 1 — Computer Organization Laboratory

Good afternoon, everyone, and welcome to the Computer Organization Laboratory.

My name is Gandhi Contreras, and during this semester I will be working with you in the laboratory portion of EE362, Introduction to Computer Organization.

The main perspective I want us to have in this lab is shown directly in the title: **Digital Systems Design using VHDL**.

So, although we are going to learn VHDL, the objective is not simply to learn another language. Our objective is to understand how we can take a digital-system specification, describe it, verify it, synthesize it, and eventually obtain actual hardware.

Today is our introduction to that process. We will first build the conceptual foundation, and then we will move into the practical workflow that we will use throughout the semester.

---

## Slide 2 — Today’s Content

Today we are going to build the big picture first.

We will begin by defining a digital system and connecting the physical world with digital signals and VHDL. Then we will discuss the technologies used to implement digital systems, the different ways we can represent a system, and the different levels of abstraction.

After that, we will connect these concepts to binary values, combinational and sequential logic, digital-system hierarchy, and computer organization.

Finally, we will discuss what VHDL is, the complete digital-design workflow, what you will do in every laboratory, how the laboratory will be assessed, and where all of these exercises are taking us during the semester.

---

## Slide 3 — Transition: What is a Digital System?

So, before we write any VHDL, we need to answer the most fundamental question: **what exactly is a digital system?**

---

## Slide 4 — What is a Digital System?

A digital system is an interconnected set of hardware components that represents, processes, stores, and transfers information using a finite set of discrete values in order to perform a specified function.

There are three ideas here that I want you to remember.

First, we have **information** coming into the system as inputs.

Second, the hardware does something with that information. It may process it, store it, transfer it, or combine several of those operations.

And third, the system produces an output that corresponds to a defined function.

If you look at the diagram in the center, this input-process-output idea is something we will see repeatedly during the semester: inputs enter the system, the hardware processes, stores, or transfers information, and then outputs are produced.

At the bottom, there is another way to summarize exactly the same concept: **discrete information goes into digital hardware, and the hardware implements a defined function**.

This definition can describe something as simple as a logic gate or something as complex as a complete processor.

**Optional interaction:** Can someone give me an example of a digital system that you used today?

Whatever example you choose — a phone, a laptop, a digital watch, or a car controller — internally it is constructed from the same basic principles that we will study here.

---

## Slide 5 — Transition: From the Physical World to VHDL

Now that we know what a digital system is, let us connect this definition to the real physical world.

---

## Slide 6 — From the Physical World to VHDL

This slide is important because it connects everything we are going to do in software tools with actual electronics.

Start on the left.

In the **physical world**, we have things such as switches, buttons, and sensors. Those devices produce or modify an **electrical signal**, which is ultimately represented by a voltage on a wire.

But in digital design, we do not normally want to reason continuously about every possible voltage. Instead, we establish **logic levels**, for example LOW and HIGH.

Those logic levels can then be represented as binary values: zero and one.

In VHDL, we describe those logical values and the relationships between them. Finally, the FPGA implements the resulting logic as a real hardware circuit.

So the direction is:

**physical phenomenon → electrical signal → logic level → binary representation → VHDL description → FPGA hardware.**

Now look at the center figure. An analog signal varies continuously, while a digital signal uses discrete values or levels.

The image on the right gives us a familiar example. Sound pressure is naturally analog. We can sample that signal, convert the samples into discrete numerical information, and then process that information digitally.

The key idea is that **VHDL is not disconnected from the physical world**. The code we write eventually represents electrical behavior implemented by hardware.

---

## Slide 7 — Transition: Device Technologies

Once we have a digital design, the next question is: **what kind of physical technology can implement it?**

---

## Slide 8 — Device Technologies

There are different technologies available for implementing digital systems.

At a broad level, this slide separates two important families.

The first family is **ASICs — Application-Specific Integrated Circuits**. These are devices in which customization is performed as part of the fabrication process.

Within ASIC technologies we can distinguish full-custom ASICs, standard-cell ASICs, and gate-array ASICs.

The images on the right help us see that this is not only an abstract description. We are looking at actual physical layouts on silicon: a die, analog blocks, standard-cell logic, and even a NAND gate at the physical level.

The second family is **programmable logic devices**.

Here we have SPLDs, CPLDs, and finally FPGAs.

The essential distinction for this course is that an FPGA gives us a programmable hardware fabric. Instead of fabricating a new chip every time we change our design, we configure the resources that already exist inside the FPGA to implement our circuit.

That is why FPGA technology is so useful for learning digital design and for rapid hardware development.

---

## Slide 9 — Device Technologies: Comparison

This slide makes those differences more concrete.

At the top, a **full-custom ASIC** gives very fine control. The transistor structures and physical layout are customized for one application.

With a **standard-cell ASIC**, the designer works with predefined cells and customizes their placement and routing.

A **gate-array ASIC** begins with a prefabricated base structure and customizes the interconnections.

Then we move into programmable technologies.

An SPLD provides relatively simple programmable AND/OR logic.

A CPLD combines multiple macrocells with programmable interconnections.

And finally, the FPGA contains a much richer array of resources: lookup tables, flip-flops, programmable routing, memory, and DSP resources.

The example at the bottom is an **Altera Cyclone V**, which is especially relevant to the kind of FPGA workflow we will use.

For our laboratory, the important technology is the **FPGA**, because it allows us to repeatedly design, synthesize, test, modify, and reimplement hardware without manufacturing a new integrated circuit.

---

## Slide 10 — Transition: System Representation and Levels of Abstraction

Now we know what a digital system is and where it can be implemented. The next major concept is **how engineers describe the same system from different viewpoints and at different levels of detail**.

---

## Slide 11 — System Representation and Levels of Abstraction

There are two concepts on this slide that are closely related, but they are not identical.

First: **system representation**.

We can represent the same system behaviorally, structurally, or physically.

A **behavioral representation** tells us **what the system does**.

A **structural representation** tells us **which components are used and how those components are interconnected**.

And a **physical representation** tells us how those components and connections are actually implemented and located in the device.

This distinction will become very important when we compare behavioral and structural VHDL later.

Now look at the table below. Here we are talking about **levels of abstraction**.

At the processor level, we think in terms of processors, memory, buses, computation, and communication.

At the register-transfer, or RT, level, we think in terms of registers, adders, multiplexers, finite-state machines, and operations that occur over clock cycles.

At gate level, the building blocks are gates, latches, and flip-flops.

And at transistor level, we are considering continuous electrical behavior involving transistors, resistance, and capacitance.

The important engineering idea is that **we do not need to think about every transistor every time we design a processor**.

Abstraction allows us to manage complexity.

Throughout this laboratory we will primarily work around the logic and RTL levels, while still understanding how they connect upward to computer organization and downward to physical hardware.

---

## Slide 12 — System Representation Diagrams

These two diagrams illustrate the previous idea visually.

On the left, notice that we can move from a behavioral view toward a structural view and eventually toward a physical view.

At a high behavioral level we might talk about algorithms. At another level we can describe register-transfer operations. Below that, Boolean equations.

On the structural side, the corresponding building blocks change: processors and memories at high levels, then adders, registers, multiplexers, gates and flip-flops, and eventually transistors and physical layout.

The diagram on the right gives us another way to visualize the same idea: there are different domains of representation and several levels of abstraction.

The key point is not to memorize every label in these diagrams.

The key point is this: **the same digital system can be viewed in multiple ways, and a good digital designer must be able to move between those views**.

Later, when Quartus generates an RTL schematic from your VHDL, you will actually see this transition happen.

---

## Slide 13 — Transition: Binary Values in VHDL

Now let us move from these high-level representations to the values we use to describe digital information.

---

## Slide 14 — Binary Values in VHDL

One small distinction is very important here:

**digital does not automatically mean binary**.

Digital means that the system uses a finite set of discrete states.

If there are exactly two states, then the system is binary. If there are more than two, it is multivalued.

For most of our hardware, the two physical states are represented as LOW and HIGH, and we commonly label them zero and one.

But zero and one are only symbols.

A binary system can also be interpreted as FALSE and TRUE, OFF and ON, open and closed, a released or pressed button, reset and set, or an LED being off and on.

So the sentence at the bottom is the most important one:

**Binary does not require the symbols zero and one. It requires two distinguishable states.**

This becomes especially clear when we connect VHDL signals to switches, buttons, and LEDs on actual FPGA hardware.

**Optional interaction:** If an LED can only be OFF or ON, is that binary? Yes — even though I did not use the symbols zero and one.

---

## Slide 15 — `std_logic`

Now we need to make one important distinction between physical hardware and our VHDL model.

Physical FPGA hardware is fundamentally binary, but during design and simulation we often need more information than simply zero and one.

That is why `std_logic` provides several possible values.

The two values you will use constantly are `'0'`, logic LOW, and `'1'`, logic HIGH.

But two other values are extremely important for debugging.

`'U'` means **uninitialized**. When you see U in a simulation, it often means that a signal has not yet been assigned a known value.

`'X'` means **unknown**. That tells us that the simulator cannot determine whether the value should be zero or one.

You may also encounter `'Z'`, which represents high impedance, and the dash, which can represent a don't-care condition.

The weak values L, H, and W are less important for our introductory exercises.

So remember the distinction:

**The hardware is binary. The simulation model is richer so that it can help us describe and diagnose digital behavior.**

When you run your first simulations in Questa and suddenly see U or X, do not panic. Those values are giving you useful information about your design.

---

## Slide 16 — Transition: Combinational vs Sequential

With that foundation, we can now separate digital circuits into two major categories that we will use throughout the semester.

---

## Slide 17 — Combinational vs Sequential Digital Systems

The fundamental distinction is shown in the first row of this table.

In a **combinational circuit**, the output depends only on the **present inputs**.

There is no stored state.

For example, if I change the inputs of an adder, decoder, or multiplexer, the output is determined by those current inputs.

This is represented by the diagram on the lower left: **inputs → logic → outputs**.

Sequential logic adds something very important: **state or memory**.

Now the output depends on the present inputs **and on information stored from the past**.

That is why the lower-right diagram has a feedback relationship with state or memory.

Latches, flip-flops, registers, and counters are examples of sequential elements.

Sequential systems also commonly involve a clock because state changes must be coordinated in time.

From the VHDL perspective, this is the difference between describing purely logical relationships and describing **state plus timing**.

This distinction is fundamental. Almost everything we construct later in a processor is built by combining combinational and sequential hardware.

---

## Slide 18 — Transition: Digital-System Hierarchy

So how do these small components grow into something as complex as a processor? Through hierarchy.

---

## Slide 19 — Digital-System Hierarchy

This slide shows the progression from the smallest pieces to the complete system.

We begin with **bits**.

Bits are manipulated by **logic gates**.

Gates are combined to form **combinational and sequential circuits**.

Those circuits become larger **functional blocks**.

Functional blocks are organized into the **datapath and control**.

Datapath and control form the core of a **processor**.

And the processor becomes part of a complete **digital system**.

This hierarchy is important because throughout the semester we will gradually move upward.

Today, something like a full adder may look like a small exercise. Later, adders become part of an ALU. The ALU becomes part of a datapath. The datapath combines with control and memory to form a processor.

So every small circuit we build has a place in the larger architecture.

---

## Slide 20 — Transition: From Digital Logic to Computer Organization

And this brings us directly to the connection between digital logic and the main subject of this course: computer organization.

---

## Slide 21 — From Digital Logic to Computer Organization

Look at the diagram from bottom to top.

At the bottom, we have **digital logic**.

Using digital logic, we build registers, ALUs, multiplexers, and buses. These elements form the **datapath**.

The processor also requires **control** and **memory**.

Together, these elements define the organization of the computer hardware.

Above that sits the **Instruction Set Architecture, or ISA**.

The ISA is the interface between software and processor hardware.

Software sees instructions and an architectural interface. Underneath that interface, the hardware organization has to make those instructions actually happen.

So this laboratory is helping you understand what exists **below the software interface**.

When a processor performs an arithmetic instruction, somewhere underneath that instruction are registers, multiplexers, logic, control signals, memory, and an ALU — all constructed from the digital concepts we have just discussed.

---

## Slide 22 — Transition: VHDL

Now we have all the pieces needed to understand the role of VHDL.

---

## Slide 23 — VHDL: Describing Hardware

This is the central idea I want you to associate with VHDL:

**VHDL describes hardware.**

It may look like programming when we type it, but our goal is very different from writing an ordinary software program.

When we write synthesizable VHDL, we are describing hardware behavior or hardware structure that a synthesis tool can translate into a circuit.

That is why throughout this laboratory I will continually ask you questions such as:

**What hardware does this line infer?**

**What circuit do you expect Quartus to generate?**

And:

**Does the generated circuit match your design intention?**

We should always connect the code back to hardware.

---

## Slide 24 — Transition: The Digital Design Workflow

And because digital design is much more than writing code, we are going to use a complete engineering workflow.

---

## Slide 25 — The Digital Design Workflow

This slide is probably the most important operational slide in today's presentation.

This is the workflow I want you to become comfortable with during the semester.

It begins on the left with **design**.

First, we need a **specification**. Before touching VHDL, we need to know exactly what the circuit is supposed to do.

From that specification, depending on the problem, we may build a **truth table or timing table**.

Then we derive or understand the **logic and schematic**.

Only after we understand the intended hardware do we move to the **VHDL RTL description**.

Now we move into verification.

We create a **testbench**.

We simulate the design.

We inspect the **waveforms** to determine whether the observed behavior matches the specification.

Then we synthesize the design in **Quartus**.

After synthesis we inspect the **RTL Viewer and Technology Map**. These tools allow us to see the hardware that Quartus inferred from our VHDL.

Then we can examine **timing and resource utilization**.

And when appropriate, the final stage is to implement and test the design using **FPGA hardware**.

Notice something extremely important:

**Writing VHDL is only one step in this process.**

A design that compiles is not automatically a correct design.

A design that simulates correctly still needs to be understood after synthesis.

And a professional digital designer should be able to connect the original specification to the final hardware implementation.

This complete chain is what I want you to practice repeatedly.

### Workflow sentence to say slowly

**Specification → truth or timing table → logic and schematic → VHDL RTL → testbench → simulation → waveform analysis → synthesis → RTL Viewer and Technology Map → timing and resources → FPGA hardware.**

---

## Slide 26 — Transition: What Will You Do in Every Laboratory?

So how will we turn that workflow into something you actually do every week?

---

## Slide 27 — What Will You Do in Every Laboratory?

Each laboratory follows a progression from learning to independent application.

We begin with **introductory concepts**, so you understand the theory and the objective of the circuit.

Then I will work through **instructor examples**. Those examples are where we can examine the workflow together and discuss what is happening at every stage.

After that comes the most important part: the **student practice case**.

You will receive a related problem, and now you will perform the workflow yourselves.

Your progress and results from that practice become your **lab submission**.

At the same time, you will progressively document your work in the **Overleaf project**.

By the end, the laboratory project should not be a collection of disconnected answers. It should document how you designed, implemented, verified, and interpreted digital systems during the semester.

So the progression is:

**learn → observe → practice → submit → document → complete the project.**

---

## Slide 28 — Transition: Laboratory Assessment

That structure is also reflected directly in how the laboratory will be assessed.

---

## Slide 29 — Laboratory Assessment

There are two main components, each worth fifty percent.

The first is **Laboratory Practices**, worth 100 points.

Here I expect you to complete the assigned design exercise using the full workflow and submit evidence showing your progress and results.

This evaluates whether you can take a specification, translate it into digital hardware, develop the VHDL, simulate it, synthesize it, and analyze the result.

The second component is the **Project or Overleaf documentation**, also worth 100 points.

Here the emphasis is not just getting an answer. I expect you to professionally document the concept, specification, schematic, VHDL workflow, simulation waveforms, results, and your engineering interpretation.

In other words: **show me not only what happened, but that you understand why it happened.**

We will also have **periodic reviews**.

These are opportunities to demonstrate progress, receive feedback, correct problems, and improve your design.

That iterative process — design, test, identify a problem, modify, and test again — is normal engineering practice.

---

## Slide 30 — Transition: Laboratory Philosophy

All of that assessment comes from one simple philosophy for this laboratory.

---

## Slide 31 — Laboratory Philosophy

I would like you to remember this sentence during the semester:

**We are not learning VHDL syntax in isolation. We are learning how to transform a specification into digital hardware.**

That means I care about correct VHDL, of course.

But I also care about whether you understand the specification, whether your schematic makes sense, whether your simulation verifies the correct behavior, and whether the synthesized hardware corresponds to what you intended.

If you simply memorize VHDL syntax, you have missed the purpose of the laboratory.

The real skill is being able to move from **an engineering idea to a verified hardware implementation**.

---

## Slide 32 — Transition: Course Progression

Finally, let me show you where these introductory exercises are taking us during the semester.

---

## Slide 33 — Course Progression

This diagram gives you the roadmap for the complete course.

We begin at the top with the foundations of digital systems.

On one side we have **combinational logic**: Boolean algebra, decoders, multiplexers, comparators, and adders.

On the other side we have **sequential logic**: latches, flip-flops, master-slave structures, registers, and counters.

These two branches come together as we build more useful computational structures, including the **ALU**.

From there we move toward the components needed by a processor: the **instruction decoder**, memory and load-store operations, the **program counter**, and the **register file**.

These elements form the **datapath**.

The datapath works together with **control**, including finite-state-machine concepts.

Eventually these pieces come together into a **single-cycle CPU**.

Then we can explore how processor organization becomes more sophisticated: **pipelining**, **memory hierarchy**, **cache**, and **virtual memory**.

Below that we reach buses, memory-mapped I/O, interrupts, performance analysis, and modern acceleration concepts.

So when you are working on a decoder, multiplexer, latch, register, or adder in an early laboratory, remember this diagram.

Those are not isolated textbook circuits.

They are the building blocks we need in order to understand how an actual computer is organized.

We are going to construct that understanding progressively from logic-level hardware all the way to processor-level organization.

---

## Slide 34 — Closing

So that is the framework we are going to use for the Computer Organization Laboratory this semester.

We will begin with relatively small digital circuits, but every exercise will train the same engineering process: understand the specification, design the hardware, describe it in VHDL, verify it, synthesize it, and analyze the implementation.

As the semester progresses, those small circuits will become larger functional blocks and ultimately components of a processor.

Thank you, everyone.

Now, let us move from the introduction to our first practical design.

---

# Five sentences worth memorizing

1. **VHDL is not disconnected from the physical world; the code we write eventually represents hardware.**
2. **Behavioral tells us what the system does, structural tells us what components it uses and how they connect, and physical tells us how those components are implemented.**
3. **Combinational logic depends on present inputs; sequential logic depends on present inputs plus stored state.**
4. **Writing VHDL is only one step in the digital design workflow.**
5. **We are not learning VHDL syntax in isolation; we are learning how to transform a specification into digital hardware.**

# First-class VHDL vocabulary

- **ENTITY:** what goes into and comes out of the circuit.
- **ARCHITECTURE:** what the circuit does or how it is constructed.
- **SIGNAL:** a value that represents a hardware connection or wire.
- **BEHAVIORAL DESCRIPTION:** describes the function of the circuit.
- **STRUCTURAL DESCRIPTION:** describes components and their interconnections.
- **TESTBENCH:** simulation-only VHDL used to verify a design.
- **SYNTHESIS:** translation from an HDL description to a hardware implementation.
