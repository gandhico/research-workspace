library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.DecodeLogic_Pkg.all;
use work.ALU_Pkg.all;

entity TestDecoder is
end entity;

architecture tb of TestDecoder is
    signal Instruction : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal CtrlSgnls   : CTRL_SIGNL_REC;
begin
    UUT : entity work.Decoder
        port map(
            Instruction => Instruction,
            CtrlSgnls   => CtrlSgnls
        );

    stim : process
    begin
        -- ADDI R5, R6, 4
        Instruction <= "00100000110001010000000000000100";
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_ADD report "Decoder ADDI: ALU_func mismatch" severity error;
        assert CtrlSgnls.RF_Wsel  = RF_WSEL_RT    report "Decoder ADDI: RF_Wsel mismatch" severity error;

        -- AND R9, R3, R4
        Instruction <= "00000000011001000100100000100100";
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_AND report "Decoder AND: ALU_func mismatch" severity error;
        assert CtrlSgnls.RF_Wsel  = RF_WSEL_RD   report "Decoder AND: RF_Wsel mismatch" severity error;

        -- J target
        Instruction <= "00001000000000000000000000111111";
        wait for 10 ns;
        assert CtrlSgnls.NIAG_sel = NIAG_SEL_ABS  report "Decoder J: NIAG_sel mismatch" severity error;
        assert CtrlSgnls.RF_strb  = RF_STRB_HOLD  report "Decoder J: RF_strb mismatch" severity error;

        -- LW R5, 4(R3)
        Instruction <= "10001100011001010000000000000100";
        wait for 10 ns;
        assert CtrlSgnls.DM_rw   = DM_RW_RD      report "Decoder LW: DM_rw mismatch" severity error;
        assert CtrlSgnls.RF_Dsel = RF_DSEL_MEM   report "Decoder LW: RF_Dsel mismatch" severity error;

        -- SLL R9, R4, 3
        Instruction <= "00000000000001000100100011000000";
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_SLL report "Decoder SLL: ALU_func mismatch" severity error;
        assert CtrlSgnls.ALU_Ssel = ALU_SSEL_RS  report "Decoder SLL: ALU_Ssel mismatch" severity error;

        -- Invalid instruction should float
        Instruction <= (others => '1');
        wait for 10 ns;
        assert CtrlSgnls = CtrlSgnls_Float report "Decoder: expected float output on invalid instruction" severity error;

        wait;
    end process;
end architecture;
