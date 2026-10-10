--------------------------------------------------------------------------------
-- EE 362 - Lab 11, Example 1 - Where LW and SW agree, and where they must not
--
-- The first group of checks proves they agree on the address arithmetic.
-- The second group proves they are opposite on everything after it.
--
-- The two checks worth staring at are the SW ones: RF_strb must be HOLD, and
-- RF_oe must be DRIVE. Those two signals are the difference between storing
-- and corrupting.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity decode_lw_sw_tb is
end entity decode_lw_sw_tb;

architecture test of decode_lw_sw_tb is

    signal Instr : std_logic_vector(31 downto 0) := (others => '0');
    signal Ctrl  : CTRL_REC;

    constant I_LW : std_logic_vector(31 downto 0) := x"8C220004"; -- LW r2,4(r1)
    constant I_SW : std_logic_vector(31 downto 0) := x"AC020000"; -- SW r2,0(r0)

begin

    DUT : entity work.decode_lw_sw
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
        -- LW: the address arithmetic, then the load
        ----------------------------------------------------------------------
        Instr <= I_LW; wait for 10 ns;
        chk(Ctrl.ALU_func = ALU_FUNC_ADD,   "1. LW: the ALU ADDS - same as ADDI");
        chk(Ctrl.ALU_Asel = ALU_ASEL_IMMED, "2. LW: A input is the offset");
        chk(Ctrl.IR_Xsel  = IR_XSEL_SIGN,   "3. LW: offsets can be negative");
        chk(Ctrl.IR_Xlsft = IR_XLSFT_NONE,  "4. LW: a byte offset, NOT scaled");
        chk(Ctrl.DM_en    = DM_EN_ENABLE,   "5. LW: memory enabled");
        chk(Ctrl.DM_rw    = DM_RW_RD,       "6. LW: reading");
        chk(Ctrl.RF_Dsel  = RF_DSEL_MEM,    "7. LW: write-back comes from MEMORY");
        chk(Ctrl.RF_strb  = RF_STRB_STROBE, "8. LW: a register IS written");
        chk(Ctrl.RF_oe    = RF_OE_HIZ,      "9. LW: register file does NOT drive the bus");

        ----------------------------------------------------------------------
        -- SW: the SAME address arithmetic
        ----------------------------------------------------------------------
        Instr <= I_SW; wait for 10 ns;
        chk(Ctrl.ALU_func = ALU_FUNC_ADD,   "10. SW: the ALU ADDS - shared adder");
        chk(Ctrl.ALU_Asel = ALU_ASEL_IMMED, "11. SW: A input is the offset");
        chk(Ctrl.IR_Xsel  = IR_XSEL_SIGN,   "12. SW: sign-extended offset");

        ----------------------------------------------------------------------
        -- ...and the opposite of everything after it
        ----------------------------------------------------------------------
        chk(Ctrl.DM_rw   = DM_RW_WR,       "13. SW: writing");
        chk(Ctrl.DM_strb = DM_STRB_STORE,  "14. SW: the store actually happens");

        -- THE TWO THAT MATTER
        chk(Ctrl.RF_strb = RF_STRB_HOLD,
            "15. *** SW writes MEMORY, not a register - RF_strb must be HOLD ***");
        chk(Ctrl.RF_oe   = RF_OE_DRIVE,
            "16. *** SW: the register file must DRIVE the memory bus ***");

        report "If RF_strb were left STROBE for SW, every store would silently" &
               " corrupt a register - and because the store itself still works," &
               " the program would fail somewhere else entirely." severity note;

        report "If RF_oe were left HiZ, the store would write 'Z' - which the" &
               " RAM happily stores, and the data is gone." severity note;

        report "Notice ALU_func and ALU_Asel are IDENTICAL for LW, SW and ADDI." &
               " Computing a+b and computing base+offset are the same operation," &
               " so they share one adder. That is why a load costs no more" &
               " hardware than an add." severity note;

        if errors = 0 then
            report "PASS - decode_lw_sw: all 16 checks passed." severity note;
        else
            report "FAILED - decode_lw_sw: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
