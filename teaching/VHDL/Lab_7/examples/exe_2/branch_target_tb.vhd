--------------------------------------------------------------------------------
-- EE 362 - Lab 7, Example 2 - Testbench, using real instructions
--
-- Every vector here is either an instruction from the Lab 12 ROM program or a
-- deliberately chosen boundary. Hand-compute each one before you run it - the
-- point of this example is that you can predict the hardware.
--
-- The BACKWARD branch is the one that catches sign-extension bugs. A negative
-- offset that was zero-extended produces a target roughly 256 KB away instead
-- of a few instructions back, which is very obvious once you look and very easy
-- to miss if all your test offsets are positive.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity branch_target_tb is
end entity branch_target_tb;

architecture test of branch_target_tb is

    signal PC     : std_logic_vector(31 downto 0) := (others => '0');
    signal Immed  : std_logic_vector(15 downto 0) := (others => '0');
    signal NSA    : std_logic_vector(31 downto 0);
    signal Target : std_logic_vector(31 downto 0);

begin

    DUT : entity work.branch_target
        port map (PC => PC, Immed => Immed, NSA => NSA, Target => Target);

    stimulus : process

        variable errors : natural := 0;

        procedure check (wnsa, wtgt : in std_logic_vector(31 downto 0);
                         msg : in string) is
        begin
            if NSA /= wnsa then
                report "FAIL (NSA): " & msg severity error;
                errors := errors + 1;
            end if;
            if Target /= wtgt then
                report "FAIL (Target): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- THE REAL ONE. BLEZ r1, +2 at address 0x0C in the Lab 12 program.
        --   NSA    = 0x0C + 4 = 0x10
        --   offset = 2 x 4    = 0x08
        --   target = 0x18       <- the SW instruction, the loop exit
        PC <= x"0000000C"; Immed <= x"0002"; wait for 10 ns;
        check(x"00000010", x"00000018",
              "1. BLEZ r1,+2 at 0x0C targets 0x18 - the loop exit");

        -- Offset zero: the target is simply the next instruction. A branch
        -- that is taken but goes nowhere special.
        PC <= x"00000010"; Immed <= x"0000"; wait for 10 ns;
        check(x"00000014", x"00000014", "2. offset 0 targets the next instruction");

        -- BACKWARD BRANCH. offset -1 means "one instruction before the next
        -- one", i.e. branch to the instruction currently being executed.
        --   NSA    = 0x20 + 4 = 0x24
        --   offset = -1 x 4   = -4 = 0xFFFFFFFC
        --   target = 0x24 - 4 = 0x20
        PC <= x"00000020"; Immed <= x"FFFF"; wait for 10 ns;
        check(x"00000024", x"00000020",
              "3. BACKWARD: offset -1 lands back on this instruction");

        -- A real loop-shaped backward branch: -4 instructions
        --   NSA    = 0x30 + 4 = 0x34
        --   offset = -4 x 4   = -16 = 0xFFFFFFF0
        --   target = 0x34 - 16 = 0x24
        PC <= x"00000030"; Immed <= x"FFFC"; wait for 10 ns;
        check(x"00000034", x"00000024", "4. BACKWARD: -4 instructions");

        -- Largest positive offset: 0x7FFF instructions forward
        --   offset = 0x7FFF x 4 = 0x0001FFFC
        PC <= x"00000000"; Immed <= x"7FFF"; wait for 10 ns;
        check(x"00000004", x"00020000", "5. largest forward offset");

        -- Most negative offset: -0x8000 instructions back
        --   offset = -32768 x 4 = -131072 = 0xFFFE0000
        --   target = 0x00100004 - 0x20000 = 0x000E0004
        PC <= x"00100000"; Immed <= x"8000"; wait for 10 ns;
        check(x"00100004", x"000E0004", "6. most negative offset");

        if errors = 0 then
            report "PASS - branch_target: all targets computed correctly."
                severity note;
        else
            report "FAILED - branch_target: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
