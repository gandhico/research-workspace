library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.DecodeLogic_Pkg.all;
use work.ALU_Pkg.all;

entity TestDecode_SLL is
end entity;

architecture tb of TestDecode_SLL is
    signal Instruction : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal CtrlSgnls   : CTRL_SIGNL_REC;
begin
    UUT : entity work.Decode_SLL
        port map(
            Instruction => Instruction,
            CtrlSgnls   => CtrlSgnls
        );

    stim : process
    begin
        -- Valid SLL: SLL R5, R4, 6
        Instruction <= "00000000000001000010100110000000";
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_SLL report "SLL: ALU_func mismatch" severity error;
        assert CtrlSgnls.ALU_Asel = ALU_ASEL_AOUT report "SLL: ALU_Asel mismatch" severity error;
        assert CtrlSgnls.ALU_Ssel = ALU_SSEL_RS report "SLL: ALU_Ssel mismatch" severity error;
        assert CtrlSgnls.RF_Dsel  = RF_DSEL_ALU report "SLL: RF_Dsel mismatch" severity error;
        assert CtrlSgnls.RF_Wsel  = RF_WSEL_RD report "SLL: RF_Wsel mismatch" severity error;
        assert CtrlSgnls.NIAG_sel = NIAG_SEL_NSA report "SLL: NIAG_sel mismatch" severity error;

        Instruction <= (others => '1');
        wait for 10 ns;
        assert CtrlSgnls.ALU_func = ALU_FUNC_FLOAT report "SLL: expected float output on invalid instruction" severity error;

        wait;
    end process;
end architecture;
