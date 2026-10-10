library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.DecodeLogic_Pkg.all;
use work.ALU_Pkg.all;

entity TestDecode_J is
end entity;

architecture tb of TestDecode_J is
    signal Instruction : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal CtrlSgnls   : CTRL_SIGNL_REC;
begin
    UUT : entity work.Decode_J
        port map(
            Instruction => Instruction,
            CtrlSgnls   => CtrlSgnls
        );

    stim : process
    begin
        -- Valid J with arbitrary target
        Instruction <= "00001000000000000000000000111111";
        wait for 10 ns;
        assert CtrlSgnls.NIAG_sel  = NIAG_SEL_ABS report "J: NIAG_sel mismatch" severity error;
        assert CtrlSgnls.NIAG_strb = NIAG_STRB_STROBE report "J: NIAG_strb mismatch" severity error;
        assert CtrlSgnls.NIAG_cond = NIAG_COND_NONE report "J: NIAG_cond mismatch" severity error;
        assert CtrlSgnls.RF_strb   = RF_STRB_HOLD report "J: RF_strb mismatch" severity error;
        assert CtrlSgnls.DM_en     = DM_EN_DISABLE report "J: DM_en mismatch" severity error;

        Instruction <= (others => '1');
        wait for 10 ns;
        assert CtrlSgnls.NIAG_sel = NIAG_SEL_FLOAT report "J: expected float output on invalid instruction" severity error;

        wait;
    end process;
end architecture;
