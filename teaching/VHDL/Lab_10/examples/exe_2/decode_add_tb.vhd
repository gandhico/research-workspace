--------------------------------------------------------------------------------
-- EE 362 - Lab 10, Example 2 - Checking a control bundle
--
-- Testing a decoder is different from testing a datapath component. There is
-- no waveform to squint at: you feed in an encoded instruction and assert the
-- exact value of every control signal.
--
-- THE SECOND VECTOR IS THE IMPORTANT ONE. An unimplemented opcode must produce
-- the SAFE DEFAULT - no register write, no memory write, PC advances. A decoder
-- that does something arbitrary with an instruction it does not recognise is a
-- CPU that corrupts memory when it hits bad data.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity decode_add_tb is
end entity decode_add_tb;

architecture test of decode_add_tb is

    signal Instr : std_logic_vector(31 downto 0) := (others => '0');
    signal Ctrl  : CTRL_REC;

begin

    DUT : entity work.decode_add
        port map (Instr => Instr, Ctrl => Ctrl);

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
        -- ADD r3, r1, r2  =  000000 00001 00010 00011 00000 100000
        --                 =  0x00221820
        ----------------------------------------------------------------------
        Instr <= x"00221820"; wait for 10 ns;

        chk(Ctrl.ALU_func = ALU_FUNC_ADD,   "1. ALU does an addition");
        chk(Ctrl.ALU_Asel = ALU_ASEL_AOUT,  "2. ALU A input from the register file");
        chk(Ctrl.RF_Dsel  = RF_DSEL_ALU,    "3. write-back data comes from the ALU");
        chk(Ctrl.RF_Wsel  = RF_WSEL_RD,     "4. destination is the rd field");
        chk(Ctrl.RF_strb  = RF_STRB_STROBE, "5. the register write actually happens");

        -- ...and the eleven defaults, still safe
        chk(Ctrl.DM_en     = DM_EN_DISABLE,   "6. memory is not touched");
        chk(Ctrl.DM_strb   = DM_STRB_HOLD,    "7. nothing is stored");
        chk(Ctrl.RF_oe     = RF_OE_HIZ,       "8. the memory bus is not driven");
        chk(Ctrl.NIAG_sel  = NIAG_SEL_NSA,    "9. PC advances sequentially");
        chk(Ctrl.NIAG_cond = NIAG_COND_NONE,  "10. unconditionally");

        ----------------------------------------------------------------------
        -- AN UNIMPLEMENTED OPCODE. The safe default, every time.
        ----------------------------------------------------------------------
        Instr <= x"FC000000"; wait for 10 ns;      -- opcode 111111

        chk(Ctrl.RF_strb  = RF_STRB_HOLD,    "11. unknown opcode: NO register write");
        chk(Ctrl.DM_strb  = DM_STRB_HOLD,    "12. unknown opcode: NO memory write");
        chk(Ctrl.DM_en    = DM_EN_DISABLE,   "13. unknown opcode: memory disabled");
        chk(Ctrl.RF_oe    = RF_OE_HIZ,       "14. unknown opcode: bus not driven");
        chk(Ctrl.NIAG_sel = NIAG_SEL_NSA,    "15. unknown opcode: PC still advances");

        report "A decoder that does something arbitrary with an instruction it" &
               " does not recognise is a CPU that corrupts memory when it hits" &
               " bad data. The default is a safety property, not tidiness."
            severity note;

        ----------------------------------------------------------------------
        -- SPECIAL opcode but a different func: also not ADD.
        -- This is why R-type needs BOTH fields checked.
        ----------------------------------------------------------------------
        Instr <= x"00221825"; wait for 10 ns;      -- SPECIAL, func 100101 (OR)

        chk(Ctrl.RF_strb = RF_STRB_HOLD,
            "16. SPECIAL with a different func is not ADD - func must be checked too");

        if errors = 0 then
            report "PASS - decode_add: all 16 checks passed." severity note;
        else
            report "FAILED - decode_add: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
