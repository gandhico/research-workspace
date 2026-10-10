--------------------------------------------------------------------------------
-- EE 362 - Lab 10, Example 1 - Field extraction on real instructions
--
-- Every instruction here is out of the Lab 12 program. Decode each one by hand
-- against the format diagrams before you look at the expected values.
--
-- The last check is the interesting one: the SAME bits mean different things
-- depending on the format. Fields do not have meanings on their own - the
-- opcode gives them meanings.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity fields_tb is
end entity fields_tb;

architecture test of fields_tb is

    signal Instr  : std_logic_vector(31 downto 0) := (others => '0');
    signal Opcode : std_logic_vector(5 downto 0);
    signal RS, RT, RD, SA : std_logic_vector(4 downto 0);
    signal Func   : std_logic_vector(5 downto 0);
    signal Immed  : std_logic_vector(15 downto 0);
    signal Index  : std_logic_vector(25 downto 0);

begin

    DUT : entity work.fields
        port map (Instr => Instr, Opcode => Opcode, RS => RS, RT => RT,
                  RD => RD, SA => SA, Func => Func, Immed => Immed,
                  Index => Index);

    stimulus : process

        variable errors : natural := 0;

        procedure chk (cond : in boolean; msg : in string) is
        begin
            if not cond then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure chk;

    begin

        ----------------------------------------------------------------------
        -- ADDI r1, r1, -1     at 0x08     I-type
        ----------------------------------------------------------------------
        Instr <= x"2021FFFF"; wait for 10 ns;
        chk(Opcode = "001000", "1. ADDI opcode is 001000");
        chk(RS     = "00001",  "2. ADDI rs is r1");
        chk(RT     = "00001",  "3. ADDI rt is r1 - the DESTINATION for I-type");
        chk(Immed  = x"FFFF",  "4. ADDI immediate is -1");

        ----------------------------------------------------------------------
        -- SLL r2, r2, 1       at 0x10     R-type
        ----------------------------------------------------------------------
        Instr <= x"00021040"; wait for 10 ns;
        chk(Opcode = "000000", "5. SLL opcode is SPECIAL - the func field decides");
        chk(Func   = "000000", "6. SLL func is 000000");
        chk(RT     = "00010",  "7. SLL rt is r2 - the SOURCE for a shift");
        chk(RD     = "00010",  "8. SLL rd is r2 - the DESTINATION for R-type");
        chk(SA     = "00001",  "9. SLL shift amount is 1");

        ----------------------------------------------------------------------
        -- J 0x08              at 0x14     J-type
        ----------------------------------------------------------------------
        Instr <= x"08000002"; wait for 10 ns;
        chk(Opcode = "000010", "10. J opcode is 000010");
        chk(Index  = "00" & x"000002", "11. J index is 2");

        ----------------------------------------------------------------------
        -- SW r2, 0(r0)        at 0x18     I-type
        ----------------------------------------------------------------------
        Instr <= x"AC020000"; wait for 10 ns;
        chk(Opcode = "101011", "12. SW opcode is 101011");
        chk(RS     = "00000",  "13. SW rs is r0 - the base address register");
        chk(RT     = "00010",  "14. SW rt is r2 - the value being STORED");
        chk(Immed  = x"0000",  "15. SW offset is 0");

        ----------------------------------------------------------------------
        -- THE POINT: the same bits, read as different formats.
        -- For J 0x08 the extractor also produced rs, rt, rd, sa and func
        -- values. They are meaningless - but the hardware computed them anyway.
        ----------------------------------------------------------------------
        Instr <= x"08000002"; wait for 10 ns;
        chk(RS = "00000" and RT = "00000",
            "16. a J instruction still 'has' rs and rt - they just mean nothing");

        report "Field extraction is unconditional: all three formats are pulled" &
               " out of every instruction, always. The OPCODE is what gives the" &
               " fields meaning - which is why it lives at a fixed position."
            severity note;

        if errors = 0 then
            report "PASS - fields: all 16 checks passed." severity note;
        else
            report "FAILED - fields: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
