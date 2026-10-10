--------------------------------------------------------------------------------
-- EE 362 - Lab 11, Example 3 - Checking the control-flow rows
--
-- Two checks are worth staring at:
--
--   BLEZ must have IR_Xlsft = TWO. It is the only instruction in this CPU that
--   scales its immediate. Miss it and every branch lands a quarter of the way
--   to its target - Lab 7's "off by a factor", arriving through the decoder
--   instead of through the adder.
--
--   BLEZ and J must both have RF_strb = HOLD. Control flow writes no register.
--   Leave either at STROBE and the branch silently corrupts one.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity decode_flow_tb is
end entity decode_flow_tb;

architecture test of decode_flow_tb is

    signal Instr : std_logic_vector(31 downto 0) := (others => '0');
    signal Ctrl  : CTRL_REC;

    constant I_BLEZ : std_logic_vector(31 downto 0) := x"18200002"; -- BLEZ r1,+2
    constant I_J    : std_logic_vector(31 downto 0) := x"08000002"; -- J 0x08

begin

    DUT : entity work.decode_flow
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
        -- BLEZ r1, +2   - the loop exit in the Lab 12 program
        ----------------------------------------------------------------------
        Instr <= I_BLEZ; wait for 10 ns;

        chk(Ctrl.NIAG_sel  = NIAG_SEL_REL,  "1. BLEZ: relative target");
        chk(Ctrl.NIAG_cond = NIAG_COND_LEZ, "2. BLEZ: taken when result <= 0");
        chk(Ctrl.IR_Xsel   = IR_XSEL_SIGN,  "3. BLEZ: signed offset");

        chk(Ctrl.IR_Xlsft  = IR_XLSFT_TWO,
            "4. *** BLEZ: the offset is SCALED BY 4 - the only one that is ***");

        chk(Ctrl.ALU_func  = ALU_FUNC_ADD,
            "5. BLEZ: the ALU runs, to produce the FLAGS that decide the branch");

        chk(Ctrl.RF_strb   = RF_STRB_HOLD,
            "6. *** BLEZ writes no register - RF_strb must be HOLD ***");

        chk(Ctrl.DM_en     = DM_EN_DISABLE, "7. BLEZ: memory untouched");
        chk(Ctrl.RF_oe     = RF_OE_HIZ,     "8. BLEZ: bus not driven");

        ----------------------------------------------------------------------
        -- J 0x08   - the jump that closes the loop
        ----------------------------------------------------------------------
        Instr <= I_J; wait for 10 ns;

        chk(Ctrl.NIAG_sel  = NIAG_SEL_ABS,   "9.  J: absolute target");
        chk(Ctrl.NIAG_cond = NIAG_COND_NONE, "10. J: unconditional");
        chk(Ctrl.RF_strb   = RF_STRB_HOLD,   "11. J writes no register");
        chk(Ctrl.DM_en     = DM_EN_DISABLE,  "12. J: memory untouched");
        chk(Ctrl.RF_oe     = RF_OE_HIZ,      "13. J: bus not driven");
        chk(Ctrl.NIAG_strb = NIAG_STRB_STROBE, "14. J: the PC is still loaded");

        report "J changes exactly TWO control signals and leaves fourteen at" &
               " their defaults. A control unit is mostly 'do nothing' with a" &
               " few exceptions per row - which is why default-first is the" &
               " natural shape of the problem, not a convenience." severity note;

        report "BLEZ is the ONLY instruction in this CPU with IR_Xlsft = TWO." &
               " Miss it and every branch lands a quarter of the way to its" &
               " target - Lab 7's 'off by a factor', arriving through the" &
               " decoder instead of the adder." severity note;

        if errors = 0 then
            report "PASS - decode_flow: all 14 checks passed." severity note;
        else
            report "FAILED - decode_flow: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
