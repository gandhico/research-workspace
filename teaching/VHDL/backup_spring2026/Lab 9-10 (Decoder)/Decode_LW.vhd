-------------------------------------------------------------------------------------
-- File: Decode_LW.vhd
-- Purpose: Student decoder for the LW instruction
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.DecodeLogic_Pkg.all;
use work.ALU_Pkg.all;

entity Decode_LW is
    port(
        Instruction : in  STD_LOGIC_VECTOR(31 downto 0);
        CtrlSgnls   : out CTRL_SIGNL_REC
    );
end entity;

architecture Behavioral of Decode_LW is
    signal IR : I_INSTRUCTION;
begin
    IR <= IR_to_Itype(Instruction);

    process(Instruction, IR)
    begin
        if (IR.I_OPCODE = CPU_LW_OPCODE) then
            -- LW rt, immed(rs)
            -- rt <- MEM[rs + sign_extended(immed)]
            CtrlSgnls.ALU_func  <= ALU_FUNC_ADD;
            CtrlSgnls.ALU_Asel  <= ALU_ASEL_IMMED;
            CtrlSgnls.ALU_Ssel  <= ALU_SSEL_FLOAT;
            CtrlSgnls.DM_strb   <= DM_STRB_HOLD;
            CtrlSgnls.DM_rw     <= DM_RW_RD;
            CtrlSgnls.IR_Xsel   <= IR_XSEL_SIGN;
            CtrlSgnls.IR_Xlsft  <= IR_XLSFT_NONE;
            CtrlSgnls.IR_strb   <= IR_STRB_STROBE;
            CtrlSgnls.NIAG_sel  <= NIAG_SEL_NSA;
            CtrlSgnls.NIAG_strb <= NIAG_STRB_STROBE;
            CtrlSgnls.DM_en     <= DM_EN_ENABLE;
            CtrlSgnls.NIAG_cond <= NIAG_COND_NONE;
            CtrlSgnls.RF_Dsel   <= RF_DSEL_MEM;
            CtrlSgnls.RF_strb   <= RF_STRB_STROBE;
            CtrlSgnls.RF_Wsel   <= RF_WSEL_RT;
            CtrlSgnls.RF_oe     <= RF_OE_HiZ;
        else
            CtrlSgnls <= CtrlSgnls_Float;
        end if;
    end process;
end architecture;
