library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.DecodeLogic_Pkg.all;
use work.ALU_Pkg.all;

entity TestDecode_ADDI is
end entity;

architecture tb of TestDecode_ADDI is
    signal Instruction : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal CtrlSgnls   : CTRL_SIGNL_REC;
begin
    UUT : entity work.Decode_ADDI
        port map(
            Instruction => Instruction,
            CtrlSgnls   => CtrlSgnls
        );

    stim : process
    begin
        -- Valid ADDI: ADDI R5, R3, 0x0004
        Instruction <= "00100000011001010000000000000100";
        wait for 10 ns;
        assert CtrlSgnls.ALU_func  = ALU_FUNC_ADD report "ADDI: ALU_func mismatch" severity error;
        assert CtrlSgnls.ALU_Asel  = ALU_ASEL_IMMED report "ADDI: ALU_Asel mismatch" severity error;
        assert CtrlSgnls.IR_Xsel   = IR_XSEL_SIGN report "ADDI: IR_Xsel mismatch" severity error;
        assert CtrlSgnls.IR_Xlsft  = IR_XLSFT_NONE report "ADDI: IR_Xlsft mismatch" severity error;
        assert CtrlSgnls.RF_Dsel   = RF_DSEL_ALU report "ADDI: RF_Dsel mismatch" severity error;
        assert CtrlSgnls.RF_Wsel   = RF_WSEL_RT report "ADDI: RF_Wsel mismatch" severity error;
        assert CtrlSgnls.RF_strb   = RF_STRB_STROBE report "ADDI: RF_strb mismatch" severity error;
        assert CtrlSgnls.NIAG_sel  = NIAG_SEL_NSA report "ADDI: NIAG_sel mismatch" severity error;

        -- Invalid instruction: decoder should float
        Instruction <= (others => '1');
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_FLOAT report "ADDI: expected float output on invalid instruction" severity error;

        wait;
    end process;
end architecture;
