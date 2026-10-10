--------------------------------------------------------------------------------
-- EE 362 - Lab 11, Example 2 - Proving two different answers are both right
--
-- The testbench walks all eight instructions and does two things:
--
--   1. asserts the two implementations AGREE wherever the extender is read
--   2. reports where they DISAGREE, and confirms those are exactly the
--      instructions that ignore the extender
--
-- If (1) ever failed, one of them would be wrong. (2) failing would mean the
-- minimisation was pointless.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity dontcare_tb is
end entity dontcare_tb;

architecture test of dontcare_tb is

    signal Instr : std_logic_vector(31 downto 0) := (others => '0');
    signal Xsel_table, Xsel_min, Reads_Ext : std_logic;

    type instr_array is array (natural range <>) of std_logic_vector(31 downto 0);

    -- All eight instructions of this CPU.
    constant PROG : instr_array := (
        x"00221820",    -- ADD  r3,r1,r2
        x"00021040",    -- SLL  r2,r2,1
        x"2021FFFF",    -- ADDI r1,r1,-1
        x"3C01000B",    -- LUI  r1,11
        x"8C220004",    -- LW   r2,4(r1)
        x"AC020000",    -- SW   r2,0(r0)
        x"18200002",    -- BLEZ r1,+2
        x"08000002"     -- J    0x08
    );

    type name_array is array (natural range <>) of string(1 to 4);
    constant NAMES : name_array := ("ADD ", "SLL ", "ADDI", "LUI ",
                                    "LW  ", "SW  ", "BLEZ", "J   ");

begin

    DUT : entity work.dontcare
        port map (Instr => Instr, Xsel_table => Xsel_table,
                  Xsel_min => Xsel_min, Reads_Ext => Reads_Ext);

    stimulus : process
        variable errors    : natural := 0;
        variable disagreed : natural := 0;
    begin

        report "instr | reads extender | table | minimised | agree?" severity note;

        for i in PROG'range loop
            Instr <= PROG(i);
            wait for 10 ns;

            -- (1) Where the extender IS read, the two must agree.
            if Reads_Ext = '1' and Xsel_table /= Xsel_min then
                report "FAIL: " & NAMES(i) &
                       " reads the extender but the two implementations disagree"
                    severity error;
                errors := errors + 1;
            end if;

            -- (2) Note the disagreements, and check they are all don't cares.
            if Xsel_table /= Xsel_min then
                disagreed := disagreed + 1;
                if Reads_Ext = '1' then
                    report "FAIL: disagreement on an instruction that CARES"
                        severity error;
                    errors := errors + 1;
                else
                    report "  " & NAMES(i) &
                           "  |      no        |   " &
                           std_logic'image(Xsel_table) & "  |    " &
                           std_logic'image(Xsel_min) &
                           "   |  differ - and it cannot matter" severity note;
                end if;
            else
                report "  " & NAMES(i) & "  |      " &
                       std_logic'image(Reads_Ext) &
                       "       |   " & std_logic'image(Xsel_table) &
                       "  |    " & std_logic'image(Xsel_min) &
                       "   |  same" severity note;
            end if;
        end loop;

        -- The minimisation must actually differ somewhere, or it bought nothing.
        if disagreed = 0 then
            report "FAIL: the two implementations never differ - " &
                   "then the 'minimisation' is not one" severity error;
            errors := errors + 1;
        else
            report "The two implementations differ on " &
                   integer'image(disagreed) &
                   " instructions, and every one of them ignores the extender." &
                   " Both are correct; the minimised one is cheaper."
                severity note;
        end if;

        report "Testing note: a testbench that pinned IR_Xsel down for ADD would" &
               " be testing an accident of the implementation, not a requirement." &
               " Over-specifying a test is its own kind of bug." severity note;

        if errors = 0 then
            report "PASS - dontcare: both implementations agree wherever it matters."
                severity note;
        else
            report "FAILED - dontcare: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
