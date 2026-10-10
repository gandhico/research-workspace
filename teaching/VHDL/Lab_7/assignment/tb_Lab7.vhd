--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 7 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- NOTE HOW THE FOUR COMPONENTS ARE WIRED. This is exactly how the CPU wires
-- them in Lab 12:
--
--     NIAG_Reg  --PC-->  NIAG_NSA  --NSA-->  NIAG_Rel  --Rel-->
--                                               ^
--     ImmedXtnd  --Xtnd32-------------------- ---'
--
-- The extender is SHARED: in the CPU its output also feeds the ALU. That is why
-- NIAG_Rel takes an already-extended value instead of extending it itself.
--
-- REQUIRED, at least six checked vectors, including all of:
--
--   [required] the real BLEZ from the Lab 12 program: PC = 0x0C, offset +2.
--              Target must be 0x18. HAND-COMPUTE IT FIRST.
--   [required] a BACKWARD branch with a negative offset. If your offsets are
--              all positive you have not tested sign extension at all.
--   [required] NSA tracking PC with NO clock edge, proving it is combinational
--   [required] the PC loading an address that is NOT NSA - it is a register,
--              not a counter
--   [required] Strb = '0' at a clock edge: the PC must hold (a stall)
--   [required] asynchronous reset asserted BETWEEN edges
--
-- HAND-COMPUTE EVERY TARGET BEFORE YOU SIMULATE. Write the arithmetic in your
-- report. If you cannot predict the hardware you cannot debug it, and Lab 12
-- is entirely debugging.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab7 is
end entity tb_Lab7;

architecture test of tb_Lab7 is

    constant PERIOD : time := 20 ns;

    signal NextPC : std_logic_vector(31 downto 0) := (others => '0');
    signal Strb, Rst, clk : std_logic := '0';
    signal PC : std_logic_vector(31 downto 0);

    signal NSA, Rel : std_logic_vector(31 downto 0);

    signal Immed16 : std_logic_vector(15 downto 0) := (others => '0');
    signal Xsel, Xlsft : std_logic := '1';       -- branch mode: sign-extend, x4
    signal Xtnd32 : std_logic_vector(31 downto 0);

    signal running : boolean := true;

begin

    U_PC : entity work.NIAG_Reg
        port map (NextPC => NextPC, Strb => Strb, Rst => Rst, clk => clk, PC => PC);

    U_NSA : entity work.NIAG_NSA
        port map (PC => PC, NSA => NSA);

    U_XTND : entity work.ImmedXtnd
        port map (Immed16 => Immed16, Xsel => Xsel, Xlsft => Xlsft,
                  Xtnd32 => Xtnd32);

    U_REL : entity work.NIAG_Rel
        port map (NSA => NSA, Xtnd32 => Xtnd32, Rel => Rel);

    clock_gen : process
    begin
        while running loop
            clk <= '0'; wait for PERIOD / 2;
            clk <= '1'; wait for PERIOD / 2;
        end loop;
        wait;
    end process clock_gen;

    stimulus : process

        variable errors : natural := 0;

        procedure chk (got, want : in std_logic_vector(31 downto 0);
                       msg : in string) is
        begin
            if got /= want then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure chk;

        -- Load the PC on the next rising edge. One line per PC change.
        procedure setpc (addr : in std_logic_vector(31 downto 0)) is
        begin
            wait until falling_edge(clk);
            NextPC <= addr; Strb <= '1';
            wait until rising_edge(clk);
            wait for 1 ns;
            Strb <= '0';
        end procedure setpc;

    begin

        ----------------------------------------------------------------------
        -- Reset. This one fails until NIAG_Reg is built.
        ----------------------------------------------------------------------
        Rst <= '1'; wait for 3 ns;
        chk(PC, x"00000000", "reset vector is 0");
        -- TODO: check NSA is already 0x04 here - it is combinational
        Rst <= '0';

        ----------------------------------------------------------------------
        -- *** REQUIRED *** The real BLEZ from the Lab 12 program
        --   PC = 0x0C, offset = +2.  Hand-compute NSA, the scaled offset,
        --   and the target BEFORE you fill these in.
        ----------------------------------------------------------------------
        setpc(x"0000000C");
        Immed16 <= x"0002"; wait for 5 ns;
        -- TODO: check NSA, Xtnd32 and Rel. The target is 0x18.


        ----------------------------------------------------------------------
        -- *** REQUIRED *** A BACKWARD branch
        --   Try offset -1 (0xFFFF) and offset -4 (0xFFFC).
        --   If all your offsets are positive, sign extension is untested.
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** NSA is combinational
        --   Change the PC, then check NSA followed with no further clock edge.
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** The PC is a register, not a counter
        --   Load an arbitrary address that is not NSA.
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** Strb low at an edge: the PC holds (a stall)
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** Asynchronous reset, asserted BETWEEN edges
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- Verdict - do not delete
        ----------------------------------------------------------------------
        if errors = 0 then
            report "PASS - Lab 7: all checks passed." severity note;
        else
            report "FAILED - Lab 7: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
