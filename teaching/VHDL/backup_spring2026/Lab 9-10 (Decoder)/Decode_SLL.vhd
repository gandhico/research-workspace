-------------------------------------------------------------------------------------
-- File: Decode_SLL.vhd
-- Purpose: Student decoder for the SLL instruction
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.DecodeLogic_Pkg.all;
use work.ALU_Pkg.all;

entity Decode_SLL is
    port(
        Instruction : in  STD_LOGIC_VECTOR(31 downto 0);
        CtrlSgnls   : out CTRL_SIGNL_REC
    );
end entity;

architecture Behavioral of Decode_SLL is
    signal IR : R_INSTRUCTION;
begin
    IR <= IR_to_Rtype(Instruction);

    process(Instruction, IR)
    begin
        if ((IR.R_OPCODE = CPU_SLL_OPCODE) and (IR.R_FUNC = CPU_SLL_FUNC)) then
            -- SLL rd, rt, shift
            -- rd <- rt << shift
            CtrlSgnls.ALU_func  <= ALU_FUNC_SLL;
            CtrlSgnls.ALU_Asel  <= ALU_ASEL_AOUT;
            CtrlSgnls.ALU_Ssel  <= ALU_SSEL_RS;
            CtrlSgnls.DM_strb   <= DM_STRB_HOLD;
            CtrlSgnls.DM_rw     <= DM_RW_FLOAT;
            CtrlSgnls.IR_Xsel   <= IR_XSEL_FLOAT;
            CtrlSgnls.IR_Xlsft  <= IR_XLSFT_FLOAT;
            CtrlSgnls.IR_strb   <= IR_STRB_STROBE;
            CtrlSgnls.NIAG_sel  <= NIAG_SEL_NSA;
            CtrlSgnls.NIAG_strb <= NIAG_STRB_STROBE;
            CtrlSgnls.DM_en     <= DM_EN_DISABLE;
            CtrlSgnls.NIAG_cond <= NIAG_COND_NONE;
            CtrlSgnls.RF_Dsel   <= RF_DSEL_ALU;
            CtrlSgnls.RF_strb   <= RF_STRB_STROBE;
            CtrlSgnls.RF_Wsel   <= RF_WSEL_RD;
            CtrlSgnls.RF_oe     <= RF_OE_HiZ;
        else
            CtrlSgnls <= CtrlSgnls_Float;
        end if;
    end process;
end architecture;
