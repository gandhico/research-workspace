--------------------------------------------------------------------------------
-- EE 362 - Lab 7 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- 20 checks. The three components are wired together exactly as the CPU wires
-- them: ImmedXtnd feeds NIAG_Rel, NIAG_NSA feeds both NIAG_Rel and the PC's
-- NextPC input.
--
-- Every branch target here is hand-computable and several come straight out of
-- the Lab 12 ROM program.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab7 is
end entity tb_Lab7;

architecture test of tb_Lab7 is

    constant PERIOD : time := 20 ns;

    -- PC and its inputs
    signal NextPC : std_logic_vector(31 downto 0) := (others => '0');
    signal Strb, Rst, clk : std_logic := '0';
    signal PC : std_logic_vector(31 downto 0);

    -- address arithmetic
    signal NSA, Rel : std_logic_vector(31 downto 0);

    -- the shared extender
    signal Immed16 : std_logic_vector(15 downto 0) := (others => '0');
    signal Xsel, Xlsft : std_logic := '1';       -- sign-extend, x4: branch mode
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

        -- Load the PC on the next rising edge
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
        -- Reset behaviour
        ----------------------------------------------------------------------
        Rst <= '1'; wait for 3 ns;
        chk(PC,  x"00000000", "1. reset vector is 0");
        chk(NSA, x"00000004", "2. NSA is available immediately after reset");
        Rst <= '0';

        ----------------------------------------------------------------------
        -- Sequential execution
        ----------------------------------------------------------------------
        setpc(x"00000004");
        chk(PC,  x"00000004", "3. PC loaded with 0x04");
        chk(NSA, x"00000008", "4. NSA tracks PC combinationally");

        setpc(x"00000008");
        chk(NSA, x"0000000C", "5. NSA again, no clock delay");

        ----------------------------------------------------------------------
        -- THE REAL BRANCH: BLEZ r1,+2 at 0x0C in the Lab 12 program
        --   NSA = 0x10, offset = 2x4 = 8, target = 0x18 (the SW)
        ----------------------------------------------------------------------
        setpc(x"0000000C");
        Immed16 <= x"0002"; wait for 5 ns;
        chk(NSA,    x"00000010", "6. NSA for the real BLEZ");
        chk(Xtnd32, x"00000008", "7. offset +2 scaled to +8 bytes");
        chk(Rel,    x"00000018", "8. BLEZ target is 0x18 - the loop exit");

        ----------------------------------------------------------------------
        -- Offset zero: the branch target is the next instruction
        ----------------------------------------------------------------------
        Immed16 <= x"0000"; wait for 5 ns;
        chk(Rel, x"00000010", "9. offset 0 targets the next instruction");

        ----------------------------------------------------------------------
        -- BACKWARD branches - these catch sign-extension errors
        ----------------------------------------------------------------------
        Immed16 <= x"FFFF"; wait for 5 ns;              -- -1
        chk(Xtnd32, x"FFFFFFFC", "10. offset -1 scaled to -4 bytes");
        chk(Rel,    x"0000000C", "11. -1 lands back on this instruction");

        Immed16 <= x"FFFC"; wait for 5 ns;              -- -4
        chk(Xtnd32, x"FFFFFFF0", "12. offset -4 scaled to -16 bytes");
        chk(Rel,    x"00000000", "13. -4 lands at address 0");

        ----------------------------------------------------------------------
        -- Boundary offsets
        ----------------------------------------------------------------------
        setpc(x"00000000");
        Immed16 <= x"7FFF"; wait for 5 ns;              -- largest positive
        chk(Rel, x"00020000", "14. largest forward offset");

        setpc(x"00100000");
        Immed16 <= x"8000"; wait for 5 ns;              -- most negative
        chk(Rel, x"000E0004", "15. most negative offset");

        ----------------------------------------------------------------------
        -- The PC is a REGISTER, not a counter: it can jump anywhere
        ----------------------------------------------------------------------
        setpc(x"DEADBEE0");
        chk(PC,  x"DEADBEE0", "16. PC accepts an arbitrary address");
        chk(NSA, x"DEADBEE4", "17. and NSA follows");

        ----------------------------------------------------------------------
        -- Strb low: a stall. The edge arrives and the PC holds.
        ----------------------------------------------------------------------
        wait until falling_edge(clk);
        NextPC <= x"00000000"; Strb <= '0';
        wait until rising_edge(clk); wait for 1 ns;
        chk(PC, x"DEADBEE0", "18. Strb low: PC holds through the edge");

        ----------------------------------------------------------------------
        -- Asynchronous reset, asserted between edges
        ----------------------------------------------------------------------
        wait for 3 ns;
        Rst <= '1'; wait for 1 ns;
        chk(PC,  x"00000000", "19. async reset acts between edges");
        chk(NSA, x"00000004", "20. and NSA follows immediately");
        Rst <= '0';

        if errors = 0 then
            report "PASS - Lab 7: all 20 checks passed." severity note;
        else
            report "FAILED - Lab 7: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
