library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.ALU_Pkg.all;
use work.DecodeLogic_Pkg.all;

entity Decoder is
    Port (
        Instruction : in  STD_LOGIC_VECTOR(31 downto 0);
        CtrlSgnls   : out CTRL_SIGNL_REC
    );
end Decoder;

architecture Behavioral of Decoder is
    signal IR_R : R_INSTRUCTION;
    signal IR_I : I_INSTRUCTION;
    signal IR_J : J_INSTRUCTION;

    function default_ctrl return CTRL_SIGNL_REC is
        variable c : CTRL_SIGNL_REC;
    begin
        c := CtrlSgnls_Float;
        c.ALU_Asel  := ALU_ASEL_AOUT;
        c.DM_strb   := DM_STRB_HOLD;
        c.DM_rw     := DM_RW_RD;
        c.DM_en     := DM_EN_DISABLE;
        c.IR_Xsel   := IR_XSEL_ZERO;
        c.IR_Xlsft  := IR_XLSFT_TWO;
        c.IR_strb   := IR_STRB_STROBE;
        c.NIAG_sel  := NIAG_SEL_NSA;
        c.NIAG_strb := NIAG_STRB_STROBE;
        c.NIAG_cond := NIAG_COND_NONE;
        c.RF_Dsel   := RF_DSEL_ALU;
        c.RF_strb   := RF_STRB_HOLD;
        c.RF_Wsel   := RF_WSEL_RD;
        c.RF_oe     := RF_OE_HiZ;
        return c;
    end function;
begin
    IR_R <= IR_to_Rtype(Instruction);
    IR_I <= IR_to_Itype(Instruction);
    IR_J <= IR_to_Jtype(Instruction);

    process(Instruction, IR_R, IR_I, IR_J)
        variable c : CTRL_SIGNL_REC;
    begin
        c := default_ctrl;

        -- R-type ADD
        if (IR_R.R_OPCODE = CPU_ADD_OPCODE) and (IR_R.R_FUNC = CPU_ADD_FUNC) then
            c.ALU_func := ALU_FUNC_ADD;
            c.ALU_Asel := ALU_ASEL_AOUT;
            c.RF_Dsel  := RF_DSEL_ALU;
            c.RF_strb  := RF_STRB_STROBE;
            c.RF_Wsel  := RF_WSEL_RD;

        -- I-type ADDI
        elsif IR_I.I_OPCODE = CPU_ADDI_OPCODE then
            c.ALU_func := ALU_FUNC_ADD;
            c.ALU_Asel := ALU_ASEL_IMMED;
            c.IR_Xsel  := IR_XSEL_SIGN;
            c.IR_Xlsft := IR_XLSFT_NONE;
            c.RF_Dsel  := RF_DSEL_ALU;
            c.RF_strb  := RF_STRB_STROBE;
            c.RF_Wsel  := RF_WSEL_RT;

        -- LUI (used like a simple immediate load in this lab)
        elsif IR_I.I_OPCODE = CPU_LUI_OPCODE then
            c.ALU_func := ALU_FUNC_ADD;
            c.ALU_Asel := ALU_ASEL_IMMED;
            c.IR_Xsel  := IR_XSEL_ZERO;
            c.IR_Xlsft := IR_XLSFT_NONE;
            c.RF_Dsel  := RF_DSEL_ALU;
            c.RF_strb  := RF_STRB_STROBE;
            c.RF_Wsel  := RF_WSEL_RT;

        -- BLEZ rs, offset
        elsif IR_I.I_OPCODE = CPU_BLEZ_OPCODE then
            c.ALU_func := ALU_FUNC_ADD;  -- rs + r0, so flags reflect rs
            c.ALU_Asel := ALU_ASEL_AOUT; -- Aout comes from rt = r0 for BLEZ
            c.IR_Xsel  := IR_XSEL_SIGN;
            c.IR_Xlsft := IR_XLSFT_TWO;
            c.NIAG_sel := NIAG_SEL_REL;
            c.NIAG_cond:= NIAG_COND_LEZ;

        -- J target
        elsif IR_J.J_OPCODE = CPU_J_OPCODE then
            c.NIAG_sel := NIAG_SEL_ABS;
            c.NIAG_cond:= NIAG_COND_NONE;

        -- R-type SLL
        elsif (IR_R.R_OPCODE = CPU_SLL_OPCODE) and (IR_R.R_FUNC = CPU_SLL_FUNC) then
            c.ALU_func := ALU_FUNC_SLL;
            c.ALU_Asel := ALU_ASEL_AOUT;
            c.ALU_Ssel := ALU_SSEL_RS; -- choose IR shift amount
            c.RF_Dsel  := RF_DSEL_ALU;
            c.RF_strb  := RF_STRB_STROBE;
            c.RF_Wsel  := RF_WSEL_RD;

        -- SW rt, offset(rs)
        elsif IR_I.I_OPCODE = CPU_SW_OPCODE then
            c.ALU_func := ALU_FUNC_ADD;
            c.ALU_Asel := ALU_ASEL_IMMED;
            c.IR_Xsel  := IR_XSEL_SIGN;
            c.IR_Xlsft := IR_XLSFT_NONE;
            c.DM_strb  := DM_STRB_STORE;
            c.DM_rw    := DM_RW_WR;
            c.DM_en    := DM_EN_ENABLE;
            c.RF_oe    := RF_OE_DRIVE;

        -- Optional LW support, useful for debugging.
        elsif IR_I.I_OPCODE = CPU_LW_OPCODE then
            c.ALU_func := ALU_FUNC_ADD;
            c.ALU_Asel := ALU_ASEL_IMMED;
            c.IR_Xsel  := IR_XSEL_SIGN;
            c.IR_Xlsft := IR_XLSFT_NONE;
            c.DM_rw    := DM_RW_RD;
            c.DM_en    := DM_EN_ENABLE;
            c.RF_Dsel  := RF_DSEL_MEM;
            c.RF_strb  := RF_STRB_STROBE;
            c.RF_Wsel  := RF_WSEL_RT;
        end if;

        CtrlSgnls <= c;
    end process;
end Behavioral;
