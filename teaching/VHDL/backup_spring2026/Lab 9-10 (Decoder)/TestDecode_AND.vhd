library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.DecodeLogic_Pkg.all;
use work.ALU_Pkg.all;

entity TestDecode_AND is
end entity;

architecture tb of TestDecode_AND is
    signal Instruction : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal CtrlSgnls   : CTRL_SIGNL_REC;
begin
    UUT : entity work.Decode_AND
        port map(
            Instruction => Instruction,
            CtrlSgnls   => CtrlSgnls
        );

    stim : process
    begin
        -- Valid AND: AND R5, R3, R4
        Instruction <= "00000000011001000010100000100100";
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_AND report "AND: ALU_func mismatch" severity error;
        assert CtrlSgnls.ALU_Asel = ALU_ASEL_AOUT report "AND: ALU_Asel mismatch" severity error;
        assert CtrlSgnls.RF_Dsel  = RF_DSEL_ALU report "AND: RF_Dsel mismatch" severity error;
        assert CtrlSgnls.RF_Wsel  = RF_WSEL_RD report "AND: RF_Wsel mismatch" severity error;
        assert CtrlSgnls.DM_en    = DM_EN_DISABLE report "AND: DM_en mismatch" severity error;
        assert CtrlSgnls.NIAG_sel = NIAG_SEL_NSA report "AND: NIAG_sel mismatch" severity error;

        Instruction <= (others => '1');
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_FLOAT report "AND: expected float output on invalid instruction" severity error;

        wait;
    end process;
end architecture;
