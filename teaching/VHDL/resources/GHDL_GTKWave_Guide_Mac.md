# GHDL + GTKWave Setup Guide for macOS
## VHDL Simulation & Waveform Viewing

---

## Part 1: Installation

### Prerequisites
- macOS 10.13 or later
- Homebrew installed ([install here](https://brew.sh) if needed)

### Step 1: Install GHDL and GTKWave

Open Terminal and run:

```bash
brew install ghdl gtkwave
```

That's it! Both tools will be installed automatically.

### Step 2: Verify Installation

Check if everything works:

```bash
ghdl --version
gtkwave --version
```

You should see version info for both tools. ✓

---

## Part 2: Your First VHDL Simulation

### Step 1: Create a Working Directory

```bash
mkdir ~/vhdl_projects
cd ~/vhdl_projects
```

### Step 2: Create a Simple VHDL File

Create a file called `adder.vhdl` with this code:

```vhdl
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity adder is
    Port ( 
        A : in STD_LOGIC_VECTOR (3 downto 0);
        B : in STD_LOGIC_VECTOR (3 downto 0);
        SUM : out STD_LOGIC_VECTOR (4 downto 0)
    );
end adder;

architecture Behavioral of adder is
begin
    SUM <= STD_LOGIC_VECTOR(unsigned(A) + unsigned(B));
end Behavioral;
```

### Step 3: Create a Testbench

Create a file called `adder_tb.vhdl`:

```vhdl
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity adder_tb is
end adder_tb;

architecture tb of adder_tb is
    component adder
        Port ( 
            A : in STD_LOGIC_VECTOR (3 downto 0);
            B : in STD_LOGIC_VECTOR (3 downto 0);
            SUM : out STD_LOGIC_VECTOR (4 downto 0)
        );
    end component;

    signal A_tb : STD_LOGIC_VECTOR (3 downto 0);
    signal B_tb : STD_LOGIC_VECTOR (3 downto 0);
    signal SUM_tb : STD_LOGIC_VECTOR (4 downto 0);

begin
    UUT: adder port map (A => A_tb, B => B_tb, SUM => SUM_tb);

    process
    begin
        -- Test case 1: 3 + 5 = 8
        A_tb <= "0011";
        B_tb <= "0101";
        wait for 10 ns;

        -- Test case 2: 7 + 9 = 16
        A_tb <= "0111";
        B_tb <= "1001";
        wait for 10 ns;

        -- Test case 3: 15 + 1 = 16
        A_tb <= "1111";
        B_tb <= "0001";
        wait for 10 ns;

        wait;
    end process;

end tb;
```

---

## Part 3: Simulate & View Waveforms

### Step 1: Analyze the Design

In Terminal (from `~/vhdl_projects`), run:

```bash
ghdl -a adder.vhdl
ghdl -a adder_tb.vhdl
```

This compiles your VHDL files. (No output = success!)

### Step 2: Elaborate (Bind) the Testbench

```bash
ghdl -e adder_tb
```

Again, no output = success. ✓

### Step 3: Run Simulation & Generate Waveforms

```bash
ghdl -r adder_tb --vcd=adder_sim.vcd
```

This creates a file called `adder_sim.vcd` (waveform data).

You should see output like:
```
note: simulator finished at 31 ns with status ok
```

### Step 4: Open Waveforms in GTKWave

```bash
gtkwave adder_sim.vcd
```

GTKWave will open with your simulation waveforms! 🎉

#### How to Use GTKWave:

1. **Left panel**: Shows all signals. Expand the testbench to see A_tb, B_tb, SUM_tb
2. **Drag signals** to the right panel to view them
3. **Zoom**: Scroll or use the zoom controls
4. **Search**: Use Ctrl+F to find signals
5. **Measure**: Click markers on the timeline

---

## Quick Reference: Workflow

Once set up, every time you simulate:

```bash
# Compile
ghdl -a your_design.vhdl
ghdl -a your_testbench.vhdl

# Elaborate
ghdl -e testbench_entity_name

# Simulate
ghdl -r testbench_entity_name --vcd=output_name.vcd

# View
gtkwave output_name.vcd
```

---

## Troubleshooting

### "ghdl: command not found"
- Make sure Homebrew installed it: `brew list | grep ghdl`
- If missing, reinstall: `brew install ghdl`

### "Elaboration error" or "Compilation error"
- Check your VHDL syntax
- Make sure entity and architecture names match
- Verify testbench component instantiation

### GTKWave won't open the .vcd file
- Make sure simulation completed successfully (look for "finished at X ns")
- Try: `gtkwave output_name.vcd &` (run in background)

### Signals not showing in GTKWave
- Expand the tree in the left panel
- Make sure you dragged signals to the right panel
- Click "Insert" or drag signals from the tree

---

## Example: Full Simulation from Scratch

```bash
# Create directory
mkdir ~/vhdl_lab
cd ~/vhdl_lab

# Create adder.vhdl (copy code from Step 2 above)
nano adder.vhdl

# Create adder_tb.vhdl (copy code from Step 3 above)
nano adder_tb.vhdl

# Simulate
ghdl -a adder.vhdl
ghdl -a adder_tb.vhdl
ghdl -e adder_tb
ghdl -r adder_tb --vcd=adder_sim.vcd

# View
gtkwave adder_sim.vcd
```

---

## Notes for Your Assignments

- ✅ **GHDL works great for**: Behavioral simulation, debugging logic, verifying test cases
- ❌ **Missing from GHDL**: RTL schematic viewer, synthesis, place-and-route
- 💡 **For synthesis/mapping**: You'll need access to Vivado or Quartus (lab machine or VirtualBox)

Good luck! 🚀

---

*Created by your TA for VHDL Lab | Questions? Ask during lab hours*
