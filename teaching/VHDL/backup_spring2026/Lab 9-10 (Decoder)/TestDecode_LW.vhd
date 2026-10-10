library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

library EE_362_ALU;
use EE_362_ALU.ALU_Pkg.all;

entity TestDecode_LW is
end entity;

architecture tb of TestDecode_LW is
    signal Instruction : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal CtrlSgnls   : CTRL_SIGNL_REC;
begin
    UUT : entity work.Decode_LW
        port map(
            Instruction => Instruction,
            CtrlSgnls   => CtrlSgnls
        );

    stim : process
    begin
        -- Valid LW: LW R5, 0x0004(R3)
        Instruction <= "10001100011001010000000000000100";
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_ADD report "LW: ALU_func mismatch" severity error;
        assert CtrlSgnls.ALU_Asel = ALU_ASEL_IMMED report "LW: ALU_Asel mismatch" severity error;
        assert CtrlSgnls.DM_rw    = DM_RW_RD report "LW: DM_rw mismatch" severity error;
        assert CtrlSgnls.DM_en    = DM_EN_ENABLE report "LW: DM_en mismatch" severity error;
        assert CtrlSgnls.RF_Dsel  = RF_DSEL_MEM report "LW: RF_Dsel mismatch" severity error;
        assert CtrlSgnls.RF_Wsel  = RF_WSEL_RT report "LW: RF_Wsel mismatch" severity error;
        assert CtrlSgnls.IR_Xsel  = IR_XSEL_SIGN report "LW: IR_Xsel mismatch" severity error;

        Instruction <= (others => '1');
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_FLOAT report "LW: expected float output on invalid instruction" severity error;

        wait;
    end process;
end architecture;