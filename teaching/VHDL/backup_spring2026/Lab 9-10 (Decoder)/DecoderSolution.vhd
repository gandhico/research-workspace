library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.DecodeLogic_Pkg.all;
use work.ALU_Pkg.all;

entity Decoder is
    port(
        Instruction : in  STD_LOGIC_VECTOR(31 downto 0);
        CtrlSgnls   : out CTRL_SIGNL_REC
    );
end entity;

architecture Behavioral of Decoder is
    signal Ctrl_ADDI : CTRL_SIGNL_REC;
    signal Ctrl_AND  : CTRL_SIGNL_REC;
    signal Ctrl_J    : CTRL_SIGNL_REC;
    signal Ctrl_LW   : CTRL_SIGNL_REC;
    signal Ctrl_SLL  : CTRL_SIGNL_REC;
begin
    U_ADDI : entity work.Decode_ADDI port map(Instruction => Instruction, CtrlSgnls => Ctrl_ADDI);
    U_AND  : entity work.Decode_AND  port map(Instruction => Instruction, CtrlSgnls => Ctrl_AND);
    U_J    : entity work.Decode_J    port map(Instruction => Instruction, CtrlSgnls => Ctrl_J);
    U_LW   : entity work.Decode_LW   port map(Instruction => Instruction, CtrlSgnls => Ctrl_LW);
    U_SLL  : entity work.Decode_SLL  port map(Instruction => Instruction, CtrlSgnls => Ctrl_SLL);

    process(Ctrl_ADDI, Ctrl_AND, Ctrl_J, Ctrl_LW, Ctrl_SLL)
    begin
        CtrlSgnls <= CtrlSgnls_Float;

        if Ctrl_ADDI /= CtrlSgnls_Float then
            CtrlSgnls <= Ctrl_ADDI;
        elsif Ctrl_AND /= CtrlSgnls_Float then
            CtrlSgnls <= Ctrl_AND;
        elsif Ctrl_J /= CtrlSgnls_Float then
            CtrlSgnls <= Ctrl_J;
        elsif Ctrl_LW /= CtrlSgnls_Float then
            CtrlSgnls <= Ctrl_LW;
        elsif Ctrl_SLL /= CtrlSgnls_Float then
            CtrlSgnls <= Ctrl_SLL;
        end if;
    end process;
end architecture;
