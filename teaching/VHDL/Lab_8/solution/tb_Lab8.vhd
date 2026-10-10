--------------------------------------------------------------------------------
-- EE 362 - Lab 8 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- The centrepiece is the SCRIPTED SEQUENCE at the end: the PC walking through
-- sequential, taken branch, not-taken branch, J, JR and a return, in one
-- continuous run. That waveform is the report's main figure.
--
-- 24 checks.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity tb_Lab8 is
end entity tb_Lab8;

architecture test of tb_Lab8 is

    constant PERIOD : time := 20 ns;

    signal Index   : std_logic_vector(25 downto 0) := (others => '0');
    signal Xtnd32  : std_logic_vector(31 downto 0) := (others => '0');
    signal RegAddr : std_logic_vector(31 downto 0) := (others => '0');
    signal Sel     : std_logic_vector(1 downto 0)  := NIAG_SEL_NSA;
    signal Cond    : std_logic_vector(2 downto 0)  := NIAG_COND_NONE;
    signal Strb    : std_logic := '1';
    signal Zero, Neg, Rst : std_logic := '0';
    signal clk : std_logic := '0';
    signal PC, NSA, Rtn : std_logic_vector(31 downto 0);
    signal running : boolean := true;

begin

    DUT : entity work.NIAG
        port map (Index => Index, Xtnd32 => Xtnd32, RegAddr => RegAddr,
                  Sel => Sel, Cond => Cond, Strb => Strb,
                  Zero => Zero, Neg => Neg, Rst => Rst, clk => clk,
                  PC => PC, NSA => NSA, Rtn => Rtn);

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

        -- Advance one instruction with the current control settings.
        procedure step is
        begin
            wait until rising_edge(clk);
            wait for 1 ns;
        end procedure step;

    begin

        ----------------------------------------------------------------------
        -- Reset
        ----------------------------------------------------------------------
        Rst <= '1'; wait for 3 ns;
        chk(PC,  x"00000000", "1. reset vector");
        chk(NSA, x"00000004", "2. NSA available immediately");
        chk(Rtn, x"00000004", "3. Rtn is NSA");
        Rst <= '0';

        ----------------------------------------------------------------------
        -- Sequential execution
        ----------------------------------------------------------------------
        Sel <= NIAG_SEL_NSA; Cond <= NIAG_COND_NONE;
        step; chk(PC, x"00000004", "4. sequential to 0x04");
        step; chk(PC, x"00000008", "5. sequential to 0x08");
        step; chk(PC, x"0000000C", "6. sequential to 0x0C");

        ----------------------------------------------------------------------
        -- NOT-TAKEN branch at 0x0C: BLEZ with a positive result.
        -- LEZ = N + Z. With Z=0 and N=0 the branch is not taken, so the PC
        -- must fall back to NSA = 0x10.
        ----------------------------------------------------------------------
        Sel <= NIAG_SEL_REL; Cond <= NIAG_COND_LEZ;
        Xtnd32 <= x"00000008";              -- offset +2 instructions
        Zero <= '0'; Neg <= '0';            -- result is positive
        wait for 1 ns;
        step;
        chk(PC, x"00000010", "7. BLEZ not taken -> falls back to NSA");

        ----------------------------------------------------------------------
        -- Go back to 0x0C and take the branch this time (result zero).
        ----------------------------------------------------------------------
        Sel <= NIAG_SEL_ABS; Index <= "00" & x"000003"; Cond <= NIAG_COND_NONE;
        wait for 1 ns;
        step;
        chk(PC, x"0000000C", "8. jumped back to 0x0C");

        Sel <= NIAG_SEL_REL; Cond <= NIAG_COND_LEZ;
        Xtnd32 <= x"00000008";
        Zero <= '1'; Neg <= '0';            -- result is zero -> LEZ taken
        wait for 1 ns;
        chk(NSA, x"00000010", "9. NSA at 0x0C is 0x10");
        step;
        chk(PC, x"00000018", "10. BLEZ TAKEN -> 0x18, the loop exit");

        ----------------------------------------------------------------------
        -- The real J from the Lab 12 program: at 0x14, index 2 -> 0x08
        ----------------------------------------------------------------------
        Sel <= NIAG_SEL_ABS; Index <= "00" & x"000005"; Cond <= NIAG_COND_NONE;
        wait for 1 ns;
        step;
        chk(PC, x"00000014", "11. positioned at 0x14");

        Index <= "00" & x"000002";
        wait for 1 ns;
        step;
        chk(PC, x"00000008", "12. J 0x08 - the jump that closes the loop");

        ----------------------------------------------------------------------
        -- Register jump (JR): a FULL 32-bit address, which is how JR escapes
        -- the 256 MB region that J is confined to.
        ----------------------------------------------------------------------
        Sel <= NIAG_SEL_REG; RegAddr <= x"A0000040"; wait for 1 ns;
        step;
        chk(PC, x"A0000040", "13. JR to a full 32-bit address");
        chk(Rtn, x"A0000044", "14. Rtn from there is that address + 4");

        -- ...and confirm a J from HERE stays in region 0xA
        Sel <= NIAG_SEL_ABS; Index <= "00" & x"000002"; wait for 1 ns;
        step;
        chk(PC, x"A0000008", "15. J from region 0xA stays in region 0xA");

        ----------------------------------------------------------------------
        -- Strb low: a stall. The PC holds through the edge.
        ----------------------------------------------------------------------
        Strb <= '0'; Sel <= NIAG_SEL_NSA; wait for 1 ns;
        step;
        chk(PC, x"A0000008", "16. Strb low: PC holds (a stall)");
        Strb <= '1';

        ----------------------------------------------------------------------
        -- Every condition, exercised through the whole NIAG
        ----------------------------------------------------------------------
        Rst <= '1'; wait for 3 ns; Rst <= '0';
        Sel <= NIAG_SEL_REL; Xtnd32 <= x"00000010";   -- +4 instructions

        Cond <= NIAG_COND_EQ;  Zero <= '1'; Neg <= '0'; wait for 1 ns;
        step; chk(PC, x"00000014", "17. EQ with Z=1 -> taken");

        Rst <= '1'; wait for 3 ns; Rst <= '0';
        Cond <= NIAG_COND_EQ;  Zero <= '0'; Neg <= '0'; wait for 1 ns;
        step; chk(PC, x"00000004", "18. EQ with Z=0 -> not taken, NSA");

        Rst <= '1'; wait for 3 ns; Rst <= '0';
        Cond <= NIAG_COND_LTZ; Zero <= '0'; Neg <= '1'; wait for 1 ns;
        step; chk(PC, x"00000014", "19. LTZ with N=1 -> taken");

        Rst <= '1'; wait for 3 ns; Rst <= '0';
        Cond <= NIAG_COND_GEZ; Zero <= '0'; Neg <= '1'; wait for 1 ns;
        step; chk(PC, x"00000004", "20. GEZ with N=1 -> not taken");

        Rst <= '1'; wait for 3 ns; Rst <= '0';
        Cond <= NIAG_COND_GTZ; Zero <= '1'; Neg <= '0'; wait for 1 ns;
        step; chk(PC, x"00000004", "21. GTZ with Z=1 -> NOT taken (zero is not > 0)");

        ----------------------------------------------------------------------
        -- Backward branch through the full NIAG
        ----------------------------------------------------------------------
        Rst <= '1'; wait for 3 ns; Rst <= '0';
        Sel <= NIAG_SEL_ABS; Index <= "00" & x"00000C"; Cond <= NIAG_COND_NONE;
        wait for 1 ns; step;
        chk(PC, x"00000030", "22. positioned at 0x30");

        Sel <= NIAG_SEL_REL; Cond <= NIAG_COND_NONE;
        Xtnd32 <= x"FFFFFFF0";              -- -4 instructions
        wait for 1 ns;
        chk(NSA, x"00000034", "23. NSA at 0x30");
        step;
        chk(PC, x"00000024", "24. backward branch -4 lands at 0x24");

        if errors = 0 then
            report "PASS - Lab 8: all 24 checks passed." severity note;
        else
            report "FAILED - Lab 8: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
