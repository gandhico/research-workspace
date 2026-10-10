-------------------------------------------------------------------------------------
-- File: Decode_J.vhd
-- Purpose: Student decoder for the J instruction
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.DecodeLogic_Pkg.all;
use work.ALU_Pkg.all;

entity Decode_J is
    port(
        Instruction : in  STD_LOGIC_VECTOR(31 downto 0);
        CtrlSgnls   : out CTRL_SIGNL_REC
    );
end entity;

architecture Behavioral of Decode_J is
    signal IR : J_INSTRUCTION;
begin
    IR <= IR_to_Jtype(Instruction);

    process(Instruction, IR)
    begin
        if (IR.J_OPCODE = CPU_J_OPCODE) then
            -- J target
            -- PC <- absolute target address
            CtrlSgnls.ALU_func  <= ALU_FUNC_FLOAT;
            CtrlSgnls.ALU_Asel  <= ALU_ASEL_FLOAT;
            CtrlSgnls.ALU_Ssel  <= ALU_SSEL_FLOAT;
            CtrlSgnls.DM_strb   <= DM_STRB_HOLD;
            CtrlSgnls.DM_rw     <= DM_RW_FLOAT;
            CtrlSgnls.IR_Xsel   <= IR_XSEL_FLOAT;
            CtrlSgnls.IR_Xlsft  <= IR_XLSFT_FLOAT;
            CtrlSgnls.IR_strb   <= IR_STRB_STROBE;
            CtrlSgnls.NIAG_sel  <= NIAG_SEL_ABS;
            CtrlSgnls.NIAG_strb <= NIAG_STRB_STROBE;
            CtrlSgnls.DM_en     <= DM_EN_DISABLE;
            CtrlSgnls.NIAG_cond <= NIAG_COND_NONE;
            CtrlSgnls.RF_Dsel   <= RF_DSEL_FLOAT;
            CtrlSgnls.RF_strb   <= RF_STRB_HOLD;
            CtrlSgnls.RF_Wsel   <= RF_WSEL_FLOAT;
            CtrlSgnls.RF_oe     <= RF_OE_HiZ;
        else
            CtrlSgnls <= CtrlSgnls_Float;
        end if;
    end process;
end architecture;
